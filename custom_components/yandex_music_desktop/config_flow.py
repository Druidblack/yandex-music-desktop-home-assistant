"""Setup from the HA integrations UI: IP address + port for every instance."""

from __future__ import annotations

import ipaddress

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import CDPConnectionError, YandexMusicCDP
from .const import CONF_NAME, DEFAULT_NAME, DEFAULT_PORT, DOMAIN


def clean_host(host: str) -> str:
    host = host.strip().strip("[]")
    if not host or "/" in host or "://" in host or "@" in host or "?" in host or "#" in host:
        raise ValueError("Host must be an IP address or hostname without a scheme")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        if ":" in host or " " in host:
            raise ValueError("Invalid hostname") from None
    return host


class YandexMusicCDPConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None):
        errors = {}
        if user_input is not None:
            try:
                host = clean_host(user_input[CONF_HOST])
                port = user_input[CONF_PORT]
            except ValueError:
                errors["base"] = "invalid_host"
            else:
                api = YandexMusicCDP(async_get_clientsession(self.hass), host, port, "")
                try:
                    await api.async_probe()
                except CDPConnectionError:
                    errors["base"] = "cannot_connect"
                else:
                    await self.async_set_unique_id(f"{host.lower()}:{port}")
                    self._abort_if_unique_id_configured()
                    user_input[CONF_HOST] = host
                    return self.async_create_entry(
                        title=user_input[CONF_NAME].strip() or f"Yandex Music {port}",
                        data=user_input,
                    )
        values = user_input or {}
        schema = vol.Schema({
            vol.Required(CONF_NAME, default=values.get(CONF_NAME, DEFAULT_NAME)): str,
            vol.Required(CONF_HOST, default=values.get(CONF_HOST, "192.168.1.100")): str,
            vol.Required(CONF_PORT, default=values.get(CONF_PORT, DEFAULT_PORT)):
                vol.All(vol.Coerce(int), vol.Range(min=1, max=65535)),
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
