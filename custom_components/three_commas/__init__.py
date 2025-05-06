"""
Custom integration to integrate 3Commas with Home Assistant.

For more details about this integration, please refer to the documentation.
"""

from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ThreeCommasApiClient
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
    UPDATE_INTERVAL,
)
from .coordinator import ThreeCommasDataUpdateCoordinator

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up 3Commas from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Extract configuration data
    api_key = entry.data[CONF_API_KEY]
    auth_method = entry.data.get(CONF_AUTH_METHOD, AUTH_METHOD_HMAC)
    api_secret = entry.data.get(CONF_API_SECRET)
    private_key = entry.data.get(CONF_PRIVATE_KEY)
    user_mode = entry.data.get(CONF_USER_MODE)

    # Create API client based on authentication method
    if auth_method == AUTH_METHOD_RSA:
        api_client = ThreeCommasApiClient(
            api_key=api_key,
            auth_method=AUTH_METHOD_RSA,
            private_key=private_key,
            user_mode=user_mode,
            session=async_get_clientsession(hass),
        )
    else:
        # Default to HMAC authentication
        api_client = ThreeCommasApiClient(
            api_key=api_key,
            auth_method=AUTH_METHOD_HMAC,
            api_secret=api_secret,
            user_mode=user_mode,
            session=async_get_clientsession(hass),
        )

    coordinator = ThreeCommasDataUpdateCoordinator(
        hass=hass,
        client=api_client,
        logger=LOGGER,
        update_interval=timedelta(minutes=UPDATE_INTERVAL),
        config_entry=entry,
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store the coordinator for this entry
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Set up all platforms for this device/entry
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unloaded := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
