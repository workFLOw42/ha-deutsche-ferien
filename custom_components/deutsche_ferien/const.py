"""Constants for Deutsche Schulferien & Feiertage integration."""
from __future__ import annotations

DOMAIN = "deutsche_ferien"

CONF_BUNDESLAND = "bundesland"
CONF_FEIERTAGE_NATIONAL = "feiertage_national"
CONF_FEIERTAGE_REGIONAL = "feiertage_regional"

# Refresh once per day (seconds)
DEFAULT_SCAN_INTERVAL = 86400

# How many years ahead to fetch (including summer holidays of target year)
YEARS_AHEAD = 3

# All 16 Bundesländer: code → name
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

# Mapping to date.nager.at county codes
BUNDESLAND_TO_COUNTY: dict[str, str] = {
    code: f"DE-{code}" for code in BUNDESLAENDER
}