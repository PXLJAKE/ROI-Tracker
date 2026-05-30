"""Registriert die mitgelieferte Lovelace-Karte automatisch als Frontend-Ressource.

So muss der Nutzer die Karten-JS nicht manuell als Ressource hinzufügen. Die
Datei wird unter einer statischen URL bereitgestellt und als JS-Modul geladen.

Bewusst defensiv: Alle Home-Assistant-spezifischen Importe passieren erst zur
Laufzeit innerhalb der Funktion. So kann ein Versions-Unterschied im Frontend-
oder HTTP-API niemals den Import der Integration (und damit den Config-Flow)
verhindern. Schlägt die Registrierung fehl, läuft die Integration trotzdem –
nur die Karte muss dann ggf. manuell als Ressource hinzugefügt werden.
"""

from __future__ import annotations

import logging
import os

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

CARD_FILENAME = "roi-tracker-card.js"
CARD_URL = "/roi_tracker/roi-tracker-card.js"


async def async_register_card(hass: HomeAssistant) -> None:
    """Stellt die Karte als statische Datei bereit und lädt sie als Modul.

    Greift nie nach oben durch: Jeder Fehler wird nur protokolliert.
    """
    try:
        await _async_register_card(hass)
    except Exception as err:  # noqa: BLE001 - defensiv, darf Setup nie stoppen
        _LOGGER.warning(
            "ROI-Tracker-Karte konnte nicht automatisch registriert werden "
            "(%s). Die Integration funktioniert weiterhin; füge die Karte bei "
            "Bedarf manuell als Lovelace-Ressource hinzu: %s",
            err,
            CARD_URL,
        )


async def _async_register_card(hass: HomeAssistant) -> None:
    card_path = os.path.join(os.path.dirname(__file__), "www", CARD_FILENAME)
    if not os.path.exists(card_path):
        _LOGGER.debug("Karten-Datei nicht gefunden: %s", card_path)
        return

    # Schon registriert? (Setup wird pro Anlage aufgerufen.)
    if getattr(hass.data.setdefault("roi_tracker_frontend", {}), "get", None):
        if hass.data["roi_tracker_frontend"].get("registered"):
            return

    # --- Statische Datei bereitstellen --------------------------------------
    registered_static = False
    try:
        # Neuer Weg (HA 2024.7+)
        from homeassistant.components.http import StaticPathConfig

        await hass.http.async_register_static_paths(
            [StaticPathConfig(CARD_URL, card_path, cache_headers=False)]
        )
        registered_static = True
    except ImportError:
        # Älterer Weg (synchron, deprecated, aber funktional)
        try:
            hass.http.register_static_path(CARD_URL, card_path, cache_headers=False)
            registered_static = True
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("register_static_path (Fallback) fehlgeschlagen: %s", err)

    if not registered_static:
        return

    # --- Als zusätzliches JS-Modul im Frontend registrieren -----------------
    try:
        from homeassistant.components.frontend import add_extra_js_url

        add_extra_js_url(hass, CARD_URL)
    except Exception as err:  # noqa: BLE001
        _LOGGER.debug("add_extra_js_url fehlgeschlagen: %s", err)
        return

    hass.data.setdefault("roi_tracker_frontend", {})["registered"] = True
    _LOGGER.debug("ROI-Tracker-Karte registriert: %s", CARD_URL)
