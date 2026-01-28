import logging
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.const import UnitOfTemperature, REVOLUTIONS_PER_MINUTE
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Setup sensoren via de coordinator (Config Entry)."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        SaeySensor(coordinator, "Saey Rookgas", "flue_gas_temp", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, "mdi:thermometer"),
        SaeySensor(coordinator, "Saey RPM", "fan_speed", REVOLUTIONS_PER_MINUTE, None, "mdi:fan"),
        SaeySensor(coordinator, "Saey Status", "burner_status", None, None, "mdi:fire")
    ]
    async_add_entities(entities)

class SaeySensor(CoordinatorEntity, SensorEntity):
    """Representatie van een Saey Sensor gekoppeld aan de Coordinator."""
    
    def __init__(self, coordinator, name, attribute, unit, device_class, icon):
        """Initialiseer de sensor en koppel aan de coordinator."""
        super().__init__(coordinator)
        self._attr_name = name
        self._attribute = attribute
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_icon = icon
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{attribute}"

    @property
    def native_value(self):
        """Haal de waarde direct uit de coordinator data dictionary."""
        return self.coordinator.data.get(self._attribute)