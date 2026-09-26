"""WebSocket-API für die Dashboard-Karte: ``roi_tracker/data``.

Liefert Kennzahlen, Monate, Jahre und die Tage eines Monats. So muss die Karte
keine großen Statistik-Attribute über den Recorder laden.
"""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN

_REGISTERED = f"{DOMAIN}_ws_registered"


@callback
def async_register_websocket(hass: HomeAssistant) -> None:
    if hass.data.get(_REGISTERED):
        return
    hass.data[_REGISTERED] = True
    websocket_api.async_register_command(hass, ws_get_data)


def _find_coordinator(hass: HomeAssistant, msg: dict[str, Any]):
    entry_ids: set[str] = set()
    if msg.get("entry_id"):
        entry_ids.add(msg["entry_id"])
    if msg.get("device_id"):
        device = dr.async_get(hass).async_get(msg["device_id"])
        if device:
            entry_ids |= set(device.config_entries)
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.entry_id in entry_ids and entry.state is ConfigEntryState.LOADED:
            return entry.runtime_data
    return None


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/data",
        vol.Optional("entry_id"): str,
        vol.Optional("device_id"): str,
        vol.Optional("month"): vol.Match(r"^\d{4}-\d{2}$"),
    }
)
@callback
def ws_get_data(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    coordinator = _find_coordinator(hass, msg)
    if coordinator is None:
        connection.send_error(msg["id"], "not_found", "ROI-Tracker-Anlage nicht gefunden")
        return
    connection.send_result(msg["id"], coordinator.export(msg.get("month")))
