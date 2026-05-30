# ROI Tracker für Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![Validate](https://github.com/pxljake/roi-tracker/actions/workflows/validate.yml/badge.svg)](https://github.com/pxljake/roi-tracker/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Universeller Return-on-Investment-Rechner für Home Assistant.** Verfolge, wann
sich eine Investition amortisiert – ob **PV-Anlage**, **Elektroauto**,
**Wärmepumpe/Heizung** oder etwas **Benutzerdefiniertes**. Du wählst beim Anlegen
einfach deine vorhandenen Sensoren aus, und ROI Tracker rechnet laufend
Ersparnis, Amortisation und Restlaufzeit – inklusive einer schönen Dashboard-Karte.

> 🇬🇧 *English description below.*

---

## ✨ Funktionen

- **Mehrere Anlagen**: Lege beliebig viele unabhängige ROI-Rechner an (z. B. „PV Haus", „E-Auto", „Wärmepumpe").
- **Vorlagen**: PV-Anlage · Elektroauto · Heizung/Wärmepumpe · Benutzerdefiniert – jede zeigt nur die passenden Felder.
- **Flexible Preisquellen** – nimm, was du hast:
  - **Fester Wert** (€/kWh)
  - **Dynamischer Sensor** (z. B. Tibber aktueller Preis €/kWh)
  - **Fertiger Kosten-Sensor** in € (z. B. Tibbers „accumulated cost")
- **Einspeisevergütung**: fester Tarif oder Ertrags-Sensor (€).
- **Vergleich mit Alt-Lösung** (Baseline) für E-Auto/Heizung – z. B. was der Verbrenner gekostet hätte.
- **Echte Sensoren** für Automationen, Verlauf und andere Karten.
- **Persistenter Zustand**: übersteht Neustarts, robust gegen Zähler-Resets der Quell-Sensoren.
- **Eigene Lovelace-Karte** mit grafischem Editor und Amortisations-Balken.
- **Zweisprachig**: Deutsch (Hauptsprache) & Englisch.

## 📊 Erzeugte Sensoren (pro Anlage)

| Sensor | Einheit | Beschreibung |
|---|---|---|
| Gesamtrückfluss | € | Ersparnis + Batterie-Ersparnis + Einspeiseertrag, kumuliert |
| Ersparnis | € | gesparter Netzbezug durch Eigenverbrauch |
| Ersparnis durch Batterie | € | gesparter Netzbezug durch Batterie-Entladung |
| Einspeiseertrag | € | Einnahmen aus Einspeisung/Abgabe |
| Offener Restbetrag | € | noch nicht amortisierter Teil der Investition |
| Amortisation | % | wie viel der Investition zurückgeflossen ist |
| ROI | % | Gewinn über die Investition hinaus |
| Restlaufzeit bis Break-Even | d | geschätzte Tage bis zur vollen Amortisation |
| Autarkiegrad | % | Eigenverbrauch / (Eigenverbrauch + Einspeisung) |

## 📦 Installation über HACS

1. HACS öffnen → **Drei-Punkte-Menü** → **Benutzerdefinierte Repositories**.
2. URL `https://github.com/pxljake/roi-tracker` hinzufügen, Kategorie **Integration**.
3. **ROI Tracker** installieren und Home Assistant neu starten.
4. **Einstellungen → Geräte & Dienste → Integration hinzufügen → ROI Tracker**.

> Die Dashboard-Karte wird beim Setup automatisch als Frontend-Ressource registriert.
> Falls nicht, füge `/hacsfiles/roi-tracker/roi-tracker-card.js` manuell als
> Lovelace-Ressource (Typ *JavaScript-Modul*) hinzu.

### Manuelle Installation
Kopiere `custom_components/roi_tracker` in deinen `config/custom_components`-Ordner und starte HA neu.

## ⚙️ Einrichtung einer Anlage

1. **Vorlage wählen** (PV / E-Auto / Heizung / Benutzerdefiniert).
2. **Investition** eintragen (Anschaffungskosten in €).
3. **Sensoren auswählen** – nur die, die du hast:
   - *Erzeugte/erbrachte Menge* (z. B. PV-Ertrag in kWh)
   - *Eigenverbrauch* (kWh)
   - *Einspeisung/Abgabe* (kWh)
   - *Batterie* laden/entladen (optional, PV)
4. **Preis-Quelle** für den Bezug wählen (fest / Sensor / Kosten-Sensor in €).
5. Bei PV: **Einspeisevergütung** wählen (fest oder Ertrags-Sensor).

Alles lässt sich später jederzeit über **Konfigurieren** an der Integration ändern.

## 🃏 Dashboard-Karte

Karte hinzufügen → **ROI Tracker Card** suchen → im Editor die **Anlage** auswählen. Oder per YAML:

```yaml
type: custom:roi-tracker-card
device: <Geräte-ID der Anlage>
title: Meine PV-Anlage
# language: de   # optional, sonst HA-Sprache
```

Alternativ einzelne Entitäten direkt angeben:

```yaml
type: custom:roi-tracker-card
title: E-Auto
entities:
  total_return: sensor.roi_e_auto_gesamtrueckfluss
  amortization: sensor.roi_e_auto_amortisation
  savings: sensor.roi_e_auto_ersparnis
  breakeven_days: sensor.roi_e_auto_restlaufzeit_bis_break_even
```

## 🔋 Batterie

Wählst du bei der PV-Vorlage einen **Batterie-Entlade-Sensor** (kumulierte kWh),
zählt jede aus der Batterie entnommene kWh als zusätzliche Ersparnis zum
Bezugspreis (sie ersetzt Netzbezug) und fließt in den **Autarkiegrad** ein. Die
Ladung wird bewusst nicht als Ausgabe gerechnet, da sie i. d. R. aus
PV-Überschuss stammt. Nutzt du einen fertigen €-Kosten-Sensor (z. B. Tibber),
ist die Batterie meist bereits enthalten – dann wird sie nicht doppelt gezählt.

## ⏳ Rückwirkend rechnen (Startdatum)

Im Setup kannst du ein optionales **Startdatum** angeben – auch in der
Vergangenheit. ROI Tracker liest dann beim Anlegen aus den **gespeicherten
Langzeit-Statistiken** deiner Sensoren den Zählerstand zu diesem Datum und nimmt
ihn als Basislinie. So erscheint sofort die seit dem Startdatum aufgelaufene
Ersparnis, statt erst „ab jetzt" zu zählen.

- **Exakt** bei festem Preis oder fertigem €-Kosten-Sensor.
- Bei einem **dynamischen Preis-Sensor** ist eine rückwirkende Rechnung nur
  näherungsweise möglich (kein stundengenauer Verlauf in der Vergangenheit).
- Voraussetzung: Die Quell-Sensoren existieren seit dem Datum und haben eine
  `state_class` (sonst speichert der Recorder keine Langzeit-Statistik).

Jederzeit neu anstoßen lässt sich das über den Service **`roi_tracker.recalculate`**:

```yaml
action: roi_tracker.recalculate
target:
  device_id: <Geräte-ID der Anlage>
data:
  start_date: "2025-01-01"   # optional; sonst das konfigurierte Startdatum
```

## 🔄 Zurücksetzen

Über den Service **`roi_tracker.reset`** (Ziel: das Gerät der Anlage) setzt du
einen Rechner auf null zurück – alle kumulierten Werte und der gespeicherte
Zustand werden gelöscht und die Messung beginnt neu.

```yaml
action: roi_tracker.reset
target:
  device_id: <Geräte-ID der Anlage>
```

## 🧮 Wie wird gerechnet?

ROI Tracker arbeitet **inkrementell** auf den kumulierten Zählerständen deiner
Sensoren. Bei jeder Aktualisierung wird das Delta (z. B. +2 kWh Eigenverbrauch)
mit dem aktuellen Preis multipliziert und aufaddiert. Bei dynamischen Tarifen
entsteht so automatisch ein zeitlich gewichteter Wert. Fertige €-Sensoren werden
direkt per Delta übernommen. Sinkt ein Quell-Zähler (Tagesreset), wird kein
negatives Delta gezählt. Der Stand wird persistent gespeichert und überlebt Neustarts.

---

## 🇬🇧 English

**Universal return-on-investment tracker for Home Assistant.** Track when an
investment pays off — **solar PV**, **electric vehicle**, **heat pump/heating**
or anything **custom**. Pick your existing sensors during setup and ROI Tracker
continuously computes savings, amortization and remaining time — including a nice
dashboard card.

- **Multiple assets**, each its own ROI calculator.
- **Templates**: PV · EV · Heating · Custom (only relevant fields are shown).
- **Flexible price sources**: fixed €/unit, dynamic price sensor (e.g. Tibber),
  or a ready-made cost sensor in € ("accumulated cost").
- **Feed-in reward**: fixed tariff or revenue sensor.
- **Baseline comparison** for EV/heating (cost of the old solution).
- **Real sensors** usable in automations and other cards.
- **Persistent**, restart-safe, robust against source counter resets.
- **Bundled Lovelace card** with a graphical editor.
- Bilingual: German (primary) & English.

Install via HACS as a **custom repository** (category *Integration*), restart,
then add **ROI Tracker** under *Settings → Devices & Services*.

## 🤝 Mitwirken / Contributing

Pull Requests und Issues sind willkommen! Tests der Berechnungslogik:

```bash
python3 tests/test_calculator.py
```

## 📄 Lizenz / License

[MIT](LICENSE)
