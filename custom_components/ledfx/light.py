"""Support for LEDFX lights."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_RGB_COLOR,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL
from .ledfx_client import LEDFXClient

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LEDFX light entities."""
    client: LEDFXClient = hass.data[DOMAIN][config_entry.entry_id]

    async def async_update_data() -> dict[str, Any]:
        """Fetch data from LEDFX."""
        try:
            return await client.get_virtuals()
        except Exception as err:
            raise UpdateFailed(f"Error communicating with LEDFX: {err}") from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="ledfx",
        update_method=async_update_data,
        update_interval=DEFAULT_SCAN_INTERVAL,
    )

    await coordinator.async_config_entry_first_refresh()
    
    # Store coordinator for use by other platforms
    hass.data[DOMAIN][f"{config_entry.entry_id}_coordinator"] = coordinator

    entities = []
    for virtual_id, virtual_data in coordinator.data.items():
        entities.append(LEDFXLight(coordinator, client, virtual_id, virtual_data))

    async_add_entities(entities)


def get_coordinator(hass: HomeAssistant, entry_id: str) -> DataUpdateCoordinator | None:
    """Get the coordinator for an entry."""
    return hass.data[DOMAIN].get(f"{entry_id}_coordinator")


class LEDFXLight(CoordinatorEntity, LightEntity):
    """Representation of a LEDFX light."""

    _attr_has_entity_name = True
    _attr_color_mode = ColorMode.RGB
    _attr_supported_color_modes = {ColorMode.RGB}

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        client: LEDFXClient,
        virtual_id: str,
        virtual_data: dict[str, Any],
    ) -> None:
        """Initialize the light."""
        super().__init__(coordinator)
        self._client = client
        self._virtual_id = virtual_id
        self._attr_unique_id = f"ledfx_{virtual_id}"
        virtual_name = virtual_data.get("config", {}).get("name", virtual_id)
        self._attr_name = virtual_name
        
        # Device info for grouping with select entity
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
        """Return true if light is on."""
        # Virtual is on if active=true
        return self.virtual_data.get("active", False)

    @property
    def brightness(self) -> int | None:
        """Return the brightness of the light."""
        effect_config = self.virtual_data.get("effect", {}).get("config", {})
        brightness = effect_config.get("brightness", 1.0)
        # LEDFX brightness is 0.0-1.0, HA expects 0-255
        return int(brightness * 255)

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        """Return the RGB color value."""
        effect_config = self.virtual_data.get("effect", {}).get("config", {})
        
        # First try to parse gradient (for solid colors set by HA)
        if "gradient" in effect_config:
            gradient = effect_config["gradient"]
            # Parse: linear-gradient(90deg, rgb(255, 0, 0) 0%, rgb(255, 0, 0) 100%)
            # Extract first rgb() value
            import re
            match = re.search(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', gradient)
            if match:
                return (int(match.group(1)), int(match.group(2)), int(match.group(3)))
        
        # Fallback to color property
        if "color" in effect_config:
            color = effect_config["color"]
            if isinstance(color, list) and len(color) == 3:
                return tuple(color)
            elif isinstance(color, str):
                # Parse hex color if needed
                color = color.lstrip("#")
                if len(color) == 6:
                    return tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        
        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light."""
        effect_config = {}
        
        # Get current effect or use last_effect or default
        current_effect = self.virtual_data.get("effect", {})
        effect_type = current_effect.get("type")
        is_active = self.virtual_data.get("active", False)
        
        # If no current effect, try last_effect
        if not effect_type:
            effect_type = self.virtual_data.get("last_effect", "gradient")
        
        if current_effect.get("config"):
            effect_config = current_effect["config"].copy()

        # Update brightness if provided
        if ATTR_BRIGHTNESS in kwargs:
            brightness = kwargs[ATTR_BRIGHTNESS] / 255.0  # Convert to 0.0-1.0
            effect_config["brightness"] = brightness

        # Update color if provided
        if ATTR_RGB_COLOR in kwargs:
            rgb = kwargs[ATTR_RGB_COLOR]
            r, g, b = rgb
            # Set gradient to solid color (same color at 0% and 100%)
            gradient = f"linear-gradient(90deg, rgb({r}, {g}, {b}) 0%, rgb({r}, {g}, {b}) 100%)"
            effect_config["gradient"] = gradient
            # Also set color for effects that use it
            effect_config["color"] = list(rgb)

        # If not active, use POST to set new effect
        # If active and we're changing color/brightness, use PUT to update
        if not is_active:
            # POST - set new effect
            await self._client.set_virtual_effect(self._virtual_id, effect_type, effect_config)
        elif ATTR_BRIGHTNESS in kwargs or ATTR_RGB_COLOR in kwargs:
            # PUT - update existing effect config (needs type too!)
            await self._client.update_virtual_effect(self._virtual_id, effect_type, effect_config)

        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the light."""
        await self._client.clear_virtual_effect(self._virtual_id)
        await self.coordinator.async_request_refresh()
