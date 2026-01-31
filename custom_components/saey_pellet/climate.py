from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature, HVACMode, HVACAction
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    """Setup via de Config Entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SaeyPelletDevice(coordinator, entry)])

class SaeyPelletDevice(CoordinatorEntity, ClimateEntity): 
    def __init__(self, coordinator, entry) -> None:
        """Koppel de coordinator aan deze entiteit."""
        super().__init__(coordinator)
        self._attr_name = entry.data.get("name", "Saey Pelletstove")
        self._attr_unique_id = f"{entry.entry_id}_climate"
        
        self._attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
        self._attr_fan_modes = ["1", "2", "3", "4", "5"]
        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE | 
            ClimateEntityFeature.TURN_OFF | 
            ClimateEntityFeature.TURN_ON |
            ClimateEntityFeature.FAN_MODE
        )
        self._attr_temperature_unit = "°C"
        self._attr_target_temperature_step = 1.0

    @property
    def current_temperature(self):
        return self.coordinator.data.get("room_temp")

    @property
    def target_temperature(self):
        return self.coordinator.data.get("target_temp")

    @property
    def hvac_mode(self):
        status = self.coordinator.data.get("burner_status")
        if status in ["Off", "Stove power off", "Eco Idle"]:
            return HVACMode.OFF
        return HVACMode.HEAT

    @property
    def hvac_action(self):
        status = self.coordinator.data.get("burner_status")
        heating_statuses = ["Ignition starting", "Ignition starting, fire on", "Flame On", "Stove On", "Stove On, Clean", "Turbo Mode"]
        if status in heating_statuses:
            return HVACAction.HEATING
        if status == "Eco Idle":
            return HVACAction.IDLE
        return HVACAction.OFF
    
    @property
    def fan_mode(self):
        """Huidig vermogensniveau."""
        return str(self.coordinator.data.get("power_level", "1"))

    @property
    def extra_state_attributes(self):
        """Toon het toerental en pelletsnelheid in de attributenlijst."""
        return {
            "exhaust_fan_speed": self.coordinator.data.get("exhaust_fan_speed", 0),
            "pellet_speed": self.coordinator.data.get("pellet_speed", 0),
            "error_status": self.coordinator.data.get("error_code", "OK")
        }

    async def async_set_temperature(self, **kwargs):
        temp = kwargs.get("temperature")
        if temp is None: return
        set_point_hex = f"{int(temp):02X}"
        await self.coordinator.api.send_cmd(f"F2{set_point_hex}0")
        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode):
        if hvac_mode == HVACMode.OFF:
            await self.coordinator.api.send_cmd("F0000")
        elif hvac_mode == HVACMode.HEAT:
            await self.coordinator.api.send_cmd("F0010")
        await self.coordinator.async_request_refresh()

    async def async_set_fan_mode(self, fan_mode):
        """Stuur het nieuwe vermogensniveau naar de kachel."""
        try:
            level = int(fan_mode)
            
            cmd = f"F100{level}0"
            
            _LOGGER.debug("Sending fan mode command: %s", cmd)
            await self.coordinator.api.send_cmd(cmd)
            
            await self.coordinator.async_request_refresh()
        except Exception as e:
            _LOGGER.error("Fout bij instellen fan_mode: %s", e)
            raise