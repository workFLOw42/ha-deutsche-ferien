"""API clients for openholidaysapi.org (Ferien + Feiertage)."""
from __future__ import annotations

import logging
import traceback
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
    """Make an API request with full error logging."""
    _LOGGER.info("API request [%s]: %s", label, url)

    try:
        timeout = aiohttp.ClientTimeout(total=30)
        async with session.get(
            url,
            headers=REQUEST_HEADERS,
            timeout=timeout,
        ) as resp:
            _LOGGER.info(
                "API response [%s]: HTTP %s, Content-Type: %s",
                label,
                resp.status,
                resp.content_type,
            )

            if resp.status != 200:
                body = await resp.text()
                _LOGGER.error(
                    "API error [%s]: HTTP %s – %s",
                    label, resp.status, body[:500],
                )
                return None

            data = await resp.json()

            if isinstance(data, list):
                _LOGGER.info(
                    "API success [%s]: %d entries received",
                    label, len(data),
                )
            else:
                _LOGGER.warning(
                    "API unexpected [%s]: response is %s, not list",
                    label, type(data).__name__,
                )
                return None

            return data

    except aiohttp.ClientError as err:
        _LOGGER.error("API client error [%s]: %s", label, err)
        return None
    except TimeoutError:
        _LOGGER.error("API timeout [%s]: %s", label, url)
        return None
    except Exception as err:
        _LOGGER.error(
            "API unexpected error [%s]: %s\n%s",
            label, err, traceback.format_exc(),
        )
        return None


async def fetch_ferien(
    hass: HomeAssistant,
    bundesland: str,
    von: date,
    bis: date,
) -> tuple[list[dict[str, Any]], list[int]]:
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

    ferien: list[dict[str, Any]] = []
    all_years = list(range(von.year, bis.year + 1))

    data = await _api_request(session, url, f"Ferien-{bundesland}")
    if data is None:
        return ferien, all_years

    seen: set[tuple[str, str, str]] = set()
    years_with_data: set[int] = set()

    for i, entry in enumerate(data):
        try:
            start_str = entry.get("startDate", "")
            end_str = entry.get("endDate", "")

            if not start_str or not end_str:
                _LOGGER.warning(
                    "Entry %d missing dates: %s", i, entry
                )
                continue

            start = date.fromisoformat(start_str)
            end = date.fromisoformat(end_str)
        except (ValueError, TypeError) as err:
            _LOGGER.warning(
                "Entry %d date parse error: %s – %s", i, entry, err
            )
            continue

        name = _get_localized_name(entry.get("name", []), "Ferien")

        years_with_data.add(start.year)
        years_with_data.add(end.year)

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

    requested_years = set(range(von.year, bis.year + 1))
    missing_years = sorted(requested_years - years_with_data)

    ferien.sort(key=lambda x: x["start"])

    _LOGGER.info(
        "RESULT Ferien %s: %d entries, years with data: %s, missing: %s",
        bundesland,
        len(ferien),
        sorted(years_with_data),
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

    feiertage: list[dict[str, Any]] = []
    all_years = list(range(von.year, bis.year + 1))

    data = await _api_request(session, url, f"Feiertage-{bundesland}")
    if data is None:
        return feiertage, all_years

    seen: set[tuple[str, str]] = set()
    years_with_data: set[int] = set()

    for i, entry in enumerate(data):
        try:
            d = date.fromisoformat(entry.get("startDate", ""))
        except (ValueError, TypeError):
            _LOGGER.warning("Entry %d date parse error: %s", i, entry)
            continue

        name = _get_localized_name(entry.get("name", []), "Feiertag")

        # Determine type based on API response
        nationwide = entry.get("nationwide", False)
        subdivisions = entry.get("subdivisions") or []
        subdivision_codes = [s.get("code", "") for s in subdivisions]
        is_regional = subdivision in subdivision_codes

        # When subdivisionCode is set in request, API returns
        # both national and regional holidays for that subdivision.
        # We need to classify them correctly.
        include = False
        tag_type = ""

        if nationwide and include_national:
            include = True
            tag_type = "national"
        elif is_regional and include_regional:
            include = True
            tag_type = "regional"
        elif not nationwide and not subdivisions and include_national:
            # Edge case: no subdivision info, treat as national
            include = True
            tag_type = "national"

        if not include:
            _LOGGER.debug(
                "Skipping Feiertag '%s' (%s): nationwide=%s, regional=%s, "
                "include_national=%s, include_regional=%s",
                name, d, nationwide, is_regional,
                include_national, include_regional,
            )
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
        "RESULT Feiertage %s: %d entries, years with data: %s, missing: %s",
        bundesland,
        len(feiertage),
        sorted(years_with_data),
        missing_years or "none",
    )

    return feiertage, missing_years