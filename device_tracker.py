"""Device tracker platform for Cudy Router."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MODULE_DEVICES, OPTIONS_DEVICELIST
from .coordinator import CudyRouterDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up device tracker entities from config entry."""
    coordinator: CudyRouterDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    device_list = config_entry.options.get(OPTIONS_DEVICELIST, "")
    tracked_macs = [mac.strip() for mac in device_list.split(",") if mac.strip()]
    entities = []
    for mac in tracked_macs:
        entities.append(CudyRouterDeviceTracker(coordinator, mac))
    async_add_entities(entities)

class CudyRouterDeviceTracker(CoordinatorEntity, TrackerEntity):
    """Device tracker for a device connected to the Cudy Router."""

    def __init__(self, coordinator: CudyRouterDataUpdateCoordinator, mac: str) -> None:
        super().__init__(coordinator)
        self._mac = mac
        self._attr_unique_id = f"cudy_router_{mac.replace(':', '').replace('-', '')}"
        self._attr_name = f"Cudy Device {mac}"
        self._attr_source_type = SourceType.ROUTER
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.config_entry.entry_id)},
            "manufacturer": "Cudy",
            "name": "Cudy Router",
        }

    @property
    def is_connected(self) -> bool:
        """Return true if the device is connected: Wired or has a valid signal."""
        devices = self.coordinator.data.get(MODULE_DEVICES, [])
        _LOGGER.warning("[CudyRouterDeviceTracker] Devices in coordinator: %s", devices)
        _LOGGER.warning("[CudyRouterDeviceTracker] Looking for MAC: %s", self._mac)
        for dev in devices:
            _LOGGER.warning("[CudyRouterDeviceTracker] Checking device: %s", dev)
            if isinstance(dev, dict) and dev.get("mac") and dev["mac"].lower() == self._mac.lower():
                connection = dev.get("connection", "").lower()
                signal = dev.get("signal")
                _LOGGER.warning("[CudyRouterDeviceTracker] Found device with MAC %s: connection=%s, signal=%s", self._mac, connection, signal)
                # Connected if Wired, or signal is present and not empty or '---'
                if connection == "wired":
                    return True
                if signal and str(signal).strip() != "" and str(signal).strip() != "---":
                    return True
                return False
        _LOGGER.warning("[CudyRouterDeviceTracker] Device with MAC %s not found in devices list", self._mac)
        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes for the device tracker."""
        devices = self.coordinator.data.get(MODULE_DEVICES, [])
        for dev in devices:
            if isinstance(dev, dict) and dev.get("mac") and dev["mac"].lower() == self._mac.lower():
                return dev.copy()
        return {}
