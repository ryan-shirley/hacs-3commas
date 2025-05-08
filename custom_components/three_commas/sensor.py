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
from homeassistant.helpers.device_registry import DeviceInfo

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
        state_class=SensorStateClass.TOTAL,
    ),
    SensorEntityDescription(
        key="today_usd_profit",
        name="Today's USD Profit",
        icon="mdi:currency-usd",
        native_unit_of_measurement=CURRENCY_DOLLAR,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
    ),
    SensorEntityDescription(
        key="active_deals_usd_profit",
        name="Active Deals USD Profit",
        icon="mdi:currency-usd",
        native_unit_of_measurement=CURRENCY_DOLLAR,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
    ),
    SensorEntityDescription(
        key="funds_locked_in_active_deals",
        name="Funds Locked in Active Deals",
        icon="mdi:currency-usd-off",
        native_unit_of_measurement=CURRENCY_DOLLAR,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
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

    # Add sensors for account balances and utilization
    accounts = coordinator.data.get("accounts", {})
    for account_id, account_data in accounts.items():
        # Add balance sensor
        sensors.append(
            ThreeCommasAccountBalanceSensor(
                coordinator=coordinator,
                account_id=account_id,
                account_data=account_data,
            )
        )

        # Add utilization sensor
        sensors.append(
            ThreeCommasAccountUtilizationSensor(
                coordinator=coordinator,
                account_id=account_id,
                account_data=account_data,
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


class ThreeCommasAccountBalanceSensor(ThreeCommasEntity, SensorEntity):
    """3Commas account balance sensor entity."""

    def __init__(
        self,
        coordinator: ThreeCommasDataUpdateCoordinator,
        account_id: str,
        account_data: dict,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.account_id = account_id
        self.account_data = account_data
        entry_id = coordinator.config_entry.entry_id if coordinator.config_entry else ""

        # Set unique ID and name
        account_name = account_data.get("name", "Unknown")
        exchange_name = account_data.get("exchange_name", "Unknown Exchange")
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_account_{account_id}_balance"
        self._attr_name = f"{account_name} Balance ({exchange_name} 3Commas)"

        # Set entity properties
        self._attr_icon = "mdi:currency-usd"
        self._attr_native_unit_of_measurement = CURRENCY_DOLLAR
        self._attr_device_class = SensorDeviceClass.MONETARY
        self._attr_state_class = SensorStateClass.TOTAL

        # Set up device info for this specific account
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"3commas_account_{account_id}")},
            name=f"3Commas {exchange_name} - {account_name}",
            manufacturer="3Commas",
        )

    @property
    def native_value(self) -> float | None:
        """Return the sensor value."""
        # Get the latest account data
        account_data = self.accounts_data.get(self.account_id, {})

        # If no data is available, return None
        if not account_data:
            return None

        # Extract the USD amount
        value = account_data.get("usd_amount")
        if value is None:
            return None

        try:
            # If the value is a string or complex object, convert it
            if isinstance(value, dict) and "amount" in value:
                return float(str(value["amount"]))
            return float(str(value))
        except (ValueError, TypeError):
            LOGGER.error("Unable to convert account balance %s to float", value)
            return None


class ThreeCommasAccountUtilizationSensor(ThreeCommasEntity, SensorEntity):
    """3Commas account utilization percentage sensor entity."""

    def __init__(
        self,
        coordinator: ThreeCommasDataUpdateCoordinator,
        account_id: str,
        account_data: dict,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.account_id = account_id
        self.account_data = account_data
        entry_id = coordinator.config_entry.entry_id if coordinator.config_entry else ""

        # Set unique ID and name
        account_name = account_data.get("name", "Unknown")
        exchange_name = account_data.get("exchange_name", "Unknown Exchange")
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_account_{account_id}_utilization"
        self._attr_name = f"{account_name} Utilisation ({exchange_name} 3Commas)"

        # Set entity properties
        self._attr_icon = "mdi:percent"
        self._attr_native_unit_of_measurement = "%"
        self._attr_state_class = SensorStateClass.MEASUREMENT

        # Set up device info for this specific account (same device as balance sensor)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"3commas_account_{account_id}")},
            name=f"3Commas {exchange_name} - {account_name}",
            manufacturer="3Commas",
        )

    @property
    def native_value(self) -> float | None:
        """Return the sensor value."""
        # Get the latest account data
        account_data = self.accounts_data.get(self.account_id, {})

        # If no data is available, return None
        if not account_data:
            return None

        # Return the utilization percentage
        value = account_data.get("utilization_percentage")
        if value is None:
            return None

        try:
            # Convert to float and ensure it's rounded to 2 decimal places
            return round(float(value), 2)
        except (ValueError, TypeError):
            LOGGER.error("Unable to convert utilization percentage %s to float", value)
            return None
