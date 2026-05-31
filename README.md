# ROI Tracker für Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![Validate](https://github.com/pxljake/roi-tracker/actions/workflows/validate.yml/badge.svg)](https://github.com/pxljake/roi-tracker/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.2.0--beta.1-orange.svg)](https://github.com/pxljake/roi-tracker/releases)

> **⚠️ Beta-Software – Hinweis / Beta Notice**
>
> ROI Tracker befindet sich in aktiver Entwicklung. Alle angezeigten Werte sind
> **berechnete Schätzungen** auf Basis der angegebenen Sensoren und Preise.
> Sie ersetzen keine Steuerberatung, Energieabrechnung oder Herstellergarantien.
> Werte können durch fehlerhafte Sensor-Konfiguration, Messfehler oder
> dynamische Preisschwankungen abweichen. Nutzung auf eigene Verantwortung.
>
> *All displayed values are calculated estimates based on the configured sensors
> and prices. They do not replace professional energy accounting or official billing.
> Use at your own risk.*

---

**Verfolge, wann sich deine PV-Anlage amortisiert hat** – mit dynamischen
Tibber-Preisen, Batterie-Ersparnis und Einspeisevergütung.
Inklusive übersichtlicher Dashboard-Karte mit Donut-Chart und Monatshistogramm.

> 🇬🇧 *English description below.*

---

## ✨ Funktionen

- **PV-Amortisationsrechner** – wie viel hast du seit Inbetriebnahme verdient und gespart?
- **Tibber-Unterstützung** – dynamischer Strompreis als Sensor; jede selbst verbrauchte kWh wird zum aktuellen Preis bewertet
- **Batterie** – Entlade-kWh zählen als Ersparnis zum aktuellen Bezugspreis
- **Einspeisevergütung** – fester Tarif oder Sensor
- **Netzbezugs-Sensor (optional)** – transparente Anzeige, wie viel du noch vom Netz kaufst (kWh + Kosten) ohne den ROI zu verfälschen
- **Rückwirkend rechnen** – Startdatum setzen und aus gespeicherter Sensor-Historie laden
- **12 HA-Sensoren** pro Anlage für Automationen, Verlauf und andere Karten
- **Lovelace-Karte** mit Donut-Chart, Monatsbalken-Histogramm (letzten 12 Monate), Aufschlüsselung und Prognosen

## 🧮 Wie wird gerechnet?

```
Gesamtrückfluss = Eigenverbrauch-Ersparnis + Batterie-Ersparnis + Einspeiseertrag

Eigenverbrauch-Ersparnis = verbrauchte_kWh × Tibber-Preis (was du sonst gekauft hättest)
Batterie-Ersparnis       = entladene_kWh  × Tibber-Preis
Einspeiseertrag          = eingespeiste_kWh × Vergütung
Break-Even               = wenn Gesamtrückfluss ≥ Investition
```

**Netzbezug wird absichtlich nicht abgezogen.** Der ROI der PV-Anlage misst,
wie viel Geld sie *zurückbringt* (durch vermiedene Kosten + Erlöse). Was du
weiterhin aus dem Netz kaufst, würdest du auch ohne PV zahlen – der Vergleich
wäre sonst verzerrt. Der Netzbezug wird als transparente Zusatz-Information angezeigt.

## 📊 Erzeugte Sensoren pro Anlage (12 Stück)

| Sensor | Einheit | Beschreibung |
|---|---|---|
| Gesamtrückfluss | € | Ersparnis + Batterie + Einspeisung (kumuliert) |
| Ersparnis (Eigenverbrauch) | € | gesparter Netzbezug durch direkten PV-Verbrauch |
| Ersparnis (Batterie) | € | gesparter Netzbezug durch Batterie-Entladung |
| Einspeiseertrag | € | Einnahmen aus Einspeisung ins Netz |
| Offener Restbetrag | € | noch nicht amortisierter Betrag |
| Amortisation | % | zurückgeflossener Anteil der Investition |
| ROI | % | Gewinn über die Investition hinaus |
| Restlaufzeit bis Break-Even | d | geschätzte Tage bis zur vollen Amortisation |
| Eigenverbrauchsquote | % | wie viel % der PV-Energie selbst genutzt wird |
| Tages-Ø Rückfluss | € | Ø täglicher Rückfluss (Basis für Prognosen) |
| Monatliche Prognose | € | hochgerechneter monatlicher Rückfluss |
| Netzbezug (Kosten) | € | kumulierte Kosten für Netzbezug (nur wenn Sensor konfiguriert) |

## 📦 Installation über HACS

1. HACS öffnen → **Drei-Punkte-Menü** → **Benutzerdefinierte Repositories**
2. URL `https://github.com/pxljake/roi-tracker`, Kategorie **Integration**
3. **ROI Tracker** installieren und Home Assistant neu starten
4. **Einstellungen → Geräte & Dienste → Integration hinzufügen → ROI Tracker**

> **Karte nicht sichtbar?** Nach dem ersten Setup das HA-Frontend im Browser
> mit **Strg+F5** (Hard Reload) neu laden. Die Karte wird beim Setup automatisch
> registriert. Falls das nicht klappt: `ROI Tracker Card` unter
> **Einstellungen → Dashboards → Ressourcen** manuell als JavaScript-Modul eintragen:
> `/roi_tracker/roi-tracker-card.js`

### Manuelle Installation
Kopiere `custom_components/roi_tracker` in deinen `config/custom_components`-Ordner
und starte HA neu.

## ⚙️ Einrichtung (Tibber + PV mit Speicher)

1. **Vorlage:** PV-Anlage (mit Speicher)
2. **Investition:** z. B. `20000` €
3. **Startdatum:** Inbetriebnahme-Datum (optional, rückwirkend aus HA-Historie)
4. **Sensoren auswählen:**
   | Feld | Was eintragen |
   |---|---|
   | Eigenverbrauch aus PV/Batterie | kumulierter Eigenverbrauch-kWh-Sensor |
   | Einspeisung ins Netz | kumulierter Einspeisung-kWh-Sensor |
   | Aus Batterie entnommen | kumulierter Batterie-Entlade-kWh-Sensor |
   | Netzbezug (optional) | Tibber `energy`-Sensor oder Smartmeter |
5. **Strompreis:** Dynamischer Preis-Sensor → `sensor.tibber_xyz_current_price`
6. **Einspeisevergütung:** Fester Wert → z. B. `0.082` (8,2 ct/kWh)

> **Wichtig für Tibber:** Wähle als Strompreis immer `sensor.…current_price`
> (€/kWh), nicht `accumulated_cost`. Letzteres ist ein kumulierter Kostensensor,
> kein Preis-Sensor.

## 🃏 Dashboard-Karte

```yaml
type: custom:roi-tracker-card
device: <Geräte-ID der Anlage>
title: Meine PV-Anlage
# show_chart: true         # Monatsbalken ein (Standard)
# show_breakdown: true     # Aufschlüsselung ein (Standard)
# language: de             # optional, sonst HA-Sprache
```

Die Karte zeigt:
- **Donut-Chart**: Amortisationsgrad in %
- **Metriken-Kacheln**: tägl. Ø, monatl. Prognose, Break-Even-Datum, ROI, Eigenverbrauchsquote
- **Aufschlüsselung**: Stacked-Bar (Eigenverbrauch / Einspeisung / Batterie)
- **Monatshistogramm**: letzten 12 Monate aus HA-Statistics (lädt automatisch)

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
  device_id: <Geräte-ID>
data:
  start_date: "2025-01-01"   # optional
```

## 🔄 Zurücksetzen

```yaml
action: roi_tracker.reset
target:
  device_id: <Geräte-ID>
```

## 🤝 Mitwirken / Contributing

Pull Requests und Issues sind willkommen!

Tests ausführen:
```bash
python3 tests/test_calculator.py
```

---

## 🇬🇧 English

> **⚠️ Beta software.** All displayed values are **calculated estimates** based
> on the configured sensors and prices. They do not replace professional energy
> accounting or official billing. Use at your own risk.

**Track when your solar PV investment pays off** — with Tibber dynamic pricing,
battery savings and feed-in revenue. Includes a Lovelace card with donut chart
and monthly histogram.

**Calculation:**
```
Total return = self-consumption savings + battery savings + feed-in revenue

Self-consumption savings = consumed_kWh × current_Tibber_price
Battery savings          = discharged_kWh × current_Tibber_price
Feed-in revenue          = exported_kWh × feed-in tariff
Break-even               = when total return ≥ investment
```

Grid import is intentionally **not subtracted** from ROI — you pay it with or
without PV. It is displayed as transparent additional information only.

**Setup (Tibber + PV with battery storage):**
1. Template: *PV system (with battery)*
2. Investment: e.g. `20000` €
3. Start date: commissioning date (optional, retroactive from HA history)
4. Sensors: self-consumption kWh, export kWh, battery discharge kWh, grid import kWh (optional)
5. Price source: dynamic sensor → `sensor.tibber_xyz_current_price`
6. Feed-in: fixed → e.g. `0.082` (8.2 ct/kWh)

**Card not visible?** Hard-reload the browser (Ctrl+F5) after the first setup.

Install via HACS as a custom repository (category *Integration*), restart HA,
then add **ROI Tracker** under *Settings → Devices & Services*.

## 📄 Lizenz / License

[MIT](LICENSE)
