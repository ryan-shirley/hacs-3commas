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
    ) -> None:
        """Initialize entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}"

        # Set up device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, "3commas_bot_stats")},
            name="3Commas Bot Stats",
            manufacturer="3Commas",
        )

    @property
    def profit_data(self):
        """Return profit data."""
        return self.coordinator.data.get("profit_data", {})
