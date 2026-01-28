import logging
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.const import UnitOfTemperature, REVOLUTIONS_PER_MINUTE
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Setup Saey sensoren."""
    entities = [
        SaeySensor("Saey Rookgas", "flu_gas_temp", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, "mdi:thermometer"),
        SaeySensor("Saey RPM", "exh_fan_speed", REVOLUTIONS_PER_MINUTE, None, "mdi:fan"),
        SaeySensor("Saey Pellet", "pellet_speed", None, None, "mdi:speedometer"),
        SaeySensor("Saey Status", "burner_status", None, None, "mdi:fire")
    ]
    async_add_entities(entities, True)

class SaeySensor(SensorEntity):
    def __init__(self, name, attribute, unit, device_class, icon):
        self._name = name
        self._attribute = attribute
        self._unit = unit
        self._attr_device_class = device_class
        self._icon = icon

    @property
    def name(self):
        return self._name

    @property
    def icon(self):
        return self._icon

    @property
    def native_unit_of_measurement(self):
        return self._unit

    @property
    def native_value(self):
        # Zoek de climate entiteit die door de integratie is aangemaakt
        state = self.hass.states.get("climate.pelletstove")
        if state and self._attribute in state.attributes:
            val = state.attributes[self._attribute]
            if isinstance(val, str):
                # Haalt '115 °C' -> '115' of '1400 rpm' -> '1400'
                return val.split(' ')[0]
            return val
        return None