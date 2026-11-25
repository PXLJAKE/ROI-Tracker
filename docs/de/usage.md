# Nutzung

## So wird gerechnet

Grundlage ist die **Langzeitstatistik von Home Assistant**, also dieselben Daten wie im
Energie-Dashboard. Für jede Stunde gilt:

```text
Ersparnis    = selbst genutzte kWh × Strompreis dieser Stunde
Einspeisung  = eingespeiste kWh    × Einspeisevergütung

Gesamtertrag = Σ Ersparnis + Σ Einspeisung
Amortisation = Gesamtertrag / Investition
ROI          = (Gesamtertrag − Investition) / Investition
```

Wie die selbst genutzten kWh ermittelt werden, hängt von der
[Berechnungsart](configuration.md#berechnungsart) ab.

Warum stündlich aus der Statistik?

- **Dynamische Preise** werden korrekt bewertet: Mittags-kWh zum Mittagspreis, Abend-kWh zum Abendpreis.
- **Batterie-Laden aus dem Netz** (günstige Stunden) und Entladen (teure Stunden) wird korrekt als
  Ersparnis gewertet. Der Eigenverbrauch einer Stunde darf dabei negativ sein.
- **Zähler-Resets, Tageszähler, Ausfälle und Neustarts** sind in der HA-Statistik bereits sauber
  behandelt, es wird nichts doppelt gezählt.
- Änderst du Startdatum, Sensoren oder Preise, wird **automatisch komplett neu gerechnet**.

### Aktualisierung

ROI Tracker aktualisiert alle **5 Minuten**. Fertig kompilierte Stunden werden bewertet und als
Tageswerte gespeichert; die laufende Stunde wird aus der 5-Minuten-Statistik geschätzt und nur
angezeigt, nicht gespeichert.

### Hochrechnung und Break-Even

- **Ab 12 Monaten Daten:** Jahresprognose = Summe der letzten 365 Tage. Sommer und Winter
  gleichen sich aus.
- **Vorher:** Tagesdurchschnitt × 365. In der Karte als *vorläufig* markiert.
- Gezählt wird ab dem **ersten Tag mit Daten**, nicht ab dem eingetragenen Startdatum. Reicht die
  HA-Statistik nicht so weit zurück, wäre der Durchschnitt sonst zu niedrig.
- **Break-Even-Datum:** heute + offener Restbetrag ÷ Tagesdurchschnitt. Ist die Anlage schon
  abbezahlt, der Tag, an dem der Gesamtertrag die Investition erreicht hat.

## Sensoren pro Anlage

| Sensor | Einheit | Beschreibung |
|---|---|---|
| Gesamtertrag | € | Ersparnis + Einspeiseertrag |
| Ersparnis | € | Vermiedene Stromkosten durch Eigenverbrauch |
| Einspeiseertrag | € | Vergütung für eingespeisten Strom (nur mit Einspeise-Sensor) |
| Offener Restbetrag | € | Noch nicht amortisierter Betrag |
| Amortisation | % | Zurückgeflossener Anteil der Investition |
| ROI | % | Gewinn/Verlust bezogen auf die Investition |
| Jahresprognose | € | Erwarteter Ertrag pro Jahr |
| Break-Even-Datum | Datum | Voraussichtlich (oder tatsächlich) abbezahlt am |
| Eigenverbrauch gesamt | kWh | Selbst genutzte Energie seit Start |
| Einspeisung gesamt | kWh | Eingespeiste Energie seit Start (nur mit Einspeise-Sensor) |

Die Währung der €-Sensoren ist die in Home Assistant eingestellte Währung.

Der Sensor **Gesamtertrag** hat zusätzlich diese Attribute:

| Attribut | Bedeutung |
|---|---|
| `investment` | Anschaffungskosten |
| `data_since` | Erster Tag mit Daten |
| `daily_average` | Ertrag pro Tag laut Hochrechnung |
| `month_total` | Ertrag im laufenden Monat |
| `month_forecast` | Prognose für den laufenden Monat |
| `today_total` | Ertrag heute |
| `avg_price` | Durchschnittlicher Strompreis der selbst genutzten kWh |
| `years_to_breakeven` | Jahre bis zum Break-Even |
| `projection_provisional` | `true`, solange weniger als 12 Monate Daten vorliegen |

## Dashboard-Karte

Die Karte wird automatisch registriert. Im Karten-Editor Anlage und Darstellung wählen:

| Variante | Inhalt |
|---|---|
| `mini` | Eine Zeile: Gesamtertrag + Amortisations-Balken |
| `compact` | Donut, Gesamtertrag, Ersparnis / Einspeisung |
| `standard` | Zusätzlich: dieser Monat, Jahresprognose, Break-Even, ROI |
| `full` | Zusätzlich: Balkendiagramm der letzten 12 Monate |

```yaml
type: custom:roi-tracker-card
device: <Geräte-ID der Anlage>
variant: standard   # mini | compact | standard | full
title: PV-Anlage    # optional
language: de        # optional: de oder en, Standard ist die Sprache von Home Assistant
```

**Ein Klick auf die Karte öffnet das Detail-Popup:**

- **Übersicht**: alle Kennzahlen, kWh, Ø Strompreis, Preisquelle
- **Monate**: Balkendiagramm und Tabelle pro Jahr, Jahresübersicht; Klick auf einen Monat zeigt die Tageswerte
- **Prognose**: kumulierter Ertrag gegen Investition mit Hochrechnung bis zum Break-Even

Die Karte lädt ihre Daten alle 5 Minuten neu.

## Neu berechnen

Normalerweise nicht nötig: Geänderte Einstellungen lösen die Neuberechnung automatisch aus.
Manuell über die Aktion `roi_tracker.recalculate`:

```yaml
action: roi_tracker.recalculate
target:
  entity_id: sensor.<anlage>_gesamtertrag
data:
  start_date: "2025-01-01"   # optional, wird in der Anlage gespeichert
```

## Anlage löschen

Wird eine Anlage unter **Geräte & Dienste** gelöscht, werden auch ihre gespeicherten Tageswerte
entfernt.
