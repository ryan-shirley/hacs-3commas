"""DataUpdateCoordinator for three_commas."""

from __future__ import annotations

from datetime import timedelta
from logging import Logger
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import ThreeCommasApiClient
from .const import DOMAIN


class ThreeCommasDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        logger: Logger,
        client: ThreeCommasApiClient,
        update_interval: timedelta,
    ) -> None:
        """Initialize."""
        self.client = client
        self.accounts = {}

        super().__init__(
            hass=hass,
            logger=logger,
            name=DOMAIN,
            update_interval=update_interval,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via API."""
        self.accounts = await self.client.async_get_accounts()
        data = {}

        for account in self.accounts:
            account_id = account.get("id")
            if account_id:
                account_info = await self.client.async_get_account_info(str(account_id))
                data[str(account_id)] = account_info

        return data
