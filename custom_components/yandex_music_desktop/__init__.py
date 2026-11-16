from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import CDPError, CDPConnectionError, YandexMusicCDP
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.MEDIA_PLAYER, Platform.SWITCH, Platform.BUTTON]


class YandexMusicCoordinator(DataUpdateCoordinator[dict]):
    """Keep one configured CDP app separate from every other configured port."""

    def __init__(self, hass: HomeAssistant, api: YandexMusicCDP, entry: ConfigEntry):
        super().__init__(
            hass,
            _LOGGER,
            name=f"Yandex Music Desktop {entry.entry_id}",
            update_interval=timedelta(seconds=20),
        )
        self.api = api
        self.entry = entry
        self.api.set_state_callback(self.async_set_updated_data)

    async def _async_update_data(self) -> dict:
        try:
            state = await self.api.async_state()
            self.update_interval = timedelta(seconds=20 if self.api.observer_active else 4)
            return state
        except CDPError as exc:
            raise UpdateFailed(str(exc)) from exc

    async def send_command(self, action: str, value=None) -> None:
        previous_version = self.api.event_version
        await self.api.async_command(action, value)
        # Normally the browser immediately pushes a changed DOM snapshot.
        # For an action that did not trigger an observer event, fall back to a
        # one-off read; it also covers controls without observable DOM changes.
        await asyncio.sleep(0.25)
        if previous_version == self.api.event_version:
            await self.async_request_refresh()


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    script = await hass.async_add_executor_job(
        Path(__file__).with_name("player_dom.js").read_text, "utf-8"
    )
    observer = await hass.async_add_executor_job(
        Path(__file__).with_name("ha_observer.js").read_text, "utf-8"
    )
    api = YandexMusicCDP(
        async_get_clientsession(hass), entry.data[CONF_HOST], entry.data[CONF_PORT], script, observer
    )
    coordinator = YandexMusicCoordinator(hass, api, entry)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    # Allow the entry to load while the Windows player is shut down: retry periodically.
    # The entity becomes unavailable until the player starts, then automatically reconnects.
    await coordinator.async_refresh()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.api.async_close()
    return ok
