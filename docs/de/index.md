# ROI Tracker

**Wann hat sich deine PV-Anlage bezahlt gemacht?**

ROI Tracker ist eine Integration für [Home Assistant](https://www.home-assistant.io/).
Sie rechnet aus, wie viel du durch selbst genutzten Solarstrom **gespart** und durch
Einspeisung **verdient** hast, mit festem oder dynamischem Strompreis (Tibber,
aWATTar, EPEX …), und zeigt Amortisation, ROI, Monatsstatistik und eine
Hochrechnung bis zum Break-Even.

!!! warning "Schätzwerte"
    Alle Werte sind **berechnete Schätzungen** auf Basis deiner Sensoren und Preise.
    Sie ersetzen keine Energieabrechnung und keine Steuerberatung.

## Funktionen

- **Ersparnis**: jede selbst genutzte kWh × Strompreis *der jeweiligen Stunde*
- **Einspeiseertrag**: eingespeiste kWh × Einspeisevergütung
- **ROI & Amortisation**: Gesamtertrag gegen Investition, offener Restbetrag, Break-Even-Datum
- **Monats- und Jahresstatistik** mit Tageswerten
- **Hochrechnung**: ab 12 Monaten Daten saisonal korrekt aus den echten Erträgen
- **Rückwirkend** ab Inbetriebnahme, soweit Home Assistant Statistikdaten hat
- **Dashboard-Karte** in 4 Größen, ein Klick öffnet ein Popup mit allen Details
- Oberfläche auf **Deutsch und Englisch**

## In drei Schritten zum Ergebnis

1. [Installieren](installation.md) über HACS
2. [Anlage einrichten](configuration.md): Preise und Energie-Sensoren wählen
3. [Karte aufs Dashboard](usage.md#dashboard-karte) legen

## Weiter

- [So wird gerechnet](usage.md#so-wird-gerechnet)
- [Häufige Fragen](faq.md)
- [Fehlersuche](troubleshooting.md)
- [Änderungen pro Version](changelog.md)
- Quellcode und Issues auf [GitHub](https://github.com/PXLJAKE/ROI-Tracker)
