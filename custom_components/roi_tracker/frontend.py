"""Registriert die mitgelieferte Lovelace-Karte automatisch als Frontend-Ressource.

So muss der Nutzer die Karten-JS nicht manuell als Ressource hinzufügen. Die
Datei wird unter einer statischen URL bereitgestellt und als JS-Modul geladen.
"""

from __future__ import annotations

import logging
import os

from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

CARD_FILENAME = "roi-tracker-card.js"
CARD_URL = "/roi_tracker/roi-tracker-card.js"


async def async_register_card(hass: HomeAssistant) -> None:
    """Stellt die Karte als statische Datei bereit und lädt sie als Modul."""
    card_path = os.path.join(os.path.dirname(__file__), "www", CARD_FILENAME)
    if not os.path.exists(card_path):
        # Fallback: Karte liegt während der Entwicklung unter /dist im Repo-Root.
        _LOGGER.debug("Karten-Datei nicht in www/ gefunden (%s)", card_path)
        return

    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_URL, card_path, cache_headers=False)]
    )

    # Als zusätzliches JS-Modul registrieren (idempotent).
    try:
        from homeassistant.components.frontend import add_extra_js_url

        add_extra_js_url(hass, CARD_URL)
        _LOGGER.debug("ROI-Tracker-Karte als Frontend-Ressource registriert: %s", CARD_URL)
    except Exception as err:  # pragma: no cover - defensiv
        _LOGGER.warning("Karte konnte nicht automatisch registriert werden: %s", err)
