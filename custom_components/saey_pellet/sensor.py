import logging
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.const import UnitOfTemperature, REVOLUTIONS_PER_MINUTE, PERCENTAGE
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        SaeySensor(coordinator, "Saey Kamer Temperatuur", "room_temp", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, "mdi:home-thermometer"),
        SaeySensor(coordinator, "Saey Rookgas Temperatuur", "flue_gas_temp", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, "mdi:thermometer-high"),
        SaeySensor(coordinator, "Saey Toerental ventilator", "exhaust_fan_speed", REVOLUTIONS_PER_MINUTE, None, "mdi:fan"),
        SaeySensor(coordinator, "Saey Pelletsnelheid", "pellet_speed", None, None, "mdi:speedometer"),
        SaeySensor(coordinator, "Saey Status", "burner_status", None, None, "mdi:fire"),
        SaeySensor(coordinator, "Saey Foutmelding", "error_code", None, None, "mdi:alert-circle"),
        SaeySensor(coordinator, "Saey Totale Branduren", "total_hours", "h", None, "mdi:timer-outline")
    ]
    async_add_entities(entities)

class SaeySensor(CoordinatorEntity, SensorEntity):
    
    def __init__(self, coordinator, name, attribute, unit, device_class, icon):
        super().__init__(coordinator)
        self._attr_name = name
        self._attribute = attribute
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_icon = icon
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{attribute}"

    @property
    def native_value(self):
        val = self.coordinator.data.get(self._attribute)
        if val is None:
            return "N/A"
        return val

    @property
    def extra_state_attributes(self):
        if self._attribute == "burner_status":
            return {
                "last_update": self.coordinator.last_update_success,
                "stove_type": "Duepi EVO Base"
            }
        return None