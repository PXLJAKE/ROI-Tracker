# Konfiguration

Eine Anlage wird unter **Einstellungen → Geräte & Dienste → Integration
hinzufügen → ROI Tracker** in zwei Schritten angelegt. Du kannst mehrere Anlagen
anlegen; jede bekommt ein eigenes Gerät mit eigenen Sensoren.

## Schritt 1: Grunddaten

| Feld | Pflicht | Bedeutung |
|---|---|---|
| Name | ja | Name der Anlage (Standard: „PV-Anlage“) |
| Anschaffungskosten | ja | Gesamtkosten der Anlage in €, die sich amortisieren sollen |
| Inbetriebnahme / Startdatum | ja | Ab diesem Tag wird gerechnet, auch in der Vergangenheit, soweit HA Statistikdaten hat |
| Wie wird der Eigenverbrauch ermittelt? | ja | Die [Berechnungsart](#berechnungsart), bestimmt die Sensoren in Schritt 2 |
| Dynamischer Strompreis (Sensor) | eins von beiden | Preis-Sensor, z. B. Tibber, aWATTar, EPEX. Erlaubt sind `sensor`- und `input_number`-Entitäten |
| Fester Strompreis (€/kWh) | eins von beiden | Dein Arbeitspreis, z. B. `0.32`. Mit Preis-Sensor dient er nur als Ersatz für Zeiten ohne Preisdaten |
| Einspeisevergütung (€/kWh) | ja | Z. B. `0.082` für 8,2 ct/kWh, `0` ohne Vergütung |

### Berechnungsart

Die Berechnungsart legt fest, wie die **selbst genutzten kWh** pro Stunde ermittelt werden:

| Berechnungsart | Formel pro Stunde | Wann nutzen |
|---|---|---|
| **Hausverbrauch − Netzbezug** *(empfohlen)* | Hausverbrauch − Netzbezug | Du hast einen Sensor für den gesamten Hausverbrauch |
| **PV-Erzeugung − Einspeisung** | PV − Einspeisung + Batterie-Entladung − Batterie-Ladung | Du hast die Sensoren aus dem Energie-Dashboard |
| **Fertiger Eigenverbrauch** | Eigenverbrauch (+ Batterie-Entladung) | Dein Wechselrichter liefert den Eigenverbrauch direkt |

Bei „Hausverbrauch − Netzbezug“ ist eine Batterie automatisch korrekt enthalten.

### Strompreis

- **Einheit:** €/kWh, ct/kWh oder €/MWh wird anhand der Einheit des Sensors automatisch erkannt.
- **Mit Langzeitstatistik** (`state_class: measurement`): Die Rückrechnung ist stundengenau.
- **Ohne Langzeitstatistik** (z. B. `sensor.tibber_current_price`): Der Preis wird aus der
  Zustands-Historie gelesen (Standard: die letzten 10 Tage). Liegt das Startdatum mehr als
  10 Tage zurück, verlangt die Einrichtung deshalb einen **Festpreis als Ersatz**.
- **Lücken in den Preisdaten:** Für eine Stunde ohne Preis gilt der zuletzt bekannte Preis.
  Vor dem ersten bekannten Preis wird höchstens **6 Stunden** rückwärts aufgefüllt, davor gilt
  der Festpreis. Ohne Festpreis wird der erste bekannte Preis verwendet.

## Schritt 2: Energie-Sensoren

Alle Energie-Sensoren müssen **kumulierte kWh-Zähler mit Langzeitstatistik** sein
(`device_class: energy` und eine `state_class`), also genau die Sensoren, die auch im
Energie-Dashboard funktionieren. Jeder Sensor darf nur einmal gewählt werden.

=== "Hausverbrauch − Netzbezug"

    | Sensor | Pflicht | Hinweis |
    |---|---|---|
    | Hausverbrauch gesamt (kWh) | ja | Gesamter Stromverbrauch des Hauses, egal ob aus PV, Batterie oder Netz |
    | Netzbezug (kWh) | ja | Import-/Bezugszähler, **nicht** die Einspeisung. Im Energie-Dashboard: Stromnetz → Netzbezug |
    | Einspeisung (kWh) | nein | Export-Zähler, nötig für den Einspeiseertrag. Im Energie-Dashboard: Stromnetz → Netzeinspeisung |

=== "PV-Erzeugung − Einspeisung"

    | Sensor | Pflicht | Hinweis |
    |---|---|---|
    | PV-Erzeugung (kWh) | ja | Ein oder mehrere Zähler; mehrere Strings oder Wechselrichter werden addiert |
    | Einspeisung (kWh) | ja | Export-Zähler |
    | Batterie geladen (kWh) | nein | Nur zusammen mit „Batterie entladen“ |
    | Batterie entladen (kWh) | nein | Nur zusammen mit „Batterie geladen“ |

    Am genauesten sind **AC-Zähler** des Wechselrichters. DC-String-Zähler enthalten noch
    die Wandlungsverluste (typisch 3–5 % zu viel Eigenverbrauch).

=== "Fertiger Eigenverbrauch"

    | Sensor | Pflicht | Hinweis |
    |---|---|---|
    | PV-Eigenverbrauch (kWh) | ja | Direkt genutzter PV-Strom, **nicht** der Hausverbrauch und **nicht** der Netzbezug |
    | Batterie entladen (kWh) | nein | Nur angeben, wenn der Eigenverbrauch die Batterie **nicht** bereits enthält |
    | Einspeisung (kWh) | nein | Export-Zähler, nötig für den Einspeiseertrag |

## Nachträglich ändern

Alle Einstellungen lassen sich unter **Einstellungen → Geräte & Dienste → ROI Tracker →
Konfigurieren** ändern. Änderungen an Startdatum, Berechnungsart, Sensoren oder Preisen
lösen automatisch eine **komplette Neuberechnung** ab dem Startdatum aus. Eine Änderung
der Anschaffungskosten ändert nur ROI, Amortisation und Prognose; die Tageswerte bleiben.

Probleme bei der Einrichtung: siehe [Fehlersuche](troubleshooting.md#fehlermeldungen-bei-der-einrichtung).
