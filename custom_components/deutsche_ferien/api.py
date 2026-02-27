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
) -> list[dict[str, Any]]:
    """Fetch school holidays for a Bundesland.

    Returns:
        [{"name": "...", "slug": "...", "start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}, ...]
    """
    session = async_get_clientsession(hass)
    jahre = sorted(set(range(von.year, bis.year + 1)))
    ferien: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()

    for jahr in jahre:
        url = f"{FERIEN_API_BASE}/{bundesland}/{jahr}"
        _LOGGER.debug("Fetching Ferien: %s", url)

        try:
            async with session.get(url, timeout=15) as resp:
                if resp.status == 404:
                    _LOGGER.warning(
                        "No holiday data for %s/%s (404) – "
                        "ferien-api.de may not have data yet",
                        bundesland,
                        jahr,
                    )
                    continue
                if resp.status != 200:
                    _LOGGER.error("HTTP %s for %s", resp.status, url)
                    continue
                data = await resp.json()
        except Exception as err:
            _LOGGER.error("Error fetching %s: %s", url, err)
            continue

        for entry in data:
            try:
                start = _parse_iso_date(entry.get("start", ""))
                end = _parse_iso_date(entry.get("end", ""))
            except (ValueError, TypeError) as err:
                _LOGGER.warning("Cannot parse dates in %s: %s", entry, err)
                continue

            name = entry.get("name", "Ferien")
            slug = entry.get("slug", "")

            # De-duplicate across year boundaries
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

    ferien.sort(key=lambda x: x["start"])
    return ferien


async def fetch_feiertage(
    hass: HomeAssistant,
    bundesland: str,
    von: date,
    bis: date,
    include_national: bool = True,
    include_regional: bool = True,
) -> list[dict[str, Any]]:
    """Fetch public holidays (national and/or regional).

    Returns:
        [{"name": "...", "datum": "YYYY-MM-DD", "wochentag": "...", "typ": "..."}, ...]
    """
    session = async_get_clientsession(hass)
    county_code = BUNDESLAND_TO_COUNTY.get(bundesland, f"DE-{bundesland}")
    jahre = sorted(set(range(von.year, bis.year + 1)))
    feiertage: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    for jahr in jahre:
        url = f"{NAGER_API_BASE}/{jahr}/DE"
        _LOGGER.debug("Fetching Feiertage: %s", url)

        try:
            async with session.get(url, timeout=15) as resp:
                if resp.status != 200:
                    _LOGGER.error("HTTP %s for %s", resp.status, url)
                    continue
                data = await resp.json()
        except Exception as err:
            _LOGGER.error("Error fetching %s: %s", url, err)
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

            # National holidays have no counties list
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
    return feiertage