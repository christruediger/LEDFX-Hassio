"""Support for LEDFX as light entities with RGB color control."""
from __future__ import annotations

import logging
import re
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
)

from .const import COLOR_LOCKS_KEY, DOMAIN, EFFECTS_SCHEMA_KEY
from .ledfx_client import LEDFXClient

_LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Color utility helpers
# ---------------------------------------------------------------------------

def rgb_to_gradient(r: int, g: int, b: int) -> str:
    """Create a monochromatic gradient from a single RGB color.

    Produces a dark → full → light → full sweep so the hue is unmistakably
    the chosen color while still giving depth to animated effects.
    """
    r_dark = max(0, int(r * 0.45))
    g_dark = max(0, int(g * 0.45))
    b_dark = max(0, int(b * 0.45))
    r_light = min(255, r + int((255 - r) * 0.45))
    g_light = min(255, g + int((255 - g) * 0.45))
    b_light = min(255, b + int((255 - b) * 0.45))
    return (
        f"linear-gradient(90deg, "
        f"rgb({r_dark},{g_dark},{b_dark}) 0%, "
        f"rgb({r},{g},{b}) 35%, "
        f"rgb({r_light},{g_light},{b_light}) 65%, "
        f"rgb({r},{g},{b}) 100%)"
    )


def rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02x}{g:02x}{b:02x}"


def hex_to_rgb(hex_color: str) -> tuple[int, int, int] | None:
    """Parse '#rrggbb' or 'rrggbb' to (r, g, b)."""
    hex_color = hex_color.strip().lstrip("#")
    if len(hex_color) == 6:
        try:
            return (
                int(hex_color[0:2], 16),
                int(hex_color[2:4], 16),
                int(hex_color[4:6], 16),
            )
        except ValueError:
            pass
    return None


def extract_rgb_from_gradient(gradient: str) -> tuple[int, int, int] | None:
    """Extract the dominant (first) color from a CSS gradient string."""
    match = re.search(r"rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)", gradient)
    if match:
        return int(match.group(1)), int(match.group(2)), int(match.group(3))
    return None


def apply_color_to_config(
    rgb: tuple[int, int, int],
    effect_schema: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    """Apply the main color to an effect config, respecting its parameter schema."""
    r, g, b = rgb
    result = config.copy()
    props = effect_schema.get("schema", {}).get("properties", {})

    if "gradient" in props:
        result["gradient"] = rgb_to_gradient(r, g, b)

    if "color" in props:
        result["color"] = rgb_to_hex(r, g, b)

    # Multi-band color effects (energy, scroll, rain, …)
    r_hi = min(255, r + int((255 - r) * 0.4))
    g_hi = min(255, g + int((255 - g) * 0.4))
    b_hi = min(255, b + int((255 - b) * 0.4))
    r_lo = max(0, int(r * 0.65))
    g_lo = max(0, int(g * 0.65))
    b_lo = max(0, int(b * 0.65))

    for key, rv, gv, bv in [
        ("color_high", r_hi, g_hi, b_hi),
        ("color_lows", r_lo, g_lo, b_lo),
        ("color_mids", r, g, b),
        ("lows_color", r_lo, g_lo, b_lo),
        ("mids_color", r, g, b),
        ("high_color", r_hi, g_hi, b_hi),
        ("color_low", r_lo, g_lo, b_lo),
        ("color_mid", r, g, b),
    ]:
        if key in props:
            result[key] = rgb_to_hex(rv, gv, bv)

    return result


# ---------------------------------------------------------------------------
# Entity setup
# ---------------------------------------------------------------------------

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LEDFX light entities."""
    client: LEDFXClient = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = hass.data[DOMAIN][f"{config_entry.entry_id}_coordinator"]

    try:
        devices = await client.get_devices()
    except Exception as err:
        _LOGGER.error("Failed to get devices: %s", err)
        devices = {}

    entities = []
    for virtual_id, virtual_data in coordinator.data.items():
        device_id = virtual_data.get("is_device")
        device_online = (
            devices.get(device_id, {}).get("online", True) if device_id else True
        )
        entities.append(
            LEDFXLight(coordinator, client, config_entry.entry_id, virtual_id, virtual_data, device_online)
        )

    async_add_entities(entities)


class LEDFXLight(CoordinatorEntity, LightEntity):
    """LEDFX virtual represented as a Home Assistant light.

    Supports on/off, brightness (maps to max_brightness), and RGB color.
    The chosen color is stored as a "color lock" so that every subsequent
    effect change automatically inherits it.
    """

    _attr_has_entity_name = True
    _attr_color_mode = ColorMode.RGB
    _attr_supported_color_modes: set[ColorMode] = {ColorMode.RGB}

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        client: LEDFXClient,
        entry_id: str,
        virtual_id: str,
        virtual_data: dict[str, Any],
        device_online: bool,
    ) -> None:
        super().__init__(coordinator)
        self._client = client
        self._entry_id = entry_id
        self._virtual_id = virtual_id
        self._device_online = device_online

        self._attr_unique_id = f"ledfx_{virtual_id}_light"
        self._attr_name = "Licht"

        virtual_name = virtual_data.get("config", {}).get("name", virtual_id)
        self._attr_device_info = {
            "identifiers": {(DOMAIN, virtual_id)},
            "name": virtual_name,
            "manufacturer": "LEDFX",
            "model": "Virtual LED",
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @property
    def _virtual_data(self) -> dict[str, Any]:
        return self.coordinator.data.get(self._virtual_id, {})

    @property
    def _color_locks(self) -> dict:
        return self.hass.data[DOMAIN].get(COLOR_LOCKS_KEY, {})

    def _set_color_lock(self, rgb: tuple[int, int, int]) -> None:
        self.hass.data[DOMAIN].setdefault(COLOR_LOCKS_KEY, {})[self._virtual_id] = rgb

    def _clear_color_lock(self) -> None:
        self.hass.data[DOMAIN].get(COLOR_LOCKS_KEY, {}).pop(self._virtual_id, None)

    # ------------------------------------------------------------------
    # State properties
    # ------------------------------------------------------------------

    @property
    def is_on(self) -> bool:
        return self._virtual_data.get("active", False)

    @property
    def brightness(self) -> int:
        max_b = self._virtual_data.get("config", {}).get("max_brightness", 1.0)
        return int(max_b * 255)

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        # 1. Prefer locked color
        locked = self._color_locks.get(self._virtual_id)
        if locked:
            return locked

        # 2. Extract from active effect
        effect_config = self._virtual_data.get("effect", {}).get("config", {})
        if "gradient" in effect_config:
            return extract_rgb_from_gradient(effect_config["gradient"])
        if "color" in effect_config:
            return hex_to_rgb(effect_config["color"])
        if "color_lows" in effect_config:
            return hex_to_rgb(effect_config["color_lows"])

        return None

    @property
    def available(self) -> bool:
        return self._device_online

    @property
    def _effects_data(self) -> dict[str, Any]:
        """Return cached effects schema – loaded once at integration startup."""
        return self.hass.data[DOMAIN].get(EFFECTS_SCHEMA_KEY, {})

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the virtual, optionally with a new RGB color or brightness."""
        brightness: int | None = kwargs.get(ATTR_BRIGHTNESS)
        rgb: tuple[int, int, int] | None = kwargs.get(ATTR_RGB_COLOR)

        # Update virtual brightness
        if brightness is not None:
            await self._client.update_virtual_config(
                self._virtual_id, {"max_brightness": round(brightness / 255, 3)}
            )

        # Persist color lock
        if rgb is not None:
            self._set_color_lock(rgb)

        # Determine which effect to activate
        effect_data = self._virtual_data.get("effect", {})
        effect_type = effect_data.get("type") or self._virtual_data.get("last_effect", "singleColor")
        config = effect_data.get("config", {}).copy()

        # Apply color (new or existing lock) to the effect config
        active_rgb = rgb or self._color_locks.get(self._virtual_id)
        if active_rgb and effect_type in self._effects_data:
            config = apply_color_to_config(active_rgb, self._effects_data[effect_type], config)
        elif active_rgb and not self._effects_data:
            # Fallback if effects schema not loaded: just use singleColor
            effect_type = "singleColor"
            config = {"color": rgb_to_hex(*active_rgb)}

        await self._client.set_virtual_effect(self._virtual_id, effect_type, config)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the virtual (clear active effect)."""
        await self._client.clear_virtual_effect(self._virtual_id)
        await self.coordinator.async_request_refresh()
