# ROI Tracker für Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![Validate](https://github.com/pxljake/roi-tracker/actions/workflows/validate.yml/badge.svg)](https://github.com/pxljake/roi-tracker/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Release](https://img.shields.io/github/v/release/pxljake/roi-tracker)](https://github.com/pxljake/roi-tracker/releases)

**Verfolge, wann sich deine PV-Anlage amortisiert hat** – mit dynamischen
Tibber-Preisen, Batterie-Ersparnis und Einspeisevergütung.
Inklusive Dashboard-Karte mit Donut-Chart, Tageswerten und Monatshistogramm.

> 🇬🇧 *English description below.*

> **Hinweis:** Alle angezeigten Werte sind **berechnete Schätzungen** auf Basis
> der konfigurierten Sensoren und Preise. Sie ersetzen keine Energieabrechnung
> und keine Steuerberatung.

---

## ✨ Funktionen

- **PV-Amortisationsrechner** – wie viel hast du seit Inbetriebnahme verdient und gespart?
- **Tibber-Unterstützung** – dynamischer Strompreis als Sensor; jede selbst verbrauchte kWh wird zum aktuellen Preis bewertet
- **Batterie** – Entlade-kWh zählen als Ersparnis zum aktuellen Bezugspreis
- **Einspeisevergütung** – fester Tarif oder Sensor
- **Netzbezugs-Sensor (optional)** – transparente Anzeige, wie viel du noch vom Netz kaufst (kWh + Kosten), ohne den ROI zu verfälschen
- **Rückwirkend rechnen** – Startdatum setzen und aus gespeicherter Sensor-Historie laden
- **Bis zu 16 HA-Sensoren** pro Anlage – es werden nur die angelegt, für die auch eine Datenquelle konfiguriert ist
- **Lovelace-Karte** mit Donut-Chart, Heute-Sektion (Tages-Ersparnis & -Einspeisung), Monatsbalken-Histogramm, Aufschlüsselung und Prognosen – alle Abschnitte und Kacheln einzeln abschaltbar

## 🧮 Wie wird gerechnet?

```
Gesamtrückfluss = Eigenverbrauch-Ersparnis + Batterie-Ersparnis + Einspeiseertrag

Eigenverbrauch-Ersparnis = verbrauchte_kWh × Strompreis (was du sonst gekauft hättest)
Batterie-Ersparnis       = entladene_kWh  × Strompreis
Einspeiseertrag          = eingespeiste_kWh × Vergütung
Break-Even               = wenn Gesamtrückfluss ≥ Investition
```

**Netzbezug wird absichtlich nicht abgezogen.** Der ROI der PV-Anlage misst,
wie viel Geld sie *zurückbringt* (durch vermiedene Kosten + Erlöse). Was du
weiterhin aus dem Netz kaufst, würdest du auch ohne PV zahlen – der Vergleich
wäre sonst verzerrt. Der Netzbezug wird als transparente Zusatz-Information angezeigt.

**Doppelzählung vermeiden:** Wenn du einen separaten Batterie-Sensor angibst,
darf der Eigenverbrauchs-Sensor die Batterie-Entnahme **nicht** enthalten.
Enthält dein Eigenverbrauchs-Sensor die Batterie bereits, lass das Batterie-Feld leer.

## 📊 Erzeugte Sensoren pro Anlage

Sensoren werden nur angelegt, wenn die zugehörige Datenquelle konfiguriert ist –
keine leeren Entitäten.

| Sensor | Einheit | Voraussetzung | Beschreibung |
|---|---|---|---|
| Gesamtrückfluss | € | – | Ersparnis + Batterie + Einspeisung (kumuliert) |
| Ersparnis (Eigenverbrauch) | € | – | gesparter Netzbezug durch direkten PV-Verbrauch |
| Ersparnis (Batterie) | € | Batterie-Sensor | gesparter Netzbezug durch Batterie-Entladung |
| Einspeiseertrag | € | – | Einnahmen aus Einspeisung ins Netz |
| Offener Restbetrag | € | – | noch nicht amortisierter Betrag |
| Amortisation | % | – | zurückgeflossener Anteil der Investition |
| ROI | % | – | Gewinn über die Investition hinaus |
| Restlaufzeit bis Break-Even | d | – | geschätzte Tage bis zur vollen Amortisation |
| Eigenverbrauchsquote | % | Verbrauchs-Sensor | wie viel % der PV-Energie selbst genutzt wird |
| Tages-Ø Rückfluss | € | – | Ø täglicher Rückfluss (Basis für Prognosen) |
| Monatliche Prognose | € | – | hochgerechneter monatlicher Rückfluss |
| Netzbezug (Kosten) | € | Netzbezugs-Sensor | kumulierte Kosten für Netzbezug |
| Eigenverbrauch gesamt | kWh | Verbrauchs-Sensor | dauerhaft kumuliert, auch über Sensor-Resets |
| Einspeisung gesamt | kWh | Einspeise-Sensor | dauerhaft kumuliert |
| Batterie-Entladung gesamt | kWh | Batterie-Sensor | dauerhaft kumuliert |
| Netzbezug gesamt | kWh | Netzbezugs-Sensor | dauerhaft kumuliert |

## 📦 Installation über HACS

1. HACS öffnen → **Drei-Punkte-Menü** → **Benutzerdefinierte Repositories**
2. URL `https://github.com/pxljake/roi-tracker`, Kategorie **Integration**
3. **ROI Tracker** installieren und Home Assistant neu starten
4. **Einstellungen → Geräte & Dienste → Integration hinzufügen → ROI Tracker**

> **Karte nicht sichtbar?** Nach dem ersten Setup das HA-Frontend im Browser
> mit **Strg+F5** (Hard Reload) neu laden. Die Karte wird beim Setup automatisch
> als versionierte Ressource registriert. Falls das nicht klappt:
> `/roi_tracker/roi-tracker-card.js` unter
> **Einstellungen → Dashboards → Ressourcen** manuell als JavaScript-Modul eintragen.

### Manuelle Installation
Kopiere `custom_components/roi_tracker` in deinen `config/custom_components`-Ordner
und starte HA neu.

## ⚙️ Einrichtung (Tibber + PV mit Speicher)

1. **Vorlage:** PV-Anlage (mit Speicher)
2. **Investition:** z. B. `20000` €
3. **Startdatum:** Inbetriebnahme-Datum (optional, rückwirkend aus HA-Historie)
4. **Sensoren auswählen** (alle als kumulierte kWh-Zählerstände, keine kW-Leistung):
   | Feld | Was eintragen |
   |---|---|
   | PV-Eigenverbrauch | direkter PV-Eigenverbrauch (ohne Batterie, wenn Batterie-Sensor gesetzt) |
   | Einspeisung ins Netz | kumulierter Einspeisung-kWh-Sensor |
   | Aus Batterie entnommen (optional) | kumulierter Batterie-Entlade-kWh-Sensor |
   | Netzbezug (optional) | Tibber `energy`-Sensor oder Smartmeter |
5. **Strompreis:** Dynamischer Preis-Sensor → `sensor.tibber_xyz_current_price`
6. **Einspeisevergütung:** Fester Wert → z. B. `0.082` (8,2 ct/kWh)

> **Wichtig für Tibber:** Wähle als Strompreis immer `sensor.…current_price`
> (€/kWh), nicht `accumulated_cost`. Letzteres ist ein kumulierter Kostensensor,
> kein Preis-Sensor.

## 🃏 Dashboard-Karte

Die Karte lässt sich komplett im **visuellen Editor** konfigurieren – Anlage
auswählen, Titel setzen und jeden Abschnitt sowie jede Kachel einzeln ein-/ausschalten.

```yaml
type: custom:roi-tracker-card
device: <Geräte-ID der Anlage>
title: Meine PV-Anlage    # optional – weglassen = kein Titel, kompaktere Karte
# language: de            # optional, sonst HA-Sprache
# show_hero: true         # Oberer Block (Gesamtrückfluss & Amortisation)
# show_donut: true        #   Amortisations-Donut (Teil des oberen Blocks)
# show_tiles: true        # Kennzahlen-Kacheln (Gruppe)
# tile_daily: true        #   Kachel: Ø täglich
# tile_monthly: true      #   Kachel: Ø monatlich
# tile_yearly: true       #   Kachel: Prognose/Jahr
# tile_breakeven: true    #   Kachel: Break-Even
# tile_roi: true          #   Kachel: ROI
# tile_self: true         #   Kachel: Eigenverbrauch-%
# show_today: true        # Heute: Ersparnis & Einspeisung des Tages
# show_breakdown: true    # Rückfluss-Aufschlüsselung
# show_energy: true       # kWh-Statistiken (Gruppe)
# energy_consumption: true #   Zeile: Eigenverbrauch (kWh)
# energy_export: true     #   Zeile: Einspeisung (kWh)
# energy_battery: true    #   Zeile: Batterie (kWh)
# energy_grid: true       #   Zeile: Netzbezug (kWh)
# energy_grid_cost: true  #   Zeile: Netzbezug-Kosten (€)
# show_chart: true        # Monatsbalken-Histogramm
```

Die Karte zeigt:
- **Donut-Chart**: Amortisationsgrad in %
- **Kennzahlen-Kacheln**: tägl. Ø, monatl. Prognose, Jahres-Prognose, Break-Even-Datum, ROI, Eigenverbrauchsquote – einzeln abschaltbar
- **Heute**: heutige Eigenverbrauch-Ersparnis, Batterie-Ersparnis und Einspeisevergütung (aus der HA-Langzeitstatistik)
- **Aufschlüsselung**: Stacked-Bar (Eigenverbrauch / Einspeisung / Batterie)
- **Energie seit Start**: kWh-Summen inkl. Netzbezug und Netzbezugs-Kosten
- **Monatshistogramm**: letzte 12 Monate aus HA-Statistics (lädt automatisch)

## 🔋 Batterie-Logik

Jede aus der Batterie entnommene kWh ersetzt Netzbezug → wird mit dem
aktuellen Bezugspreis als Ersparnis gewertet. Bei fertigem €-Kosten-Sensor
(`cost_sensor`-Modus) wird die Batterie **nicht** doppelt gezählt.

## ⏳ Rückwirkend rechnen

Setzt du ein **Startdatum**, liest ROI Tracker beim ersten Setup die
Zählerstände zu diesem Datum aus der HA-Langzeitstatistik. Voraussetzung: Die
Sensoren haben seit dem Datum eine `state_class` (sonst kein Langzeitverlauf).

Jederzeit neu anstoßen:
```yaml
action: roi_tracker.recalculate
target:
  entity_id: sensor.<anlage>_gesamtrueckfluss
data:
  start_date: "2025-01-01"   # optional
```

## 🔄 Zurücksetzen

```yaml
action: roi_tracker.reset
target:
  entity_id: sensor.<anlage>_gesamtrueckfluss
```

## 🤝 Mitwirken / Contributing

Pull Requests und Issues sind willkommen!

Tests ausführen:
```bash
python3 tests/test_calculator.py
```

---

## 🇬🇧 English

**Track when your solar PV investment pays off** — with Tibber dynamic pricing,
battery savings and feed-in revenue. Includes a Lovelace card with donut chart,
today's values and a monthly histogram.

> **Note:** All displayed values are **calculated estimates** based on the
> configured sensors and prices. They do not replace professional energy
> accounting or official billing.

**Calculation:**
```
Total return = self-consumption savings + battery savings + feed-in revenue

Self-consumption savings = consumed_kWh × current price
Battery savings          = discharged_kWh × current price
Feed-in revenue          = exported_kWh × feed-in tariff
Break-even               = when total return ≥ investment
```

Grid import is intentionally **not subtracted** from ROI — you pay it with or
without PV. It is displayed as transparent additional information only.

**Avoid double counting:** if you configure a separate battery sensor, your
self-consumption sensor must **not** include battery discharge.

**Setup (Tibber + PV with battery storage):**
1. Template: *PV system (with battery)*
2. Investment: e.g. `20000` €
3. Start date: commissioning date (optional, retroactive from HA history)
4. Sensors: PV self-consumption kWh, export kWh, battery discharge kWh (optional), grid import kWh (optional)
5. Price source: dynamic sensor → `sensor.tibber_xyz_current_price`
6. Feed-in: fixed → e.g. `0.082` (8.2 ct/kWh)

**Card:** fully configurable in the visual editor — every section and every
metric tile can be toggled individually; leave the title empty for a more
compact card. A "Today" section shows today's self-consumption savings and
feed-in revenue from HA long-term statistics.

**Card not visible?** Hard-reload the browser (Ctrl+F5) after the first setup.

Install via HACS as a custom repository (category *Integration*), restart HA,
then add **ROI Tracker** under *Settings → Devices & Services*.

## 📄 Lizenz / License

[MIT](LICENSE)
