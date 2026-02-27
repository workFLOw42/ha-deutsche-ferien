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
)
from .yaml_writer import write_ferien_yaml

_LOGGER = logging.getLogger(__name__)

# OpenHolidaysAPI max range is 1095 days – we use 1090 to be safe
MAX_API_DAYS = 1090


def _compute_date_range() -> tuple[date, date]:
    """Compute date range: today → today + 1090 days.

    Simply fetches everything the API can deliver in one request.
    No school year logic needed – we just grab what's available.
    """
    today = date.today()
    bis = today + timedelta(days=MAX_API_DAYS)
    return today, bis


class FerienCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Manages fetching holiday data, computing sensor values, and writing YAML."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_data: dict[str, Any],
    ) -> None:
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
            "Updating %s: %s → %s (%d days)",
            self.bundesland, von, bis, (bis - von).days,
        )

        try:
            ferien = await fetch_ferien(
                self.hass, self.bundesland, von, bis
            )

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

            config_dir = self.hass.config.path()
            self.last_yaml_path = await self.hass.async_add_executor_job(
                write_ferien_yaml,
                config_dir,
                self.bundesland,
                ferien,
                feiertage,
            )
        except Exception as err:
            _LOGGER.error(
                "Error updating %s: %s", self.bundesland, err,
                exc_info=True,
            )
            raise UpdateFailed(
                f"Error updating {self.bundesland}: {err}"
            ) from err

        today = date.today()
        today_str = today.isoformat()

        # Last date with Ferien data
        last_ferien_date = None
        if ferien:
            last_ferien_date = max(f["end"] for f in ferien)

        result: dict[str, Any] = {
            "bundesland": self.bundesland,
            "ferien_count": len(ferien),
            "feiertage_count": len(feiertage) if feiertage else 0,
            "ferien": ferien,
            "feiertage": feiertage or [],
            "yaml_path": self.last_yaml_path,
            "von": von.isoformat(),
            "bis": bis.isoformat(),
            "ferien_daten_bis": last_ferien_date,
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

        # Current / next Ferien
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

        # Next Feiertag
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

        # Is today school-free?
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

        _LOGGER.info(
            "Done %s: %d Ferien (bis %s), %d Feiertage, schulfrei=%s",
            self.bundesland,
            result["ferien_count"],
            last_ferien_date or "?",
            result["feiertage_count"],
            result["heute_schulfrei"],
        )

        return result