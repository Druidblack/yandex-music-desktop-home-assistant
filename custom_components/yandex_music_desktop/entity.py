"""Shared platform entity for one Yandex Music CDP instance."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from homeassistant.const import CONF_PORT


class YandexMusicEntity(CoordinatorEntity):
    """Base class for CDP entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, suffix: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.unique_id or coordinator.entry.entry_id}_{suffix}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry.unique_id or coordinator.entry.entry_id)},
            name=coordinator.entry.title,
            manufacturer="Yandex Music",
            model="Yandex Music Desktop",
        )

    @property
    def available(self) -> bool:
        return super().available and bool((self.coordinator.data or {}).get("online"))

    @property
    def current(self) -> dict:
        return self.coordinator.data or {}

    @property
    def extra_state_attributes(self) -> dict:
        return {"debug_port": self.coordinator.entry.data[CONF_PORT]}
