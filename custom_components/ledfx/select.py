"""Support for LEDFX effect selection."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import COLOR_LOCKS_KEY, DOMAIN, EFFECTS_SCHEMA_KEY, GRADIENT_PRESETS, AUDIO_REACTIVE_CATEGORIES, NON_REACTIVE_CATEGORIES
from .ledfx_client import LEDFXClient

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LEDFX select entities."""
    client: LEDFXClient = hass.data[DOMAIN][config_entry.entry_id]
    
    # Try to get coordinator from light platform, or create it if it doesn't exist yet
    coordinator = hass.data[DOMAIN].get(f"{config_entry.entry_id}_coordinator")
    
    if not coordinator:
        # Light platform hasn't been loaded yet, create coordinator here
        from datetime import timedelta
        
        async def async_update_data():
            """Fetch data from LEDFX."""
            try:
                return await client.get_virtuals()
            except Exception as err:
                from homeassistant.helpers.update_coordinator import UpdateFailed
                raise UpdateFailed(f"Error communicating with LEDFX: {err}") from err
        
        coordinator = DataUpdateCoordinator(
            hass,
            _LOGGER,
            name="ledfx",
            update_method=async_update_data,
            update_interval=timedelta(seconds=30),
        )
        
        await coordinator.async_config_entry_first_refresh()
        
        # Store it for light platform to use
        hass.data[DOMAIN][f"{config_entry.entry_id}_coordinator"] = coordinator
    
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

        # Add audio-reactive effect selector
        entities.append(LEDFXEffectSelect(coordinator, client, config_entry.entry_id, virtual_id, virtual_data, device_online, is_reactive=True))
        # Add non-reactive effect selector
        entities.append(LEDFXEffectSelect(coordinator, client, config_entry.entry_id, virtual_id, virtual_data, device_online, is_reactive=False))
        # Add gradient selector
        entities.append(LEDFXGradientSelect(coordinator, client, config_entry.entry_id, virtual_id, virtual_data, device_online))

    async_add_entities(entities)


class LEDFXEffectSelect(CoordinatorEntity, SelectEntity):
    """Representation of a LEDFX effect selector."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        client: LEDFXClient,
        entry_id: str,
        virtual_id: str,
        virtual_data: dict[str, Any],
        device_online: bool,
        is_reactive: bool = True,
    ) -> None:
        """Initialize the select."""
        super().__init__(coordinator)
        self._client = client
        self._entry_id = entry_id
        self._virtual_id = virtual_id
        self._is_reactive = is_reactive
        
        # Set unique ID and name based on type
        if is_reactive:
            self._attr_unique_id = f"ledfx_{virtual_id}_effect_reactive"
            self._attr_name = "Effect (Audio Reactive)"
        else:
            self._attr_unique_id = f"ledfx_{virtual_id}_effect_static"
            self._attr_name = "Effect (Static)"
            
        self._effects_list: list[str] = []
        self._effects_data: dict[str, Any] = {}
        self._current_effect: str | None = None
        self._attr_options: list[str] = []  # Initialize options as empty list
        self._device_online = device_online
        
        # Device info for grouping
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

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass, build options from cached schema."""
        await super().async_added_to_hass()
        self._build_options_from_cache()

    def _build_options_from_cache(self) -> None:
        """Filter available effects using the schema cached at startup."""
        effects = self.hass.data[DOMAIN].get(EFFECTS_SCHEMA_KEY, {})
        self._effects_data = effects
        filtered = [
            name for name, info in effects.items()
            if (self._is_reactive and info.get("category", "") in AUDIO_REACTIVE_CATEGORIES)
            or (not self._is_reactive and info.get("category", "") in NON_REACTIVE_CATEGORIES)
        ]
        self._effects_list = sorted(filtered)
        self._attr_options = self._effects_list
    
    @property
    def options(self) -> list[str]:
        """Return available options."""
        return self._attr_options

    @property
    def current_option(self) -> str | None:
        """Return the current effect."""
        # Get from coordinator data
        effect = self.virtual_data.get("effect", {})
        effect_type = effect.get("type")
        
        # Only show if effect is in our filtered list
        if effect_type and effect_type in self._effects_list:
            return effect_type
        
        # Check last_effect if no active effect
        if not effect_type:
            last_effect = self.virtual_data.get("last_effect")
            if last_effect and last_effect in self._effects_list:
                return last_effect
        
        return None

    async def async_update(self) -> None:
        """Update the current effect state."""
        # This is called by coordinator, we just use coordinator data
        pass

    async def async_select_option(self, option: str) -> None:
        """Change the selected effect, preserving any locked color."""
        try:
            effect_schema = self._effects_data.get(option, {})

            # Build defaults from schema properties
            default_config: dict[str, Any] = {}
            props = effect_schema.get("schema", {}).get("properties", {})
            for key, meta in props.items():
                if isinstance(meta, dict) and "default" in meta:
                    default_config[key] = meta["default"]

            final_config = default_config.copy()

            # Apply locked color so the main color persists across effect changes
            locked_rgb = self.hass.data[DOMAIN].get(COLOR_LOCKS_KEY, {}).get(self._virtual_id)
            if locked_rgb:
                from .light import apply_color_to_config
                final_config = apply_color_to_config(locked_rgb, effect_schema, final_config)

            await self._client.set_virtual_effect(self._virtual_id, option, final_config)
            await self.coordinator.async_request_refresh()

        except Exception as err:
            _LOGGER.error("Error setting effect %s: %s", option, err)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._device_online and len(self._effects_list) > 0


class LEDFXGradientSelect(CoordinatorEntity, SelectEntity):
    """Representation of a LEDFX gradient preset selector."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        client: LEDFXClient,
        entry_id: str,
        virtual_id: str,
        virtual_data: dict[str, Any],
        device_online: bool,
    ) -> None:
        """Initialize the select."""
        super().__init__(coordinator)
        self._client = client
        self._entry_id = entry_id
        self._virtual_id = virtual_id
        self._attr_unique_id = f"ledfx_{virtual_id}_gradient"
        self._attr_name = "Gradient"
        self._attr_options = list(GRADIENT_PRESETS.keys())
        self._device_online = device_online
        
        # Device info for grouping
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

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()

    @property
    def options(self) -> list[str]:
        """Return available options."""
        return self._attr_options

    @property
    def current_option(self) -> str | None:
        """Return the current gradient preset."""
        # Get from coordinator data
        current_gradient = self.virtual_data.get("effect", {}).get("config", {}).get("gradient")
        
        # Try to match to a preset
        if current_gradient:
            for preset_name, preset_gradient in GRADIENT_PRESETS.items():
                if current_gradient == preset_gradient:
                    return preset_name
        return None

    async def async_update(self) -> None:
        """Update the current gradient state."""
        # This is called by coordinator, we just use coordinator data
        pass

    async def async_select_option(self, option: str) -> None:
        """Change the selected gradient preset and clear any color lock."""
        try:
            # Selecting a gradient preset explicitly overrides the color lock
            self.hass.data[DOMAIN].get(COLOR_LOCKS_KEY, {}).pop(self._virtual_id, None)

            effect = self.virtual_data.get("effect", {})
            effect_type = effect.get("type")
            if not effect_type:
                effect_type = self.virtual_data.get("last_effect", "gradient")

            effect_config = effect.get("config", {}).copy()
            effect_config["gradient"] = GRADIENT_PRESETS[option]

            await self._client.set_virtual_effect(self._virtual_id, effect_type, effect_config)
            await self.coordinator.async_request_refresh()

        except Exception as err:
            _LOGGER.error("Error setting gradient %s: %s", option, err)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._device_online
