"""YAML writer – exports Ferien & Feiertage to {BL}_Ferien.yaml in HA config root."""
from __future__ import annotations

import logging
import os
from collections import OrderedDict
from datetime import date, datetime, timedelta
from typing import Any

import yaml

_LOGGER = logging.getLogger(__name__)

WOCHENTAGE = [
    "Montag",
    "Dienstag",
    "Mittwoch",
    "Donnerstag",
    "Freitag",
    "Samstag",
    "Sonntag",
]


# ── Custom YAML representers ──────────────────────────────────────────────


def _represent_ordereddict(dumper: yaml.Dumper, data: OrderedDict) -> Any:
    """Preserve insertion order."""
    return dumper.represent_mapping("tag:yaml.org,2002:map", data.items())


def _represent_str(dumper: yaml.Dumper, data: str) -> Any:
    """Quote date-like strings so YAML loaders don't auto-convert them."""
    if len(data) == 10 and data[4:5] == "-" and data[7:8] == "-":
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style='"')
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


yaml.add_representer(OrderedDict, _represent_ordereddict)
yaml.add_representer(str, _represent_str)


# ── Public API ─────────────────────────────────────────────────────────────


def write_ferien_yaml(
    hass_config_dir: str,
    bundesland: str,
    ferien: list[dict[str, Any]],
    feiertage: list[dict[str, Any]] | None = None,
) -> str:
    """Write the YAML file and return the absolute file path."""
    filename = f"{bundesland}_Ferien.yaml"
    filepath = os.path.join(hass_config_dir, filename)

    # ── Build document ────────────────────────────────────────────────
    doc = OrderedDict()

    doc["info"] = OrderedDict(
        [
            ("bundesland", bundesland),
            ("erstellt", datetime.now().isoformat(timespec="seconds")),
            ("hinweis", "Automatisch generiert – nicht manuell bearbeiten"),
        ]
    )

    # ── Ferien ────────────────────────────────────────────────────────
    ferien_list = []
    for f in ferien:
        ferien_list.append(
            OrderedDict(
                [
                    ("name", f["name"]),
                    ("von", f["start"]),
                    ("bis", f["end"]),
                ]
            )
        )
    doc["ferien"] = ferien_list

    # ── Feiertage ─────────────────────────────────────────────────────
    if feiertage:
        ft_list = []
        for ft in feiertage:
            ft_list.append(
                OrderedDict(
                    [
                        ("name", ft["name"]),
                        ("datum", ft["datum"]),
                        ("wochentag", ft["wochentag"]),
                        ("typ", ft.get("typ", "national")),
                    ]
                )
            )
        doc["feiertage"] = ft_list

    # ── Expanded free days (individual school-free weekdays) ──────────
    alle_tage: dict[date, str] = {}

    for f in ferien:
        start = date.fromisoformat(f["start"])
        end = date.fromisoformat(f["end"])
        current = start
        while current <= end:
            if current.weekday() < 5:  # Mo–Fr
                alle_tage[current] = f["name"]
            current += timedelta(days=1)

    if feiertage:
        for ft in feiertage:
            d = date.fromisoformat(ft["datum"])
            if d in alle_tage:
                alle_tage[d] = f"{alle_tage[d]} / {ft['name']}"
            else:
                alle_tage[d] = ft["name"]

    expanded = []
    for d in sorted(alle_tage.keys()):
        expanded.append(
            OrderedDict(
                [
                    ("datum", d.isoformat()),
                    ("wochentag", WOCHENTAGE[d.weekday()]),
                    ("grund", alle_tage[d]),
                ]
            )
        )
    doc["alle_freien_tage"] = expanded

    # ── Write file ────────────────────────────────────────────────────
    with open(filepath, "w", encoding="utf-8") as fh:
        yaml.dump(
            doc,
            fh,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
            width=120,
        )

    _LOGGER.info(
        "Wrote %s (%d Ferien, %d Feiertage, %d freie Tage)",
        filepath,
        len(ferien),
        len(feiertage) if feiertage else 0,
        len(expanded),
    )
    return filepath