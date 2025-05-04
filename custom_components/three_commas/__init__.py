"""
Custom integration to integrate 3Commas with Home Assistant.

For more details about this integration, please refer to the documentation.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    ThreeCommasApiClient,
    ThreeCommasApiClientAuthenticationError,
    ThreeCommasApiClientCommunicationError,
    ThreeCommasApiClientError,
)
from .const import CONF_API_KEY, CONF_API_SECRET, DOMAIN, LOGGER
from .coordinator import ThreeCommasDataUpdateCoordinator

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up 3Commas from a config entry."""
    # Store an instance of the API client
    client = ThreeCommasApiClient(
        api_key=entry.data[CONF_API_KEY],
        api_secret=entry.data[CONF_API_SECRET],
        session=async_get_clientsession(hass),
    )

    # Create a coordinator for data updates
    coordinator = ThreeCommasDataUpdateCoordinator(
        hass=hass,
        logger=LOGGER,
        client=client,
        update_interval=timedelta(minutes=5),
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store the coordinator for this entry
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Set up all platforms for this device/entry
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    if unloaded := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
