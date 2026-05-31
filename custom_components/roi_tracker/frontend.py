"""Registriert die mitgelieferte Lovelace-Karte als Frontend-Ressource.

Strategie (von zuverlässig nach veraltet):
  1. Lovelace-Resource-Storage – persistiert über Neustarts, löst sofort im
     Browser aus ohne Seiten-Reload.
  2. add_extra_js_url – lädt das Modul beim nächsten Seiten-Reload.
  3. Statischer Pfad ohne JS-Registrierung – URL erreichbar, Nutzer muss die
     Ressource manuell in Lovelace eintragen.

Alle Fehler werden nur protokolliert; die Integration läuft immer weiter.
"""

from __future__ import annotations

import logging
import os

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

CARD_FILENAME = "roi-tracker-card.js"
CARD_URL = "/roi_tracker/roi-tracker-card.js"
_REGISTERED_KEY = "roi_tracker_card_registered"


async def async_register_card(hass: HomeAssistant) -> None:
    """Registriert die Karte einmalig; schlägt niemals durch."""
    if hass.data.get(_REGISTERED_KEY):
        return
    try:
        await _async_do_register(hass)
    except Exception as err:  # noqa: BLE001
        _LOGGER.warning(
            "ROI-Tracker-Karte konnte nicht automatisch registriert werden (%s). "
            "Füge '%s' manuell als Lovelace-Ressource (Typ: JavaScript-Modul) hinzu.",
            err, CARD_URL,
        )


async def _async_do_register(hass: HomeAssistant) -> None:
    card_path = os.path.join(os.path.dirname(__file__), "www", CARD_FILENAME)
    if not os.path.exists(card_path):
        _LOGGER.warning("Karten-Datei nicht gefunden: %s", card_path)
        return

    # ── 1. Statischen Pfad bereitstellen ──────────────────────────────────────
    await _register_static_path(hass, card_path)

    # ── 2a. Lovelace Resource Storage (bevorzugt) ─────────────────────────────
    if await _register_lovelace_resource(hass):
        hass.data[_REGISTERED_KEY] = True
        _LOGGER.debug("ROI-Tracker-Karte via Lovelace-Storage registriert: %s", CARD_URL)
        return

    # ── 2b. add_extra_js_url (Fallback) ───────────────────────────────────────
    try:
        from homeassistant.components.frontend import add_extra_js_url
        add_extra_js_url(hass, CARD_URL)
        hass.data[_REGISTERED_KEY] = True
        _LOGGER.debug("ROI-Tracker-Karte via add_extra_js_url registriert: %s", CARD_URL)
    except Exception as err:  # noqa: BLE001
        _LOGGER.debug("add_extra_js_url fehlgeschlagen: %s – bitte manuell eintragen.", err)


async def _register_static_path(hass: HomeAssistant, card_path: str) -> None:
    """Stellt die JS-Datei unter CARD_URL bereit."""
    try:
        from homeassistant.components.http import StaticPathConfig
        await hass.http.async_register_static_paths(
            [StaticPathConfig(CARD_URL, card_path, cache_headers=False)]
        )
    except Exception:  # noqa: BLE001
        try:
            hass.http.register_static_path(CARD_URL, card_path, cache_headers=False)
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("Statischen Pfad registrieren fehlgeschlagen: %s", err)


async def _register_lovelace_resource(hass: HomeAssistant) -> bool:
    """Trägt die Karte in den Lovelace-Resource-Storage ein.

    Gibt True zurück wenn erfolgreich, False wenn nicht verfügbar.
    """
    try:
        from homeassistant.components.lovelace.resources import ResourceStorageCollection

        lovelace_data = hass.data.get("lovelace", {})
        resources = lovelace_data.get("resources")
        if not isinstance(resources, ResourceStorageCollection):
            return False

        # Prüfen ob schon eingetragen
        for item in resources.async_items():
            if item.get("url") == CARD_URL:
                return True  # Bereits vorhanden

        await resources.async_create_item({"res_type": "module", "url": CARD_URL})
        return True
    except Exception:  # noqa: BLE001
        return False
