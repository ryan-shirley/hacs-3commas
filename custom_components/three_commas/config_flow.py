"""Adds config flow for Three Commas integration."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import (
    ThreeCommasApiClient,
    ThreeCommasApiClientAuthenticationError,
    ThreeCommasApiClientCommunicationError,
    ThreeCommasApiClientError,
)
from .const import CONF_API_KEY, CONF_API_SECRET, DOMAIN, LOGGER


class ThreeCommasFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Three Commas."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}
        if user_input is not None:
            try:
                await self._test_credentials(
                    api_key=user_input[CONF_API_KEY],
                    api_secret=user_input[CONF_API_SECRET],
                )
            except ThreeCommasApiClientAuthenticationError as exception:
                LOGGER.warning(exception)
                _errors["base"] = "auth"
            except ThreeCommasApiClientCommunicationError as exception:
                LOGGER.error(exception)
                _errors["base"] = "connection"
            except ThreeCommasApiClientError as exception:
                LOGGER.exception(exception)
                _errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title="3Commas",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_API_KEY,
                        default=(user_input or {}).get(CONF_API_KEY, ""),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        ),
                    ),
                    vol.Required(CONF_API_SECRET): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD,
                        ),
                    ),
                },
            ),
            errors=_errors,
        )

    async def _test_credentials(self, api_key: str, api_secret: str) -> None:
        """Validate credentials."""
        client = ThreeCommasApiClient(
            api_key=api_key,
            api_secret=api_secret,
            session=async_create_clientsession(self.hass),
        )
        await client.async_get_accounts()
