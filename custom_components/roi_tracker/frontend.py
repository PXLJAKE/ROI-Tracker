"""Registriert die Lovelace-Karte als Frontend-Ressource.

WICHTIG – Cache-Busting:
Browser und HA-Service-Worker cachen ES-Module unter ihrer URL extrem
aggressiv. Bleibt die URL gleich (``/roi_tracker/roi-tracker-card.js``), wird
eine aktualisierte Datei NICHT neu geladen – auch nicht bei Reinstall.
Deshalb hängen wir die Integrations-Version als Query an
(``?v=0.2.7``). Ändert sich die Version, ändert sich die URL → der Browser
lädt das Modul garantiert neu.

Strategie:
  1. Statischen Pfad (ohne Query) immer (re-)registrieren.
  2. Bestehende Lovelace-Ressource auf die versionierte URL aktualisieren
     (oder neu anlegen) – persistent, kein Browser-Reload nötig.
  3. add_extra_js_url mit versionierter URL als Fallback.
"""

from __future__ import annotations

import json
import logging
import os

from homeassistant.core import HomeAssistant
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED

_LOGGER = logging.getLogger(__name__)

CARD_FILENAME = "roi-tracker-card.js"
CARD_PATH = "/roi_tracker/roi-tracker-card.js"  # statischer Pfad (ohne Query)
_SESSION_KEY = "roi_tracker_card_js_registered"


def _read_version() -> str:
    """Liest die Version aus manifest.json (Cache-Busting-Query)."""
    try:
        manifest = os.path.join(os.path.dirname(__file__), "manifest.json")
        with open(manifest, encoding="utf-8") as f:
            return str(json.load(f).get("version", "0"))
    except Exception:  # noqa: BLE001
        return "0"


async def async_register_card(hass: HomeAssistant) -> None:
    """Karte registrieren. Sicher mehrfach aufrufbar."""
    card_file = os.path.join(os.path.dirname(__file__), "www", CARD_FILENAME)
    if not os.path.exists(card_file):
        _LOGGER.error("Karten-Datei nicht gefunden: %s", card_file)
        return

    version = await hass.async_add_executor_job(_read_version)
    versioned_url = f"{CARD_PATH}?v={version}"

    # 1. Statischen Pfad immer (re-)registrieren (HTTP-Handler reset bei Neustart)
    await _register_static_path(hass, card_file)

    # 2. add_extra_js_url mit versionierter URL (greift bei nächstem Browser-Reload)
    _add_extra_js(hass, versioned_url)

    # 3. Lovelace-Resource-Storage: erst nach HA-Start verfügbar
    if hass.data.get(_SESSION_KEY) == versioned_url:
        return

    async def _do_lovelace() -> None:
        if await _register_lovelace_resource(hass, versioned_url):
            hass.data[_SESSION_KEY] = versioned_url

    if hass.is_running:
        await _do_lovelace()
    else:
        async def _on_started(_event) -> None:
            try:
                await _do_lovelace()
            except Exception as err:  # noqa: BLE001
                _LOGGER.debug("Lovelace-Registrierung nach Start fehlgeschlagen: %s", err)

        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, _on_started)


async def _register_static_path(hass: HomeAssistant, card_file: str) -> None:
    """Stellt die JS-Datei unter CARD_PATH bereit (Query wird ignoriert)."""
    try:
        from homeassistant.components.http import StaticPathConfig
        await hass.http.async_register_static_paths(
            [StaticPathConfig(CARD_PATH, card_file, cache_headers=False)]
        )
        return
    except Exception:  # noqa: BLE001
        pass
    try:
        hass.http.register_static_path(CARD_PATH, card_file, cache_headers=False)
    except Exception as err:  # noqa: BLE001
        _LOGGER.debug("Statischen Pfad registrieren fehlgeschlagen: %s", err)


def _add_extra_js(hass: HomeAssistant, url: str) -> None:
    """Fügt die Karte als extra JS-Modul hinzu (wirkt beim nächsten Seiten-Reload)."""
    try:
        from homeassistant.components.frontend import add_extra_js_url
        add_extra_js_url(hass, url)
    except Exception as err:  # noqa: BLE001
        _LOGGER.debug("add_extra_js_url fehlgeschlagen: %s", err)


async def _register_lovelace_resource(hass: HomeAssistant, url: str) -> bool:
    """Trägt die Karte in den Lovelace-Resource-Storage ein bzw. aktualisiert sie.

    Findet eine bestehende roi_tracker-Ressource und aktualisiert deren URL auf
    die versionierte Variante (Cache-Busting). Existiert keine, wird sie neu
    angelegt.
    """
    try:
        from homeassistant.components.lovelace.resources import ResourceStorageCollection
        resources = hass.data.get("lovelace", {}).get("resources")
        if not isinstance(resources, ResourceStorageCollection):
            _LOGGER.debug(
                "Lovelace-Resource-Storage nicht verfügbar (YAML-Modus?). "
                "Karte manuell als Ressource eintragen: %s", url,
            )
            return False

        # Storage ggf. erst laden
        if hasattr(resources, "async_get_info"):
            try:
                await resources.async_get_info()
            except Exception:  # noqa: BLE001
                pass

        existing = None
        for item in resources.async_items():
            item_url = item.get("url", "")
            if item_url.split("?")[0] == CARD_PATH:
                existing = item
                break

        if existing:
            if existing.get("url") == url:
                return True  # Schon aktuell
            # URL auf neue Version aktualisieren → Browser lädt neu
            await resources.async_update_item(existing["id"], {"url": url})
            _LOGGER.info("ROI-Tracker-Karten-Ressource aktualisiert: %s", url)
            return True

        await resources.async_create_item({"res_type": "module", "url": url})
        _LOGGER.info("ROI-Tracker-Karten-Ressource angelegt: %s", url)
        return True
    except Exception as err:  # noqa: BLE001
        _LOGGER.debug("Lovelace-Resource-Storage Fehler: %s", err)
        return False
