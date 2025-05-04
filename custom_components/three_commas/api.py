"""3Commas API Client."""

from __future__ import annotations

import hashlib
import hmac
import socket
import time
from typing import Any

import aiohttp
import async_timeout

from .const import BASE_URL


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

    async def async_get_account_info(self, account_id: str) -> Any:
        """Get account information from the API."""
        endpoint = f"/v1/accounts/{account_id}"
        return await self._api_wrapper(
            method="get",
            endpoint=endpoint,
        )

    async def async_get_accounts(self) -> Any:
        """Get list of accounts from the API."""
        endpoint = "/v1/accounts"
        return await self._api_wrapper(
            method="get",
            endpoint=endpoint,
        )

    def _generate_signature(self, request_path: str) -> dict:
        """Generate signature for API request."""
        timestamp = int(time.time() * 1000)
        signature = hmac.new(
            self._api_secret.encode(),
            f"{timestamp}{request_path}".encode(),
            hashlib.sha256,
        ).hexdigest()

        return {
            "APIKEY": self._api_key,
            "Signature": signature,
            "Timestamp": str(timestamp),
        }

    async def _api_wrapper(
        self,
        method: str,
        endpoint: str,
        data: dict | None = None,
        additional_headers: dict | None = None,
    ) -> Any:
        """Get information from the API."""
        url = f"{BASE_URL}{endpoint}"
        headers = self._generate_signature(endpoint)

        if additional_headers:
            headers.update(additional_headers)

        try:
            async with async_timeout.timeout(10):
                response = await self._session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                )
                _verify_response_or_raise(response)
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
