# Changelog

Alle Versionen mit Download stehen unter
[GitHub Releases](https://github.com/PXLJAKE/ROI-Tracker/releases). Nach jedem Update
Home Assistant neu starten und den Browser einmal mit **Strg+F5** neu laden.

## v0.5.1 (22.11.2026)

**Korrekte Werte vor dem ersten PV-Zähler und bei Preis-Lücken** ([Release](https://github.com/PXLJAKE/ROI-Tracker/releases/tag/v0.5.1))

- **Kein negativer Eigenverbrauch mehr**, wenn der Erzeugungs- bzw. Verbrauchs-Zähler erst nach dem
  Startdatum angelegt wurde. Für Stunden ohne Statistik-Zeile dieses Zählers wird nur noch die
  Einspeisung vergütet; Einspeisung und Batterie werden nicht mehr vom (fehlenden) Eigenverbrauch
  abgezogen.
- **Festpreis hat Vorrang vor weitem Rückwärtsfüllen:** Beginnt die Preis-Historie erst später, wurde
  bisher der erste bekannte Preis über bis zu 31 Tage rückwärts verteilt. Jetzt wird höchstens
  6 Stunden rückwärts gefüllt, davor gilt der eingetragene Festpreis.
- Nach dem Update wird jede Anlage einmal automatisch neu berechnet.

## v0.5.0 (22.11.2026)

**Mehrere PV-Strings, sichere Preise für dynamische Tarife, robustere Karte** ([Release](https://github.com/PXLJAKE/ROI-Tracker/releases/tag/v0.5.0))

- **Neu:** Mehrere PV-Erzeugungs-Zähler (Strings/Wechselrichter) bei „PV-Erzeugung − Einspeisung“,
  sie werden addiert. Ein Summen-Helfer ist nicht mehr nötig.
- **Dynamischer Preis ohne Langzeitstatistik** (z. B. `sensor.tibber_current_price`): Liegt das
  Startdatum mehr als 10 Tage zurück, verlangt die Einrichtung einen Festpreis als Ersatz. Vorher
  wurde die Ersparnis für Stunden ohne Preis-Historie mit 0 € gerechnet.
- **Karte:** Nach Löschen und Neuanlegen der Anlage verwendet die Karte automatisch die einzige
  vorhandene Anlage, sonst erscheint ein klarer Hinweis.
- **Dashboard-Ressource:** Doppelte Einträge der Karte werden beim Start entfernt.
- **Doku:** Installation zuerst über die HACS-Suche; Hinweis zu DC- vs. AC-Zählern.

## v0.4.1 (29.09.2026)

**Dashboard-Karte wird wieder zuverlässig registriert** ([Release](https://github.com/PXLJAKE/ROI-Tracker/releases/tag/v0.4.1))

- Die Karte wurde auf aktuellen Home-Assistant-Versionen nicht als Dashboard-Ressource eingetragen.
  Sie wird jetzt automatisch unter *Einstellungen → Dashboards → Ressourcen* registriert; ein manuell
  eingetragener Eintrag wird auf die neue Version aktualisiert.
- Klarere Hilfetexte: **Netzbezug** = Import-Zähler, **Einspeisung** = Export-Zähler.
- Probleme bei der Karten-Registrierung erscheinen als Warnung im Log.

## v0.4.0 (26.09.2026)

**Neuaufbau: stündlich aus der HA-Statistik, Monatsstatistik und Detail-Popup** ([Release](https://github.com/PXLJAKE/ROI-Tracker/releases/tag/v0.4.0))

Behobene Rechenfehler:

- Ein kurzer Sensor-Einbruch (z. B. 0 nach einem Neustart) hat den kompletten Zählerstand erneut
  gezählt; Tages-Resets wurden teils doppelt gezählt.
- Batterie-Entladung wurde doppelt gezählt, wenn der Verbrauchs-Sensor sie schon enthielt; Netzbezug
  wurde nie abgezogen.
- Rückwirkende Berechnung hat alles mit dem aktuellen Preis bewertet; Preis-Sensoren ohne Statistik
  haben sie abgebrochen.
- Geänderte Einstellungen wirkten nie rückwirkend; das Monatsdiagramm blieb leer; die Hochrechnung war
  saisonal verzerrt; die Preis-Einheit wurde ignoriert.

Neu:

- 3 Berechnungsarten, dynamische Preise stundengenau, Monats-/Jahres-/Tagesstatistik rückwirkend,
  Hochrechnung ab 12 Monaten aus den letzten 365 Tagen, automatische Neuberechnung,
  Karte in 4 Größen mit Detail-Popup.

### Update von 0.3.x

Beim ersten Start wird die bestehende Anlage automatisch übernommen (Berechnungsart „Fertiger
Eigenverbrauch“) und neu berechnet. Bitte danach prüfen:

- **Berechnungsart:** Ist dein Verbrauchs-Sensor eigentlich der *Hausverbrauch*? Dann auf
  „Hausverbrauch − Netzbezug“ umstellen.
- **Preis:** Der Modus „fertiger €-Sensor“ entfällt, bitte Preis-Sensor oder Festpreis eintragen.
- Der Schalter „Sensoren setzen täglich zurück“ entfällt (wird automatisch richtig behandelt).
- Der Service `roi_tracker.reset` entfällt, stattdessen `roi_tracker.recalculate`.
- Nicht mehr benötigte Sensoren werden entfernt (16 → 10); Gesamtertrag, Ersparnis, Einspeiseertrag,
  Restbetrag, Amortisation und ROI behalten ihre Entity-IDs.
- Karte: Die alten `show_*`/`tile_*`-Optionen werden ignoriert, stattdessen `variant` wählen.
- Mindestversion: Home Assistant 2025.1.

## Ältere Versionen

| Version | Datum | Titel |
|---|---|---|
| [v0.3.3](https://github.com/PXLJAKE/ROI-Tracker/releases/tag/v0.3.3) | 13.06.2026 | Heute-Sektion zeigt zuverlässig Werte |
| [v0.3.2](https://github.com/PXLJAKE/ROI-Tracker/releases/tag/v0.3.2) | 13.06.2026 | Energie-Zeilen und oberer Block einzeln ausblendbar |
| [v0.3.1](https://github.com/PXLJAKE/ROI-Tracker/releases/tag/v0.3.1) | 13.06.2026 | Fix: Heute-Sektion |
| [v0.3.0](https://github.com/PXLJAKE/ROI-Tracker/releases/tag/v0.3.0) | 13.06.2026 | Erster Stable-Release |

Vorabversionen 0.2.x (Mai/Juni 2026) sind auf
[GitHub Releases](https://github.com/PXLJAKE/ROI-Tracker/releases) aufgeführt.
