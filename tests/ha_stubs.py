"""Minimale Home-Assistant-Attrappen, um den Coordinator ohne HA zu testen.

Es werden nur die Teile nachgebildet, die ``coordinator.py`` und ``history.py``
benutzen. Die Integration wird als Paket ``rt`` geladen, ohne ``__init__.py``
auszuführen (das bräuchte die komplette HA-Installation).
"""

from __future__ import annotations

import importlib
import os
import sys
import types
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

LOCAL_TZ = ZoneInfo("Europe/Berlin")
COMPONENT_DIR = os.path.join(
    os.path.dirname(__file__), "..", "custom_components", "roi_tracker"
)


class Clock:
    now: datetime = datetime(2026, 5, 3, 10, 20, tzinfo=timezone.utc)


# ── homeassistant.util.dt ─────────────────────────────────────────────────────


def _make_dt_module() -> types.ModuleType:
    dt = types.ModuleType("homeassistant.util.dt")
    dt.DEFAULT_TIME_ZONE = LOCAL_TZ
    dt.utcnow = lambda: Clock.now
    dt.now = lambda: Clock.now.astimezone(LOCAL_TZ)
    dt.as_utc = lambda d: d.astimezone(timezone.utc)
    dt.as_local = lambda d: d.astimezone(LOCAL_TZ)
    dt.utc_from_timestamp = lambda ts: datetime.fromtimestamp(ts, timezone.utc)

    def parse_date(s):
        try:
            return date.fromisoformat(s)
        except (TypeError, ValueError):
            return None

    def parse_datetime(s):
        try:
            return datetime.fromisoformat(s)
        except (TypeError, ValueError):
            return None

    def start_of_local_day(d):
        if isinstance(d, datetime):
            d = d.astimezone(LOCAL_TZ).date()
        return datetime(d.year, d.month, d.day, tzinfo=LOCAL_TZ)

    dt.parse_date = parse_date
    dt.parse_datetime = parse_datetime
    dt.start_of_local_day = start_of_local_day
    return dt


# ── Store / Coordinator / Core ───────────────────────────────────────────────


class Store:
    DATA: dict[str, dict] = {}

    def __init__(self, hass, version, key):
        self.key = key

    async def async_load(self):
        return Store.DATA.get(self.key)

    async def async_save(self, data):
        import json

        Store.DATA[self.key] = json.loads(json.dumps(data))  # wie auf Platte

    async def async_remove(self):
        Store.DATA.pop(self.key, None)


class DataUpdateCoordinator:
    def __class_getitem__(cls, item):
        return cls

    def __init__(self, hass, logger, name, update_interval):
        self.hass = hass
        self.data = None

    async def async_refresh(self):
        self.data = await self._async_update_data()

    async_request_refresh = async_refresh


class State:
    def __init__(self, state, attributes=None):
        self.state = state
        self.attributes = attributes or {}


class States(dict):
    def get(self, entity_id):  # noqa: D401 - dict-API wie hass.states
        return super().get(entity_id)


class HomeAssistant:
    def __init__(self):
        self.states = States()
        self.config = types.SimpleNamespace(currency="EUR")


class ConfigEntry:
    def __init__(self, data, options=None, entry_id="abc", title="PV"):
        self.data = data
        self.options = options or {}
        self.entry_id = entry_id
        self.title = title


def install() -> types.ModuleType:
    """Registriert die Attrappen und lädt ``rt.coordinator``."""
    modules = {
        "homeassistant": types.ModuleType("homeassistant"),
        "homeassistant.util": types.ModuleType("homeassistant.util"),
        "homeassistant.util.dt": _make_dt_module(),
        "homeassistant.core": types.ModuleType("homeassistant.core"),
        "homeassistant.config_entries": types.ModuleType("homeassistant.config_entries"),
        "homeassistant.helpers": types.ModuleType("homeassistant.helpers"),
        "homeassistant.helpers.storage": types.ModuleType("homeassistant.helpers.storage"),
        "homeassistant.helpers.update_coordinator": types.ModuleType(
            "homeassistant.helpers.update_coordinator"
        ),
    }
    modules["homeassistant.util"].dt = modules["homeassistant.util.dt"]
    modules["homeassistant.core"].HomeAssistant = HomeAssistant
    modules["homeassistant.config_entries"].ConfigEntry = ConfigEntry
    modules["homeassistant.helpers.storage"].Store = Store
    modules["homeassistant.helpers.update_coordinator"].DataUpdateCoordinator = (
        DataUpdateCoordinator
    )
    sys.modules.update(modules)

    pkg = types.ModuleType("rt")
    pkg.__path__ = [os.path.abspath(COMPONENT_DIR)]
    sys.modules["rt"] = pkg
    return importlib.import_module("rt.coordinator")
