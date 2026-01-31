import logging
from .const import DOMAIN
from .script import PelletStoveCoordinator
from .api import MyPelletApi 

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry):
    host = entry.data.get("host")
    port = entry.data.get("port", 23)   
    api = MyPelletApi(host, port)    
    coordinator = PelletStoveCoordinator(hass, api)  
    coordinator.config_entry = entry
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, ["climate", "sensor"])    
    return True

async def async_unload_entry(hass, entry):
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["climate", "sensor"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok