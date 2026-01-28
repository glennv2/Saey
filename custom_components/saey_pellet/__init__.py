import logging
from homeassistant.helpers import discovery
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass, config):
    """Set up the Saey component via YAML."""
    if DOMAIN not in config:
        return True

    conf = config.get(DOMAIN)

    # Dit zorgt ervoor dat climate.py en sensor.py worden aangeroepen
    hass.async_create_task(
        discovery.async_load_platform(hass, "climate", DOMAIN, conf, config)
    )
    hass.async_create_task(
        discovery.async_load_platform(hass, "sensor", DOMAIN, conf, config)
    )

    return True