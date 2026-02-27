"""API clients for openholidaysapi.org (Ferien + Feiertage)."""
from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import BUNDESLAND_TO_SUBDIVISION

_LOGGER = logging.getLogger(__name__)

OPENHOLIDAYS_BASE = "https://openholidaysapi.org"

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


def _get_localized_name(name_list: list[dict], fallback: str = "Ferien") -> str:
    """Extract German name from OpenHolidaysAPI name array."""
    for entry in name_list:
        if entry.get("language") == "DE":
            return entry.get("text", fallback)
    # Fallback to first entry
    if name_list:
        return name_list[0].get("text", fallback)
    return fallback


async def fetch_ferien(
    hass: HomeAssistant,
    bundesland: str,
    von: date,
    bis: date,
) -> tuple[list[dict[str, Any]], list[int]]:
    """Fetch school holidays from OpenHolidaysAPI.

    Returns:
        Tuple of (ferien_list, missing_years)
    """
    session = async_get_clientsession(hass)
    subdivision = BUNDESLAND_TO_SUBDIVISION.get(bundesland, f"DE-{bundesland}")

    url = (
        f"{OPENHOLIDAYS_BASE}/SchoolHolidays"
        f"?countryIsoCode=DE"
        f"&languageIsoCode=DE"
        f"&validFrom={von.isoformat()}"
        f"&validTo={bis.isoformat()}"
        f"&subdivisionCode={subdivision}"
    )

    _LOGGER.debug("Fetching Ferien: %s", url)

    ferien: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    years_with_data: set[int] = set()

    try:
        async with session.get(url, timeout=30) as resp:
            if resp.status != 200:
                _LOGGER.error("HTTP %s for %s", resp.status, url)
                return ferien, list(range(von.year, bis.year + 1))
            data = await resp.json()
    except Exception as err:
        _LOGGER.error("Error fetching %s: %s", url, err)
        return ferien, list(range(von.year, bis.year + 1))

    if not data:
        _LOGGER.warning("Empty response from %s", url)
        return ferien, list(range(von.year, bis.year + 1))

    _LOGGER.debug("Received %d school holiday entries", len(data))

    for entry in data:
        try:
            start = date.fromisoformat(entry.get("startDate", ""))
            end = date.fromisoformat(entry.get("endDate", ""))
        except (ValueError, TypeError) as err:
            _LOGGER.warning("Cannot parse dates in %s: %s", entry, err)
            continue

        name = _get_localized_name(entry.get("name", []), "Ferien")

        years_with_data.add(start.year)
        years_with_data.add(end.year)

        # De-duplicate
        key = (name, start.isoformat(), end.isoformat())
        if key in seen:
            continue
        seen.add(key)

        ferien.append(
            {
                "name": name,
                "start": start.isoformat(),
                "end": end.isoformat(),
            }
        )

    # Determine missing years
    requested_years = set(range(von.year, bis.year + 1))
    missing_years = sorted(requested_years - years_with_data)

    if missing_years:
        _LOGGER.warning(
            "No Ferien data for years: %s", missing_years
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
    """Fetch public holidays from OpenHolidaysAPI.

    Returns:
        Tuple of (feiertage_list, missing_years)
    """
    session = async_get_clientsession(hass)
    subdivision = BUNDESLAND_TO_SUBDIVISION.get(bundesland, f"DE-{bundesland}")

    url = (
        f"{OPENHOLIDAYS_BASE}/PublicHolidays"
        f"?countryIsoCode=DE"
        f"&languageIsoCode=DE"
        f"&validFrom={von.isoformat()}"
        f"&validTo={bis.isoformat()}"
        f"&subdivisionCode={subdivision}"
    )

    _LOGGER.debug("Fetching Feiertage: %s", url)

    feiertage: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    years_with_data: set[int] = set()

    try:
        async with session.get(url, timeout=30) as resp:
            if resp.status != 200:
                _LOGGER.error("HTTP %s for %s", resp.status, url)
                return feiertage, list(range(von.year, bis.year + 1))
            data = await resp.json()
    except Exception as err:
        _LOGGER.error("Error fetching %s: %s", url, err)
        return feiertage, list(range(von.year, bis.year + 1))

    if not data:
        return feiertage, list(range(von.year, bis.year + 1))

    _LOGGER.debug("Received %d public holiday entries", len(data))

    for entry in data:
        try:
            d = date.fromisoformat(entry.get("startDate", ""))
        except (ValueError, TypeError):
            continue

        name = _get_localized_name(entry.get("name", []), "Feiertag")

        # Determine type
        is_national = entry.get("nationwide", False)
        subdivisions = entry.get("subdivisions") or []
        subdivision_codes = [s.get("code", "") for s in subdivisions]
        is_regional = subdivision in subdivision_codes

        # Filter based on user preferences
        include = False
        tag_type = ""
        if is_national and include_national:
            include = True
            tag_type = "national"
        elif is_regional and include_regional:
            include = True
            tag_type = "regional"
        elif not subdivisions and include_national:
            # No subdivision info = treat as national
            include = True
            tag_type = "national"

        if not include:
            continue

        years_with_data.add(d.year)

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

    requested_years = set(range(von.year, bis.year + 1))
    missing_years = sorted(requested_years - years_with_data)

    feiertage.sort(key=lambda x: x["datum"])

    _LOGGER.info(
        "Fetched %d Feiertage for %s (%s → %s), missing years: %s",
        len(feiertage),
        bundesland,
        von,
        bis,
        missing_years or "none",
    )

    return feiertage, missing_years