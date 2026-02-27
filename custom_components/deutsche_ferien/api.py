"""API clients for ferien-api.de and date.nager.at."""
from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import BUNDESLAND_TO_COUNTY

_LOGGER = logging.getLogger(__name__)

FERIEN_API_BASE = "https://ferien-api.de/api/v1/holidays"
NAGER_API_BASE = "https://date.nager.at/api/v3/PublicHolidays"

WOCHENTAGE = [
    "Montag",
    "Dienstag",
    "Mittwoch",
    "Donnerstag",
    "Freitag",
    "Samstag",
    "Sonntag",
]


class FerienApiError(Exception):
    """Error communicating with holiday APIs."""


def _parse_iso_date(raw: str) -> date:
    """Parse an ISO date string, tolerating trailing time/timezone parts."""
    return datetime.fromisoformat(raw.replace("Z", "+00:00")).date()


async def fetch_ferien(
    hass: HomeAssistant,
    bundesland: str,
    von: date,
    bis: date,
) -> tuple[list[dict[str, Any]], list[int]]:
    """Fetch ALL school holidays for a Bundesland, then filter by date range.

    Uses the /api/v1/holidays/{state} endpoint which returns ALL available
    years in a single request – much more reliable than per-year requests.

    Returns:
        Tuple of (ferien_list, missing_years)
    """
    session = async_get_clientsession(hass)
    url = f"{FERIEN_API_BASE}/{bundesland}"
    _LOGGER.debug("Fetching ALL Ferien for %s: %s", bundesland, url)

    ferien: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    years_with_data: set[int] = set()
    missing_years: list[int] = []

    try:
        async with session.get(url, timeout=30) as resp:
            if resp.status != 200:
                _LOGGER.error("HTTP %s for %s", resp.status, url)
                missing_years = list(range(von.year, bis.year + 1))
                return ferien, missing_years
            data = await resp.json()
    except Exception as err:
        _LOGGER.error("Error fetching %s: %s", url, err)
        missing_years = list(range(von.year, bis.year + 1))
        return ferien, missing_years

    if not data:
        _LOGGER.warning("Empty response from %s", url)
        missing_years = list(range(von.year, bis.year + 1))
        return ferien, missing_years

    _LOGGER.debug(
        "Received %d total holiday entries for %s", len(data), bundesland
    )

    for entry in data:
        try:
            start = _parse_iso_date(entry.get("start", ""))
            end = _parse_iso_date(entry.get("end", ""))
        except (ValueError, TypeError) as err:
            _LOGGER.warning("Cannot parse dates in %s: %s", entry, err)
            continue

        name = entry.get("name", "Ferien")
        slug = entry.get("slug", "")

        # Track which years have data
        years_with_data.add(start.year)
        years_with_data.add(end.year)

        # De-duplicate
        key = (name, start.isoformat(), end.isoformat())
        if key in seen:
            continue
        seen.add(key)

        # Only include if overlapping with requested range
        if end < von or start > bis:
            continue

        # Clip to requested range
        ferien.append(
            {
                "name": name,
                "slug": slug,
                "start": max(start, von).isoformat(),
                "end": min(end, bis).isoformat(),
            }
        )

    # Determine which requested years have no data
    requested_years = set(range(von.year, bis.year + 1))
    missing_years = sorted(requested_years - years_with_data)

    if missing_years:
        _LOGGER.warning(
            "No Ferien data available for %s years: %s "
            "(ferien-api.de may not have published data yet)",
            bundesland,
            missing_years,
        )

    ferien.sort(key=lambda x: x["start"])

    _LOGGER.info(
        "Fetched %d Ferien for %s (%s → %s), missing years: %s",
        len(ferien),
        bundesland,
        von,
        bis,
        missing_years or "none",
    )

    return ferien, missing_years


async def fetch_feiertage(
    hass: HomeAssistant,
    bundesland: str,
    von: date,
    bis: date,
    include_national: bool = True,
    include_regional: bool = True,
) -> tuple[list[dict[str, Any]], list[int]]:
    """Fetch public holidays (national and/or regional).

    Note: date.nager.at requires per-year requests – no bulk endpoint available.

    Returns:
        Tuple of (feiertage_list, missing_years)
    """
    session = async_get_clientsession(hass)
    county_code = BUNDESLAND_TO_COUNTY.get(bundesland, f"DE-{bundesland}")
    jahre = sorted(set(range(von.year, bis.year + 1)))
    feiertage: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    missing_years: list[int] = []

    for jahr in jahre:
        url = f"{NAGER_API_BASE}/{jahr}/DE"
        _LOGGER.debug("Fetching Feiertage: %s", url)

        try:
            async with session.get(url, timeout=15) as resp:
                if resp.status != 200:
                    _LOGGER.error("HTTP %s for %s", resp.status, url)
                    missing_years.append(jahr)
                    continue
                data = await resp.json()
        except Exception as err:
            _LOGGER.error("Error fetching %s: %s", url, err)
            missing_years.append(jahr)
            continue

        if not data:
            missing_years.append(jahr)
            continue

        for entry in data:
            try:
                d = date.fromisoformat(entry["date"])
            except (ValueError, TypeError):
                continue

            if d < von or d > bis:
                continue

            name = entry.get("localName", entry.get("name", "Feiertag"))
            counties = entry.get("counties") or []

            is_national = len(counties) == 0
            is_regional = county_code in counties

            include = False
            tag_type = ""
            if is_national and include_national:
                include = True
                tag_type = "national"
            elif is_regional and include_regional:
                include = True
                tag_type = "regional"

            if not include:
                continue

            key = (name, d.isoformat())
            if key in seen:
                continue
            seen.add(key)

            feiertage.append(
                {
                    "name": name,
                    "datum": d.isoformat(),
                    "wochentag": WOCHENTAGE[d.weekday()],
                    "typ": tag_type,
                }
            )

    feiertage.sort(key=lambda x: x["datum"])
    return feiertage, missing_years