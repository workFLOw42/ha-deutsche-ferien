# 🎒 Deutsche Schulferien & Feiertage

<p align="center">
  <img src="https://raw.githubusercontent.com/workFLOw42/ha-deutsche-ferien/main/images/logo-hires.png" alt="Deutsche Schulferien & Feiertage" width="256">
</p>

<p align="center">
  <a href="https://github.com/workFLOw42/ha-deutsche-ferien/actions/workflows/validate.yml">
    <img src="https://github.com/workFLOw42/ha-deutsche-ferien/actions/workflows/validate.yml/badge.svg" alt="Validate Integration">
  </a>
  <a href="https://github.com/hacs/integration">
    <img src="https://img.shields.io/badge/HACS-Custom-41BDF5.svg" alt="HACS Custom">
  </a>
  <a href="https://github.com/workFLOw42/ha-deutsche-ferien/releases">
    <img src="https://img.shields.io/github/v/release/workFLOw42/ha-deutsche-ferien" alt="GitHub Release">
  </a>
  <a href="https://github.com/workFLOw42/ha-deutsche-ferien/releases">
    <img src="https://img.shields.io/github/downloads/workFLOw42/ha-deutsche-ferien/total?label=Downloads&color=blue" alt="Downloads">
  </a>
  <a href="https://github.com/workFLOw42/ha-deutsche-ferien">
    <img src="https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fanalytics.home-assistant.io%2Fcustom_integrations.json&query=%24.deutsche_ferien.total&label=HACS%20Installs&color=41BDF5" alt="HACS Installs">
  </a>
  <a href="https://github.com/workFLOw42/ha-deutsche-ferien/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT">
  </a>
</p>

<p align="center">
  Home Assistant Integration für <strong>deutsche Schulferien und Feiertage</strong> aller 16 Bundesländer.
</p>

---

## ✨ Features

- 📅 **Schulferien** aller 16 Bundesländer via [OpenHolidaysAPI](https://openholidaysapi.org)
- 🎌 **Nationale & regionale Feiertage** aus derselben Quelle
- 📝 **YAML-Export** im HA-Konfigurationsverzeichnis (`{BL}_Ferien.yaml`)
- 🔄 **Tägliche automatische Aktualisierung** + manueller Update-Button
- 📊 **6 Sensoren**: Heute schulfrei?, Aktuelle/Nächste Ferien, Countdown, etc.
- 🤖 **Service** `deutsche_ferien.update_ferien` für Automationen & Scripts
- 🔮 Daten für die **nächsten ~3 Jahre** – alles was die API liefert

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
| `sensor.ferien_bayern_aktuelle_ferien` | `Pfingstferien` / `Keine` |
| `sensor.ferien_bayern_naechste_ferien` | `Sommerferien` |
| `sensor.ferien_bayern_tage_bis_ferien` | `42` |
| `sensor.ferien_bayern_naechster_feiertag` | `Fronleichnam` |
| `sensor.ferien_bayern_uebersicht` | `15 Ferien (bis 2029-01-07), 30 Feiertage` |

### 🔘 Button

| Entity | Beschreibung |
|---|---|
| `button.ferien_bayern_aktualisieren` | Manuelles Update der Daten auslösen |

### 📋 Sensor-Attribute

<details>
<summary><strong>Heute Schulfrei</strong></summary>

| Attribut | Beschreibung |
|---|---|
| `grund` | Name der Ferien / des Feiertags |

</details>

<details>
<summary><strong>Nächste Ferien</strong></summary>

| Attribut | Beschreibung |
|---|---|
| `start` | Startdatum der nächsten Ferien |

</details>

<details>
<summary><strong>Nächster Feiertag</strong></summary>

| Attribut | Beschreibung |
|---|---|
| `datum` | Datum des nächsten Feiertags |
| `tage_bis` | Tage bis zum nächsten Feiertag |

</details>

<details>
<summary><strong>Übersicht</strong></summary>

| Attribut | Beschreibung |
|---|---|
| `ferien_count` | Anzahl Ferienabschnitte |
| `feiertage_count` | Anzahl Feiertage |
| `yaml_pfad` | Pfad zur erzeugten YAML-Datei |
| `zeitraum_von` | Startdatum des abgedeckten Zeitraums |
| `zeitraum_bis` | Enddatum des abgedeckten Zeitraums |
| `ferien_daten_bis` | Letztes Datum mit verfügbaren Feriendaten |
| `ferien_liste` | Alle Ferien als Liste |
| `feiertage_liste` | Alle Feiertage als Liste |

</details>

---

## 📝 YAML-Output

Die Integration erzeugt eine Datei `{BL}_Ferien.yaml` im HA-Konfigurationsverzeichnis (z.B. `BY_Ferien.yaml`):

<details>
<summary><strong>Beispiel: BY_Ferien.yaml</strong></summary>

```yaml
info:
  bundesland: "BY"
  erstellt: "2026-02-27T15:30:00"
  hinweis: "Automatisch generiert – nicht manuell bearbeiten"

ferien:
  - name: "Osterferien"
    von: "2026-03-30"
    bis: "2026-04-10"
  - name: "Pfingstferien"
    von: "2026-05-26"
    bis: "2026-06-05"
  - name: "Sommerferien"
    von: "2026-08-03"
    bis: "2026-09-14"
  - name: "Herbstferien"
    von: "2026-11-02"
    bis: "2026-11-06"
  - name: "Buß- und Bettag"
    von: "2026-11-18"
    bis: "2026-11-18"
  - name: "Weihnachtsferien"
    von: "2026-12-24"
    bis: "2027-01-08"
  # ... weiter bis ~2029

feiertage:
  - name: "Karfreitag"
    datum: "2026-04-03"
    wochentag: "Freitag"
    typ: "national"
  - name: "Fronleichnam"
    datum: "2026-06-04"
    wochentag: "Donnerstag"
    typ: "regional"
  - name: "Tag der Deutschen Einheit"
    datum: "2026-10-03"
    wochentag: "Samstag"
    typ: "national"
  - name: "Allerheiligen"
    datum: "2026-11-01"
    wochentag: "Sonntag"
    typ: "regional"
  # ...

alle_freien_tage:
  - datum: "2026-03-30"
    wochentag: "Montag"
    grund: "Osterferien"
  - datum: "2026-04-03"
    wochentag: "Freitag"
    grund: "Osterferien / Karfreitag"
  # ... jeder einzelne schulfreie Werktag
```

</details>

---

## 🤖 Automationen & Scripts

### Service aufrufen

```yaml
service: deutsche_ferien.update_ferien
```

### Automation: Monatliches Update

```yaml
automation:
  - alias: "Ferien monatlich aktualisieren"
    trigger:
      - platform: time
        at: "03:00:00"
    condition:
      - condition: template
        value_template: "{{ now().day == 1 }}"
    action:
      - service: deutsche_ferien.update_ferien
```

### Script: Manuelles Update

```yaml
script:
  ferien_update:
    alias: "Ferien Daten aktualisieren"
    sequence:
      - service: deutsche_ferien.update_ferien
```

### Template-Sensor: Schulstatus

```yaml
template:
  - sensor:
      - name: "Schulstatus"
        state: >
          {% if is_state('sensor.ferien_bayern_heute_schulfrei', 'Ja') %}
            Schulfrei – {{ state_attr('sensor.ferien_bayern_heute_schulfrei', 'grund') }}
          {% else %}
            Schule
          {% endif %}
```

### Automation: Benachrichtigung vor Ferienstart

```yaml
automation:
  - alias: "Ferien starten morgen"
    trigger:
      - platform: numeric_state
        entity_id: sensor.ferien_bayern_tage_bis_ferien
        below: 2
    action:
      - service: notify.mobile_app
        data:
          title: "🎒 Ferien!"
          message: >
            {{ states('sensor.ferien_bayern_naechste_ferien') }} starten
            in {{ states('sensor.ferien_bayern_tage_bis_ferien') }} Tag(en)!
```

### Automation: HACS Update verfügbar

```yaml
automation:
  - alias: "HACS Update verfügbar"
    trigger:
      - platform: state
        entity_id: sensor.hacs
    condition:
      - condition: template
        value_template: "{{ states('sensor.hacs') | int > 0 }}"
    action:
      - service: notify.mobile_app
        data:
          title: "🔄 HACS Update"
          message: "{{ states('sensor.hacs') }} Update(s) verfügbar!"
          data:
            clickAction: /hacs
```

---

## 🗺️ Unterstützte Bundesländer

| Kürzel | Bundesland | Kürzel | Bundesland |
|---|---|---|---|
| BW | Baden-Württemberg | NI | Niedersachsen |
| BY | Bayern | NW | Nordrhein-Westfalen |
| BE | Berlin | RP | Rheinland-Pfalz |
| BB | Brandenburg | SL | Saarland |
| HB | Bremen | SN | Sachsen |
| HH | Hamburg | ST | Sachsen-Anhalt |
| HE | Hessen | SH | Schleswig-Holstein |
| MV | Mecklenburg-Vorpommern | TH | Thüringen |

---

## 🌐 Datenquelle

| Quelle | API | Daten |
|---|---|---|
| [OpenHolidaysAPI](https://openholidaysapi.org) | `/SchoolHolidays` | Schulferien aller Bundesländer |
| [OpenHolidaysAPI](https://openholidaysapi.org) | `/PublicHolidays` | Nationale & regionale Feiertage |

Die Integration fragt ab heute die **nächsten ~3 Jahre** ab (1090 Tage, innerhalb des API-Limits von 1095 Tagen). Alles was die API liefert, wird übernommen – ohne künstliche Einschränkungen.

> **Seit v2.0.0**: Beide Datenquellen (Ferien + Feiertage) kommen von [OpenHolidaysAPI](https://openholidaysapi.org) – einer aktiv gepflegten, kostenlosen API.
>
> v1.x nutzte ferien-api.de (nicht mehr gepflegt, nur bis 2026) und date.nager.at.

---

## 🔄 Migration von v1.x auf v2.0

| | v1.x | v2.0 |
|---|---|---|
| Ferien-Quelle | ferien-api.de (veraltet) | openholidaysapi.org ✅ |
| Feiertage-Quelle | date.nager.at | openholidaysapi.org ✅ |
| Ferien-Daten bis | 2026 | ~2029 ✅ |
| API-Calls | 1 + N pro Jahr | 2 total ✅ |
| Sensoren | 7 (inkl. Datenstatus) | 6 (vereinfacht) ✅ |

**Upgrade**: Über HACS aktualisieren → HA neu starten. Die YAML-Datei wird automatisch neu generiert. Sensoren bleiben erhalten.

> ⚠️ Der `sensor.ferien_*_datenstatus` Sensor aus v1.x existiert in v2.0 nicht mehr. Falls du ihn in Automationen nutzt, entferne die Referenz vor dem Update.

---

## ❓ FAQ

<details>
<summary><strong>Wie oft werden die Daten aktualisiert?</strong></summary>

Automatisch **einmal täglich**. Zusätzlich jederzeit manuell über den **Button** oder den **Service** `deutsche_ferien.update_ferien`.

</details>

<details>
<summary><strong>Kann ich mehrere Bundesländer gleichzeitig nutzen?</strong></summary>

Ja! Füge die Integration einfach mehrfach hinzu – einmal pro Bundesland. Jedes Bundesland bekommt seine eigene YAML-Datei und eigene Sensoren.

</details>

<details>
<summary><strong>Wohin wird die YAML-Datei geschrieben?</strong></summary>

In dein **HA-Konfigurationsverzeichnis** (dort wo `configuration.yaml` liegt). Der Dateiname ist `{BL}_Ferien.yaml`, z.B. `BY_Ferien.yaml`.

</details>

<details>
<summary><strong>Wie weit in die Zukunft reichen die Daten?</strong></summary>

Die Integration fragt die **nächsten ~3 Jahre** ab. Es werden alle Daten übernommen, die die API liefert. Aktuell hat OpenHolidaysAPI Feriendaten bis ca. 2029. Sobald neue Daten veröffentlicht werden, sind sie beim nächsten Update automatisch dabei.

</details>

<details>
<summary><strong>Der HACS-Installs-Badge zeigt „no result"?</strong></summary>

Normal bei neuen Integrationen. Der Badge speist sich aus den [HA Analytics](https://analytics.home-assistant.io/) – Nutzer müssen unter Einstellungen → Analytics die Option „Benutzerdefinierte Integrationen teilen" aktiviert haben. Dauert ca. 1–2 Wochen.

</details>

<details>
<summary><strong>Warum v2.0? Was hat sich geändert?</strong></summary>

v2.0 wechselt die Datenquelle von ferien-api.de (nicht mehr gepflegt, nur bis 2026) zu [OpenHolidaysAPI](https://openholidaysapi.org) (aktiv gepflegt, Daten bis ~2029). Feiertage kommen jetzt ebenfalls von OpenHolidaysAPI statt date.nager.at. Weniger API-Calls, mehr Daten, einfacherer Code.

</details>

---

## 🐛 Probleme & Feature-Wünsche

[Issue erstellen](https://github.com/workFLOw42/ha-deutsche-ferien/issues)

---

## 🙏 Danke

An die Betreiber von [OpenHolidaysAPI](https://openholidaysapi.org) für ihre kostenlose und aktiv gepflegte API!

---

## 📄 Lizenz

[MIT](https://github.com/workFLOw42/ha-deutsche-ferien/blob/main/LICENSE) – © 2025 [workFLOw42](https://github.com/workFLOw42)