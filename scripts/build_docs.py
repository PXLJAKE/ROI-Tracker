#!/usr/bin/env python3
"""Baut die Doku-Website für das Hosting unter /docs/roi-tracker/.

1. ``mkdocs build --strict`` mit der Platzhalter-Domain aus mkdocs.yml
   (site_url: https://docs.invalid/docs/roi-tracker/).
2. Nachbearbeitung: Die Platzhalter-Domain wird aus HTML und Sitemap entfernt,
   alle relativen Links und Assets (inkl. Sprachumschalter und Theme-Konfiguration)
   werden zu absoluten Pfaden, die mit /docs/roi-tracker/ beginnen. So funktioniert
   die Seite auf jeder Domain, ohne dass diese beim Bauen bekannt ist.
3. Optional (--zip): ZIP mit genau einem Ordner roi-tracker/.

Nur Standardbibliothek + MkDocs (requirements-docs.txt).

    python scripts/build_docs.py                      # → site/
    python scripts/build_docs.py --zip 0.5.1          # → dist-docs/roi-tracker-docs-0.5.1.zip
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from urllib.parse import urljoin

PROJECT = "roi-tracker"
PLACEHOLDER = "https://docs.invalid"
PREFIX = f"/docs/{PROJECT}/"
DEFAULT_LANG = "de"

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
DIST = ROOT / "dist-docs"

ATTR_RE = re.compile(r'(\s(?:href|src)=)(["\'])(.*?)\2', re.S)
SWITCH_RE = re.compile(r'<a href="[^"]*" hreflang="([a-z-]+)" class="md-select__link">')
SCOPE_RE = re.compile(r'(__md_scope=new URL\(")([^"]*)(",location\))')
CONFIG_RE = re.compile(
    r'(<script id="__config" type="application/json">)(.*?)(</script>)', re.S
)
EXTERNAL = re.compile(r"^(?:[a-zA-Z][a-zA-Z0-9+.-]*:|//|#)")


def check_site_url() -> None:
    text = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    match = re.search(r"^site_url:\s*(\S+)\s*$", text, re.M)
    expected = PLACEHOLDER + PREFIX
    if not match or match.group(1) != expected:
        sys.exit(f"mkdocs.yml: site_url muss {expected} sein")


def page_url(html_file: Path) -> str:
    rel = html_file.relative_to(SITE).as_posix()
    return PREFIX + rel  # urljoin ignoriert den Dateinamen


def absolutize(value: str, base: str) -> str:
    if value.startswith(PLACEHOLDER):
        value = value[len(PLACEHOLDER):]
    if value == "" or EXTERNAL.match(value) or value.startswith("/"):
        return value
    return urljoin(base, value)


def process_html(html_file: Path) -> None:
    base = page_url(html_file)
    text = html_file.read_text(encoding="utf-8")

    def attr(m: re.Match) -> str:
        return f"{m.group(1)}{m.group(2)}{absolutize(m.group(3), base)}{m.group(2)}"

    def config(m: re.Match) -> str:
        cfg = json.loads(m.group(2))
        # base braucht den abschließenden "/", sonst löst Material
        # "search/search_index.json" eine Ebene zu hoch auf.
        cfg["base"] = absolutize(cfg["base"].rstrip("/") + "/", base)
        cfg["search"] = absolutize(cfg["search"], base)
        return m.group(1) + json.dumps(cfg, ensure_ascii=False) + m.group(3)

    text = ATTR_RE.sub(attr, text)
    if html_file == SITE / "404.html":
        # mkdocs-static-i18n setzt auf der 404-Seite die Sprachlinks einer
        # anderen Seite ein → auf die Startseite der jeweiligen Sprache zeigen.
        text = SWITCH_RE.sub(
            lambda m: '<a href="{}" hreflang="{}" class="md-select__link">'.format(
                PREFIX if m.group(1) == DEFAULT_LANG else f"{PREFIX}{m.group(1)}/", m.group(1)
            ),
            text,
        )
    text = CONFIG_RE.sub(config, text)
    # Material speichert Einstellungen (z. B. Hell/Dunkel) pro "Scope" = Basis-URL.
    text = SCOPE_RE.sub(lambda m: m.group(1) + absolutize(m.group(2).rstrip("/") + "/", base) + m.group(3), text)
    text = text.replace(PLACEHOLDER + PREFIX, PREFIX)
    if PLACEHOLDER in text:
        sys.exit(f"{html_file}: Platzhalter-Domain nicht vollständig entfernt")
    html_file.write_text(text, encoding="utf-8")


def process_sitemap() -> None:
    sitemap = SITE / "sitemap.xml"
    if not sitemap.exists():
        return
    text = sitemap.read_text(encoding="utf-8").replace(PLACEHOLDER, "")
    sitemap.write_text(text, encoding="utf-8")
    with gzip.GzipFile(SITE / "sitemap.xml.gz", "wb", mtime=0) as fh:
        fh.write(text.encode("utf-8"))


def build() -> None:
    check_site_url()
    env = {**os.environ, "NO_MKDOCS_2_WARNING": "1"}
    subprocess.run(
        [sys.executable, "-m", "mkdocs", "build", "--strict", "--clean", "-d", str(SITE)],
        cwd=ROOT, env=env, check=True,
    )
    for html_file in sorted(SITE.rglob("*.html")):
        process_html(html_file)
    process_sitemap()
    print(f"Doku gebaut: {SITE} (Pfade beginnen mit {PREFIX})")


def make_zip(version: str) -> Path:
    if not re.fullmatch(r"[0-9A-Za-z][0-9A-Za-z.+-]*", version):
        sys.exit(f"Ungültige Version: {version}")
    DIST.mkdir(exist_ok=True)
    target = DIST / f"{PROJECT}-docs-{version}.zip"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(SITE.rglob("*")):
            if path.is_file():
                zf.write(path, f"{PROJECT}/{path.relative_to(SITE).as_posix()}")
    print(f"ZIP erstellt: {target}")
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--zip", metavar="VERSION", help="zusätzlich ZIP für diese Version bauen")
    args = parser.parse_args()
    build()
    if args.zip:
        make_zip(args.zip.removeprefix("v"))


if __name__ == "__main__":
    main()
