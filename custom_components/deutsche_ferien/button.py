"""Button platform – manual refresh trigger."""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import BUNDESLAENDER, DOMAIN
from .coordinator import FerienCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up button entity from config entry."""
    coordinator: FerienCoordinator = hass.data[DOMAIN][entry.entry_id]
    bl = coordinator.bundesland
    bl_name = BUNDESLAENDER.get(bl, bl)
    async_add_entities([FerienUpdateButton(coordinator, bl, bl_name)])


class FerienUpdateButton(
    CoordinatorEntity[FerienCoordinator], ButtonEntity
):
    """Button to manually trigger a data refresh and YAML re-write."""

    def __init__(
        self,
        coordinator: FerienCoordinator,
        bl: str,
        bl_name: str,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_{bl}_update"
        self._attr_name = f"Ferien {bl_name} Aktualisieren"
        self._attr_icon = "mdi:refresh"
        self._attr_has_entity_name = False

    async def async_press(self) -> None:
        """Handle button press."""
        _LOGGER.info(
            "Manual refresh triggered for %s", self.coordinator.bundesland
        )
        await self.coordinator.async_request_refresh()