"""Base entity class for 3Commas integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN
from .coordinator import ThreeCommasDataUpdateCoordinator


class ThreeCommasEntity(CoordinatorEntity[ThreeCommasDataUpdateCoordinator]):
    """Base entity for 3Commas integration."""

    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        coordinator: ThreeCommasDataUpdateCoordinator,
        account_id: str,
    ) -> None:
        """Initialize entity."""
        super().__init__(coordinator)
        self._account_id = account_id
        self._attr_unique_id = f"{DOMAIN}_{account_id}"

        # Set up device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, account_id)},
            name=f"3Commas Account {account_id}",
            manufacturer="3Commas",
        )

    @property
    def account_data(self):
        """Return account data."""
        return self.coordinator.data.get(self._account_id, {})
