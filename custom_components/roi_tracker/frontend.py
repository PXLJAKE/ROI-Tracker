"""Registriert die mitgelieferte Lovelace-Karte als Frontend-Ressource.

Strategie:
  1. Statischen Pfad bei JEDEM Setup-Aufruf (re-)registrieren – HTTP-Handler
     werden bei HA-Neustart zurückgesetzt, der Pfad muss neu registriert werden.
  2. Lovelace-Resource-Storage (persistent, kein Browser-Reload nötig).
  3. add_extra_js_url als Fallback (braucht Browser-Reload).

Alle Fehler werden nur geloggt; die Integration läuft immer weiter.
"""

from __future__ import annotations

import logging
import os

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

CARD_FILENAME = "roi-tracker-card.js"
CARD_URL = "/roi_tracker/roi-tracker-card.js"
_SESSION_KEY = "roi_tracker_card_resource_registered"


async def async_register_card(hass: HomeAssistant) -> None:
    """Registriert die Karte. Kann sicher mehrfach aufgerufen werden."""
    try:
        await _async_do_register(hass)
    except Exception as err:  # noqa: BLE001
        _LOGGER.warning(
            "ROI-Tracker-Karte konnte nicht automatisch registriert werden (%s). "
            "Füge '%s' manuell als Lovelace-Ressource (JavaScript-Modul) hinzu.",
            err, CARD_URL,
        )


async def _async_do_register(hass: HomeAssistant) -> None:
    card_path = os.path.join(os.path.dirname(__file__), "www", CARD_FILENAME)
    if not os.path.exists(card_path):
        _LOGGER.error("Karten-Datei nicht gefunden: %s", card_path)
        return

    # Statischen Pfad IMMER (re-)registrieren – nach HA-Neustart nötig.
    await _register_static_path(hass, card_path)

    # Lovelace-Ressource + add_extra_js_url nur einmal pro Session nötig.
    if hass.data.get(_SESSION_KEY):
        return

    if await _register_lovelace_resource(hass):
        hass.data[_SESSION_KEY] = True
        _LOGGER.debug("ROI-Tracker-Karte via Lovelace-Storage registriert: %s", CARD_URL)
        return

    # Fallback: add_extra_js_url (wirkt nach nächstem Browser-Reload)
    try:
        from homeassistant.components.frontend import add_extra_js_url
        add_extra_js_url(hass, CARD_URL)
        hass.data[_SESSION_KEY] = True
        _LOGGER.info(
            "ROI-Tracker-Karte via add_extra_js_url registriert: %s "
            "(Browser-Reload nötig wenn Karte nicht sichtbar)", CARD_URL
        )
    except Exception as err:  # noqa: BLE001
        _LOGGER.warning(
            "add_extra_js_url fehlgeschlagen: %s – bitte '%s' manuell als "
            "Lovelace-Ressource eintragen.", err, CARD_URL
        )


async def _register_static_path(hass: HomeAssistant, card_path: str) -> None:
    """Stellt die JS-Datei unter CARD_URL bereit (nach jedem Neustart nötig)."""
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


async def _register_lovelace_resource(hass: HomeAssistant) -> bool:
    """Trägt die Karte in den Lovelace-Resource-Storage ein (persistent)."""
    try:
        from homeassistant.components.lovelace.resources import ResourceStorageCollection
        resources = hass.data.get("lovelace", {}).get("resources")
        if not isinstance(resources, ResourceStorageCollection):
            return False
        for item in resources.async_items():
            if item.get("url") == CARD_URL:
                return True  # Bereits vorhanden
        await resources.async_create_item({"res_type": "module", "url": CARD_URL})
        return True
    except Exception:  # noqa: BLE001
        return False
