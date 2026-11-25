# Fehlersuche

## Fehlermeldungen bei der Einrichtung

| Meldung | Ursache | Lösung |
|---|---|---|
| Bitte einen Strompreis-Sensor oder einen festen Strompreis angeben. | Beide Preisfelder sind leer | Preis-Sensor wählen oder Festpreis eintragen |
| Dieser Preis-Sensor hat keine Langzeitstatistik … Bitte einen festen Strompreis als Ersatz eintragen. | Preis-Sensor ohne `state_class` und Startdatum älter als 10 Tage | Festpreis eintragen, z. B. deinen Ø-Arbeitspreis |
| Dieser Sensor hat keine Langzeitstatistik (state_class fehlt) und kann nicht verwendet werden. | Energie-Sensor ohne `state_class` | Einen kumulierten kWh-Zähler wählen, der auch im Energie-Dashboard funktioniert |
| Jeder Sensor darf nur einmal ausgewählt werden. | Derselbe Sensor in zwei Feldern | Jedem Feld einen eigenen Sensor zuordnen |
| Batterie geladen und Batterie entladen bitte gemeinsam angeben (oder beide leer lassen). | Nur eines der beiden Batterie-Felder gefüllt | Beide angeben oder beide leer lassen |
| Bitte mindestens einen Sensor auswählen. | Pflicht-Sensor fehlt | Pflichtfeld füllen, siehe [Schritt 2](configuration.md#schritt-2-energie-sensoren) |

## Dashboard-Karte

### Die Karte fehlt in der Kartenauswahl oder zeigt eine alte Version

Die Karte wird beim Start als Dashboard-Ressource eingetragen, mit der Version in der URL
(`/roi_tracker/roi-tracker-card.js?v=…`). Doppelte oder veraltete Einträge werden beim Start
entfernt.

1. Home Assistant neu starten.
2. Browser einmal mit **Strg+F5** neu laden. In der Companion App: *Einstellungen → Companion App →
   Fehlerbehebung → Frontend-Cache leeren*.
3. Unter **Einstellungen → Dashboards → Ressourcen** prüfen, ob die Karte eingetragen ist.

Konnte die Ressource nicht eingetragen werden, steht im Home-Assistant-Log eine Warnung
„Karte konnte nicht als Dashboard-Ressource eingetragen werden“.

### „Die gewählte Anlage gibt es nicht mehr“

Die Anlage wurde gelöscht und neu angelegt und hat dadurch eine neue Geräte-ID. Gibt es genau eine
ROI-Tracker-Anlage, nimmt die Karte sie automatisch. Sonst im Karten-Editor die Anlage neu wählen.

### „Keine ROI-Tracker-Anlage gefunden“ im Karten-Editor

Es ist noch keine Anlage eingerichtet. Zuerst die [Integration einrichten](configuration.md).

### „Noch keine Daten“

Die Werte erscheinen, sobald Home Assistant die erste Stunde der Statistik kompiliert hat.

## Werte wirken falsch

- **Ersparnis viel zu hoch oder zu niedrig:** Berechnungsart und Sensoren prüfen. Typische Verwechslung:
  Einspeisung statt Netzbezug gewählt, oder bei „Fertiger Eigenverbrauch“ den Hausverbrauch gewählt.
- **Batterie doppelt gezählt:** Bei „Fertiger Eigenverbrauch“ nur dann „Batterie entladen“ angeben,
  wenn der Eigenverbrauchs-Sensor die Batterie nicht schon enthält.
- **Eigenverbrauch leicht zu hoch:** DC-String-Zähler statt AC-Zähler (siehe [FAQ](faq.md#ac-oder-dc-zahler-fur-die-pv-erzeugung)).
- **Negative Werte vor dem ersten Zähler:** In Versionen vor 0.5.1 möglich, wenn ein Zähler erst
  nach dem Startdatum angelegt wurde. Auf 0.5.1 oder neuer aktualisieren.
- **Ersparnis 0 € in älteren Zeiträumen mit dynamischem Preis:** In Versionen vor 0.5.0 möglich.
  Aktualisieren und einen Festpreis als Ersatz eintragen.
- **Preislücken:** Fehlten für einzelne Stunden Preisdaten, zeigt das Detail-Popup unter **Übersicht** einen Hinweis mit der Anzahl der Stunden. Dort wurde der letzte bekannte Preis bzw. der Festpreis verwendet.

## Logs

!!! question "Offen"
    ROI Tracker beschreibt bisher kein eigenes Vorgehen für Logs. Allgemein gilt in Home Assistant:
    **Einstellungen → System → Protokolle**; ausführlicheres Logging per
    `logger:` in der `configuration.yaml` für `custom_components.roi_tracker`.
    Das ist ein allgemeiner Home-Assistant-Hinweis, nicht projektspezifisch geprüft.

## Fehler melden

Issues bitte auf [GitHub](https://github.com/PXLJAKE/ROI-Tracker/issues) mit Version von
ROI Tracker und Home Assistant, Berechnungsart und den relevanten Log-Zeilen.
