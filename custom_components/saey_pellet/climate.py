from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature, HVACMode
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    """Setup via de Config Entry (aanbevolen)."""
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

    @property
    def current_temperature(self):
        """Haal de temp rechtstreeks uit de coordinator data."""
        return self.coordinator.data.get("room_temp")

    @property
    def hvac_action(self):
        """Bepaal of hij echt brandt op basis van de status."""
        status = self.coordinator.data.get("burner_status")
        if status in ["Stove On", "Flame On", "Eco Idle"]:
            return HVACAction.HEATING
        return HVACAction.IDLE

    async def async_set_hvac_mode(self, hvac_mode):
        """Stuur commando naar de kachel via de API in de coordinator."""
        if hvac_mode == HVACMode.HEAT:
            # Voorbeeld: start commando
            await self.coordinator.api.send_cmd(self.coordinator.calculate_checksum("F001"))
        elif hvac_mode == HVACMode.OFF:
            # Voorbeeld: stop commando
            await self.coordinator.api.send_cmd(self.coordinator.calculate_checksum("F000"))
        
        await self.coordinator.async_request_refresh()