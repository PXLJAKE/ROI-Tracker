"""Services für ROI Tracker (z. B. einen Rechner zurücksetzen)."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN, SERVICE_RESET

_LOGGER = logging.getLogger(__name__)


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Registriert die ROI-Tracker-Services (einmalig)."""
    if hass.services.has_service(DOMAIN, SERVICE_RESET):
        return

    async def _handle_reset(call: ServiceCall) -> None:
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
            if entry.entry_id in entry_ids
            and entry.state is ConfigEntryState.LOADED
        ]

        if not coordinators:
            raise HomeAssistantError(
                "Keine ROI-Tracker-Anlage im Ziel gefunden. Bitte ein Gerät der "
                "Integration auswählen."
            )

        for coordinator in coordinators:
            _LOGGER.info("Setze ROI-Rechner zurück: %s", coordinator.entry.title)
            await coordinator.async_reset()

    hass.services.async_register(
        DOMAIN,
        SERVICE_RESET,
        _handle_reset,
        schema=cv.make_entity_service_schema({}),
    )


@callback
def async_unload_services(hass: HomeAssistant) -> None:
    """Entfernt die Services, wenn keine Einträge mehr geladen sind."""
    if not hass.config_entries.async_loaded_entries(DOMAIN):
        hass.services.async_remove(DOMAIN, SERVICE_RESET)
