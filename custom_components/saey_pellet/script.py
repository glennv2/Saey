import logging
import asyncio
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import DOMAIN, BURNER_STATES

_LOGGER = logging.getLogger(__name__)

class PelletStoveCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api_client):
        super().__init__(
            hass, 
            _LOGGER, 
            name=DOMAIN, 
            update_interval=timedelta(seconds=10)
        )
        self.api = api_client 

    def calculate_checksum(self, cmd):
        """Vertaalt bijv 'D9000' naar een compleet Duepi frame."""
        full_str = f"R{cmd}0"
        checksum = sum(full_str.encode('ascii')) & 0xFF
        return f"\x1b{full_str}{checksum:02X}&"

    def translate_status(self, raw_resp):
        """Vertaalt het hex-antwoord naar tekst op basis van BURNER_STATES."""
        try:
            state_hex = raw_resp[1:5]
            state_int = int(state_hex, 16)
            return BURNER_STATES.get(state_int, f"Onbekend ({state_hex})")
        except (ValueError, IndexError):
            return "Fout bij uitlezen"

    async def _async_update_data(self):
        """De polling loop die alles ophaalt."""
        try:
            
            # 1. Status ophalen
            cmd_status = self.calculate_checksum("D90005") # Overeenkomstig met jouw ESPHome
            status_raw = await self.api.send_cmd(cmd_status)
            
            # 2. Temperatuur ophalen
            cmd_temp = self.calculate_checksum("D10005")
            temp_raw = await self.api.send_cmd(cmd_temp)

            # 3. Rookgas (D0000)
            cmd_smoke = self.calculate_checksum("D00005")
            smoke_raw = await self.api.send_cmd(cmd_smoke)

            return {
                "burner_status": self.translate_status(status_raw),
                "room_temp": int(temp_raw[1:5], 16) / 10.0,
                "flue_gas_temp": int(smoke_raw[1:5], 16),
            }
            
        except Exception as err:
            raise UpdateFailed(f"Communicatie met kachel mislukt: {err}")