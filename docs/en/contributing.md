# Contributing

Pull requests and issues are welcome:
[Issues](https://github.com/PXLJAKE/ROI-Tracker/issues) ·
[Pull requests](https://github.com/PXLJAKE/ROI-Tracker/pulls)

## Project layout

| Path | Content |
|---|---|
| [`custom_components/roi_tracker/`](https://github.com/PXLJAKE/ROI-Tracker/tree/main/custom_components/roi_tracker) | The integration |
| `calculator.py` | Pure calculation without Home Assistant dependencies |
| `coordinator.py` | Reads statistics, values hours, stores daily values |
| `config_flow.py` | Setup and options dialog |
| `www/roi-tracker-card.js` | Dashboard card |
| `translations/` | German/English texts |
| [`tests/`](https://github.com/PXLJAKE/ROI-Tracker/tree/main/tests) | Tests with HA stubs |
| [`release-notes/`](https://github.com/PXLJAKE/ROI-Tracker/tree/main/release-notes) | Release notes per version |
| `docs/` | This documentation (MkDocs) |

## Tests

The tests run without a Home Assistant installation:

```bash
pip install pytest
python -m pytest tests
```

Every push and pull request also runs **Hassfest**, the **HACS validation** and the tests
([validate.yml](https://github.com/PXLJAKE/ROI-Tracker/blob/main/.github/workflows/validate.yml)).

## Release process

1. Bump the version in [`manifest.json`](https://github.com/PXLJAKE/ROI-Tracker/blob/main/custom_components/roi_tracker/manifest.json)
   and add `release-notes/v<version>.md` (first line = title).
2. After merging to `main`,
   [release.yml](https://github.com/PXLJAKE/ROI-Tracker/blob/main/.github/workflows/release.yml)
   creates the release automatically with `roi_tracker.zip` and the docs as `roi-tracker-docs-<version>.zip`.

## Documentation

The docs live in `docs/de/` and `docs/en/` (same file names in both languages).

```bash
pip install --require-hashes -r requirements-docs.txt
mkdocs serve                          # preview at http://127.0.0.1:8000/docs/roi-tracker/
python scripts/build_docs.py          # as in CI: build --strict, paths under /docs/roi-tracker/
python scripts/check_docs_links.py    # fetch every link under /docs/roi-tracker/ (must return 200)
python scripts/build_docs.py --zip 0.5.1   # additionally dist-docs/roi-tracker-docs-0.5.1.zip
```

`site_url` in `mkdocs.yml` is a placeholder domain; `build_docs.py` removes it after the build so that
all links and assets start with `/docs/roi-tracker/`. The ZIP contains exactly one folder
`roi-tracker/`, which is copied into the website's `docs` folder.

Links to files outside `docs/` must be absolute GitHub links, otherwise `mkdocs build --strict`
fails. Updating dependencies:

```bash
pip install pip-tools
pip-compile --generate-hashes --allow-unsafe --strip-extras \
  -o requirements-docs.txt requirements-docs.in
```

## Guidelines

!!! question "Open"
    There are no agreed guidelines for code style, commit messages or branch names yet. From the
    history: commit messages in German in the style `feat: …` / `fix: …`; the integration's texts
    live in `strings.json` plus `translations/de.json` and `translations/en.json`.
