"""Tests für die reine ROI-Berechnung (ohne Home Assistant).

Ausführen:  python3 -m pytest tests/  – oder direkt:  python3 tests/test_calculator.py
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "custom_components", "roi_tracker")
)

import calculator  # noqa: E402
from calculator import RoiState  # noqa: E402

START = datetime(2026, 1, 1, 12, 0, 0)


def test_first_reading_sets_baseline() -> None:
    st = RoiState()
    r = calculator.update(
        st, investment=10000, now=START, consumption=10, price_per_unit=0.30
    )
    # Erste Messung etabliert die Basislinie -> noch keine Ersparnis.
    assert r.savings == 0.0


def test_savings_from_self_consumption() -> None:
    st = RoiState()
    calculator.update(st, investment=10000, now=START, consumption=10, price_per_unit=0.30)
    r = calculator.update(
        st,
        investment=10000,
        now=START + timedelta(days=30),
        consumption=300,
        price_per_unit=0.30,
    )
    # 290 kWh * 0,30 € = 87,00 €
    assert r.savings == 87.0


def test_revenue_from_export() -> None:
    st = RoiState()
    calculator.update(st, investment=10000, now=START, export=5, reward_per_unit=0.08)
    r = calculator.update(
        st, investment=10000, now=START, export=155, reward_per_unit=0.08
    )
    # 150 kWh * 0,08 € = 12,00 €
    assert r.revenue == 12.0


def test_counter_reset_is_not_negative() -> None:
    st = RoiState()
    calculator.update(st, investment=100, now=START, consumption=100, price_per_unit=0.30)
    before = st.savings
    # Quellsensor springt zurück (Tagesreset) -> kein negatives Delta.
    r = calculator.update(
        st, investment=100, now=START, consumption=2, price_per_unit=0.30
    )
    assert r.savings == round(before, 2)


def test_cost_sensor_delta_is_savings() -> None:
    st = RoiState()
    calculator.update(st, investment=1000, now=START, cost_total=12.50)
    r = calculator.update(st, investment=1000, now=START, cost_total=20.00)
    assert r.savings == 7.5  # 20,00 - 12,50


def test_amortization_and_roi() -> None:
    st = RoiState()
    calculator.update(st, investment=100, now=START, consumption=0, price_per_unit=1.0)
    r = calculator.update(
        st, investment=100, now=START, consumption=150, price_per_unit=1.0
    )
    # 150 € Rückfluss bei 100 € Investition
    assert r.amortization_percent == 150.0
    assert r.roi_percent == 50.0
    assert r.remaining_investment == 0.0


def test_persistence_roundtrip() -> None:
    st = RoiState()
    calculator.update(st, investment=1000, now=START, consumption=10, price_per_unit=0.5)
    calculator.update(
        st, investment=1000, now=START, consumption=110, price_per_unit=0.5
    )
    restored = RoiState.from_dict(st.to_dict())
    assert restored.savings == st.savings
    assert restored.last_consumption == st.last_consumption


def test_self_sufficiency() -> None:
    st = RoiState()
    calculator.update(st, investment=1, now=START, consumption=0, export=0)
    r = calculator.update(
        st, investment=1, now=START, consumption=75, export=25, price_per_unit=0.3
    )
    # 75 selbst / (75 + 25) = 75 %
    assert r.self_sufficiency_percent == 75.0


def test_battery_discharge_savings() -> None:
    st = RoiState()
    calculator.update(
        st, investment=10000, now=START, battery_discharge=0, price_per_unit=0.30
    )
    r = calculator.update(
        st,
        investment=10000,
        now=START,
        battery_discharge=50,
        price_per_unit=0.30,
    )
    # 50 kWh aus Batterie * 0,30 € = 15,00 € separate Batterie-Ersparnis
    assert r.battery_savings == 15.0
    # zählt in den Gesamtrückfluss mit hinein
    assert r.total_return == 15.0


def test_battery_not_double_counted_with_cost_sensor() -> None:
    st = RoiState()
    calculator.update(
        st, investment=1000, now=START, cost_total=0, battery_discharge=0,
        price_per_unit=0.30,
    )
    r = calculator.update(
        st, investment=1000, now=START, cost_total=10, battery_discharge=100,
        price_per_unit=0.30,
    )
    # Kosten-Sensor enthält Batterie bereits -> keine separate Batterie-Ersparnis
    assert r.battery_savings == 0.0
    assert r.savings == 10.0


def test_battery_counts_towards_self_sufficiency() -> None:
    st = RoiState()
    calculator.update(
        st, investment=1, now=START, consumption=0, export=0, battery_discharge=0
    )
    r = calculator.update(
        st,
        investment=1,
        now=START,
        consumption=50,
        battery_discharge=25,
        export=25,
        price_per_unit=0.3,
    )
    # (50 Verbrauch + 25 Batterie) / (75 + 25 Einspeisung) = 75 %
    assert r.self_sufficiency_percent == 75.0


def test_baseline_rate_for_ev() -> None:
    st = RoiState()
    calculator.update(st, investment=5000, now=START, consumption=0, baseline_rate=0.12)
    r = calculator.update(
        st,
        investment=5000,
        now=START,
        consumption=1000,
        price_per_unit=0.05,
        baseline_rate=0.12,
    )
    # baseline_rate hat Vorrang: 1000 * 0,12 = 120 €
    assert r.savings == 120.0


def _run_all() -> None:
    fns = [v for k, v in globals().items() if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"PASS  {fn.__name__}")
    print(f"\n{len(fns)} Tests bestanden.")


if __name__ == "__main__":
    _run_all()
