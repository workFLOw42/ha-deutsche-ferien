"""Sensor platform for Deutsche Schulferien & Feiertage."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import BUNDESLAENDER, DOMAIN
from .coordinator import FerienCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: FerienCoordinator = hass.data[DOMAIN][entry.entry_id]
    bl = coordinator.bundesland
    bl_name = BUNDESLAENDER.get(bl, bl)

    async_add_entities([
        FerienHeuteSchulfreiSensor(coordinator, bl, bl_name),
        FerienAktuelleSensor(coordinator, bl, bl_name),
        FerienNaechsteSensor(coordinator, bl, bl_name),
        FerienTagebisSensor(coordinator, bl, bl_name),
        FerienNaechsterFeiertagSensor(coordinator, bl, bl_name),
        FerienCountSensor(coordinator, bl, bl_name),
    ])


class _FerienBase(CoordinatorEntity[FerienCoordinator], SensorEntity):
    def __init__(self, coordinator, bl, bl_name, key, suffix):
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_{bl}_{key}"
        self._attr_name = f"Ferien {bl_name} {suffix}"
        self._attr_icon = "mdi:school-outline"
        self._attr_has_entity_name = False


class FerienHeuteSchulfreiSensor(_FerienBase):
    def __init__(self, coordinator, bl, bl_name):
        super().__init__(coordinator, bl, bl_name, "heute_schulfrei", "Heute Schulfrei")
        self._attr_icon = "mdi:party-popper"

    @property
    def native_value(self) -> str | None:
        if d := self.coordinator.data:
            return "Ja" if d.get("heute_schulfrei") else "Nein"
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if d := self.coordinator.data:
            if grund := d.get("heute_grund"):
                return {"grund": grund}
        return {}


class FerienAktuelleSensor(_FerienBase):
    def __init__(self, coordinator, bl, bl_name):
        super().__init__(coordinator, bl, bl_name, "aktuelle_ferien", "Aktuelle Ferien")
        self._attr_icon = "mdi:beach"

    @property
    def native_value(self) -> str | None:
        if d := self.coordinator.data:
            return d.get("aktuelle_ferien") or "Keine"
        return None


class FerienNaechsteSensor(_FerienBase):
    def __init__(self, coordinator, bl, bl_name):
        super().__init__(coordinator, bl, bl_name, "naechste_ferien", "Nächste Ferien")
        self._attr_icon = "mdi:calendar-arrow-right"

    @property
    def native_value(self) -> str | None:
        if d := self.coordinator.data:
            return d.get("naechste_ferien") or "Unbekannt"
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if d := self.coordinator.data:
            if s := d.get("naechste_ferien_start"):
                return {"start": s}
        return {}


class FerienTagebisSensor(_FerienBase):
    def __init__(self, coordinator, bl, bl_name):
        super().__init__(coordinator, bl, bl_name, "tage_bis_ferien", "Tage bis Ferien")
        self._attr_icon = "mdi:timer-sand"
        self._attr_native_unit_of_measurement = "Tage"

    @property
    def native_value(self) -> int | None:
        if d := self.coordinator.data:
            return d.get("tage_bis_naechste_ferien")
        return None


class FerienNaechsterFeiertagSensor(_FerienBase):
    def __init__(self, coordinator, bl, bl_name):
        super().__init__(coordinator, bl, bl_name, "naechster_feiertag", "Nächster Feiertag")
        self._attr_icon = "mdi:flag-variant"

    @property
    def native_value(self) -> str | None:
        if d := self.coordinator.data:
            return d.get("naechster_feiertag") or "Unbekannt"
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attrs: dict[str, Any] = {}
        if d := self.coordinator.data:
            if datum := d.get("naechster_feiertag_datum"):
                attrs["datum"] = datum
            if tage := d.get("tage_bis_naechster_feiertag"):
                attrs["tage_bis"] = tage
        return attrs


class FerienCountSensor(_FerienBase):
    def __init__(self, coordinator, bl, bl_name):
        super().__init__(coordinator, bl, bl_name, "uebersicht", "Übersicht")
        self._attr_icon = "mdi:counter"

    @property
    def native_value(self) -> str | None:
        if d := self.coordinator.data:
            fc = d.get("ferien_count", 0)
            ftc = d.get("feiertage_count", 0)
            bis = d.get("ferien_daten_bis", "")
            if bis:
                return f"{fc} Ferien (bis {bis}), {ftc} Feiertage"
            return f"{fc} Ferien, {ftc} Feiertage"
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attrs: dict[str, Any] = {}
        if d := self.coordinator.data:
            attrs["ferien_count"] = d.get("ferien_count", 0)
            attrs["feiertage_count"] = d.get("feiertage_count", 0)
            attrs["yaml_pfad"] = d.get("yaml_path", "")
            attrs["zeitraum_von"] = d.get("von", "")
            attrs["zeitraum_bis"] = d.get("bis", "")
            attrs["ferien_daten_bis"] = d.get("ferien_daten_bis")
            attrs["ferien_liste"] = [
                f"{f['name']}: {f['start']} – {f['end']}"
                for f in d.get("ferien", [])
            ]
            attrs["feiertage_liste"] = [
                f"{ft['name']}: {ft['datum']} ({ft['wochentag']})"
                for ft in d.get("feiertage", [])
            ]
        return attrs