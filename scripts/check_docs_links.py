#!/usr/bin/env python3
"""Prüft die gebaute Doku (site/) unter dem Unterpfad /docs/roi-tracker/.

Liefert site/ mit einem einfachen HTTP-Server unter /docs/roi-tracker/ aus und
ruft jeden Link und jedes Asset aus allen HTML-Seiten, der Sitemap und der
Theme-Konfiguration ab. Fehler, wenn
  - ein interner Link nicht mit /docs/roi-tracker/ beginnt (relativ oder anderer Pfad),
  - ein Abruf nicht 200 liefert,
  - irgendwo noch die Platzhalter-Domain steht.

    python scripts/check_docs_links.py
"""

from __future__ import annotations

import functools
import http.server
import json
import re
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from html import unescape
from pathlib import Path

PROJECT = "roi-tracker"
PREFIX = f"/docs/{PROJECT}/"
PLACEHOLDER = "docs.invalid"
SITE = Path(__file__).resolve().parent.parent / "site"

ATTR_RE = re.compile(r'\s(?:href|src)=(["\'])(.*?)\1', re.S)
CONFIG_RE = re.compile(r'<script id="__config" type="application/json">(.*?)</script>', re.S)
LOC_RE = re.compile(r"<loc>(.*?)</loc>")
EXTERNAL = re.compile(r"^(?:[a-zA-Z][a-zA-Z0-9+.-]*:|//|#)")


def main() -> int:
    if not (SITE / "index.html").exists():
        print("site/ fehlt – zuerst scripts/build_docs.py ausführen", file=sys.stderr)
        return 1

    errors: list[str] = []
    links: dict[str, set[str]] = {}

    def add(url: str, source: str) -> None:
        if url == "" or EXTERNAL.match(url):
            return
        if not url.startswith(PREFIX) or "//" in url:
            errors.append(f"{source}: Link beginnt nicht mit {PREFIX}: {url}")
            return
        links.setdefault(url.split("#")[0].split("?")[0], set()).add(source)

    for f in sorted(SITE.rglob("*")):
        if f.suffix not in (".html", ".xml", ".json", ".js", ".css") or not f.is_file():
            continue
        rel = f.relative_to(SITE).as_posix()
        text = f.read_text(encoding="utf-8", errors="replace")
        if PLACEHOLDER in text:
            errors.append(f"{rel}: enthält noch die Platzhalter-Domain")
        if f.suffix == ".html":
            for _, value in ATTR_RE.findall(text):
                add(unescape(value), rel)
            for scope in re.findall(r'__md_scope=new URL\("([^"]*)"', text):
                add(scope, f"{rel} (__md_scope)")
            m = CONFIG_RE.search(text)
            if m:
                cfg = json.loads(m.group(1))
                if not cfg["base"].endswith("/"):
                    errors.append(f"{rel}: __config.base muss mit / enden: {cfg['base']}")
                add(cfg["base"], f"{rel} (__config.base)")
                add(cfg["base"] + "search/search_index.json", f"{rel} (Suchindex)")
                add(cfg["search"], f"{rel} (__config.search)")
        elif f.name == "sitemap.xml":
            for loc in LOC_RE.findall(text):
                add(loc, rel)

    with tempfile.TemporaryDirectory() as tmp:
        webroot = Path(tmp)
        (webroot / "docs").mkdir()
        (webroot / "docs" / PROJECT).symlink_to(SITE, target_is_directory=True)
        handler = functools.partial(QuietHandler, directory=str(webroot))
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        host = f"http://127.0.0.1:{server.server_port}"
        try:
            for url in sorted(links):
                try:
                    with urllib.request.urlopen(host + url) as resp:
                        resp.read()
                        status = resp.status
                except urllib.error.HTTPError as err:
                    status = err.code
                if status != 200:
                    errors.append(f"{url}: HTTP {status} (verlinkt in {sorted(links[url])[0]})")
        finally:
            server.shutdown()

    for err in errors:
        print(f"FEHLER {err}")
    print(f"{len(links)} absolute Links unter {PREFIX} geprüft, {len(errors)} Fehler")
    return 1 if errors else 0


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args) -> None:  # noqa: D102
        pass


if __name__ == "__main__":
    sys.exit(main())
