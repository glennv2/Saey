import asyncio
import logging
import socket
from typing import Any

import voluptuous as vol

from homeassistant.components.climate import (
    PLATFORM_SCHEMA as CLIMATE_PLATFORM_SCHEMA,
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
    UnitOfTemperature,
)
from homeassistant.const import (
    ATTR_TEMPERATURE,
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
    REVOLUTIONS_PER_MINUTE,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import slugify

_LOGGER = logging.getLogger(__name__)

SUPPORT_FLAGS = (
    ClimateEntityFeature.TARGET_TEMPERATURE
    | ClimateEntityFeature.FAN_MODE
    | ClimateEntityFeature.TURN_OFF
    | ClimateEntityFeature.TURN_ON
)

SUPPORT_MODES = [HVACMode.HEAT, HVACMode.OFF]

DEFAULT_NAME = "Saey Pelletstove"
DEFAULT_HOST = ""
DEFAULT_PORT = 23
DEFAULT_MIN_TEMP = 16.0
DEFAULT_MAX_TEMP = 30.0
DEFAULT_NOFEEDBACK = 16.0
DEFAULT_AUTO_RESET = False
DEFAULT_UNIQUE_ID = "saey_unique_1"

CONF_MIN_TEMP = "min_temp"
CONF_MAX_TEMP = "max_temp"
CONF_AUTO_RESET = "auto_reset"
CONF_NOFEEDBACK = "temp_nofeedback"
CONF_UNIQUE_ID = "unique_id"

PLATFORM_SCHEMA = CLIMATE_PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.positive_int,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_MIN_TEMP, default=DEFAULT_MIN_TEMP): cv.positive_float,
        vol.Optional(CONF_MAX_TEMP, default=DEFAULT_MAX_TEMP): cv.positive_float,
        vol.Optional(CONF_AUTO_RESET, default=DEFAULT_AUTO_RESET): cv.boolean,
        vol.Optional(CONF_NOFEEDBACK, default=DEFAULT_NOFEEDBACK): cv.positive_float,
        vol.Optional(CONF_UNIQUE_ID, default=DEFAULT_UNIQUE_ID): cv.string,
    }
)

# Duepi EVO Protocol Constants
STATE_ACK =   0x00000020
STATE_OFF =   0x00000020
STATE_START = 0x01000000
STATE_ON =    0x02000000
STATE_CLEAN = 0x04000000
STATE_COOL =  0x08000000
STATE_ECO =   0x10000000

GET_SETPOINT =    "C6000"
GET_FLUGASTEMP =  "D0000"
GET_TEMPERATURE = "D1000"
GET_POWERLEVEL =  "D3000"
GET_PELLETSPEED = "D4000"
REMOTE_RESET =    "D6000"
GET_STATUS =      "D9000"
GET_ERRORSTATE =  "DA000"
GET_EXHFANSPEED = "EF000"

SET_POWERLEVEL =  "F00x0"
SET_TEMPERATURE = "F2xx0"

SUPPORT_SETPOINT = False

async def async_setup_platform(hass: HomeAssistant, config: ConfigType, add_devices: AddEntitiesCallback, discovery_info: DiscoveryInfoType | None = None) -> None:
    """Set up the Saey Pelletstove."""
    session = async_get_clientsession(hass)
    add_devices([SaeyPelletDevice(session, config)], True)

class SaeyPelletDevice(ClimateEntity):
    def __init__(self, session, config) -> None:
        self._enable_turn_on_off_backwards_compatibility = False
        self._attr_supported_features = SUPPORT_FLAGS
        self._session = session
        self._name = config.get(CONF_NAME)
        self._host = config.get(CONF_HOST)
        self._port = config.get(CONF_PORT)
        self._min_temp = config.get(CONF_MIN_TEMP)
        self._max_temp = config.get(CONF_MAX_TEMP)
        self._auto_reset = config.get(CONF_AUTO_RESET)
        self._no_feedback = config.get(CONF_NOFEEDBACK)
        self._unique_id = config.get(CONF_UNIQUE_ID)
        self._current_temperature = None
        self._target_temperature = None
        self._heating = False
        self._burner_status = "Unknown"
        self._flugas_temp = None
        self._exhaust_fan_speed = None
        self._pellet_speed = None
        self._error_code = None
        self._hvac_mode = HVACMode.OFF
        self._fan_modes = ["Off", "Min", "Low", "Medium", "High", "Max"]
        self._fan_mode_map = {"Off": 0, "Min": 1, "Low": 2, "Medium": 3, "High": 4, "Max": 5}
        self._fan_mode_map_rev = {v: k for k, v in self._fan_mode_map.items()}
        self._current_fan_mode = "Off"
        
        self._error_code_map = {
            0: "All OK", 1: "Ignition failure", 2: "Defective suction",
            3: "Insufficient air intake", 4: "Water temperature", 5: "Out of pellets",
            6: "Defective pressure switch", 8: "No current", 9: "Exhaust motor failure",
            10: "Card surge", 11: "Date expired", 14: "Overheating",
        }

    @property
    def unique_id(self) -> str: return self._unique_id
    @property
    def should_poll(self) -> bool: return True
    @property
    def temperature_unit(self) -> str: return UnitOfTemperature.CELSIUS
    @property
    def name(self) -> str: return self._name
    @property
    def current_temperature(self) -> float: return self._current_temperature
    @property
    def hvac_mode(self) -> HVACMode: return self._hvac_mode
    @property
    def hvac_modes(self) -> list[HVACMode]: return SUPPORT_MODES
    @property
    def min_temp(self) -> float: return self._min_temp
    @property
    def max_temp(self) -> float: return self._max_temp

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "burner_status": self._burner_status,
            "error_code": self._error_code,
            "exh_fan_speed": f"{self._exhaust_fan_speed} rpm",
            "flu_gas_temp": f"{self._flugas_temp} °C",
            "pellet_speed": self._pellet_speed,
        }

    @property
    def target_temperature(self) -> float:
        if self._target_temperature is None:
            self._target_temperature = int(self._no_feedback)
        return self._target_temperature

    def generate_command(self, command):
        formatted_cmd = "R" + command
        checksum = sum(ord(char) for char in formatted_cmd) & 0xFF
        return "\x1b" + formatted_cmd + f"{checksum:02X}" + "&"

    async def async_update(self) -> None:
        data = await self.get_data(SUPPORT_SETPOINT)
        if not data: return
        self._burner_status, self._current_temperature, fan_idx, self._flugas_temp, self._exhaust_fan_speed, self._pellet_speed, self._error_code = data[:7]
        self._current_fan_mode = self._fan_mode_map_rev.get(fan_idx, "Off")
        
        if self._burner_status == "Off":
            self._hvac_mode = HVACMode.OFF
            self._heating = False
        else:
            self._hvac_mode = HVACMode.HEAT
            self._heating = True

    async def get_data(self, support_setpoint):
        sock = None
        try:
            async with asyncio.timeout(5):
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3.0)
                sock.connect((self._host, self._port))

                # Status
                sock.send(self.generate_command(GET_STATUS).encode())
                resp = sock.recv(10).decode()
                bits = int(resp[1:9], 16)
                status = "Off"
                if bits & STATE_START: status = "Starting"
                elif bits & STATE_ON: status = "Flame On"
                elif bits & STATE_CLEAN: status = "Cleaning"
                elif bits & STATE_ECO: status = "Eco"
                elif bits & STATE_COOL: status = "Cooling"

                # Temp
                sock.send(self.generate_command(GET_TEMPERATURE).encode())
                current_temp = int(sock.recv(10).decode()[1:5], 16) / 10.0

                # Power/Fan
                sock.send(self.generate_command(GET_POWERLEVEL).encode())
                fan_mode = int(sock.recv(10).decode()[1:5], 16)

                # Gas Temp
                sock.send(self.generate_command(GET_FLUGASTEMP).encode())
                gas_temp = int(sock.recv(10).decode()[1:5], 16)

                # Exhaust Fan
                sock.send(self.generate_command(GET_EXHFANSPEED).encode())
                exh_fan = int(sock.recv(10).decode()[1:5], 16) * 10

                # Pellet Speed
                sock.send(self.generate_command(GET_PELLETSPEED).encode())
                pellet = int(sock.recv(10).decode()[1:5], 16)

                # Error
                sock.send(self.generate_command(GET_ERRORSTATE).encode())
                err_dec = int(sock.recv(10).decode()[1:5], 16)
                error = self._error_code_map.get(err_dec, f"Error {err_dec}")

                return [status, current_temp, fan_mode, gas_temp, exh_fan, pellet, error]
        except Exception as e:
            _LOGGER.error("Update failed for %s: %s", self._host, e)
            return None
        finally:
            if sock: sock.close()

    async def async_set_temperature(self, **kwargs):
        temp = kwargs.get(ATTR_TEMPERATURE)
        if temp is None: return
        # Logica voor versturen commando naar kachel (gelijk aan jouw origineel)
        self._target_temperature = temp
        self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode):
        self._hvac_mode = hvac_mode
        self.async_write_ha_state()