# Mitmachen

Pull Requests und Issues sind willkommen:
[Issues](https://github.com/PXLJAKE/ROI-Tracker/issues) ·
[Pull Requests](https://github.com/PXLJAKE/ROI-Tracker/pulls)

## Projektaufbau

| Pfad | Inhalt |
|---|---|
| [`custom_components/roi_tracker/`](https://github.com/PXLJAKE/ROI-Tracker/tree/main/custom_components/roi_tracker) | Die Integration |
| `calculator.py` | Reine Berechnung ohne Home-Assistant-Abhängigkeiten |
| `coordinator.py` | Liest die Statistik, bewertet Stunden, speichert Tageswerte |
| `config_flow.py` | Einrichtungs- und Options-Dialog |
| `www/roi-tracker-card.js` | Dashboard-Karte |
| `translations/` | Texte Deutsch/Englisch |
| [`tests/`](https://github.com/PXLJAKE/ROI-Tracker/tree/main/tests) | Tests mit HA-Stubs |
| [`release-notes/`](https://github.com/PXLJAKE/ROI-Tracker/tree/main/release-notes) | Release-Texte pro Version |
| `docs/` | Diese Dokumentation (MkDocs) |

## Tests

Die Tests laufen ohne Home-Assistant-Installation:

```bash
pip install pytest
python -m pytest tests
```

Bei jedem Push und Pull Request laufen außerdem **Hassfest**, die **HACS-Validierung** und die Tests
([validate.yml](https://github.com/PXLJAKE/ROI-Tracker/blob/main/.github/workflows/validate.yml)).

## Release-Ablauf

1. Version in [`manifest.json`](https://github.com/PXLJAKE/ROI-Tracker/blob/main/custom_components/roi_tracker/manifest.json)
   erhöhen und `release-notes/v<version>.md` anlegen (erste Zeile = Titel).
2. Nach dem Merge auf `main` erstellt
   [release.yml](https://github.com/PXLJAKE/ROI-Tracker/blob/main/.github/workflows/release.yml)
   automatisch das Release mit `roi_tracker.zip` und der Doku als `roi-tracker-docs-<version>.zip`.

## Dokumentation

Die Doku liegt in `docs/de/` und `docs/en/` (gleiche Dateinamen in beiden Sprachen).

```bash
pip install --require-hashes -r requirements-docs.txt
mkdocs serve                 # Vorschau auf http://127.0.0.1:8000/
mkdocs build --strict        # wie in der CI
```

Links auf Dateien außerhalb von `docs/` bitte als absolute GitHub-Links schreiben, sonst schlägt
`mkdocs build --strict` fehl. Abhängigkeiten aktualisieren:

```bash
pip install pip-tools
pip-compile --generate-hashes --allow-unsafe --strip-extras \
  -o requirements-docs.txt requirements-docs.in
```

## Richtlinien

!!! question "Offen"
    Es gibt bisher keine festgelegten Richtlinien zu Code-Stil, Commit-Nachrichten oder
    Branch-Namen. Aus der Historie: Commit-Nachrichten auf Deutsch im Stil
    `feat: …` / `fix: …`, die Texte der Integration liegen in `strings.json` sowie `translations/de.json` und `translations/en.json`.
