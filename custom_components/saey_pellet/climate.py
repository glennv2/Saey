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
        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE | 
            ClimateEntityFeature.TURN_OFF | 
            ClimateEntityFeature.TURN_ON
        )
        self._attr_temperature_unit = "°C"

    @property
    def current_temperature(self):
        return self.coordinator.data.get("room_temp")

    @property
    def target_temperature(self):
        """Leest de ingestelde doeltemperatuur uit de data."""
        return self.coordinator.data.get("target_temp")

    @property
    def target_temperature_step(self):
        """Zorgt voor stapjes van 0.5 of 1 graad in de UI."""
        return 1.0

    @property
    def hvac_mode(self):
        """Geeft de huidige modus weer (Aan/Uit)."""
        status = self.coordinator.data.get("burner_status")
        if status in ["Off", "Stove power off", "Eco Idle"]:
            return HVACMode.OFF
        return HVACMode.HEAT

    @property
    def hvac_action(self):
        """Laat het vlam-icoontje oranje worden bij actieve verbranding."""
        status = self.coordinator.data.get("burner_status")
        heating_statuses = [
            "Ignition starting", 
            "Ignition starting, fire on", 
            "Flame On",
            "Stove On", 
            "Stove On, Clean"
        ]
        if status in heating_statuses:
            return HVACAction.HEATING
        if status == "Eco Idle":
            return HVACAction.IDLE
        return HVACAction.OFF

    async def async_set_temperature(self, **kwargs):
        """Stuur de nieuwe doeltemperatuur in HEX-formaat naar de kachel."""
        temp = kwargs.get("temperature")
        if temp is None:
            return

        set_point_int = int(temp)
        set_point_hex_str = f"{set_point_int:02X}"
        cmd = f"F2{set_point_hex_str}0"
        
        await self.coordinator.api.send_cmd(cmd)
        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode):
        """Zet de kachel aan of uit via de PowerLevel commando's."""
        if hvac_mode == HVACMode.OFF:
            await self.coordinator.api.send_cmd("F0000")
        elif hvac_mode == HVACMode.HEAT:
            await self.coordinator.api.send_cmd("F0010")
        
        await self.coordinator.async_request_refresh()