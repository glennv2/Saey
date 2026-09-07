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

    async def _safe_cmd(self, code):
        try:
            return await self.api.send_cmd(code)
        except Exception as err:
            _LOGGER.debug("Command %s failed: %s", code, err)
            return None

    async def _async_update_data(self):
        status_raw = await self._safe_cmd("D9000")
        await asyncio.sleep(0.5)
        temp_raw = await self._safe_cmd("D1000")
        await asyncio.sleep(0.5)
        smoke_raw = await self._safe_cmd("D0000")
        await asyncio.sleep(0.5)
        fan_raw = await self._safe_cmd("EF000")
        await asyncio.sleep(0.5)
        pellet_raw = await self._safe_cmd("D3000")
        await asyncio.sleep(0.5)
        error_raw = await self._safe_cmd("DA000")
        await asyncio.sleep(0.5)
        hours_raw = await self._safe_cmd("D7000")
        await asyncio.sleep(0.5)
        target_raw = await self._safe_cmd("C6000")

        all_raw = (status_raw, temp_raw, smoke_raw, fan_raw, pellet_raw, error_raw, hours_raw, target_raw)
        if all(v is None for v in all_raw):
            raise UpdateFailed("All 8 commands failed — stove is likely unreachable")

        return {
            "burner_status": self.translate_status(_clean_hex(status_raw)),
            "room_temp": _clean_hex(temp_raw) / 10.0,
            "flue_gas_temp": _clean_hex(smoke_raw),
            "exhaust_fan_speed": _clean_hex(fan_raw) * 10,
            "pellet_speed": _clean_hex(pellet_raw),
            "error_code": self.translate_error(_clean_hex(error_raw)),
            "target_temp": _clean_hex(target_raw, default=20),
            "total_hours": _clean_hex(hours_raw),
        }

    def translate_error(self, error_int):
        from .const import ERROR_CODES
        return ERROR_CODES.get(error_int, "All OK")

    def translate_status(self, state_int):
        return BURNER_STATES.get(state_int, f"Onbekend (code 0x{state_int:04X})")