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
    """Compute the date range for holiday data.

    Start: 1 August of the previous year (to capture the full current school year,
           including Weihnachtsferien that start in December of the previous year).
    End:   30 September of (current_year + YEARS_AHEAD) to capture summer holidays.

    Example for today = 2026-02-27:
        von = 2025-08-01  (captures Weihnachtsferien 2025, Winterferien 2026, etc.)
        bis = 2029-09-30  (captures Sommerferien 2029)
    """
    today = date.today()

    # School year starts ~August. Go back to Aug 1 of previous year
    # to ensure we have the full current school year.
    if today.month >= 8:
        # We're in the new school year (Aug-Dec)
        start_year = today.year
    else:
        # We're in Jan-Jul, school year started previous August
        start_year = today.year - 1

    von = date(start_year, 8, 1)
    bis = date(today.year + YEARS_AHEAD, 9, 30)

    _LOGGER.debug(
        "Date range computed: %s → %s (today=%s, start_year=%s)",
        von, bis, today, start_year,
    )

    return von, bis


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

        _LOGGER.info(
            "Initializing FerienCoordinator for %s "
            "(national=%s, regional=%s)",
            self.bundesland,
            self.include_national,
            self.include_regional,
        )

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
            _LOGGER.info("Fetching Ferien for %s...", self.bundesland)
            ferien, ferien_missing = await fetch_ferien(
                self.hass, self.bundesland, von, bis
            )
            _LOGGER.info(
                "Ferien result: %d entries, missing years: %s",
                len(ferien), ferien_missing or "none",
            )

            # ── Fetch Feiertage (optional) ────────────────────────────
            feiertage: list[dict[str, Any]] | None = None
            feiertage_missing: list[int] = []

            if self.include_national or self.include_regional:
                _LOGGER.info(
                    "Fetching Feiertage for %s (national=%s, regional=%s)...",
                    self.bundesland,
                    self.include_national,
                    self.include_regional,
                )
                feiertage, feiertage_missing = await fetch_feiertage(
                    self.hass,
                    self.bundesland,
                    von,
                    bis,
                    include_national=self.include_national,
                    include_regional=self.include_regional,
                )
                _LOGGER.info(
                    "Feiertage result: %d entries, missing years: %s",
                    len(feiertage), feiertage_missing or "none",
                )
            else:
                _LOGGER.info("Feiertage disabled, skipping")

            # ── Write YAML (blocking I/O → executor) ─────────────────
            config_dir = self.hass.config.path()
            _LOGGER.info("Writing YAML to %s...", config_dir)
            self.last_yaml_path = await self.hass.async_add_executor_job(
                write_ferien_yaml,
                config_dir,
                self.bundesland,
                ferien,
                feiertage,
            )
            _LOGGER.info("YAML written to %s", self.last_yaml_path)

        except Exception as err:
            _LOGGER.error(
                "Error updating %s: %s", self.bundesland, err,
                exc_info=True,
            )
            raise UpdateFailed(
                f"Error updating {self.bundesland}: {err}"
            ) from err

        # ── Build result dict for sensors ─────────────────────────────
        today = date.today()
        today_str = today.isoformat()

        # Determine last year with Ferien data
        last_ferien_year = None
        if ferien:
            last_date = max(
                date.fromisoformat(f["end"]) for f in ferien
            )
            last_ferien_year = last_date.year

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
            "ferien_fehlende_jahre": ferien_missing,
            "feiertage_fehlende_jahre": feiertage_missing,
            "ferien_daten_bis": last_ferien_year,
            "ferien_vollstaendig": len(ferien_missing) == 0,
            "feiertage_vollstaendig": len(feiertage_missing) == 0,
            "daten_vollstaendig": (
                len(ferien_missing) == 0 and len(feiertage_missing) == 0
            ),
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

        # ── Log summary ───────────────────────────────────────────────
        _LOGGER.info(
            "Update complete for %s: %d Ferien (bis %s), %d Feiertage, "
            "heute_schulfrei=%s, naechste=%s, vollstaendig=%s",
            self.bundesland,
            result["ferien_count"],
            last_ferien_year or "?",
            result["feiertage_count"],
            result["heute_schulfrei"],
            result["naechste_ferien"],
            result["daten_vollstaendig"],
        )

        if ferien_missing:
            _LOGGER.warning(
                "Ferien data missing for %s: years %s "
                "(API has data up to %s)",
                self.bundesland,
                ferien_missing,
                last_ferien_year or "unknown",
            )

        if feiertage_missing:
            _LOGGER.warning(
                "Feiertage data missing for %s: years %s",
                self.bundesland,
                feiertage_missing,
            )

        return result