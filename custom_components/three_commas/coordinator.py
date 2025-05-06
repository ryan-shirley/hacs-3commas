"""DataUpdateCoordinator for three_commas."""

from __future__ import annotations

from datetime import timedelta
from logging import Logger
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    ThreeCommasApiClient,
    ThreeCommasApiClientAuthenticationError,
    ThreeCommasApiClientCommunicationError,
    ThreeCommasApiClientError,
)
from .const import DOMAIN, LOGGER


class ThreeCommasDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        logger: Logger,
        client: ThreeCommasApiClient,
        update_interval: timedelta,
        config_entry=None,
    ) -> None:
        """Initialize."""
        self.client = client
        self.config_entry = config_entry

        super().__init__(
            hass=hass,
            logger=logger,
            name=DOMAIN,
            update_interval=update_interval,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via API."""
        try:
            # Fetch bot stats data
            bot_stats = await self.client.async_get_bot_stats()

            # Log the full response for debugging
            LOGGER.debug("Bot stats data: %s", bot_stats)

            # Verify that the expected data structure is present
            if not bot_stats or "profits_in_usd" not in bot_stats:
                LOGGER.warning(
                    "Missing expected data structure in bot stats response: %s",
                    bot_stats,
                )
                return {"profit_data": {}}

            # Create a simplified data structure with just the profit values
            data = {
                "profit_data": {
                    "overall_usd_profit": bot_stats.get("profits_in_usd", {}).get(
                        "overall_usd_profit"
                    ),
                    "today_usd_profit": bot_stats.get("profits_in_usd", {}).get(
                        "today_usd_profit"
                    ),
                    "active_deals_usd_profit": bot_stats.get("profits_in_usd", {}).get(
                        "active_deals_usd_profit"
                    ),
                    "funds_locked_in_active_deals": bot_stats.get(
                        "profits_in_usd", {}
                    ).get("funds_locked_in_active_deals"),
                }
            }

            return data

        except ThreeCommasApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except ThreeCommasApiClientCommunicationError as exception:
            LOGGER.error("Communication error: %s", exception)
            raise UpdateFailed(exception) from exception
        except ThreeCommasApiClientError as exception:
            LOGGER.error("Unknown error: %s", exception)
            raise UpdateFailed(exception) from exception
