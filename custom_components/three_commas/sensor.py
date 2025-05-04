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
        key="total_usd_profit",
        name="Total USD Profit",
        icon="mdi:currency-usd",
        native_unit_of_measurement=CURRENCY_DOLLAR,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="usd_amount",
        name="USD Balance",
        icon="mdi:currency-usd",
        native_unit_of_measurement=CURRENCY_DOLLAR,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="day_profit_usd",
        name="Daily USD Profit",
        icon="mdi:currency-usd",
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

    # Add sensors for each account
    for account_id in coordinator.data:
        for entity_description in ENTITY_DESCRIPTIONS:
            sensors.append(
                ThreeCommasSensor(
                    coordinator=coordinator,
                    account_id=account_id,
                    entity_description=entity_description,
                )
            )

    async_add_entities(sensors)


class ThreeCommasSensor(ThreeCommasEntity, SensorEntity):
    """3Commas sensor entity."""

    def __init__(
        self,
        coordinator: ThreeCommasDataUpdateCoordinator,
        account_id: str,
        entity_description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, account_id)
        self.entity_description = entity_description
        self._attr_unique_id = f"{DOMAIN}_{account_id}_{entity_description.key}"
        self._attr_name = f"3Commas {entity_description.name}"

    @property
    def native_value(self) -> float | None:
        """Return the sensor value."""
        if not self.account_data:
            return None

        # Get the value based on the entity key
        value_obj = self.account_data.get(self.entity_description.key)
        if not value_obj:
            return None

        # Extract the amount from the value object
        if isinstance(value_obj, dict) and "amount" in value_obj:
            try:
                return float(cast(str, value_obj["amount"]))
            except (ValueError, TypeError):
                LOGGER.error("Unable to convert %s to float", value_obj["amount"])
                return None

        # Try direct extraction for non-object values
        try:
            return float(cast(str, value_obj))
        except (ValueError, TypeError):
            LOGGER.error("Unable to convert %s to float", value_obj)
            return None
