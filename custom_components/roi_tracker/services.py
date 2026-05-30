"""Services für ROI Tracker (zurücksetzen, rückwirkend neu berechnen)."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .const import ATTR_START_DATE, DOMAIN, SERVICE_RECALCULATE, SERVICE_RESET

_LOGGER = logging.getLogger(__name__)


def _resolve_coordinators(hass: HomeAssistant, call: ServiceCall) -> list:
    """Ermittelt die Ziel-Coordinatoren aus Geräten/Entitäten des Service-Aufrufs."""
    entry_ids: set[str] = set()

    dev_reg = dr.async_get(hass)
    for device_id in call.data.get("device_id", []):
        device = dev_reg.async_get(device_id)
        if device:
            entry_ids |= set(device.config_entries)

    ent_reg = er.async_get(hass)
    for entity_id in call.data.get("entity_id", []):
        entity = ent_reg.async_get(entity_id)
        if entity and entity.config_entry_id:
            entry_ids.add(entity.config_entry_id)

    coordinators = [
        entry.runtime_data
        for entry in hass.config_entries.async_entries(DOMAIN)
        if entry.entry_id in entry_ids and entry.state is ConfigEntryState.LOADED
    ]

    if not coordinators:
        raise HomeAssistantError(
            "Keine ROI-Tracker-Anlage im Ziel gefunden. Bitte ein Gerät der "
            "Integration auswählen."
        )
    return coordinators


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Registriert die ROI-Tracker-Services (einmalig)."""
    if hass.services.has_service(DOMAIN, SERVICE_RESET):
        return

    async def _handle_reset(call: ServiceCall) -> None:
        for coordinator in _resolve_coordinators(hass, call):
            _LOGGER.info("Setze ROI-Rechner zurück: %s", coordinator.entry.title)
            await coordinator.async_reset()

    async def _handle_recalculate(call: ServiceCall) -> None:
        start_date = call.data.get(ATTR_START_DATE)
        start_iso = start_date.isoformat() if start_date else None
        for coordinator in _resolve_coordinators(hass, call):
            _LOGGER.info(
                "Berechne ROI-Rechner '%s' rückwirkend neu (ab %s)",
                coordinator.entry.title,
                start_iso or "konfiguriertem Startdatum",
            )
            await coordinator.async_recalculate_from(start_iso)

    hass.services.async_register(
        DOMAIN,
        SERVICE_RESET,
        _handle_reset,
        schema=cv.make_entity_service_schema({}),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_RECALCULATE,
        _handle_recalculate,
        schema=cv.make_entity_service_schema(
            {vol.Optional(ATTR_START_DATE): cv.date}
        ),
    )


@callback
def async_unload_services(hass: HomeAssistant) -> None:
    """Entfernt die Services, wenn keine Einträge mehr geladen sind."""
    if not hass.config_entries.async_loaded_entries(DOMAIN):
        hass.services.async_remove(DOMAIN, SERVICE_RESET)
        hass.services.async_remove(DOMAIN, SERVICE_RECALCULATE)
