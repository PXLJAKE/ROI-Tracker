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


def _average(values: list[float]) -> float | None:
    """Gibt den Durchschnitt einer Liste zurück, oder None wenn leer."""
    return sum(values) / len(values) if values else None


def _nearest_price(price_by_start: dict, ts) -> float | None:
    """Fallback-Preis wenn kein exakter Treffer: Gesamtdurchschnitt."""
    if not price_by_start:
        return None
    return _average(list(price_by_start.values()))


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

    # ── Setup / Laden ─────────────────────────────────────────────────────────

    async def async_load_state(self) -> None:
        """Zustand laden. Bei leerem Store rückwirkend aus Historie berechnen."""
        stored = await self._store.async_load()
        if stored:
            self._state = RoiState.from_dict(stored)
            return

        self._state = RoiState()
        cfg = self.config
        price_mode = cfg.get(CONF_PRICE_MODE, PRICE_MODE_FIXED)

        # Genauere stündliche Statistik-Methode für dynamische Preissensoren
        seeded = False
        if price_mode == PRICE_MODE_SENSOR and cfg.get(CONF_START_DATE):
            seeded = await self.async_seed_from_statistics()

        if not seeded:
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

    # ── Rückwirkende Berechnung ───────────────────────────────────────────────

    async def async_seed_from_statistics(self) -> bool:
        """Berechnet den ROI rückwirkend aus stündlichen HA-Statistiken.

        Funktionsweise:
          - Liest stündliche Statistiken für Verbrauch-Sensor und Preis-Sensor
          - Multipliziert pro Stunde: Δverbrauch × damaliger Tibber-Preis
          - Deutlich genauer als die einfache Baseline-Methode, da historische
            Preisschwankungen berücksichtigt werden
          - Setzt last_* auf aktuelle Sensorwerte, damit künftige 5-Minuten-Updates
            korrekt weiterlaufen

        Gibt True zurück wenn mindestens Preis- und Verbrauchsdaten vorhanden.
        """
        start = self._parse_start_date()
        if start is None:
            return False

        cfg = self.config
        consumption_id = cfg.get(CONF_CONSUMPTION_SENSOR)
        price_id = cfg.get(CONF_PRICE_SENSOR)
        if not consumption_id or not price_id:
            return False

        export_id = cfg.get(CONF_EXPORT_SENSOR)
        battery_id = cfg.get(CONF_BATTERY_DISCHARGE_SENSOR)
        grid_import_id = cfg.get(CONF_GRID_IMPORT_SENSOR)

        raw_reward = cfg.get(CONF_REWARD_FIXED)
        reward_per_unit = float(raw_reward) if raw_reward not in (None, "") else 0.0

        statistic_ids = {
            s for s in [consumption_id, price_id, export_id, battery_id, grid_import_id]
            if s
        }
        now = dt_util.utcnow()

        try:
            from homeassistant.components.recorder import get_instance
            from homeassistant.components.recorder.statistics import statistics_during_period

            instance = get_instance(self.hass)
            stats = await instance.async_add_executor_job(
                statistics_during_period,
                self.hass,
                start,
                now,
                statistic_ids,
                "hour",
                None,
                {"mean", "change"},
            )
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning(
                "Stündliche Statistiken konnten nicht gelesen werden: %s. "
                "Nutze einfache Baseline-Methode.", err
            )
            return False

        # Preis-Dictionary: start-Zeitstempel → mittlerer Preis dieser Stunde
        price_by_start: dict = {}
        for row in stats.get(price_id, []):
            ts = row.get("start")
            mean = row.get("mean")
            if ts is not None and mean is not None:
                price_by_start[ts] = mean

        if not price_by_start:
            _LOGGER.info(
                "Keine Preisstatistiken für '%s' ab %s – "
                "nutze einfache Baseline-Methode.", price_id, start.date()
            )
            return False

        avg_price = _average(list(price_by_start.values()))

        total_savings = 0.0
        total_revenue = 0.0
        total_battery = 0.0
        total_grid_kwh = 0.0
        total_grid_cost = 0.0
        total_consumption = 0.0
        total_export = 0.0
        total_battery_discharge = 0.0
        matched_hours = 0
        fallback_hours = 0

        # Eigenverbrauch-Ersparnis
        for row in stats.get(consumption_id, []):
            change = row.get("change") or 0.0
            if change <= 0:
                continue
            ts = row.get("start")
            price = price_by_start.get(ts)
            if price is None:
                price = avg_price  # Durchschnitt als Fallback für fehlende Stunden
                fallback_hours += 1
            else:
                matched_hours += 1
            total_savings += change * price
            total_consumption += change

        # Einspeise-Ertrag
        if export_id:
            for row in stats.get(export_id, []):
                change = row.get("change") or 0.0
                if change <= 0:
                    continue
                total_export += change
                total_revenue += change * reward_per_unit

        # Batterie-Ersparnis
        if battery_id:
            for row in stats.get(battery_id, []):
                change = row.get("change") or 0.0
                if change <= 0:
                    continue
                ts = row.get("start")
                price = price_by_start.get(ts, avg_price)
                total_battery += change * price
                total_battery_discharge += change

        # Netzbezug (nur Anzeige)
        if grid_import_id:
            for row in stats.get(grid_import_id, []):
                change = row.get("change") or 0.0
                if change <= 0:
                    continue
                ts = row.get("start")
                price = price_by_start.get(ts, avg_price)
                total_grid_kwh += change
                total_grid_cost += change * price

        # Akkumulierten Zustand setzen
        self._state.first_update = start.isoformat()
        self._state.savings = round(total_savings, 4)
        self._state.revenue = round(total_revenue, 4)
        self._state.battery_savings = round(total_battery, 4)
        self._state.total_consumption = round(total_consumption, 4)
        self._state.total_export = round(total_export, 4)
        self._state.total_battery_discharge = round(total_battery_discharge, 4)
        self._state.grid_import_kwh = round(total_grid_kwh, 4)
        self._state.grid_import_cost = round(total_grid_cost, 4)

        # last_* auf aktuelle Sensorwerte setzen (Delta-Basis für nächste Updates)
        for conf_key, attr in [
            (CONF_CONSUMPTION_SENSOR, "last_consumption"),
            (CONF_EXPORT_SENSOR, "last_export"),
            (CONF_BATTERY_DISCHARGE_SENSOR, "last_battery_discharge"),
            (CONF_GRID_IMPORT_SENSOR, "last_grid_import"),
        ]:
            val = self._read_number(cfg.get(conf_key))
            if val is not None:
                setattr(self._state, attr, val)

        _LOGGER.info(
            "ROI rückwirkend berechnet: %d Stunden ab %s | "
            "Ersparnis=%.2f€, Ertrag=%.2f€ (Ø Preis=%.4f€/kWh, %d Stunden ohne Preismatch)",
            matched_hours + fallback_hours,
            start.date(),
            total_savings,
            total_revenue,
            avg_price or 0,
            fallback_hours,
        )
        return True

    async def async_seed_from_history(self) -> bool:
        """Setzt die Basislinie auf die Zählerstände zum Startdatum (einfache Methode).

        Wird als Fallback verwendet wenn keine Preis-Statistiken verfügbar sind
        oder kein dynamischer Preis-Sensor konfiguriert ist.
        """
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
                "Startdatum gesetzt, aber keine Historie gefunden. "
                "Berechnung startet ab jetzt."
            )
        return seeded

    async def async_recalculate_from(self, start_date: str | None = None) -> None:
        """Setzt den Rechner zurück und berechnet rückwirkend neu.

        Bei dynamischem Preis-Sensor: stündliche Statistiken.
        Sonst: einfache Baseline-Methode.
        """
        self._state = RoiState()
        await self._store.async_remove()
        if start_date:
            self._override_start_date = start_date

        cfg = self.config
        price_mode = cfg.get(CONF_PRICE_MODE, PRICE_MODE_FIXED)
        seeded = False

        if price_mode == PRICE_MODE_SENSOR:
            seeded = await self.async_seed_from_statistics()

        if not seeded:
            await self.async_seed_from_history()

        await self._async_save_state()
        await self.async_request_refresh()

    # ── Persistenz ────────────────────────────────────────────────────────────

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

    # ── Daten aktualisieren ───────────────────────────────────────────────────

    async def _async_update_data(self) -> RoiResult:
        cfg = self.config
        investment = float(cfg.get(CONF_INVESTMENT, 0) or 0)

        consumption = self._read_number(cfg.get(CONF_CONSUMPTION_SENSOR))
        export = self._read_number(cfg.get(CONF_EXPORT_SENSOR))
        battery_discharge = self._read_number(cfg.get(CONF_BATTERY_DISCHARGE_SENSOR))
        production = self._read_number(cfg.get(CONF_PRODUCTION_SENSOR))
        grid_import = self._read_number(cfg.get(CONF_GRID_IMPORT_SENSOR))

        raw_base = cfg.get(CONF_BASELINE_RATE)
        baseline_rate = float(raw_base) if raw_base not in (None, "") else None

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
