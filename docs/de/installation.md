# Installation

## Voraussetzungen

- **Home Assistant 2025.1** oder neuer
- **Recorder** aktiv (ROI Tracker rechnet aus der Langzeitstatistik)
- [HACS](https://hacs.xyz/) für die empfohlene Installation

## Über HACS (empfohlen)

ROI Tracker ist im HACS-Standardkatalog enthalten:

1. In HACS nach **ROI Tracker** suchen.
2. **ROI Tracker** herunterladen und Home Assistant neu starten.
3. **Einstellungen → Geräte & Dienste → Integration hinzufügen → ROI Tracker**.

[In HACS öffnen](https://my.home-assistant.io/redirect/hacs_repository/?owner=PXLJAKE&repository=ROI-Tracker&category=integration){ .md-button }

### Falls ROI Tracker in HACS nicht auftaucht

Ältere HACS-Versionen: HACS → **Drei-Punkte-Menü** → **Benutzerdefinierte Repositories**
→ URL `https://github.com/PXLJAKE/ROI-Tracker`, Kategorie **Integration**.
Danach wie oben herunterladen und neu starten.

## Manuelle Installation

!!! question "Offen"
    Jedes Release enthält eine Datei `roi_tracker.zip` mit dem Inhalt von
    `custom_components/roi_tracker`. Eine Anleitung zur manuellen Installation
    gibt es im Projekt bisher nicht, und sie ist nicht getestet beschrieben.

## Nach der Installation

- Die **Dashboard-Karte** wird automatisch als Dashboard-Ressource registriert.
  Falls sie nicht in der Kartenauswahl erscheint: Browser einmal mit **Strg+F5** neu laden.
- Weiter mit der [Konfiguration](configuration.md).

## Update

Updates kommen über HACS. Nach jedem Update Home Assistant neu starten und den
Browser einmal mit **Strg+F5** neu laden, damit die neue Kartenversion geladen wird.
Hinweise zu einzelnen Versionen stehen im [Changelog](changelog.md).
