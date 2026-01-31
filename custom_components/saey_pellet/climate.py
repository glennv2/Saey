import logging
from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature, HVACMode, HVACAction
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import UnitOfTemperature, ATTR_TEMPERATURE # <-- Deze ontbrak
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SaeyPelletDevice(coordinator)], True)

class SaeyPelletDevice(CoordinatorEntity, ClimateEntity): 
    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator)
        self._attr_name = "Saey Pelletkachel"
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_climate"
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS   
        self._attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
        self._attr_fan_modes = ["1", "2", "3", "4", "5"]
        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE | 
            ClimateEntityFeature.TURN_OFF | 
            ClimateEntityFeature.TURN_ON |
            ClimateEntityFeature.FAN_MODE
        )

    @property
    def current_temperature(self):
        return self.coordinator.data.get("room_temp")

    @property
    def target_temperature(self):
        return self.coordinator.data.get("target_temp")

    @property
    def hvac_mode(self):
        status = self.coordinator.data.get("burner_status", "Off")
        return HVACMode.OFF if status == "Off" else HVACMode.HEAT

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
        lvl = self.coordinator.data.get("pellet_speed")
        return str(lvl) if lvl else "1"

    @property
    def extra_state_attributes(self):
        return {
            "exhaust_fan_speed": self.coordinator.data.get("exhaust_fan_speed", 0),
            "pellet_speed": self.coordinator.data.get("pellet_speed", 0),
            "error_status": self.coordinator.data.get("error_code", "OK")
        }

    async def async_set_temperature(self, **kwargs):
        temp = kwargs.get(ATTR_TEMPERATURE)
        if temp is None: return
        try:
            temp_int = int(temp)
            checksum = temp_int + 75
            cmd = f"RF2{temp_int:02X}0{checksum:02X}"            
            _LOGGER.info(f"Temperatuur instellen op {temp_int} met commando {cmd}")
            await self.coordinator.api.send_cmd(cmd)
            await self.coordinator.async_request_refresh()
        except ValueError:
             _LOGGER.error(f"Ongeldige temperatuur: {temp}")

    async def async_set_hvac_mode(self, hvac_mode):
        if hvac_mode == HVACMode.HEAT:
            await self.coordinator.api.send_cmd("RF001059")
        else:
            await self.coordinator.api.send_cmd("RF000058")
        await self.coordinator.async_request_refresh()

    async def async_set_fan_mode(self, fan_mode):
        try:
            level = int(fan_mode)
            checksum = level + 88
            cmd = f"RF00{level}0{checksum:02X}"
            
            _LOGGER.info(f"Ventilator (vermogen) naar stand {level} met commando {cmd}")
            await self.coordinator.api.send_cmd(cmd)
            await self.coordinator.async_request_refresh()
        except ValueError:
            _LOGGER.error(f"Ongeldige fan mode: {fan_mode}")