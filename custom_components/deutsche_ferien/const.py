"""Constants for Deutsche Schulferien & Feiertage integration."""
from __future__ import annotations

DOMAIN = "deutsche_ferien"

CONF_BUNDESLAND = "bundesland"
CONF_FEIERTAGE_NATIONAL = "feiertage_national"
CONF_FEIERTAGE_REGIONAL = "feiertage_regional"

DEFAULT_SCAN_INTERVAL = 86400
YEARS_AHEAD = 3

BUNDESLAENDER: dict[str, str] = {
    "BW": "Baden-Württemberg",
    "BY": "Bayern",
    "BE": "Berlin",
    "BB": "Brandenburg",
    "HB": "Bremen",
    "HH": "Hamburg",
    "HE": "Hessen",
    "MV": "Mecklenburg-Vorpommern",
    "NI": "Niedersachsen",
    "NW": "Nordrhein-Westfalen",
    "RP": "Rheinland-Pfalz",
    "SL": "Saarland",
    "SN": "Sachsen",
    "ST": "Sachsen-Anhalt",
    "SH": "Schleswig-Holstein",
    "TH": "Thüringen",
}

# OpenHolidaysAPI uses DE-XX subdivision codes
BUNDESLAND_TO_SUBDIVISION: dict[str, str] = {
    code: f"DE-{code}" for code in BUNDESLAENDER
}