"""3Commas API Client."""

from __future__ import annotations

import hashlib
import hmac
import socket
import time
from typing import Any

import aiohttp
import async_timeout

from .const import BASE_URL, LOGGER


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
        api_secret: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """Initialize 3Commas API Client."""
        self._api_key = api_key
        self._api_secret = api_secret
        self._session = session

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

    def _generate_signature(self, request_path: str) -> dict:
        """Generate signature for API request.

        Implements 3commas signature requirements:
        https://developers.3commas.io/quick-start/signing-a-request-using-hmac-sha256
        """
        # Log the input parameters for debugging
        LOGGER.debug("Generating signature for path: %s", request_path)

        # Create signature using HMAC-SHA256
        # The path should be the full path including query params
        signature = hmac.new(
            self._api_secret.encode(), request_path.encode(), hashlib.sha256
        ).hexdigest()

        headers = {
            "APIKEY": self._api_key,
            "Signature": signature,
        }

        LOGGER.debug("Generated headers: %s", headers)
        return headers

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

        if additional_headers:
            headers.update(additional_headers)

        try:
            # Log request details for debugging
            LOGGER.debug(
                "Making API request: %s %s, headers: %s, params: %s",
                method,
                url,
                headers,
                params,
            )

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
