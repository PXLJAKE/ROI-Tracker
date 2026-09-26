"""Tests für die reine ROI-Berechnung (ohne Home Assistant).

Ausführen:  python -m pytest tests/  – oder direkt:  python tests/test_calculator.py
"""

from __future__ import annotations

import os
import sys
from datetime import date, datetime, timedelta, timezone

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "custom_components", "roi_tracker")
)

import calculator  # noqa: E402
from calculator import Amounts  # noqa: E402

UTC = timezone.utc
H0 = datetime(2026, 5, 1, 10, 0, tzinfo=UTC)
HOUSE = dict(plus=["house"], minus=["import"], export_id="export")
PV = dict(plus=["pv", "dis"], minus=["export", "chg"], export_id="export")


def _day(total_savings: float, revenue: float = 0.0) -> dict:
    return Amounts(savings=total_savings, revenue=revenue).to_store()


# ── Stundenrechnung ──────────────────────────────────────────────────────────


def test_house_mode_savings_is_consumption_minus_import() -> None:
    a = calculator.hour_amounts(
        {"house": 3.0, "import": 1.0, "export": 0.5}, **HOUSE, price=0.30, feed_in=0.08
    )
    assert round(a.self_kwh, 6) == 2.0
    assert round(a.savings, 6) == 0.60
    assert round(a.revenue, 6) == 0.04


def test_grid_charging_hour_is_negative_and_later_repaid() -> None:
    # Nachts billig: Haus 0,5 kWh, Netzbezug 3 kWh (2,5 kWh in die Batterie)
    night = calculator.hour_amounts({"house": 0.5, "import": 3.0}, **HOUSE, price=0.10, feed_in=0)
    # Abends teuer: Haus 2,5 kWh komplett aus Batterie
    evening = calculator.hour_amounts({"house": 2.5, "import": 0.0}, **HOUSE, price=0.40, feed_in=0)
    assert round(night.savings, 6) == -0.25
    # Netto: 2,5 kWh zu 0,40 statt 0,10 → 0,75 € Arbitrage-Gewinn
    assert round(night.savings + evening.savings, 6) == 0.75


def test_pv_mode_with_battery() -> None:
    a = calculator.hour_amounts(
        {"pv": 5.0, "export": 1.0, "chg": 2.0, "dis": 0.5}, **PV, price=0.30, feed_in=0.08
    )
    # 5 − 1 + 0,5 − 2 = 2,5 kWh selbst genutzt
    assert round(a.self_kwh, 6) == 2.5
    assert round(a.savings, 6) == 0.75
    assert round(a.revenue, 6) == 0.08


def test_missing_price_gives_no_savings_but_keeps_kwh() -> None:
    a = calculator.hour_amounts({"house": 2.0}, **HOUSE, price=None, feed_in=0)
    assert a.self_kwh == 2.0 and a.savings == 0.0


# ── Preise ────────────────────────────────────────────────────────────────────


def test_price_units() -> None:
    assert calculator.price_factor("EUR/kWh") == 1.0
    assert calculator.price_factor("€/kWh") == 1.0
    assert calculator.price_factor("ct/kWh") == 0.01
    assert calculator.price_factor("Cent/kWh") == 0.01
    assert calculator.price_factor("EUR/MWh") == 0.001
    assert calculator.price_factor(None) == 1.0


def test_fill_prices_forward_backward_and_fallback() -> None:
    hours = [H0 + timedelta(hours=i) for i in range(4)]
    known = {hours[1]: 0.30, hours[3]: 0.50}
    filled = calculator.fill_prices(hours, known)
    # Lücke am Anfang → erster bekannter, Lücke in der Mitte → letzter bekannter
    assert [filled[h] for h in hours] == [0.30, 0.30, 0.30, 0.50]
    # Vorheriger Preis aus älterem Abschnitt hat Vorrang vor Rückwärtsfüllen
    assert calculator.fill_prices(hours, known, previous=0.20)[hours[0]] == 0.20
    # Gar keine Preisdaten → Festpreis
    assert calculator.fill_prices(hours, {}, fallback=0.32)[hours[2]] == 0.32
    assert calculator.fill_prices(hours, {})[hours[2]] is None


def test_time_weighted_hourly_price() -> None:
    points = [
        (H0 - timedelta(minutes=30), 0.20),  # gilt ab Stundenbeginn
        (H0 + timedelta(minutes=15), 0.40),
        (H0 + timedelta(minutes=45), None),  # unavailable → zählt nicht
        (H0 + timedelta(hours=1), 0.30),
    ]
    res = calculator.time_weighted_hourly(points, H0, H0 + timedelta(hours=2))
    # 15 min × 0,20 + 30 min × 0,40 über 45 min = 0,3333
    assert round(res[H0], 4) == 0.3333
    assert res[H0 + timedelta(hours=1)] == 0.30


# ── Aggregation ───────────────────────────────────────────────────────────────


def test_days_months_years_aggregation() -> None:
    days: dict = {}
    calculator.add_to_day(days, "2026-01-31", Amounts(self_kwh=2, savings=0.6))
    calculator.add_to_day(days, "2026-01-31", Amounts(self_kwh=1, savings=0.3))
    calculator.add_to_day(days, "2026-02-01", Amounts(export_kwh=10, revenue=0.8))
    months = calculator.aggregate(days, 7)
    assert list(months) == ["2026-01", "2026-02"]
    assert round(months["2026-01"].savings, 6) == 0.9
    assert round(months["2026-02"].revenue, 6) == 0.8
    years = calculator.aggregate(days, 4, live=Amounts(savings=1.0), live_day="2026-02-01")
    assert round(years["2026"].total, 6) == 2.7
    row = calculator.period_list(months)[0]
    assert row["period"] == "2026-01" and row["avg_price"] == 0.3


# ── Kennzahlen ────────────────────────────────────────────────────────────────


def test_roi_and_amortization() -> None:
    days = {"2026-05-01": _day(100.0, 50.0)}
    r = calculator.compute(days, investment=1000, today=date(2026, 5, 2))
    assert r["total_return"] == 150.0
    assert r["amortization"] == 15.0
    assert r["roi"] == -85.0
    assert r["remaining"] == 850.0
    assert r["breakeven_reached"] is False


def test_provisional_projection_uses_daily_average() -> None:
    # 10 volle Tage à 2 €, heute (unvollständig) 0,50 € → Ø 2 €/Tag
    start = date(2026, 5, 1)
    days = {(start + timedelta(days=i)).isoformat(): _day(2.0) for i in range(10)}
    today = start + timedelta(days=10)
    days[today.isoformat()] = _day(0.5)
    r = calculator.compute(days, investment=1000, today=today)
    assert r["projection_provisional"] is True
    assert r["daily_average"] == 2.0
    assert r["yearly_estimate"] == 730.0
    # Rest 1000 − 20,5 = 979,5 € / 2 € pro Tag = 489,75 → 490 Tage
    assert r["breakeven_date"] == (today + timedelta(days=490)).isoformat()


def test_projection_after_a_year_uses_last_365_days() -> None:
    # Sommer ertragreich, Winter schwach – Ø seit Start wäre verzerrt,
    # die tatsächliche Summe der letzten 365 Tage nicht.
    start = date(2025, 1, 1)
    days = {}
    for i in range(500):
        d = start + timedelta(days=i)
        days[d.isoformat()] = _day(5.0 if d.month in (5, 6, 7, 8) else 1.0)
    today = start + timedelta(days=500)
    r = calculator.compute(days, investment=10000, today=today)
    lo = today - timedelta(days=365)
    expected = sum(
        5.0 if (lo + timedelta(days=i)).month in (5, 6, 7, 8) else 1.0 for i in range(365)
    )
    assert r["projection_provisional"] is False
    assert r["yearly_estimate"] == round(expected, 2)


def test_breakeven_date_when_paid_off() -> None:
    days = {"2026-05-01": _day(60.0), "2026-05-02": _day(60.0), "2026-05-03": _day(60.0)}
    r = calculator.compute(days, investment=100, today=date(2026, 5, 4))
    assert r["breakeven_reached"] is True
    assert r["breakeven_date"] == "2026-05-02"
    assert r["remaining"] == 0.0
    assert r["roi"] == 80.0


def test_live_amount_counts_into_today_and_month() -> None:
    days = {"2026-05-10": _day(1.0)}
    r = calculator.compute(
        days, investment=100, today=date(2026, 5, 10), live=Amounts(self_kwh=1, savings=0.5)
    )
    assert r["today"]["total"] == 1.5
    assert r["month"]["total"] == 1.5
    assert r["total_return"] == 1.5


def test_no_data() -> None:
    r = calculator.compute({}, investment=5000, today=date(2026, 5, 1))
    assert r["total_return"] == 0.0
    assert r["breakeven_date"] is None
    assert r["data_since"] is None
    assert r["avg_price"] is None


def test_store_roundtrip() -> None:
    a = Amounts(self_kwh=1.234567, export_kwh=2, savings=0.5, revenue=0.1)
    b = Amounts.from_dict(a.to_store())
    assert round(b.self_kwh, 5) == 1.23457 and b.revenue == 0.1


def _run_all() -> None:
    fns = [v for k, v in globals().items() if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"PASS  {fn.__name__}")
    print(f"\n{len(fns)} Tests bestanden.")


if __name__ == "__main__":
    _run_all()
