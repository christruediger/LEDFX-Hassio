"""Support for LEDFX effect parameter control via number entities."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN, EFFECTS_SCHEMA_KEY
from .ledfx_client import LEDFXClient

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class LEDFXNumberDescription(NumberEntityDescription):
    """Description of a LEDFX number entity."""

    effect_param: str = ""       # Key in effect config
    virtual_param: str = ""      # Key in virtual config (for max_brightness)
    is_virtual_param: bool = False


VIRTUAL_NUMBER_DESCRIPTORS: tuple[LEDFXNumberDescription, ...] = (
    LEDFXNumberDescription(
        key="max_brightness",
        name="Helligkeit",
        native_min_value=0.0,
        native_max_value=1.0,
        native_step=0.01,
        mode=NumberMode.SLIDER,
        icon="mdi:brightness-6",
        virtual_param="max_brightness",
        is_virtual_param=True,
    ),
)

# Effect-level sliders – shown as long as the device is online.
# Applied to the current effect if it supports the param; silently skipped otherwise.
EFFECT_NUMBER_DESCRIPTORS: tuple[LEDFXNumberDescription, ...] = (
    LEDFXNumberDescription(
        key="speed",
        name="Geschwindigkeit",
        native_min_value=0.1,
        native_max_value=10.0,
        native_step=0.1,
        mode=NumberMode.SLIDER,
        icon="mdi:speedometer",
        effect_param="speed",
    ),
    LEDFXNumberDescription(
        key="blur",
        name="Unschärfe",
        native_min_value=0.0,
        native_max_value=10.0,
        native_step=0.1,
        mode=NumberMode.SLIDER,
        icon="mdi:blur",
        effect_param="blur",
    ),
    LEDFXNumberDescription(
        key="intensity",
        name="Intensität",
        native_min_value=0.0,
        native_max_value=1.0,
        native_step=0.01,
        mode=NumberMode.SLIDER,
        icon="mdi:brightness-7",
        effect_param="brightness",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LEDFX number entities."""
    client: LEDFXClient = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = hass.data[DOMAIN][f"{config_entry.entry_id}_coordinator"]

    try:
        devices = await client.get_devices()
    except Exception as err:
        _LOGGER.error("Failed to get devices: %s", err)
        devices = {}

    entities: list[NumberEntity] = []
    for virtual_id, virtual_data in coordinator.data.items():
        device_id = virtual_data.get("is_device")
        device_online = (
            devices.get(device_id, {}).get("online", True) if device_id else True
        )
        for descriptor in VIRTUAL_NUMBER_DESCRIPTORS:
            entities.append(
                LEDFXVirtualNumber(
                    coordinator, client, virtual_id, virtual_data, device_online, descriptor
                )
            )
        for descriptor in EFFECT_NUMBER_DESCRIPTORS:
            entities.append(
                LEDFXEffectNumber(
                    coordinator, client, virtual_id, virtual_data, device_online, descriptor
                )
            )

    async_add_entities(entities)


# ---------------------------------------------------------------------------

class LEDFXVirtualNumber(CoordinatorEntity, NumberEntity):
    """Slider for a virtual-level parameter (currently only max_brightness)."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        client: LEDFXClient,
        virtual_id: str,
        virtual_data: dict[str, Any],
        device_online: bool,
        description: LEDFXNumberDescription,
    ) -> None:
        super().__init__(coordinator)
        self._client = client
        self._virtual_id = virtual_id
        self._device_online = device_online
        self.entity_description = description

        self._attr_unique_id = f"ledfx_{virtual_id}_{description.key}"
        self._attr_native_min_value = description.native_min_value
        self._attr_native_max_value = description.native_max_value
        self._attr_native_step = description.native_step
        self._attr_mode = description.mode

        virtual_name = virtual_data.get("config", {}).get("name", virtual_id)
        self._attr_device_info = {
            "identifiers": {(DOMAIN, virtual_id)},
            "name": virtual_name,
            "manufacturer": "LEDFX",
            "model": "Virtual LED",
        }

    @property
    def _virtual_data(self) -> dict[str, Any]:
        return self.coordinator.data.get(self._virtual_id, {})

    @property
    def native_value(self) -> float | None:
        return self._virtual_data.get("config", {}).get(self.entity_description.virtual_param)

    @property
    def available(self) -> bool:
        return self._device_online

    async def async_set_native_value(self, value: float) -> None:
        await self._client.update_virtual_config(
            self._virtual_id, {self.entity_description.virtual_param: round(value, 3)}
        )
        await self.coordinator.async_request_refresh()


class LEDFXEffectNumber(CoordinatorEntity, NumberEntity):
    """Slider for an effect-level parameter.

    Always available when the device is online.  Applying the slider to an
    effect that doesn't support the parameter is silently ignored.  This
    prevents confusing "unavailable" states just because the active effect
    happens not to support a particular knob.
    """

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        client: LEDFXClient,
        virtual_id: str,
        virtual_data: dict[str, Any],
        device_online: bool,
        description: LEDFXNumberDescription,
    ) -> None:
        super().__init__(coordinator)
        self._client = client
        self._virtual_id = virtual_id
        self._device_online = device_online
        self.entity_description = description

        self._attr_unique_id = f"ledfx_{virtual_id}_{description.key}"
        self._attr_native_min_value = description.native_min_value
        self._attr_native_max_value = description.native_max_value
        self._attr_native_step = description.native_step
        self._attr_mode = description.mode

        virtual_name = virtual_data.get("config", {}).get("name", virtual_id)
        self._attr_device_info = {
            "identifiers": {(DOMAIN, virtual_id)},
            "name": virtual_name,
            "manufacturer": "LEDFX",
            "model": "Virtual LED",
        }

    @property
    def _virtual_data(self) -> dict[str, Any]:
        return self.coordinator.data.get(self._virtual_id, {})

    @property
    def _effects_schema(self) -> dict[str, Any]:
        """Return cached effects schema from hass.data."""
        return self.hass.data[DOMAIN].get(EFFECTS_SCHEMA_KEY, {})

    def _effect_props(self) -> dict[str, Any]:
        """Return the properties dict of the current active effect."""
        effect_type = self._virtual_data.get("effect", {}).get("type")
        if not effect_type:
            return {}
        return self._effects_schema.get(effect_type, {}).get("schema", {}).get("properties", {})

    def _current_value(self) -> float | None:
        """Return value from active effect config, or schema default."""
        config = self._virtual_data.get("effect", {}).get("config", {})
        val = config.get(self.entity_description.effect_param)
        if val is None:
            props = self._effect_props()
            val = props.get(self.entity_description.effect_param, {}).get("default")
        return val

    @property
    def native_value(self) -> float | None:
        return self._current_value()

    @property
    def available(self) -> bool:
        # Always show as long as the device is reachable
        return self._device_online

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose whether the current effect actually supports this parameter."""
        param = self.entity_description.effect_param
        supported = param in self._effect_props()
        effect_type = self._virtual_data.get("effect", {}).get("type", "–")
        return {"supported_by_current_effect": supported, "current_effect": effect_type}

    async def async_set_native_value(self, value: float) -> None:
        """Apply the value to the current effect (if it supports the parameter)."""
        effect = self._virtual_data.get("effect", {})
        effect_type = effect.get("type")
        if not effect_type:
            _LOGGER.debug(
                "No active effect on %s – cannot set %s",
                self._virtual_id, self.entity_description.effect_param,
            )
            return

        props = self._effect_props()
        if self.entity_description.effect_param not in props:
            _LOGGER.debug(
                "Effect %s does not support %s – skipping",
                effect_type, self.entity_description.effect_param,
            )
            return

        config = effect.get("config", {}).copy()
        config[self.entity_description.effect_param] = round(value, 3)
        await self._client.update_virtual_effect(self._virtual_id, effect_type, config)
        await self.coordinator.async_request_refresh()
