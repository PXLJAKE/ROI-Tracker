"""Tests für den Coordinator mit simulierter Recorder-Statistik (ohne HA).

Ausführen:  python -m pytest tests/
"""

from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(__file__))

import ha_stubs  # noqa: E402

coordinator_mod = ha_stubs.install()

UTC = timezone.utc
H = timedelta(hours=1)
# Startdatum 01.05. (lokal Berlin) = 30.04. 22:00 UTC
START_UTC = datetime(2026, 4, 30, 22, 0, tzinfo=UTC)
NOW = datetime(2026, 5, 3, 10, 20, tzinfo=UTC)

BASE_CFG = {
    "name": "PV",
    "investment": 1000,
    "start_date": "2026-05-01",
    "calc_mode": "house",
    "consumption_sensor": "sensor.house",
    "grid_import_sensor": "sensor.import",
    "export_sensor": "sensor.export",
    "production_sensor": None,
    "battery_charge_sensor": None,
    "battery_discharge_sensor": None,
    "price_sensor": "sensor.price",
    "price_fixed": None,
    "reward_fixed": 0.08,
}


class FakeRecorder:
    """Liefert Statistik wie ``history.async_get_statistics``."""

    def __init__(self) -> None:
        self.hourly: dict[str, dict[datetime, float]] = {}
        self.five: dict[str, dict[datetime, float]] = {}
        self.mean: dict[str, dict[datetime, float]] = {}
        self.points: dict[str, list] = {}

    def fill_hours(self, sensor: str, value: float, start: datetime, end: datetime) -> None:
        h = start
        while h < end:
            self.hourly.setdefault(sensor, {})[h] = value
            h += H

    def fill_mean(self, sensor: str, value: float, start: datetime, end: datetime) -> None:
        h = start
        while h < end:
            self.mean.setdefault(sensor, {})[h] = value
            h += H

    async def stats(self, hass, start, end, ids, period, stat_type):
        src = self.mean if stat_type == "mean" else (self.hourly if period == "hour" else self.five)
        out = {}
        for sid in ids:
            rows = {h: v for h, v in src.get(sid, {}).items() if start <= h < end}
            if rows:
                out[sid] = rows
        return out

    async def state_points(self, hass, entity_id, start, end):
        return list(self.points.get(entity_id, []))


def _setup(cfg=None, recorder=None, price_unit="EUR/kWh", price_state="0.30"):
    ha_stubs.Clock.now = NOW
    rec = recorder or FakeRecorder()
    coordinator_mod.async_get_statistics = rec.stats
    coordinator_mod.async_get_state_points = rec.state_points
    hass = ha_stubs.HomeAssistant()
    hass.states["sensor.price"] = ha_stubs.State(price_state, {"unit_of_measurement": price_unit})
    for s in ("sensor.house", "sensor.import", "sensor.export"):
        hass.states[s] = ha_stubs.State("0", {"state_class": "total_increasing"})
    entry = ha_stubs.ConfigEntry(dict(cfg or BASE_CFG))
    return hass, entry, rec


def _standard_recorder(until: datetime = datetime(2026, 5, 3, 10, 0, tzinfo=UTC)) -> FakeRecorder:
    rec = FakeRecorder()
    rec.fill_hours("sensor.house", 2.0, START_UTC, until)
    rec.fill_hours("sensor.import", 0.5, START_UTC, until)
    rec.fill_hours("sensor.export", 1.0, START_UTC, until)
    rec.fill_mean("sensor.price", 0.30, START_UTC, until)
    return rec


async def _run(hass, entry):
    c = coordinator_mod.RoiTrackerCoordinator(hass, entry)
    await c.async_load()
    await c.async_refresh()
    return c


def setup_function() -> None:
    ha_stubs.Store.DATA.clear()


# ── Tests ─────────────────────────────────────────────────────────────────────


def test_hourly_calculation_and_local_days() -> None:
    rec = _standard_recorder()
    # Laufende Stunde (noch nicht kompiliert): 3 × 0,2 kWh Hausverbrauch
    for m in (0, 5, 10):
        rec.five.setdefault("sensor.house", {})[datetime(2026, 5, 3, 10, m, tzinfo=UTC)] = 0.2
    hass, entry, _ = _setup(recorder=rec)
    c = asyncio.run(_run(hass, entry))
    d = c.data

    # 60 Stunden à (2 − 0,5) kWh × 0,30 € = 27,00 € + 3 × 0,2 kWh × 0,30 € live
    assert round(d["savings"], 2) == round(27.0 + 0.18, 2)
    # 60 Stunden à 1 kWh × 0,08 €
    assert d["revenue"] == 4.8
    assert d["total_return"] == round(27.18 + 4.8, 2)
    # Tage nach lokaler Zeit: 01.05. und 02.05. je 24 h, 03.05. 12 h (+ live)
    assert sorted(c.days) == ["2026-05-01", "2026-05-02", "2026-05-03"]
    assert round(c.days["2026-05-03"]["savings"], 4) == 5.4
    assert d["data_since"] == "2026-05-01"


def test_uncompiled_hours_are_picked_up_later_without_double_counting() -> None:
    rec = _standard_recorder(until=datetime(2026, 5, 3, 8, 0, tzinfo=UTC))
    hass, entry, _ = _setup(recorder=rec)
    c = asyncio.run(_run(hass, entry))
    assert round(c.data["savings"], 2) == round(58 * 0.45, 2)

    # Die Stunden 08:00 und 09:00 werden nachträglich kompiliert
    rec.fill_hours("sensor.house", 2.0, datetime(2026, 5, 3, 8, 0, tzinfo=UTC), datetime(2026, 5, 3, 10, 0, tzinfo=UTC))
    rec.fill_hours("sensor.import", 0.5, datetime(2026, 5, 3, 8, 0, tzinfo=UTC), datetime(2026, 5, 3, 10, 0, tzinfo=UTC))
    ha_stubs.Clock.now = NOW + timedelta(minutes=20)
    asyncio.run(c.async_refresh())
    assert round(c.data["savings"], 2) == 27.0
    asyncio.run(c.async_refresh())  # erneutes Update ändert nichts
    assert round(c.data["savings"], 2) == 27.0


def test_restart_keeps_values_and_config_change_recalculates() -> None:
    hass, entry, rec = _setup(recorder=_standard_recorder())
    first = asyncio.run(_run(hass, entry))
    assert first.data["total_return"] == 31.8

    # Neustart mit gleicher Konfiguration: gespeicherte Tage, keine Doppelzählung
    again = asyncio.run(_run(hass, entry))
    assert again.data["total_return"] == 31.8

    # Einspeisevergütung geändert → komplette Neuberechnung
    entry.options = {"reward_fixed": 0.10}
    changed = asyncio.run(_run(hass, entry))
    assert changed.data["revenue"] == 6.0
    assert changed.data["savings"] == 27.0

    # Investition ändert nur ROI, nicht die Tageswerte
    entry.options = {"reward_fixed": 0.10, "investment": 30}
    roi = asyncio.run(_run(hass, entry))
    assert roi.data["total_return"] == 33.0
    assert roi.data["breakeven_reached"] is True
    assert roi.data["remaining"] == 0.0
    assert roi.data["roi"] == 10.0


def test_price_sensor_without_statistics_uses_history_and_unit() -> None:
    rec = _standard_recorder()
    rec.mean.clear()
    # Preis-Sensor in ct/kWh, nur als Zustands-Historie vorhanden
    rec.points["sensor.price"] = [(START_UTC - H, 30.0)]
    hass, entry, _ = _setup(recorder=rec, price_unit="ct/kWh", price_state="30")
    c = asyncio.run(_run(hass, entry))
    assert c.data["savings"] == 27.0
    assert c.missing_price_hours == 0


def test_missing_price_falls_back_to_fixed_price() -> None:
    rec = _standard_recorder()
    rec.mean.clear()
    cfg = {**BASE_CFG, "price_fixed": 0.20}
    hass, entry, _ = _setup(cfg=cfg, recorder=rec)
    c = asyncio.run(_run(hass, entry))
    assert c.data["savings"] == round(60 * 1.5 * 0.20, 2)
    assert c.missing_price_hours == 60


def test_pv_mode_with_battery_and_fixed_price() -> None:
    rec = FakeRecorder()
    end = datetime(2026, 5, 3, 10, 0, tzinfo=UTC)
    rec.fill_hours("sensor.pv", 3.0, START_UTC, end)
    rec.fill_hours("sensor.export", 1.0, START_UTC, end)
    rec.fill_hours("sensor.chg", 1.0, START_UTC, end)
    rec.fill_hours("sensor.dis", 0.5, START_UTC, end)
    cfg = {
        **BASE_CFG,
        "calc_mode": "pv",
        "production_sensor": "sensor.pv",
        "battery_charge_sensor": "sensor.chg",
        "battery_discharge_sensor": "sensor.dis",
        "price_sensor": None,
        "price_fixed": 0.30,
    }
    hass, entry, _ = _setup(cfg=cfg, recorder=rec)
    c = asyncio.run(_run(hass, entry))
    # (3 − 1 + 0,5 − 1) = 1,5 kWh/h × 60 h × 0,30 €
    assert c.data["self_kwh"] == 90.0
    assert c.data["savings"] == 27.0


def test_start_date_before_available_data() -> None:
    cfg = {**BASE_CFG, "start_date": "2026-01-01"}
    hass, entry, _ = _setup(cfg=cfg, recorder=_standard_recorder())
    c = asyncio.run(_run(hass, entry))
    assert c.data["total_return"] == 31.8
    assert c.data["data_since"] == "2026-05-01"


def test_export_for_card() -> None:
    hass, entry, _ = _setup(recorder=_standard_recorder())
    c = asyncio.run(_run(hass, entry))
    out = c.export()
    assert out["currency"] == "EUR"
    assert [m["period"] for m in out["months"]] == ["2026-05"]
    assert out["months"][0]["total"] == 31.8
    assert [y["period"] for y in out["years"]] == ["2026"]
    assert [d["period"] for d in out["days"]] == ["2026-05-01", "2026-05-02", "2026-05-03"]
    assert out["days"][0]["avg_price"] == 0.3
    assert c.export("2026-04")["days"] == []
