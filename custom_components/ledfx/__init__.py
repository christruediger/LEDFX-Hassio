"""The LEDFX integration."""
from __future__ import annotations

import logging

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_HOST, CONF_PORT, DEFAULT_SCAN_INTERVAL, DOMAIN
from .ledfx_client import LEDFXClient

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SWITCH, Platform.SELECT]


def should_include_virtual(virtual_id: str, virtual_data: dict) -> bool:
    """Determine if a virtual should be included based on its ID."""
    # Filter out background, foreground, and mask virtuals
    virtual_name = virtual_data.get("config", {}).get("name", virtual_id).lower()
    excluded_suffixes = ["-background", "-foreground", "-mask"]
    
    return not any(virtual_name.endswith(suffix) for suffix in excluded_suffixes)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up LEDFX from a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]

    session = async_get_clientsession(hass)
    client = LEDFXClient(host, port, session)

    # Test connection
    try:
        await client.get_info()
    except aiohttp.ClientError as err:
        _LOGGER.error("Could not connect to LEDFX at %s:%s - %s", host, port, err)
        return False

    async def async_update_data():
        """Fetch data from LEDFX."""
        try:
            all_virtuals = await client.get_virtuals()
            # Filter out background, foreground, and mask virtuals
            filtered_virtuals = {
                vid: vdata 
                for vid, vdata in all_virtuals.items() 
                if should_include_virtual(vid, vdata)
            }
            return filtered_virtuals
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

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = client
    hass.data[DOMAIN][f"{entry.entry_id}_coordinator"] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
        hass.data[DOMAIN].pop(f"{entry.entry_id}_coordinator")

    return unload_ok
