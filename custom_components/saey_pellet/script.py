import logging
import asyncio
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import DOMAIN, BURNER_STATES

_LOGGER = logging.getLogger(__name__)

class PelletStoveCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api):
        super().__init__(
            hass, 
            _LOGGER, 
            name="Saey Pelletstove",
            update_interval=timedelta(seconds=10)
        )
        self.api = api 

    async def _async_update_data(self):
            try:
                status_raw = await self.api.send_cmd("D9000")
                await asyncio.sleep(0.5) 
                temp_raw = await self.api.send_cmd("D1000")
                await asyncio.sleep(0.5)
                smoke_raw = await self.api.send_cmd("D0000")
                await asyncio.sleep(0.5)
                fan_raw = await self.api.send_cmd("EF000")
                await asyncio.sleep(0.5)
                power_raw = await self.api.send_cmd("D3000")   
                await asyncio.sleep(0.5)
                pellet_raw = await self.api.send_cmd("D4000")  
                await asyncio.sleep(0.5)
                error_raw = await self.api.send_cmd("DA000")   
                await asyncio.sleep(0.5)
                target_raw = await self.api.send_cmd("C6000")  

                if not status_raw or not temp_raw:
                    _LOGGER.warning("Kachel gaf een leeg antwoord, herproberen")
                    raise UpdateFailed("Kachel reageert niet")

                def clean_hex(val):
                    try:
                        stripped = val.replace('\x1b', '').replace('R', '').split('&')[0]
                        return int(stripped, 16)
                    except (ValueError, IndexError, AttributeError):
                        return 0

                return {
                    "burner_status": self.translate_status(clean_hex(status_raw)),
                    "room_temp": clean_hex(temp_raw[1:5]) / 10.0 if len(temp_raw) > 4 else 0,
                    "flue_gas_temp": clean_hex(smoke_raw[1:5]) if len(smoke_raw) > 4 else 0,
                    "exhaust_fan_speed": (clean_hex(fan_raw[1:5]) * 10) if len(fan_raw) > 4 else 0,
                    "power_level": clean_hex(power_raw[1:5]) if len(power_raw) > 4 else 1,
                    "pellet_speed": clean_hex(pellet_raw[1:5]),
                    "error_code": self.translate_error(clean_hex(error_raw[1:5])) if len(error_raw) > 4 else "OK",
                    "target_temp": clean_hex(target_raw[1:5]) if len(target_raw) > 4 else 20,
                }
            except Exception as err:
                _LOGGER.error("Fout in coordinator: %s", err)
                raise UpdateFailed(f"Fout: {err}")

    def translate_error(self, error_int):
        errors = {1: "Ontstekingsfout", 2: "Defecte afzuiging", 3: "Luchttekort", 5: "Pellets op", 9: "Rookgasventilator defect", 14: "Oververhitting"}
        return errors.get(error_int, "All OK")

    def translate_status(self, state_int):
        status_code = state_int >> 16 
        return BURNER_STATES.get(status_code, f"Onbekend (0x{status_code:04X})")