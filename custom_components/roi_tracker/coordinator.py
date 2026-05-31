"""DataUpdateCoordinator: liest Quell-Sensoren, rechnet ROI, persistiert Zustand."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from . import calculator
from .calculator import RoiResult, RoiState
from .history import async_get_sensor_value_at
from .const import (
    CONF_BASELINE_RATE,
    CONF_BATTERY_DISCHARGE_SENSOR,
    CONF_CONSUMPTION_SENSOR,
    CONF_COST_SENSOR,
    CONF_EXPORT_SENSOR,
    CONF_GRID_IMPORT_SENSOR,
    CONF_INVESTMENT,
    CONF_PRICE_FIXED,
    CONF_PRICE_MODE,
    CONF_PRICE_SENSOR,
    CONF_PRODUCTION_SENSOR,
    CONF_REWARD_FIXED,
    CONF_REWARD_MODE,
    CONF_REWARD_SENSOR,
    CONF_START_DATE,
    CONF_TEMPLATE,
    DEFAULT_UPDATE_INTERVAL_MINUTES,
    DOMAIN,
    PRICE_MODE_COST_SENSOR,
    PRICE_MODE_FIXED,
    PRICE_MODE_SENSOR,
    STORAGE_KEY,
    STORAGE_VERSION,
)

_LOGGER = logging.getLogger(__name__)


class RoiTrackerCoordinator(DataUpdateCoordinator[RoiResult]):
    """Koordiniert das periodische Aktualisieren eines ROI-Rechners."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.title}",
            update_interval=timedelta(minutes=DEFAULT_UPDATE_INTERVAL_MINUTES),
        )
        self.entry = entry
        self._store: Store = Store(
            hass, STORAGE_VERSION, STORAGE_KEY.format(entry_id=entry.entry_id)
        )
        self._state: RoiState = RoiState()
        self._override_start_date: str | None = None

    @property
    def config(self) -> dict:
        return {**self.entry.data, **self.entry.options}

    async def async_load_state(self) -> None:
        stored = await self._store.async_load()
        if stored:
            self._state = RoiState.from_dict(stored)
            return
        self._state = RoiState()
        await self.async_seed_from_history()
        await self._async_save_state()

    def _parse_start_date(self):
        raw = self._override_start_date or self.config.get(CONF_START_DATE)
        if not raw:
            return None
        try:
            dt = dt_util.parse_datetime(raw)
            if dt is None:
                date = dt_util.parse_date(raw)
                if date is None:
                    return None
                dt = datetime(date.year, date.month, date.day)
            return dt_util.as_utc(
                dt if dt.tzinfo else dt.replace(tzinfo=dt_util.DEFAULT_TIME_ZONE)
            )
        except (ValueError, TypeError):
            _LOGGER.warning("Ungültiges Startdatum: %s", raw)
            return None

    async def async_seed_from_history(self) -> bool:
        start = self._parse_start_date()
        if start is None:
            return False

        cfg = self.config
        self._state.first_update = start.isoformat()
        seeded = False

        async def _seed(conf_key: str, attr: str) -> None:
            nonlocal seeded
            entity_id = cfg.get(conf_key)
            value = await async_get_sensor_value_at(self.hass, entity_id, start)
            if value is not None:
                setattr(self._state, attr, value)
                seeded = True
                _LOGGER.debug(
                    "Basislinie %s = %s (Stand %s) aus Historie gesetzt",
                    entity_id, value, start.date(),
                )

        await _seed(CONF_CONSUMPTION_SENSOR, "last_consumption")
        await _seed(CONF_EXPORT_SENSOR, "last_export")
        await _seed(CONF_BATTERY_DISCHARGE_SENSOR, "last_battery_discharge")
        await _seed(CONF_COST_SENSOR, "last_cost_total")
        await _seed(CONF_REWARD_SENSOR, "last_reward_total")
        await _seed(CONF_GRID_IMPORT_SENSOR, "last_grid_import")

        if not seeded:
            _LOGGER.info(
                "Startdatum gesetzt, aber keine Historie für die Sensoren gefunden. "
                "Die Berechnung startet ab jetzt."
            )
        return seeded

    async def async_recalculate_from(self, start_date: str | None = None) -> None:
        self._state = RoiState()
        await self._store.async_remove()
        if start_date:
            self._override_start_date = start_date
        await self.async_seed_from_history()
        await self._async_save_state()
        await self.async_request_refresh()

    async def _async_save_state(self) -> None:
        await self._store.async_save(self._state.to_dict())

    def _read_number(self, entity_id: str | None) -> float | None:
        if not entity_id:
            return None
        state = self.hass.states.get(entity_id)
        if state is None or state.state in ("unknown", "unavailable", "", None):
            return None
        try:
            return float(state.state)
        except (ValueError, TypeError):
            _LOGGER.debug("Sensor %s liefert keinen Zahlenwert: %s", entity_id, state.state)
            return None

    async def _async_update_data(self) -> RoiResult:
        cfg = self.config
        investment = float(cfg.get(CONF_INVESTMENT, 0) or 0)

        consumption = self._read_number(cfg.get(CONF_CONSUMPTION_SENSOR))
        export = self._read_number(cfg.get(CONF_EXPORT_SENSOR))
        battery_discharge = self._read_number(cfg.get(CONF_BATTERY_DISCHARGE_SENSOR))
        production = self._read_number(cfg.get(CONF_PRODUCTION_SENSOR))
        grid_import = self._read_number(cfg.get(CONF_GRID_IMPORT_SENSOR))

        # Baseline (nur TEMPLATE_CUSTOM, manuell eingetragen)
        raw_base = cfg.get(CONF_BASELINE_RATE)
        baseline_rate = float(raw_base) if raw_base not in (None, "") else None

        # Bezugspreis
        price_mode = cfg.get(CONF_PRICE_MODE, PRICE_MODE_FIXED)
        price_per_unit: float | None = None
        cost_total: float | None = None
        if price_mode == PRICE_MODE_FIXED:
            val = cfg.get(CONF_PRICE_FIXED)
            price_per_unit = float(val) if val not in (None, "") else None
        elif price_mode == PRICE_MODE_SENSOR:
            price_per_unit = self._read_number(cfg.get(CONF_PRICE_SENSOR))
        elif price_mode == PRICE_MODE_COST_SENSOR:
            cost_total = self._read_number(cfg.get(CONF_COST_SENSOR))

        # Vergütung
        reward_mode = cfg.get(CONF_REWARD_MODE, PRICE_MODE_FIXED)
        reward_per_unit: float | None = None
        reward_total: float | None = None
        if reward_mode == PRICE_MODE_FIXED:
            val = cfg.get(CONF_REWARD_FIXED)
            reward_per_unit = float(val) if val not in (None, "") else None
        elif reward_mode == PRICE_MODE_SENSOR:
            reward_total = self._read_number(cfg.get(CONF_REWARD_SENSOR))

        result = calculator.update(
            self._state,
            investment=investment,
            now=dt_util.utcnow(),
            consumption=consumption,
            export=export,
            battery_discharge=battery_discharge,
            grid_import=grid_import,
            price_per_unit=price_per_unit,
            reward_per_unit=reward_per_unit,
            cost_total=cost_total,
            reward_total=reward_total,
            baseline_rate=baseline_rate,
        )

        result.attributes["template"] = cfg.get(CONF_TEMPLATE, "custom")
        if production is not None:
            result.attributes["total_production"] = round(production, 3)

        await self._async_save_state()
        return result

    async def async_reset(self) -> None:
        self._state = RoiState()
        await self._store.async_remove()
        await self.async_request_refresh()
