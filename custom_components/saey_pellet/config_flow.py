import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN

class SaeyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handel de configuratie van de Saey kachel af."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Eerste stap: vraag om het IP-adres."""
        errors = {}
        if user_input is not None:
            return self.async_create_entry(title=f"Saey {user_input['host']}", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("host"): str,
                vol.Optional("port", default=23): int,
            }),
            errors=errors,
        )