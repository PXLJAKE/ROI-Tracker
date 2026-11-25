# ROI Tracker für Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![Validate](https://github.com/pxljake/roi-tracker/actions/workflows/validate.yml/badge.svg)](https://github.com/pxljake/roi-tracker/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Release](https://img.shields.io/github/v/release/pxljake/roi-tracker)](https://github.com/pxljake/roi-tracker/releases)

[![Projektseite](https://img.shields.io/badge/Projektseite-pxljake.com-F5A623?style=for-the-badge)](https://pxljake.com/projects/roi-tracker/)
[![Dokumentation](https://img.shields.io/badge/Dokumentation-lesen-2A78D6?style=for-the-badge)](https://pxljake.com/docs/roi-tracker/)

**Wann hat sich deine PV-Anlage bezahlt gemacht?** ROI Tracker rechnet aus,
wie viel du durch selbst genutzten Solarstrom **gespart** und durch Einspeisung
**verdient** hast – mit festem oder dynamischem Strompreis (Tibber, aWATTar, EPEX …) –
und zeigt Amortisation, ROI, Monatsstatistik und eine Hochrechnung bis zum Break-Even.

> 🇬🇧 *English description below.*

> **Hinweis:** Alle Werte sind **berechnete Schätzungen** auf Basis deiner Sensoren
> und Preise. Sie ersetzen keine Energieabrechnung und keine Steuerberatung.

---

## ✨ Funktionen

- **Ersparnis** – jede selbst genutzte kWh × Strompreis *der jeweiligen Stunde*
- **Einspeiseertrag** – eingespeiste kWh × Einspeisevergütung
- **ROI & Amortisation** – Gesamtertrag gegen Investition, offener Restbetrag, Break-Even-Datum
- **Monats- & Jahresstatistik** mit Tageswerten
- **Hochrechnung** – ab 12 Monaten Daten saisonal korrekt aus den echten Erträgen
- **Rückwirkend** ab Inbetriebnahme, soweit Home Assistant Statistikdaten hat
- **Dashboard-Karte** in 4 Größen – ein Klick öffnet ein Popup mit allen Details

## 🧮 Wie wird gerechnet?

Grundlage ist die **Langzeitstatistik von Home Assistant** (dieselben Daten wie im
Energie-Dashboard). Für jede Stunde gilt:

```
Ersparnis    = selbst genutzte kWh × Strompreis dieser Stunde
Einspeisung  = eingespeiste kWh    × Einspeisevergütung

Gesamtertrag = Σ Ersparnis + Σ Einspeisung
Amortisation = Gesamtertrag / Investition
ROI          = (Gesamtertrag − Investition) / Investition
```

Die **selbst genutzten kWh** ermittelst du auf eine von drei Arten:

| Berechnungsart | Formel pro Stunde | Wann nutzen |
|---|---|---|
| **Hausverbrauch − Netzbezug** *(empfohlen)* | Hausverbrauch − Netzbezug | Du hast einen Sensor für den gesamten Hausverbrauch |
| **PV-Erzeugung − Einspeisung** | PV − Einspeisung + Batterie-Entladung − Batterie-Ladung | Du hast die Sensoren aus dem Energie-Dashboard |
| **Fertiger Eigenverbrauch** | Eigenverbrauch (+ Batterie-Entladung) | Dein Wechselrichter liefert den Eigenverbrauch direkt |

Warum stündlich aus der Statistik?
- **Dynamische Preise** werden korrekt bewertet: Mittags-kWh zum Mittagspreis, Abend-kWh zum Abendpreis.
- **Batterie-Laden aus dem Netz** (günstige Stunden) und Entladen (teure Stunden) wird korrekt als Ersparnis gewertet.
- **Zähler-Resets, Tageszähler, Ausfälle und Neustarts** sind in der HA-Statistik bereits sauber behandelt – es wird nichts doppelt gezählt.
- Änderst du Startdatum, Sensoren oder Preise, wird **automatisch komplett neu gerechnet**.

**Strompreis-Sensor:** Einheit €/kWh, ct/kWh oder €/MWh wird automatisch erkannt.
Hat der Sensor eine Langzeitstatistik (`state_class: measurement`), ist auch die
Rückrechnung stundengenau. Ohne Statistik wird der Preis aus der Zustands-Historie
gelesen (Standard: die letzten 10 Tage); für ältere Zeiträume wird der Festpreis
verwendet. Deshalb verlangt die Einrichtung bei einem solchen Sensor (z. B.
`sensor.tibber_current_price`) und einem Startdatum, das älter als 10 Tage ist,
einen Festpreis als Ersatz.

**Mehrere PV-Strings / Wechselrichter:** Bei „PV-Erzeugung − Einspeisung“ können
mehrere Erzeugungs-Zähler gewählt werden, sie werden addiert. Am genauesten sind
AC-Zähler des Wechselrichters; DC-String-Zähler enthalten noch die Wandlungsverluste
(typisch 3–5 % zu viel Eigenverbrauch).

**Hochrechnung:** Mit mindestens 12 Monaten Daten = Summe der letzten 365 Tage
(Sommer und Winter gleichen sich aus). Vorher = Tagesdurchschnitt × 365 – in der
Karte als *vorläufig* markiert.

## 📦 Installation über HACS

ROI Tracker ist im HACS-Standardkatalog enthalten:

1. In HACS nach **ROI Tracker** suchen
2. **ROI Tracker** herunterladen und Home Assistant neu starten
3. **Einstellungen → Geräte & Dienste → Integration hinzufügen → ROI Tracker**

[![In HACS öffnen](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=PXLJAKE&repository=ROI-Tracker&category=integration)

*Falls ROI Tracker in deiner HACS-Version noch nicht auftaucht:* HACS → **Drei-Punkte-Menü** →
**Benutzerdefinierte Repositories** → URL `https://github.com/PXLJAKE/ROI-Tracker`, Kategorie **Integration**.

Voraussetzung: Home Assistant 2025.1 oder neuer, Recorder aktiv.

## ⚙️ Einrichtung

**Schritt 1 – Grunddaten**
- Name, Anschaffungskosten, Inbetriebnahme-/Startdatum
- Berechnungsart (siehe oben)
- Strompreis: **Preis-Sensor** *oder* **Festpreis** (€/kWh). Mit Sensor dient der Festpreis nur als Fallback.
- Einspeisevergütung (€/kWh, z. B. `0.082`)

**Schritt 2 – Energie-Sensoren** passend zur Berechnungsart. Es gehen nur
kumulierte kWh-Zähler mit Langzeitstatistik (`state_class`) – also genau die
Sensoren, die auch im Energie-Dashboard funktionieren.

Alles lässt sich später unter **Konfigurieren** ändern.

## 📊 Sensoren pro Anlage

| Sensor | Einheit | Beschreibung |
|---|---|---|
| Gesamtertrag | € | Ersparnis + Einspeiseertrag |
| Ersparnis | € | vermiedene Stromkosten durch Eigenverbrauch |
| Einspeiseertrag | € | Vergütung für eingespeisten Strom (nur mit Einspeise-Sensor) |
| Offener Restbetrag | € | noch nicht amortisierter Betrag |
| Amortisation | % | zurückgeflossener Anteil der Investition |
| ROI | % | Gewinn/Verlust bezogen auf die Investition |
| Jahresprognose | € | erwarteter Ertrag pro Jahr |
| Break-Even-Datum | Datum | voraussichtlich (oder tatsächlich) abbezahlt am |
| Eigenverbrauch gesamt | kWh | selbst genutzte Energie seit Start |
| Einspeisung gesamt | kWh | eingespeiste Energie seit Start (nur mit Einspeise-Sensor) |

## 🃏 Dashboard-Karte

Die Karte wird automatisch registriert (ggf. einmal **Strg+F5** im Browser).
Im Karten-Editor Anlage und Darstellung wählen:

| Variante | Inhalt |
|---|---|
| `mini` | eine Zeile: Gesamtertrag + Amortisations-Balken |
| `compact` | Donut, Gesamtertrag, Ersparnis / Einspeisung |
| `standard` | zusätzlich: dieser Monat, Jahresprognose, Break-Even, ROI |
| `full` | zusätzlich: Balkendiagramm der letzten 12 Monate |

**Ein Klick auf die Karte öffnet das Detail-Popup:**
- **Übersicht** – alle Kennzahlen, kWh, Ø Strompreis, Preisquelle
- **Monate** – Balkendiagramm + Tabelle pro Jahr, Jahresübersicht; Klick auf einen Monat zeigt die Tageswerte
- **Prognose** – kumulierter Ertrag vs. Investition mit Hochrechnung bis zum Break-Even

```yaml
type: custom:roi-tracker-card
device: <Geräte-ID der Anlage>
variant: standard   # mini | compact | standard | full
title: PV-Anlage    # optional
```

## 🔄 Neu berechnen

Normalerweise nicht nötig – geänderte Einstellungen lösen die Neuberechnung
automatisch aus. Manuell:

```yaml
action: roi_tracker.recalculate
target:
  entity_id: sensor.<anlage>_gesamtertrag
data:
  start_date: "2025-01-01"   # optional, wird in der Anlage gespeichert
```

## ⬆️ Update von 0.3.x

Version 0.4 rechnet komplett neu aus der Langzeitstatistik. Beim ersten Start
wird die bestehende Anlage automatisch übernommen (Berechnungsart
„Fertiger Eigenverbrauch“) und neu berechnet. Bitte danach kurz prüfen:

- **Berechnungsart**: Ist dein Verbrauchs-Sensor eigentlich der *Hausverbrauch*? Dann auf „Hausverbrauch − Netzbezug“ umstellen.
- **Preis**: Der Modus „fertiger €-Sensor“ entfällt – bitte Preis-Sensor oder Festpreis eintragen.
- Der Schalter „Sensoren setzen täglich zurück“ entfällt (wird automatisch richtig behandelt).
- Der Service `roi_tracker.reset` entfällt → `roi_tracker.recalculate`.
- Nicht mehr benötigte Sensoren werden entfernt; Gesamtertrag, Ersparnis, Einspeiseertrag, Restbetrag, Amortisation und ROI behalten ihre Entity-IDs.
- Karte: Die alten `show_*`/`tile_*`-Optionen werden ignoriert – stattdessen `variant` wählen.

## 🤝 Mitwirken

Pull Requests und Issues sind willkommen! Tests (ohne Home-Assistant-Installation):

```bash
pip install pytest
python -m pytest tests
```

---

## 🇬🇧 English

[![Project page](https://img.shields.io/badge/Project_page-pxljake.com-F5A623?style=for-the-badge)](https://pxljake.com/projects/roi-tracker/)
[![Documentation](https://img.shields.io/badge/Documentation-read-2A78D6?style=for-the-badge)](https://pxljake.com/docs/roi-tracker/en/)

**When has your PV system paid for itself?** ROI Tracker calculates how much you
**saved** by using your own solar power and **earned** by feeding into the grid –
with a fixed or dynamic electricity price (Tibber, aWATTar, EPEX …) – and shows
amortization, ROI, monthly statistics and a projection to break-even.

**How it works:** Every hour from Home Assistant long-term statistics:
`savings = self-consumed kWh × price of that hour`, `feed-in = exported kWh × tariff`.
Self-consumption is either *house consumption − grid import* (recommended),
*PV production − export ± battery*, or a ready-made self-consumption sensor.
Counter resets, outages and restarts are handled by HA statistics; changing
settings triggers a full recalculation. Price units €/kWh, ct/kWh and €/MWh are
detected automatically.

**Card:** `custom:roi-tracker-card` with `variant: mini | compact | standard | full`.
Click it to open a popup with overview, monthly/yearly/daily statistics and the
break-even forecast.

**Install:** search for **ROI Tracker** in HACS (it is part of the HACS default
list), download it and restart HA, then add **ROI Tracker** under *Settings →
Devices & Services*. Fallback for older HACS versions: add
`https://github.com/PXLJAKE/ROI-Tracker` as a custom repository (category
*Integration*). Requires HA 2025.1+.

Several PV production meters (strings/inverters) can be selected and are added up.
A price sensor without long-term statistics only covers the last ~10 days, so a
fixed fallback price is required for older start dates.

## 📄 Lizenz / License

[MIT](LICENSE)
