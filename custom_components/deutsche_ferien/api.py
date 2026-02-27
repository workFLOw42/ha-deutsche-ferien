"""API clients for openholidaysapi.org (Ferien + Feiertage)."""
from __future__ import annotations

import logging
from datetime import date
from typing import Any

import aiohttp

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

REQUEST_HEADERS = {
    "Accept": "application/json",
}


class FerienApiError(Exception):
    """Error communicating with holiday APIs."""


def _get_localized_name(name_list: list[dict], fallback: str = "Ferien") -> str:
    """Extract German name from OpenHolidaysAPI name array."""
    if not name_list:
        return fallback
    for entry in name_list:
        if entry.get("language") == "DE":
            return entry.get("text", fallback)
    return name_list[0].get("text", fallback)


async def _api_request(
    session: aiohttp.ClientSession,
    url: str,
    label: str,
) -> list[dict] | None:
    """Make an API request with error logging."""
    _LOGGER.debug("API request [%s]: %s", label, url)

    try:
        timeout = aiohttp.ClientTimeout(total=30)
        async with session.get(
            url, headers=REQUEST_HEADERS, timeout=timeout,
        ) as resp:
            if resp.status != 200:
                body = await resp.text()
                _LOGGER.error(
                    "API error [%s]: HTTP %s – %s",
                    label, resp.status, body[:300],
                )
                return None

            data = await resp.json()

            if not isinstance(data, list):
                _LOGGER.warning(
                    "API [%s]: unexpected response type %s",
                    label, type(data).__name__,
                )
                return None

            _LOGGER.debug("API [%s]: %d entries", label, len(data))
            return data

    except aiohttp.ClientError as err:
        _LOGGER.error("API client error [%s]: %s", label, err)
    except TimeoutError:
        _LOGGER.error("API timeout [%s]", label)
    except Exception as err:
        _LOGGER.error("API error [%s]: %s", label, err)

    return None


async def fetch_ferien(
    hass: HomeAssistant,
    bundesland: str,
    von: date,
    bis: date,
) -> list[dict[str, Any]]:
    """Fetch school holidays from OpenHolidaysAPI."""
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

    data = await _api_request(session, url, f"Ferien-{bundesland}")
    if data is None:
        return []

    ferien: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()

    for entry in data:
        try:
            start = date.fromisoformat(entry.get("startDate", ""))
            end = date.fromisoformat(entry.get("endDate", ""))
        except (ValueError, TypeError):
            continue

        name = _get_localized_name(entry.get("name", []), "Ferien")

        key = (name, start.isoformat(), end.isoformat())
        if key in seen:
            continue
        seen.add(key)

        ferien.append({
            "name": name,
            "start": start.isoformat(),
            "end": end.isoformat(),
        })

    ferien.sort(key=lambda x: x["start"])

    _LOGGER.info(
        "Ferien %s: %d entries (%s → %s)",
        bundesland, len(ferien), von, bis,
    )

    return ferien


async def fetch_feiertage(
    hass: HomeAssistant,
    bundesland: str,
    von: date,
    bis: date,
    include_national: bool = True,
    include_regional: bool = True,
) -> list[dict[str, Any]]:
    """Fetch public holidays from OpenHolidaysAPI."""
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

    data = await _api_request(session, url, f"Feiertage-{bundesland}")
    if data is None:
        return []

    feiertage: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    for entry in data:
        try:
            d = date.fromisoformat(entry.get("startDate", ""))
        except (ValueError, TypeError):
            continue

        name = _get_localized_name(entry.get("name", []), "Feiertag")

        nationwide = entry.get("nationwide", False)
        subdivisions = entry.get("subdivisions") or []
        subdivision_codes = [s.get("code", "") for s in subdivisions]
        is_regional = subdivision in subdivision_codes

        include = False
        tag_type = ""
        if nationwide and include_national:
            include = True
            tag_type = "national"
        elif is_regional and include_regional:
            include = True
            tag_type = "regional"
        elif not nationwide and not subdivisions and include_national:
            include = True
            tag_type = "national"

        if not include:
            continue

        key = (name, d.isoformat())
        if key in seen:
            continue
        seen.add(key)

        feiertage.append({
            "name": name,
            "datum": d.isoformat(),
            "wochentag": WOCHENTAGE[d.weekday()],
            "typ": tag_type,
        })

    feiertage.sort(key=lambda x: x["datum"])

    _LOGGER.info(
        "Feiertage %s: %d entries (%s → %s)",
        bundesland, len(feiertage), von, bis,
    )

    return feiertage