"""Sensor platform for 3commas integration."""

from __future__ import annotations

from typing import Any, cast

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CURRENCY_DOLLAR
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, LOGGER
from .coordinator import ThreeCommasDataUpdateCoordinator
from .entity import ThreeCommasEntity

ENTITY_DESCRIPTIONS = (
    SensorEntityDescription(
        key="overall_usd_profit",
        name="Overall USD Profit",
        icon="mdi:currency-usd",
        native_unit_of_measurement=CURRENCY_DOLLAR,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="today_usd_profit",
        name="Today's USD Profit",
        icon="mdi:currency-usd",
        native_unit_of_measurement=CURRENCY_DOLLAR,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="active_deals_usd_profit",
        name="Active Deals USD Profit",
        icon="mdi:currency-usd",
        native_unit_of_measurement=CURRENCY_DOLLAR,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="funds_locked_in_active_deals",
        name="Funds Locked in Active Deals",
        icon="mdi:currency-usd-off",
        native_unit_of_measurement=CURRENCY_DOLLAR,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    sensors = []

    # Add sensors for profit data
    for entity_description in ENTITY_DESCRIPTIONS:
        sensors.append(
            ThreeCommasSensor(
                coordinator=coordinator,
                entity_description=entity_description,
            )
        )

    async_add_entities(sensors)


class ThreeCommasSensor(ThreeCommasEntity, SensorEntity):
    """3Commas sensor entity."""

    def __init__(
        self,
        coordinator: ThreeCommasDataUpdateCoordinator,
        entity_description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        entry_id = coordinator.config_entry.entry_id if coordinator.config_entry else ""
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{entity_description.key}"
        self._attr_name = f"3Commas {entity_description.name}"

    @property
    def native_value(self) -> float | None:
        """Return the sensor value."""
        if not self.profit_data:
            return None

        value = self.profit_data.get(self.entity_description.key)
        if value is None:
            return None

        try:
            return float(cast(str, value))
        except (ValueError, TypeError):
            LOGGER.error("Unable to convert %s to float", value)
            return None
