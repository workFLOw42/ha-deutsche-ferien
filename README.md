# 🎒 Deutsche Schulferien & Feiertage

<img src="custom_components/deutsche_ferien/brand/logo@2x.png" alt="Logo" width="256">

[![HACS Validation](https://github.com/workFLOw42/ha-deutsche-ferien/actions/workflows/validate.yml/badge.svg)](https://github.com/workFLOw42/ha-deutsche-ferien/actions/workflows/validate.yml)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/workFLOw42/ha-deutsche-ferien)](https://github.com/workFLOw42/ha-deutsche-ferien/releases)
[![GitHub Downloads](https://img.shields.io/github/downloads/workFLOw42/ha-deutsche-ferien/total?label=Downloads&color=blue)](https://github.com/workFLOw42/ha-deutsche-ferien/releases)
[![HACS Downloads](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fanalytics.home-assistant.io%2Fcustom_integrations.json&query=%24.deutsche_ferien.total&label=HACS%20Installs&color=41BDF5)](https://github.com/workFLOw42/ha-deutsche-ferien)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Home Assistant Integration für **deutsche Schulferien und Feiertage** aller 16 Bundesländer.

---

## ✨ Features

- 📅 **Schulferien** aller 16 Bundesländer via [ferien-api.de](https://ferien-api.de)
- 🎌 **Nationale & regionale Feiertage** via [date.nager.at](https://date.nager.at)
- 📝 **YAML-Export** im HA-Konfigurationsverzeichnis (`{BL}_Ferien.yaml`)
- 🔄 **Tägliche automatische Aktualisierung** + manueller Update-Button
- 📊 **6 Sensoren**: Heute schulfrei?, Aktuelle/Nächste Ferien, Countdown, etc.
- 🤖 **Service** `deutsche_ferien.update_ferien` für Automationen & Scripts
- 🔮 Daten bis **3 Jahre im Voraus** (inkl. Sommerferien des Zieljahres)

---

## 📦 Installation

### HACS (empfohlen)

1. **HACS** → Integrationen → ⋮ (Menü oben rechts) → **Benutzerdefinierte Repositories**
2. Repository-URL: `https://github.com/workFLOw42/ha-deutsche-ferien`
3. Kategorie: **Integration**
4. **Installieren** und Home Assistant neu starten

### Manuell

1. Ordner `custom_components/deutsche_ferien/` in dein HA-Konfigurationsverzeichnis kopieren
2. Home Assistant neu starten

---

## ⚙️ Einrichtung

1. **Einstellungen** → **Geräte & Dienste** → **Integration hinzufügen**
2. Suche nach **„Deutsche Schulferien"**
3. **Bundesland** auswählen (z.B. Bayern)
4. Optional: **Nationale Feiertage** und/oder **Regionale Feiertage** aktivieren
5. Fertig! Die YAML-Datei wird sofort geschrieben.

> 💡 Du kannst die Integration mehrfach hinzufügen – für jedes Bundesland separat.

---

## 📊 Sensoren

| Sensor | Beispielwert |
|---|---|
| `sensor.ferien_bayern_heute_schulfrei` | `Ja` / `Nein` |
| `sensor.ferien_bayern_aktuelle_ferien` | `Pfingstferien 2026` / `Keine` |
| `sensor.ferien_bayern_naechste_ferien` | `Sommerferien 2026` |
| `sensor.ferien_bayern_tage_bis_ferien` | `42` |
| `sensor.ferien_bayern_naechster_feiertag` | `Fronleichnam` |
| `sensor.ferien_bayern_uebersicht` | `18 Ferien, 39 Feiertage` |

### 🔘 Button

| Entity | Beschreibung |
|---|---|
| `button.ferien_bayern_aktualisieren` | Manuelles Update der Daten auslösen |

### 📋 Sensor-Attribute (Beispiel: Übersicht)

| Attribut | Beschreibung |
|---|---|
| `ferien_count` | Anzahl Ferienabschnitte |
| `feiertage_count` | Anzahl Feiertage |
| `yaml_pfad` | Pfad zur erzeugten YAML-Datei |
| `zeitraum_von` | Startdatum des abgedeckten Zeitraums |
| `zeitraum_bis` | Enddatum des abgedeckten Zeitraums |
| `ferien_liste` | Alle Ferien als Liste |
| `feiertage_liste` | Alle Feiertage als Liste |

### 📋 Sensor-Attribute (Beispiel: Heute Schulfrei)

| Attribut | Beschreibung |
|---|---|
| `grund` | Name der Ferien / des Feiertags |

### 📋 Sensor-Attribute (Beispiel: Nächster Feiertag)

| Attribut | Beschreibung |
|---|---|
| `datum` | Datum des nächsten Feiertags |
| `tage_bis` | Tage bis zum nächsten Feiertag |

---

## 📝 YAML-Output

Die Integration erzeugt eine Datei `{BL}_Ferien.yaml` im HA-Konfigurationsverzeichnis (z.B. `BY_Ferien.yaml`):

```yaml
info:
  bundesland: "BY"
  erstellt: "2026-02-27T09:46:54"
  hinweis: "Automatisch generiert – nicht manuell bearbeiten"

ferien:
  - name: "Winterferien"
    von: "2026-02-16"
    bis: "2026-02-20"
  - name: "Osterferien"
    von: "2026-03-30"
    bis: "2026-04-10"
  - name: "Pfingstferien"
    von: "2026-05-26"
    bis: "2026-06-05"
  - name: "Sommerferien"
    von: "2026-07-30"
    bis: "2026-09-09"
  # ... weiter bis inkl. Sommerferien 2029

feiertage:
  - name: "Karfreitag"
    datum: "2026-04-03"
    wochentag: "Freitag"
    typ: "national"
  - name: "Fronleichnam"
    datum: "2026-06-04"
    wochentag: "Donnerstag"
    typ: "regional"
  - name: "Mariä Himmelfahrt"
    datum: "2026-08-15"
    wochentag: "Samstag"
    typ: "regional"
  # ...

alle_freien_tage:
  - datum: "2026-02-16"
    wochentag: "Montag"
    grund: "Winterferien"
  - datum: "2026-02-17"
    wochentag: "Dienstag"
    grund: "Winterferien"
  - datum: "2026-04-03"
    wochentag: "Freitag"
    grund: "Osterferien / Karfreitag"
  # ... jeder einzelne schulfreie Werktag