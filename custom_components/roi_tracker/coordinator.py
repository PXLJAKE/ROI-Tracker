"""DataUpdateCoordinator: rechnet stündlich aus der HA-Langzeitstatistik.

Ablauf je Update (alle 5 Minuten):
  1. Alle fertig kompilierten Stunden seit ``processed_until`` aus der
     stündlichen Statistik laden, mit dem Strompreis der jeweiligen Stunde
     bewerten, auf Tage aufsummieren und speichern.
  2. Die laufende, noch nicht kompilierte Zeit live aus der
     5-Minuten-Statistik schätzen (nur Anzeige, wird nicht gespeichert).
  3. Kennzahlen (ROI, Amortisation, Hochrechnung) aus den Tageswerten ableiten.

Ändert sich die Konfiguration (Startdatum, Sensoren, Preise), wird automatisch
komplett neu ab dem Startdatum gerechnet.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from datetime import date, datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from . import calculator
from .calculator import HOUR, Amounts, floor_hour
from .const import (
    CALC_KEYS,
    CONF_BATTERY_CHARGE_SENSOR,
    CONF_BATTERY_DISCHARGE_SENSOR,
    CONF_CONSUMPTION_SENSOR,
    CONF_EXPORT_SENSOR,
    CONF_FEED_IN_TARIFF,
    CONF_GRID_IMPORT_SENSOR,
    CONF_INVESTMENT,
    CONF_MODE,
    CONF_PRICE_FIXED,
    CONF_PRICE_SENSOR,
    CONF_PRODUCTION_SENSOR,
    CONF_START_DATE,
    DEFAULT_UPDATE_INTERVAL_MINUTES,
    DOMAIN,
    LEGACY_STORAGE_KEY,
    MODE_DIRECT,
    MODE_HOUSE,
    MODE_PV,
    STORAGE_KEY,
    STORAGE_VERSION,
)
from .history import async_get_state_points, async_get_statistics

_LOGGER = logging.getLogger(__name__)

# Stunden-Statistik wird von HA kurz nach Stundenende kompiliert.
COMPILE_DELAY = timedelta(minutes=15)
# Fehlen Zeilen, die älter als das sind, kommen sie nicht mehr.
GIVE_UP_AFTER = timedelta(hours=3)
CHUNK = timedelta(days=31)
# Zustands-Historie (für Preis-Sensoren ohne Statistik) reicht so weit zurück.
HISTORY_WINDOW = timedelta(days=14)
LIVE_MAX = timedelta(hours=4)


def _num(value) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class RoiTrackerCoordinator(DataUpdateCoordinator[dict]):
    """Rechnet eine Anlage aus der Recorder-Statistik."""

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
        self._lock = asyncio.Lock()
        self.days: dict[str, dict] = {}
        self.live: Amounts | None = None
        self._processed_until: datetime | None = None
        self._last_price: float | None = None
        self.missing_price_hours = 0

    # ── Konfiguration ─────────────────────────────────────────────────────────

    @property
    def config(self) -> dict:
        return {**self.entry.data, **self.entry.options}

    def _get(self, key: str) -> str | None:
        return self.config.get(key) or None

    @property
    def investment(self) -> float:
        return _num(self.config.get(CONF_INVESTMENT)) or 0.0

    @property
    def feed_in(self) -> float:
        return _num(self.config.get(CONF_FEED_IN_TARIFF)) or 0.0

    @property
    def fixed_price(self) -> float | None:
        return _num(self.config.get(CONF_PRICE_FIXED))

    @property
    def start_date(self) -> date:
        raw = self.config.get(CONF_START_DATE)
        parsed = dt_util.parse_date(str(raw)) if raw else None
        return parsed or dt_util.now().date()

    def _roles(self) -> tuple[list[str], list[str], str | None]:
        """(Plus-Sensoren, Minus-Sensoren, Einspeise-Sensor) für den Eigenverbrauch."""
        mode = self.config.get(CONF_MODE, MODE_HOUSE)
        g = self._get
        if mode == MODE_PV:
            plus = [g(CONF_PRODUCTION_SENSOR), g(CONF_BATTERY_DISCHARGE_SENSOR)]
            minus = [g(CONF_EXPORT_SENSOR), g(CONF_BATTERY_CHARGE_SENSOR)]
        elif mode == MODE_DIRECT:
            plus = [g(CONF_CONSUMPTION_SENSOR), g(CONF_BATTERY_DISCHARGE_SENSOR)]
            minus = []
        else:
            plus = [g(CONF_CONSUMPTION_SENSOR)]
            minus = [g(CONF_GRID_IMPORT_SENSOR)]
        return (
            [s for s in plus if s],
            [s for s in minus if s],
            g(CONF_EXPORT_SENSOR),
        )

    def _energy_ids(self) -> set[str]:
        plus, minus, export = self._roles()
        return {*plus, *minus, *([export] if export else [])}

    def _config_hash(self) -> str:
        cfg = self.config
        payload = json.dumps({k: cfg.get(k) for k in CALC_KEYS}, sort_keys=True, default=str)
        return hashlib.sha1(payload.encode()).hexdigest()

    # ── Persistenz ────────────────────────────────────────────────────────────

    async def async_load(self) -> None:
        """Gespeicherte Tageswerte laden; bei geänderter Konfiguration verwerfen."""
        stored = await self._store.async_load() or {}
        if stored.get("config_hash") == self._config_hash():
            self.days = stored.get("days") or {}
            raw_until = stored.get("processed_until")
            self._processed_until = dt_util.parse_datetime(raw_until) if raw_until else None
            self._last_price = _num(stored.get("last_price"))
            self.missing_price_hours = int(stored.get("missing_price_hours") or 0)
        else:
            if stored:
                _LOGGER.info("%s: Konfiguration geändert – rechne neu", self.entry.title)
            self._clear()
        # Zustand der alten Version (inkrementelle Deltas) wird nicht mehr gebraucht.
        await Store(
            self.hass, 1, LEGACY_STORAGE_KEY.format(entry_id=self.entry.entry_id)
        ).async_remove()

    def _clear(self) -> None:
        self.days = {}
        self._processed_until = None
        self._last_price = None
        self.missing_price_hours = 0

    async def _async_save(self) -> None:
        await self._store.async_save(
            {
                "config_hash": self._config_hash(),
                "processed_until": (
                    self._processed_until.isoformat() if self._processed_until else None
                ),
                "last_price": self._last_price,
                "missing_price_hours": self.missing_price_hours,
                "days": self.days,
            }
        )

    async def async_recalculate(self) -> None:
        """Alles verwerfen und ab Startdatum neu aus der Statistik rechnen."""
        async with self._lock:
            self._clear()
            await self._async_save()
        await self.async_refresh()

    # ── Preise ────────────────────────────────────────────────────────────────

    def _price_unit_factor(self) -> float:
        sensor = self._get(CONF_PRICE_SENSOR)
        state = self.hass.states.get(sensor) if sensor else None
        unit = state.attributes.get("unit_of_measurement") if state else None
        return calculator.price_factor(unit)

    def current_price(self) -> float | None:
        sensor = self._get(CONF_PRICE_SENSOR)
        if sensor:
            state = self.hass.states.get(sensor)
            value = _num(state.state) if state else None
            if value is not None:
                return value * self._price_unit_factor()
            return self._last_price if self._last_price is not None else self.fixed_price
        return self.fixed_price

    async def _async_hour_prices(
        self, hours: list[datetime], start: datetime, end: datetime
    ) -> dict[datetime, float | None]:
        sensor = self._get(CONF_PRICE_SENSOR)
        if not sensor:
            return {h: self.fixed_price for h in hours}

        factor = self._price_unit_factor()
        stats = await async_get_statistics(self.hass, start, end, {sensor}, "hour", "mean")
        known = {h: v * factor for h, v in stats.get(sensor, {}).items()}

        # Sensor ohne Langzeitstatistik: zeitgewichtet aus der Zustands-Historie
        missing = [h for h in hours if h not in known]
        if missing and end > dt_util.utcnow() - HISTORY_WINDOW:
            points = await async_get_state_points(self.hass, sensor, start, end)
            for h, v in calculator.time_weighted_hourly(points, start, end).items():
                known.setdefault(h, v * factor)

        self.missing_price_hours += sum(1 for h in hours if h not in known)
        prices = calculator.fill_prices(hours, known, self._last_price, self.fixed_price)
        last_known = [known[h] for h in sorted(known) if h < end]
        if last_known:
            self._last_price = last_known[-1]
        return prices

    # ── Stunden verarbeiten ──────────────────────────────────────────────────

    async def _async_process_hours(self) -> None:
        now = dt_util.utcnow()
        target = floor_hour(now - COMPILE_DELAY)
        cursor = self._processed_until or dt_util.as_utc(
            dt_util.start_of_local_day(self.start_date)
        )
        changed = False
        while cursor < target:
            chunk_end = min(cursor + CHUNK, target)
            done_until = await self._async_process_range(cursor, chunk_end, now)
            if done_until is None or done_until <= cursor:
                break
            cursor = done_until
            self._processed_until = cursor
            changed = True
        if changed:
            await self._async_save()

    async def _async_process_range(
        self, start: datetime, end: datetime, now: datetime
    ) -> datetime | None:
        """Verarbeitet [start, end). Gibt zurück, bis wohin sicher verarbeitet wurde."""
        plus, minus, export = self._roles()
        ids = self._energy_ids()
        if not ids:
            return None
        stats = await async_get_statistics(self.hass, start, end, ids, "hour", "change")

        row_hours = {h for series in stats.values() for h in series}
        if row_hours:
            last_row_end = max(row_hours) + HOUR
            # Noch nicht kompilierte Stunden am Ende: später erneut versuchen.
            done_until = end if end <= now - GIVE_UP_AFTER else min(last_row_end, end)
        else:
            # Keine Daten: bei alten Zeiträumen weiter, bei jungen noch warten.
            return end if end <= now - GIVE_UP_AFTER else None

        hours = sorted(h for h in row_hours if h < done_until)
        active = [
            h for h in hours if any(stats.get(s, {}).get(h, 0.0) for s in ids)
        ]
        prices = await self._async_hour_prices(active, start, done_until) if active else {}

        for hour in active:
            changes = {s: stats.get(s, {}).get(hour, 0.0) for s in ids}
            amounts = calculator.hour_amounts(
                changes,
                plus=plus,
                minus=minus,
                export_id=export,
                price=prices.get(hour),
                feed_in=self.feed_in,
            )
            day_key = dt_util.as_local(hour).date().isoformat()
            calculator.add_to_day(self.days, day_key, amounts)
        return done_until

    async def _async_live(self) -> Amounts | None:
        """Schätzt die noch nicht kompilierte Zeit aus der 5-Minuten-Statistik."""
        if self._processed_until is None:
            return None
        now = dt_util.utcnow()
        start = max(self._processed_until, now - LIVE_MAX)
        ids = self._energy_ids()
        stats = await async_get_statistics(self.hass, start, now, ids, "5minute", "change")
        changes = {s: sum(stats.get(s, {}).values()) for s in ids}
        plus, minus, export = self._roles()
        return calculator.hour_amounts(
            changes,
            plus=plus,
            minus=minus,
            export_id=export,
            price=self.current_price(),
            feed_in=self.feed_in,
        )

    # ── Update ────────────────────────────────────────────────────────────────

    async def _async_update_data(self) -> dict:
        async with self._lock:
            await self._async_process_hours()
            self.live = await self._async_live()
            return calculator.compute(
                self.days,
                investment=self.investment,
                today=dt_util.now().date(),
                live=self.live,
            )

    # ── Export für Karte / WebSocket ─────────────────────────────────────────

    def export(self, month: str | None = None) -> dict:
        today_key = dt_util.now().date().isoformat()
        month = month or today_key[:7]
        days = {
            k: v for k, v in self.days.items() if k.startswith(month)
        }
        live_in_month = self.live if today_key.startswith(month) else None
        return {
            "entry_id": self.entry.entry_id,
            "name": self.entry.title,
            "currency": self.hass.config.currency,
            "start_date": self.start_date.isoformat(),
            "price_source": "sensor" if self._get(CONF_PRICE_SENSOR) else "fixed",
            "current_price": self.current_price(),
            "feed_in_tariff": self.feed_in,
            "missing_price_hours": self.missing_price_hours,
            "kpis": self.data or {},
            "months": calculator.period_list(
                calculator.aggregate(self.days, 7, self.live, today_key)
            ),
            "years": calculator.period_list(
                calculator.aggregate(self.days, 4, self.live, today_key)
            ),
            "month": month,
            "days": calculator.period_list(
                calculator.aggregate(days, 10, live_in_month, today_key)
            ),
        }
