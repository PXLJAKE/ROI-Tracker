"""Service ``roi_tracker.recalculate``: rückwirkend neu berechnen."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .const import ATTR_START_DATE, CONF_START_DATE, DOMAIN, SERVICE_RECALCULATE

_LOGGER = logging.getLogger(__name__)


def _resolve_entries(hass: HomeAssistant, call: ServiceCall) -> list:
    """Ermittelt die Ziel-Einträge aus Geräten/Entitäten des Service-Aufrufs."""
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

    entries = [
        entry
        for entry in hass.config_entries.async_entries(DOMAIN)
        if entry.entry_id in entry_ids and entry.state is ConfigEntryState.LOADED
    ]
    if not entries:
        raise HomeAssistantError(
            "Keine ROI-Tracker-Anlage im Ziel gefunden. Bitte ein Gerät oder eine "
            "Entität der Integration auswählen."
        )
    return entries


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, SERVICE_RECALCULATE):
        return

    async def _handle_recalculate(call: ServiceCall) -> None:
        start_date = call.data.get(ATTR_START_DATE)
        for entry in _resolve_entries(hass, call):
            _LOGGER.info("ROI Tracker '%s': rückwirkende Neuberechnung", entry.title)
            # Neues Startdatum in die Optionen schreiben → Reload → die geänderte
            # Konfiguration löst die Neuberechnung aus. Sonst direkt neu rechnen.
            if start_date:
                options = {**entry.data, **entry.options, CONF_START_DATE: start_date.isoformat()}
                if hass.config_entries.async_update_entry(entry, options=options):
                    continue
            await entry.runtime_data.async_recalculate()

    hass.services.async_register(
        DOMAIN,
        SERVICE_RECALCULATE,
        _handle_recalculate,
        schema=cv.make_entity_service_schema({vol.Optional(ATTR_START_DATE): cv.date}),
    )


@callback
def async_unload_services(hass: HomeAssistant, exclude: str | None = None) -> None:
    """Entfernt den Service, wenn keine andere Anlage mehr geladen ist."""
    others = [
        e for e in hass.config_entries.async_loaded_entries(DOMAIN) if e.entry_id != exclude
    ]
    if not others:
        hass.services.async_remove(DOMAIN, SERVICE_RECALCULATE)
