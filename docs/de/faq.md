# Häufige Fragen

## Welche Berechnungsart soll ich nehmen?

Wenn du einen Sensor für den **gesamten Hausverbrauch** hast: „Hausverbrauch − Netzbezug“.
Damit ist eine Batterie automatisch korrekt enthalten. Hast du nur die Sensoren aus dem
Energie-Dashboard (PV-Erzeugung, Einspeisung, Batterie), nimm „PV-Erzeugung − Einspeisung“.
Details: [Berechnungsart](configuration.md#berechnungsart).

## Ich habe mehrere PV-Strings oder Wechselrichter. Brauche ich einen Summen-Helfer?

Nein. Bei „PV-Erzeugung − Einspeisung“ kannst du mehrere Erzeugungs-Zähler wählen, sie werden
addiert (seit v0.5.0).

## AC- oder DC-Zähler für die PV-Erzeugung?

Am genauesten sind AC-Zähler des Wechselrichters. DC-String-Zähler enthalten noch die
Wandlungsverluste, der Eigenverbrauch fällt dann typisch 3–5 % zu hoch aus.

## Funktioniert das mit Tibber, aWATTar oder EPEX?

Ja. Wähle den Preis-Sensor als „Dynamischer Strompreis“. Die Einheit (€/kWh, ct/kWh, €/MWh)
wird automatisch erkannt. Hat der Sensor keine Langzeitstatistik (z. B.
`sensor.tibber_current_price`), sind Stundenpreise nur für etwa die letzten 10 Tage vorhanden.
Für ältere Zeiträume trägst du einen Festpreis als Ersatz ein; bei einem Startdatum, das älter
als 10 Tage ist, verlangt die Einrichtung das.

## Warum ist der Eigenverbrauch einer Stunde manchmal negativ?

Das ist gewollt, z. B. wenn die Batterie bei günstigem dynamischem Preis aus dem Netz geladen
wird. Beim späteren Entladen zum höheren Preis wird es wieder gutgeschrieben. Die Ersparnis
bildet so die tatsächliche Preisdifferenz ab.

## Wie weit zurück kann ROI Tracker rechnen?

So weit, wie Home Assistant Langzeitstatistik für deine Energie-Sensoren hat. Stunden vor dem
ersten Statistik-Eintrag eines Zählers werden nicht bewertet; Hochrechnung und Durchschnitt
beginnen am ersten Tag mit Daten.

## Warum steht die Jahresprognose auf „vorläufig“?

Solange weniger als 12 Monate Daten vorliegen, wird der Tagesdurchschnitt × 365 hochgerechnet.
Startest du im Sommer, ist das zu optimistisch, im Winter zu pessimistisch. Ab 12 Monaten gilt die
tatsächliche Summe der letzten 365 Tage.

## Muss ich nach einer Änderung neu berechnen?

Nein. Änderungen an Startdatum, Berechnungsart, Sensoren oder Preisen lösen automatisch eine
komplette Neuberechnung aus. Manuell geht es mit
[`roi_tracker.recalculate`](usage.md#neu-berechnen).

## Ersetzt das meine Stromabrechnung?

Nein. Alle Werte sind berechnete Schätzungen aus deinen Sensoren und Preisen, ohne Grundgebühren,
Steuern oder Abrechnungsdetails deines Versorgers.
