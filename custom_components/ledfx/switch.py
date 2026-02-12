"""Support for LEDFX switches."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN
from .ledfx_client import LEDFXClient

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LEDFX switch entities."""
    client: LEDFXClient = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = hass.data[DOMAIN][f"{config_entry.entry_id}_coordinator"]

    # Fetch devices to get online status
    try:
        devices = await client.get_devices()
    except Exception as err:
        _LOGGER.error("Failed to get devices: %s", err)
        devices = {}

    entities = []
    for virtual_id, virtual_data in coordinator.data.items():
        # Get device status
        device_id = virtual_data.get("is_device")
        device_online = devices.get(device_id, {}).get("online", True) if device_id else True
        
        entities.append(LEDFXSwitch(coordinator, client, virtual_id, virtual_data, device_online))

    async_add_entities(entities)


class LEDFXSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a LEDFX virtual as a switch."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        client: LEDFXClient,
        virtual_id: str,
        virtual_data: dict[str, Any],
        device_online: bool,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._client = client
        self._virtual_id = virtual_id
        self._attr_unique_id = f"ledfx_{virtual_id}"
        self._attr_name = None  # Use device name
        self._device_online = device_online
        
        # Device info
        virtual_name = virtual_data.get("config", {}).get("name", virtual_id)
        self._attr_device_info = {
            "identifiers": {(DOMAIN, virtual_id)},
            "name": virtual_name,
            "manufacturer": "LEDFX",
            "model": "Virtual LED",
        }

    @property
    def virtual_data(self) -> dict[str, Any]:
        """Return virtual data from coordinator."""
        return self.coordinator.data.get(self._virtual_id, {})

    @property
    def is_on(self) -> bool:
        """Return true if virtual is active."""
        return self.virtual_data.get("active", False)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the virtual on."""
        try:
            # Get last effect or use default
            last_effect = self.virtual_data.get("last_effect", "gradient")
            
            # Get effect config if available
            effect_config = {}
            if self.virtual_data.get("effect", {}).get("config"):
                effect_config = self.virtual_data["effect"]["config"].copy()
            
            # Set effect (this activates the virtual)
            await self._client.set_virtual_effect(self._virtual_id, last_effect, effect_config)
            
            # Trigger coordinator refresh
            await self.coordinator.async_request_refresh()
            
        except Exception as err:
            _LOGGER.error("Error turning on virtual %s: %s", self._virtual_id, err)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the virtual off."""
        try:
            # Clear effect (deactivates virtual)
            await self._client.clear_virtual_effect(self._virtual_id)
            
            # Trigger coordinator refresh
            await self.coordinator.async_request_refresh()
            
        except Exception as err:
            _LOGGER.error("Error turning off virtual %s: %s", self._virtual_id, err)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._device_online
