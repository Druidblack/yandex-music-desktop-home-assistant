"""Dislike current track through CDP."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.exceptions import HomeAssistantError

from .api import CDPError
from .entity import YandexMusicEntity


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    from .const import DOMAIN

    async_add_entities([YandexMusicDislikeButton(hass.data[DOMAIN][entry.entry_id])])


class YandexMusicDislikeButton(YandexMusicEntity, ButtonEntity):
    _attr_name = "Dislike current track"
    _attr_icon = "mdi:thumb-down"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "dislike")

    async def async_press(self) -> None:
        try:
            await self.coordinator.send_command("dislike")
        except CDPError as exc:
            raise HomeAssistantError(str(exc)) from exc
