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
    def hvac_mode(self):
        """Geeft de huidige modus weer (Aan/Uit)."""
        status = self.coordinator.data.get("burner_status")
        if status == "Uit":
            return HVACMode.OFF
        return HVACMode.HEAT

    @property
    def hvac_action(self):
        """Laat het vlam-icoontje oranje worden als hij echt brandt."""
        status = self.coordinator.data.get("burner_status")
        if status in ["Aan (Flame On)", "Ontsteken", "Eco Modus"]:
            return HVACAction.HEATING
        return HVACAction.IDLE

    async def async_set_hvac_mode(self, hvac_mode):
        """Stuur commando naar de kachel."""
        if hvac_mode == HVACMode.HEAT:
            await self.coordinator.api.send_cmd("F0010")
        elif hvac_mode == HVACMode.OFF:
            await self.coordinator.api.send_cmd("F0000")
        
        await self.coordinator.async_request_refresh()