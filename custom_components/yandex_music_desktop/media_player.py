"""Media player entity for a single Yandex Music CDP app port."""

from __future__ import annotations

from datetime import datetime, timezone

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
    RepeatMode,
)
from homeassistant.exceptions import HomeAssistantError

from .api import CDPError
from .entity import YandexMusicEntity


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    from .const import DOMAIN

    async_add_entities([YandexMusicMediaPlayer(hass.data[DOMAIN][entry.entry_id])])


class YandexMusicMediaPlayer(YandexMusicEntity, MediaPlayerEntity):
    """Playback and information from the selected desktop app."""

    _attr_name = None
    _attr_icon = "mdi:music-circle"
    _attr_device_class = MediaPlayerDeviceClass.SPEAKER
    _attr_media_image_remotely_accessible = True
    _attr_should_poll = False
    _BASE_FEATURES = (
        MediaPlayerEntityFeature.PLAY
        | MediaPlayerEntityFeature.PAUSE
        | MediaPlayerEntityFeature.NEXT_TRACK
        | MediaPlayerEntityFeature.PREVIOUS_TRACK
        | MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.SEEK
        | MediaPlayerEntityFeature.REPEAT_SET
    )

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "player")
        self._position_updated_at = datetime.now(timezone.utc)

    def _handle_coordinator_update(self) -> None:
        self._position_updated_at = datetime.now(timezone.utc)
        super()._handle_coordinator_update()

    @property
    def supported_features(self) -> MediaPlayerEntityFeature:
        features = self._BASE_FEATURES
        if self.current.get("shuffle_available", True):
            features |= MediaPlayerEntityFeature.SHUFFLE_SET
        return features

    @property
    def state(self) -> MediaPlayerState:
        if not self.current.get("title"):
            return MediaPlayerState.IDLE
        playing = self.current.get("playing")
        if playing is True:
            return MediaPlayerState.PLAYING
        if playing is False:
            return MediaPlayerState.PAUSED
        return MediaPlayerState.IDLE

    @property
    def media_content_type(self) -> MediaType:
        return MediaType.MUSIC

    @property
    def media_content_id(self) -> str | None:
        return self.current.get("track_url")

    @property
    def media_title(self) -> str | None:
        return self.current.get("title")

    @property
    def media_artist(self) -> str | None:
        return self.current.get("artist")

    @property
    def media_duration(self) -> float | None:
        return self.current.get("duration")

    @property
    def media_position(self) -> float | None:
        return self.current.get("position")

    @property
    def media_position_updated_at(self) -> datetime:
        return self._position_updated_at

    @property
    def media_image_url(self) -> str | None:
        return self.current.get("cover_url")

    @property
    def volume_level(self) -> float | None:
        return self.current.get("volume")

    @property
    def is_volume_muted(self) -> bool | None:
        return self.current.get("muted")

    @property
    def shuffle(self) -> bool | None:
        return self.current.get("shuffle")

    @property
    def repeat(self) -> RepeatMode:
        mode = self.current.get("repeat")
        return {"off": RepeatMode.OFF, "all": RepeatMode.ALL, "one": RepeatMode.ONE}.get(
            mode, RepeatMode.OFF
        )

    @property
    def extra_state_attributes(self) -> dict:
        return {**super().extra_state_attributes, "liked": self.current.get("liked")}

    async def _send(self, action: str, value=None) -> None:
        try:
            await self.coordinator.send_command(action, value)
        except CDPError as exc:
            raise HomeAssistantError(str(exc)) from exc

    async def async_media_play(self) -> None:
        await self._send("play")

    async def async_media_pause(self) -> None:
        await self._send("pause")

    async def async_media_next_track(self) -> None:
        await self._send("next")

    async def async_media_previous_track(self) -> None:
        await self._send("previous")

    async def async_media_seek(self, position: float) -> None:
        await self._send("seek", float(position))

    async def async_set_volume_level(self, volume: float) -> None:
        await self._send("volume", max(0.0, min(1.0, float(volume))))

    async def async_mute_volume(self, mute: bool) -> None:
        await self._send("mute", bool(mute))

    async def async_set_shuffle(self, shuffle: bool) -> None:
        await self._send("shuffle", bool(shuffle))

    async def async_set_repeat(self, repeat: RepeatMode) -> None:
        await self._send("repeat", repeat.value if isinstance(repeat, RepeatMode) else str(repeat))
