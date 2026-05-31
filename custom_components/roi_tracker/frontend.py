"""Registriert die Lovelace-Karte als Frontend-Ressource.

Strategie:
  1. Statischen Pfad SOFORT (re-)registrieren – HTTP-Handler reset bei HA-Neustart.
  2. add_extra_js_url SOFORT – greift beim nächsten Browser-Reload.
  3. Lovelace-Resource-Storage nach HA-Start – persistent, kein Browser-Reload nötig.
     (Muss nach EVENT_HOMEASSISTANT_STARTED aufgerufen werden, da hass.data["lovelace"]
      erst dann verfügbar ist.)

Alle Fehler werden nur geloggt; die Integration läuft immer weiter.
"""

from __future__ import annotations

import logging
import os

from homeassistant.core import HomeAssistant
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED

_LOGGER = logging.getLogger(__name__)

CARD_FILENAME = "roi-tracker-card.js"
CARD_URL = "/roi_tracker/roi-tracker-card.js"
_SESSION_KEY = "roi_tracker_card_js_registered"


async def async_register_card(hass: HomeAssistant) -> None:
    """Karte registrieren. Sicher mehrfach aufrufbar."""
    card_path = os.path.join(os.path.dirname(__file__), "www", CARD_FILENAME)
    if not os.path.exists(card_path):
        _LOGGER.error("Karten-Datei nicht gefunden: %s", card_path)
        return

    # 1. Statischen Pfad immer (re-)registrieren (wird bei HA-Neustart zurückgesetzt)
    await _register_static_path(hass, card_path)

    # 2. add_extra_js_url – greift sofort für neue Browser-Verbindungen
    _add_extra_js(hass)

    # 3. Lovelace-Resource-Storage: erst nach HA-Start verfügbar
    if not hass.data.get(_SESSION_KEY):
        if hass.is_running:
            await _register_lovelace_resource(hass)
            hass.data[_SESSION_KEY] = True
        else:
            # HA startet noch – auf EVENT_HOMEASSISTANT_STARTED warten
            async def _on_started(_event) -> None:
                try:
                    await _register_lovelace_resource(hass)
                    hass.data[_SESSION_KEY] = True
                except Exception as err:  # noqa: BLE001
                    _LOGGER.debug("Lovelace-Storage nach Start fehlgeschlagen: %s", err)

            hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, _on_started)


async def _register_static_path(hass: HomeAssistant, card_path: str) -> None:
    """Stellt die JS-Datei unter CARD_URL bereit."""
    try:
        from homeassistant.components.http import StaticPathConfig
        await hass.http.async_register_static_paths(
            [StaticPathConfig(CARD_URL, card_path, cache_headers=False)]
        )
        return
    except Exception:  # noqa: BLE001
        pass
    try:
        hass.http.register_static_path(CARD_URL, card_path, cache_headers=False)
    except Exception as err:  # noqa: BLE001
        _LOGGER.debug("Statischen Pfad registrieren fehlgeschlagen: %s", err)


def _add_extra_js(hass: HomeAssistant) -> None:
    """Fügt die Karte als extra JS-Modul hinzu (wirkt beim nächsten Seiten-Reload)."""
    try:
        from homeassistant.components.frontend import add_extra_js_url
        add_extra_js_url(hass, CARD_URL)
    except Exception as err:  # noqa: BLE001
        _LOGGER.debug("add_extra_js_url fehlgeschlagen: %s", err)


async def _register_lovelace_resource(hass: HomeAssistant) -> None:
    """Trägt die Karte in den Lovelace-Resource-Storage ein (persistent)."""
    try:
        from homeassistant.components.lovelace.resources import ResourceStorageCollection
        resources = hass.data.get("lovelace", {}).get("resources")
        if not isinstance(resources, ResourceStorageCollection):
            _LOGGER.debug(
                "Lovelace-Resource-Storage nicht verfügbar "
                "(YAML-Modus oder Lovelace nicht geladen). "
                "Karte manuell unter Einstellungen → Dashboards → Ressourcen eintragen: %s",
                CARD_URL,
            )
            return
        for item in resources.async_items():
            if item.get("url") == CARD_URL:
                return  # Bereits vorhanden
        await resources.async_create_item({"res_type": "module", "url": CARD_URL})
        _LOGGER.debug("ROI-Tracker-Karte in Lovelace-Storage eingetragen: %s", CARD_URL)
    except Exception as err:  # noqa: BLE001
        _LOGGER.debug("Lovelace-Resource-Storage Fehler: %s", err)
