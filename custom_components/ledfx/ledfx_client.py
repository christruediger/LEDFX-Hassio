"""LEDFX API Client."""
import asyncio
import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)


class LEDFXClient:
    """Client to interact with LEDFX API."""

    def __init__(self, host: str, port: int, session: aiohttp.ClientSession) -> None:
        """Initialize the LEDFX client."""
        self.host = host
        self.port = port
        self.session = session
        self.base_url = f"http://{host}:{port}"

    async def get_info(self) -> dict[str, Any]:
        """Get LEDFX server info."""
        try:
            async with self.session.get(f"{self.base_url}/api/info") as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as err:
            _LOGGER.error("Error getting LEDFX info: %s", err)
            raise

    async def get_virtuals(self) -> dict[str, Any]:
        """Get all virtuals from LEDFX."""
        try:
            async with self.session.get(f"{self.base_url}/api/virtuals") as response:
                response.raise_for_status()
                data = await response.json()
                return data.get("virtuals", {})
        except aiohttp.ClientError as err:
            _LOGGER.error("Error getting virtuals: %s", err)
            raise

    async def get_devices(self) -> dict[str, Any]:
        """Get all devices from LEDFX."""
        try:
            async with self.session.get(f"{self.base_url}/api/devices") as response:
                response.raise_for_status()
                data = await response.json()
                return data.get("devices", {})
        except aiohttp.ClientError as err:
            _LOGGER.error("Error getting devices: %s", err)
            raise

    async def get_virtual(self, virtual_id: str) -> dict[str, Any] | None:
        """Get a specific virtual."""
        virtuals = await self.get_virtuals()
        return virtuals.get(virtual_id)

    async def set_virtual_effect(
        self, virtual_id: str, effect_type: str, config: dict[str, Any]
    ) -> bool:
        """Set effect for a virtual."""
        try:
            payload = {"type": effect_type, "config": config}
            async with self.session.post(
                f"{self.base_url}/api/virtuals/{virtual_id}/effects",
                json=payload,
            ) as response:
                response.raise_for_status()
                return True
        except aiohttp.ClientError as err:
            _LOGGER.error("Error setting effect for virtual %s: %s", virtual_id, err)
            return False

    async def update_virtual_effect(
        self, virtual_id: str, effect_type: str, config: dict[str, Any]
    ) -> bool:
        """Update effect config for a virtual (when effect is already active)."""
        try:
            payload = {"type": effect_type, "config": config}
            async with self.session.put(
                f"{self.base_url}/api/virtuals/{virtual_id}/effects",
                json=payload,
            ) as response:
                response.raise_for_status()
                return True
        except aiohttp.ClientError as err:
            _LOGGER.error("Error updating effect for virtual %s: %s", virtual_id, err)
            return False

    async def clear_virtual_effect(self, virtual_id: str) -> bool:
        """Clear effect from a virtual (turn off)."""
        try:
            async with self.session.delete(
                f"{self.base_url}/api/virtuals/{virtual_id}/effects"
            ) as response:
                response.raise_for_status()
                return True
        except aiohttp.ClientError as err:
            _LOGGER.error("Error clearing effect for virtual %s: %s", virtual_id, err)
            return False

    async def get_effects(self) -> dict[str, Any]:
        """Get available effects."""
        try:
            async with self.session.get(f"{self.base_url}/api/schema") as response:
                response.raise_for_status()
                data = await response.json()
                # Effects are under the "effects" key in the schema
                return data.get("effects", {})
        except aiohttp.ClientError as err:
            _LOGGER.error("Error getting effects: %s", err)
            raise
