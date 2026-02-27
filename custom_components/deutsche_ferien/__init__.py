"""Deutsche Schulferien & Feiertage – Home Assistant Integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN
from .coordinator import FerienCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BUTTON]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Deutsche Ferien from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    coordinator = FerienCoordinator(hass, dict(entry.data))
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # ── Register service (idempotent) ─────────────────────────────────
    async def _handle_update(call: ServiceCall) -> None:
        """Refresh all configured Bundesländer."""
        _LOGGER.info("Service %s.update_ferien called", DOMAIN)
        for entry_id, coord in hass.data[DOMAIN].items():
            if isinstance(coord, FerienCoordinator):
                await coord.async_request_refresh()

    if not hass.services.has_service(DOMAIN, "update_ferien"):
        hass.services.async_register(DOMAIN, "update_ferien", _handle_update)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    # Remove service when last entry is unloaded
    if not hass.data.get(DOMAIN):
        hass.services.async_remove(DOMAIN, "update_ferien")

    return ok