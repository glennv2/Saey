import logging
from .const import DOMAIN
from .script import PelletStoveCoordinator
from .api import MyPelletApi 

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry):
    """Set up Saey Pelletstove via een config entry."""
    
    # 1. Haal de host op uit de configuratie (ingevuld via de UI)
    host = entry.data.get("host")
    port = entry.data.get("port", 23)
    
    # 2. Initialiseer de API/Socket verbinding
    api = MyPelletApi(host, port) 
    
    # 3. Maak de coordinator aan
    coordinator = PelletStoveCoordinator(hass, api)
    
    # Voeg de entry toe aan de coordinator zodat deze erbij kan
    coordinator.config_entry = entry

    # 4. Haal de eerste data op voordat de sensoren starten
    await coordinator.async_config_entry_first_refresh()

    # 5. Sla de coordinator centraal op zodat climate.py en sensor.py erbij kunnen
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # 6. Start de platformen (climate.py en sensor.py)
    await hass.config_entries.async_forward_entry_setups(entry, ["climate", "sensor"])
    
    return True

async def async_unload_entry(hass, entry):
    """Verwijder de integratie netjes."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["climate", "sensor"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok