"""Config flow for Deutsche Schulferien & Feiertage."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import (
    BUNDESLAENDER,
    CONF_BUNDESLAND,
    CONF_FEIERTAGE_NATIONAL,
    CONF_FEIERTAGE_REGIONAL,
    DOMAIN,
)


class DeutscheFerienConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow handler."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial user step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            bundesland = user_input[CONF_BUNDESLAND]

            # Prevent duplicate entries for same Bundesland
            await self.async_set_unique_id(f"{DOMAIN}_{bundesland}")
            self._abort_if_unique_id_configured()

            bl_name = BUNDESLAENDER.get(bundesland, bundesland)
            return self.async_create_entry(
                title=f"Ferien {bl_name}",
                data=user_input,
            )

        # Build dropdown: "BY" → "Bayern (BY)"
        bl_options = {
            code: f"{name} ({code})"
            for code, name in sorted(
                BUNDESLAENDER.items(), key=lambda x: x[1]
            )
        }

        schema = vol.Schema(
            {
                vol.Required(CONF_BUNDESLAND, default="BY"): vol.In(
                    bl_options
                ),
                vol.Optional(CONF_FEIERTAGE_NATIONAL, default=True): bool,
                vol.Optional(CONF_FEIERTAGE_REGIONAL, default=True): bool,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )