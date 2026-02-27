"""DataUpdateCoordinator for Deutsche Ferien integration."""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import fetch_ferien, fetch_feiertage
from .const import (
    CONF_BUNDESLAND,
    CONF_FEIERTAGE_NATIONAL,
    CONF_FEIERTAGE_REGIONAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    YEARS_AHEAD,
)
from .yaml_writer import write_ferien_yaml

_LOGGER = logging.getLogger(__name__)


def _compute_date_range() -> tuple[date, date]:
    """Today → 30 Sep of (current_year + YEARS_AHEAD).

    Ensures we always capture summer holidays of the target year
    (they end by mid-September in all Bundesländer).
    """
    today = date.today()
    target_year = today.year + YEARS_AHEAD
    return today, date(target_year, 9, 30)


class FerienCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Manages fetching holiday data, computing sensor values, and writing YAML."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_data: dict[str, Any],
    ) -> None:
        """Initialize the coordinator."""
        self.bundesland: str = config_data[CONF_BUNDESLAND]
        self.include_national: bool = config_data.get(
            CONF_FEIERTAGE_NATIONAL, False
        )
        self.include_regional: bool = config_data.get(
            CONF_FEIERTAGE_REGIONAL, False
        )
        self.last_yaml_path: str | None = None

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{self.bundesland}",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch APIs → compute state → write YAML."""
        von, bis = _compute_date_range()
        _LOGGER.info(
            "Updating %s holidays: %s → %s", self.bundesland, von, bis
        )

        try:
            # ── Fetch Ferien ──────────────────────────────────────────
            ferien = await fetch_ferien(self.hass, self.bundesland, von, bis)

            # ── Fetch Feiertage (optional) ────────────────────────────
            feiertage: list[dict[str, Any]] | None = None
            if self.include_national or self.include_regional:
                feiertage = await fetch_feiertage(
                    self.hass,
                    self.bundesland,
                    von,
                    bis,
                    include_national=self.include_national,
                    include_regional=self.include_regional,
                )

            # ── Write YAML (blocking I/O → executor) ─────────────────
            config_dir = self.hass.config.path()
            self.last_yaml_path = await self.hass.async_add_executor_job(
                write_ferien_yaml,
                config_dir,
                self.bundesland,
                ferien,
                feiertage,
            )
        except Exception as err:
            raise UpdateFailed(
                f"Error updating {self.bundesland}: {err}"
            ) from err

        # ── Build result dict for sensors ─────────────────────────────
        today = date.today()
        today_str = today.isoformat()

        result: dict[str, Any] = {
            "bundesland": self.bundesland,
            "ferien_count": len(ferien),
            "feiertage_count": len(feiertage) if feiertage else 0,
            "ferien": ferien,
            "feiertage": feiertage or [],
            "yaml_path": self.last_yaml_path,
            "von": von.isoformat(),
            "bis": bis.isoformat(),
            "aktuelle_ferien": None,
            "naechste_ferien": None,
            "naechste_ferien_start": None,
            "tage_bis_naechste_ferien": None,
            "naechster_feiertag": None,
            "naechster_feiertag_datum": None,
            "tage_bis_naechster_feiertag": None,
            "heute_schulfrei": False,
            "heute_grund": None,
        }

        # ── Current / next Ferien ─────────────────────────────────────
        for f in ferien:
            f_start = date.fromisoformat(f["start"])
            f_end = date.fromisoformat(f["end"])
            if f_start <= today <= f_end:
                result["aktuelle_ferien"] = f["name"]
                break
            if f_start > today and result["naechste_ferien"] is None:
                result["naechste_ferien"] = f["name"]
                result["naechste_ferien_start"] = f["start"]
                result["tage_bis_naechste_ferien"] = (f_start - today).days

        # ── Next Feiertag ─────────────────────────────────────────────
        if feiertage:
            for ft in feiertage:
                ft_date = date.fromisoformat(ft["datum"])
                if ft_date >= today:
                    result["naechster_feiertag"] = ft["name"]
                    result["naechster_feiertag_datum"] = ft["datum"]
                    result["tage_bis_naechster_feiertag"] = (
                        ft_date - today
                    ).days
                    break

        # ── Is today school-free? ─────────────────────────────────────
        for f in ferien:
            if f["start"] <= today_str <= f["end"]:
                result["heute_schulfrei"] = True
                result["heute_grund"] = f["name"]
                break

        if not result["heute_schulfrei"] and feiertage:
            for ft in feiertage:
                if ft["datum"] == today_str:
                    result["heute_schulfrei"] = True
                    result["heute_grund"] = ft["name"]
                    break

        return result