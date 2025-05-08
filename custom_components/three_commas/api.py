"""3Commas API Client."""

from __future__ import annotations

import base64
import hashlib
import hmac
import socket
import time
from typing import Any

import aiohttp
import async_timeout

try:
    # Python >= 3.6
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives.serialization import load_pem_private_key

    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False

from .const import AUTH_METHOD_HMAC, AUTH_METHOD_RSA, BASE_URL, LOGGER


class ThreeCommasApiClientError(Exception):
    """Exception to indicate a general API error."""


class ThreeCommasApiClientCommunicationError(
    ThreeCommasApiClientError,
):
    """Exception to indicate a communication error."""


class ThreeCommasApiClientAuthenticationError(
    ThreeCommasApiClientError,
):
    """Exception to indicate an authentication error."""


def _verify_response_or_raise(response: aiohttp.ClientResponse) -> None:
    """Verify that the response is valid."""
    if response.status in (401, 403):
        msg = "Invalid credentials"
        raise ThreeCommasApiClientAuthenticationError(
            msg,
        )
    if response.status == 204:
        # 204 is No Content - it's a valid response but has no body
        return

    response.raise_for_status()


class ThreeCommasApiClient:
    """3Commas API Client."""

    def __init__(
        self,
        api_key: str,
        auth_method: str,
        api_secret: str | None = None,
        private_key: str | None = None,
        user_mode: str | None = None,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        """Initialize 3Commas API Client.

        Args:
            api_key: The 3commas API key
            auth_method: The authentication method to use (hmac or rsa)
            api_secret: The API secret (for HMAC authentication)
            private_key: The private key in PEM format (for RSA authentication)
            user_mode: The mode to use (paper or real)
            session: The aiohttp session to use
        """
        self._api_key = api_key
        self._auth_method = auth_method
        self._api_secret = api_secret
        self._private_key = private_key
        self._user_mode = user_mode
        self._session = session

        # Validate required authentication parameters
        if auth_method == AUTH_METHOD_HMAC and not api_secret:
            raise ValueError("API secret is required for HMAC authentication")
        if auth_method == AUTH_METHOD_RSA and not private_key:
            raise ValueError("Private key is required for RSA authentication")

        # Validate RSA dependencies
        if auth_method == AUTH_METHOD_RSA and not HAS_CRYPTOGRAPHY:
            raise ImportError(
                "The cryptography package is required for RSA authentication. "
                "Please install it with `pip install cryptography`."
            )

    async def async_get_bot_stats(
        self, account_id: str | None = None, bot_id: str | None = None
    ) -> Any:
        """Get DCA bot stats from the API."""
        endpoint = "/ver1/bots/stats"
        params = {}

        if account_id:
            params["account_id"] = account_id
        if bot_id:
            params["bot_id"] = bot_id

        return await self._api_wrapper(
            method="get",
            endpoint=endpoint,
            params=params,
        )

    async def async_get_accounts(self) -> Any:
        """Get list of connected exchanges and wallets from the API."""
        endpoint = "/ver1/accounts"

        return await self._api_wrapper(
            method="get",
            endpoint=endpoint,
        )

    async def async_get_bots(
        self,
        account_id: str | None = None,
        strategy: str | None = None,
        scope: str = "enabled",
    ) -> Any:
        """Get list of DCA bots from the API.

        Args:
            account_id: Filter bots by account ID
            strategy: Filter bots by strategy type (long or short)
            scope: Filter bots by scope (enabled, disabled)
        """
        endpoint = "/ver1/bots"
        params = {}

        if account_id:
            params["account_id"] = account_id
        if strategy:
            params["strategy"] = strategy
        if scope:
            params["scope"] = scope

        return await self._api_wrapper(
            method="get",
            endpoint=endpoint,
            params=params,
        )

    def _generate_hmac_signature(self, request_path: str) -> dict:
        """Generate HMAC signature for API request.

        Implements 3commas signature requirements:
        https://developers.3commas.io/quick-start/signing-a-request-using-hmac-sha256
        """
        # Log the input parameters for debugging
        LOGGER.debug("Generating HMAC signature for path: %s", request_path)

        # Create signature using HMAC-SHA256
        # The path should be the full path including query params
        signature = hmac.new(
            self._api_secret.encode(), request_path.encode(), hashlib.sha256
        ).hexdigest()

        headers = {
            "APIKEY": self._api_key,
            "Signature": signature,
        }

        LOGGER.debug("Generated HMAC headers: %s", headers)
        return headers

    def _generate_rsa_signature(self, request_path: str) -> dict:
        """Generate RSA signature for API request.

        Implements 3commas signature requirements:
        https://developers.3commas.io/quick-start/signing-a-request-using-rsa
        """
        # Log the input parameters for debugging
        LOGGER.debug("Generating RSA signature for path: %s", request_path)

        try:
            if not self._private_key:
                raise ValueError("Private key is required for RSA authentication")

            # Load the private key
            private_key_obj = load_pem_private_key(
                self._private_key.encode("utf-8"),
                password=None,
                backend=default_backend(),
            )

            # Sign the request path using the private key
            signature_bytes = private_key_obj.sign(
                request_path.encode("utf-8"),
                padding.PKCS1v15(),
                hashes.SHA256(),
            )

            # Convert the signature to base64
            signature = base64.b64encode(signature_bytes).decode("utf-8")

            headers = {
                "APIKEY": self._api_key,
                "Signature": signature,
            }

            LOGGER.debug(
                "Generated RSA headers with signature length: %d", len(signature)
            )
            return headers

        except Exception as e:
            LOGGER.error("Error generating RSA signature: %s", e)
            raise ThreeCommasApiClientAuthenticationError(
                f"Error generating RSA signature: {e}"
            ) from e

    def _generate_signature(self, request_path: str) -> dict:
        """Generate signature for API request based on authentication method."""
        if self._auth_method == AUTH_METHOD_RSA:
            return self._generate_rsa_signature(request_path)
        # Default to HMAC
        return self._generate_hmac_signature(request_path)

    async def _api_wrapper(
        self,
        method: str,
        endpoint: str,
        data: dict | None = None,
        params: dict | None = None,
        additional_headers: dict | None = None,
    ) -> Any:
        """Get information from the API."""
        url = f"{BASE_URL}{endpoint}"

        # Create query string for signature
        query_string = ""
        if params:
            query_items = []
            for key, value in sorted(params.items()):
                query_items.append(f"{key}={value}")
            if query_items:
                query_string = "?" + "&".join(query_items)

        # Generate signature with the full path including query params
        # The path for signature must include /public/api prefix
        signature_path = f"/public/api{endpoint}{query_string}"
        LOGGER.debug("Signature path: %s", signature_path)
        headers = self._generate_signature(signature_path)

        # Add Forced-Mode header if user_mode is specified
        if self._user_mode:
            headers["Forced-Mode"] = self._user_mode
            LOGGER.debug("Added Forced-Mode header: %s", self._user_mode)

        if additional_headers:
            headers.update(additional_headers)

        try:
            # Log request details for debugging
            # LOGGER.debug(
            #     "Making API request: %s %s, headers: %s, params: %s",
            #     method,
            #     url,
            #     headers,
            #     params,
            # )

            async with async_timeout.timeout(10):
                response = await self._session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                    params=params,
                )

                # Log response status for debugging
                LOGGER.debug("Got response with status: %s", response.status)

                _verify_response_or_raise(response)

                # Return empty dict for 204 responses (No Content)
                if response.status == 204:
                    return {}

                return await response.json()

        except TimeoutError as exception:
            msg = f"Timeout error fetching information - {exception}"
            raise ThreeCommasApiClientCommunicationError(
                msg,
            ) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            msg = f"Error fetching information - {exception}"
            raise ThreeCommasApiClientCommunicationError(
                msg,
            ) from exception
        except Exception as exception:  # pylint: disable=broad-except
            msg = f"Something really wrong happened! - {exception}"
            raise ThreeCommasApiClientError(
                msg,
            ) from exception
