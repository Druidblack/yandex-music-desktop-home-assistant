"""Like/unlike current track through CDP."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.exceptions import HomeAssistantError

from .api import CDPError
from .entity import YandexMusicEntity


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    from .const import DOMAIN

    async_add_entities([YandexMusicLikeSwitch(hass.data[DOMAIN][entry.entry_id])])


class YandexMusicLikeSwitch(YandexMusicEntity, SwitchEntity):
    _attr_name = "Like current track"
    _attr_icon = "mdi:heart"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "like")

    @property
    def available(self) -> bool:
        return super().available and self.current.get("liked") is not None

    @property
    def is_on(self) -> bool:
        return self.current.get("liked") is True

    async def _send(self, value: bool) -> None:
        try:
            await self.coordinator.send_command("like", value)
        except CDPError as exc:
            raise HomeAssistantError(str(exc)) from exc

    async def async_turn_on(self, **kwargs) -> None:
        await self._send(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self._send(False)
