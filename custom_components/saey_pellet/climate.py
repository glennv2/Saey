import logging
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass, config):
    """Set up the Saey component."""
    hass.data[DOMAIN] = {}
    return True

async def async_setup_entry(hass, entry):
    """Set up Saey from a config entry (indien je config flow gebruikt, anders overslaan)."""
    return True