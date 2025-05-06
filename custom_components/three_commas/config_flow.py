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
from .const import (
    AUTH_METHOD_HMAC,
    AUTH_METHOD_RSA,
    CONF_API_KEY,
    CONF_API_SECRET,
    CONF_AUTH_METHOD,
    CONF_PRIVATE_KEY,
    CONF_USER_MODE,
    DOMAIN,
    LOGGER,
    USER_MODE_PAPER,
    USER_MODE_REAL,
)


class ThreeCommasFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Three Commas."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle a flow initialized by the user."""
        errors = {}

        if user_input is not None:
            auth_method = user_input.get(CONF_AUTH_METHOD, AUTH_METHOD_HMAC)

            if auth_method == AUTH_METHOD_HMAC:
                # Continue with HMAC authentication
                return await self.async_step_hmac(user_input)
            elif auth_method == AUTH_METHOD_RSA:
                # Continue with RSA authentication
                return await self.async_step_rsa(user_input)

            errors["base"] = "invalid_auth_method"

        # Initial form to select authentication method
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_AUTH_METHOD,
                        default=AUTH_METHOD_HMAC,
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                {
                                    "value": AUTH_METHOD_HMAC,
                                    "label": "HMAC (API Secret)",
                                },
                                {"value": AUTH_METHOD_RSA, "label": "RSA Key"},
                            ],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        ),
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_hmac(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle the HMAC authentication step."""
        errors = {}

        if (
            user_input is not None
            and CONF_API_KEY in user_input
            and CONF_API_SECRET in user_input
            and CONF_USER_MODE in user_input
        ):
            try:
                await self._test_credentials_hmac(
                    api_key=user_input[CONF_API_KEY],
                    api_secret=user_input[CONF_API_SECRET],
                    user_mode=user_input[CONF_USER_MODE],
                )

                # Store auth method in user_input
                user_input[CONF_AUTH_METHOD] = AUTH_METHOD_HMAC

                return self.async_create_entry(
                    title="3Commas",
                    data=user_input,
                )
            except ThreeCommasApiClientAuthenticationError as exception:
                LOGGER.warning(exception)
                errors["base"] = "auth"
            except ThreeCommasApiClientCommunicationError as exception:
                LOGGER.error(exception)
                errors["base"] = "connection"
            except ThreeCommasApiClientError as exception:
                LOGGER.exception(exception)
                errors["base"] = "unknown"

        # HMAC authentication form
        return self.async_show_form(
            step_id="hmac",
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
                    vol.Required(
                        CONF_USER_MODE,
                        default=(user_input or {}).get(CONF_USER_MODE, USER_MODE_PAPER),
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                {
                                    "value": USER_MODE_PAPER,
                                    "label": "Paper Trading",
                                },
                                {
                                    "value": USER_MODE_REAL,
                                    "label": "Real Trading",
                                },
                            ],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        ),
                    ),
                },
            ),
            errors=errors,
        )

    async def async_step_rsa(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle the RSA authentication step."""
        errors = {}

        if (
            user_input is not None
            and CONF_API_KEY in user_input
            and CONF_PRIVATE_KEY in user_input
            and CONF_USER_MODE in user_input
        ):
            try:
                await self._test_credentials_rsa(
                    api_key=user_input[CONF_API_KEY],
                    private_key=user_input[CONF_PRIVATE_KEY],
                    user_mode=user_input[CONF_USER_MODE],
                )

                # Store auth method in user_input
                user_input[CONF_AUTH_METHOD] = AUTH_METHOD_RSA

                return self.async_create_entry(
                    title="3Commas",
                    data=user_input,
                )
            except ThreeCommasApiClientAuthenticationError as exception:
                LOGGER.warning(exception)
                errors["base"] = "auth"
            except ThreeCommasApiClientCommunicationError as exception:
                LOGGER.error(exception)
                errors["base"] = "connection"
            except ThreeCommasApiClientError as exception:
                LOGGER.exception(exception)
                errors["base"] = "unknown"
            except ImportError as exception:
                LOGGER.error(exception)
                errors["base"] = "missing_dependency"

        # RSA authentication form
        return self.async_show_form(
            step_id="rsa",
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
                    vol.Required(CONF_PRIVATE_KEY): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                            multiline=True,
                        ),
                    ),
                    vol.Required(
                        CONF_USER_MODE,
                        default=(user_input or {}).get(CONF_USER_MODE, USER_MODE_PAPER),
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                {
                                    "value": USER_MODE_PAPER,
                                    "label": "Paper Trading",
                                },
                                {
                                    "value": USER_MODE_REAL,
                                    "label": "Real Trading",
                                },
                            ],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        ),
                    ),
                },
            ),
            errors=errors,
        )

    async def _test_credentials_hmac(
        self, api_key: str, api_secret: str, user_mode: str
    ) -> None:
        """Validate HMAC credentials."""
        client = ThreeCommasApiClient(
            api_key=api_key,
            auth_method=AUTH_METHOD_HMAC,
            api_secret=api_secret,
            user_mode=user_mode,
            session=async_create_clientsession(self.hass),
        )
        await client.async_get_bot_stats()

    async def _test_credentials_rsa(
        self, api_key: str, private_key: str, user_mode: str
    ) -> None:
        """Validate RSA credentials."""
        client = ThreeCommasApiClient(
            api_key=api_key,
            auth_method=AUTH_METHOD_RSA,
            private_key=private_key,
            user_mode=user_mode,
            session=async_create_clientsession(self.hass),
        )
        await client.async_get_bot_stats()
