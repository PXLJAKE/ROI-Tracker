"""Reine ROI-Berechnung – ohne Home-Assistant-Abhängigkeiten, damit testbar.

Das Modul arbeitet inkrementell: Es bekommt aktuelle Zählerstände (kumulierte
kWh/km/...) und Preise und führt einen persistenten Zustand fort. So überstehen
die berechneten Werte einen Neustart, ohne dass von vorn gezählt wird.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta


@dataclass
class RoiState:
    """Persistenter Zustand eines ROI-Rechners."""

    # Zuletzt gesehene Zählerstände (zur Delta-Bildung)
    last_consumption: float | None = None
    last_export: float | None = None
    last_battery_discharge: float | None = None
    # Zuletzt gesehene "fertige" €-Zählerstände
    last_cost_total: float | None = None
    last_reward_total: float | None = None
    last_grid_import: float | None = None

    # Kumulierte Geldbeträge
    savings: float = 0.0  # gespart durch Eigenverbrauch (€)
    revenue: float = 0.0  # eingenommen durch Einspeisung/Abgabe (€)
    battery_savings: float = 0.0  # gespart durch Batterie-Entladung (€)

    # Kumulierte Mengen (für Autarkie/Statistik)
    total_consumption: float = 0.0
    total_export: float = 0.0
    total_battery_discharge: float = 0.0
    grid_import_kwh: float = 0.0   # aus dem Netz bezogene Energie (kWh)
    grid_import_cost: float = 0.0  # dafür bezahlter Betrag (€)

    first_update: str | None = None  # ISO-Zeitstempel der ersten Messung

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict | None) -> "RoiState":
        if not data:
            return cls()
        known = {f for f in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class RoiResult:
    """Ergebnis einer Berechnung – das, was die Sensoren anzeigen."""

    savings: float = 0.0
    revenue: float = 0.0
    battery_savings: float = 0.0
    total_return: float = 0.0
    remaining_investment: float = 0.0
    amortization_percent: float = 0.0
    roi_percent: float = 0.0
    breakeven_days: float | None = None
    self_sufficiency_percent: float | None = None
    daily_average: float = 0.0
    monthly_estimate: float = 0.0
    yearly_estimate: float = 0.0
    grid_import_kwh: float = 0.0
    grid_import_cost: float = 0.0
    # Kumulierte Mengen als eigene Felder → werden als permanente HA-Sensoren exponiert
    total_consumption_kwh: float = 0.0
    total_export_kwh: float = 0.0
    total_battery_discharge_kwh: float = 0.0
    attributes: dict = field(default_factory=dict)


def _delta(current: float | None, last: float | None) -> float:
    """Delta für kumulierte Dauerzähler (z.B. Gesamtertrag seit Installation).

    Sinkt der Wert (Sensor-Reset oder Zähleraustausch), wird 0 zurückgegeben,
    um falsches Negativ-Delta zu vermeiden.
    """
    if current is None:
        return 0.0
    if last is None:
        return 0.0
    if current < last:
        return 0.0
    return current - last


def _delta_reset(current: float | None, last: float | None) -> float:
    """Delta für Sensoren die täglich/monatlich zurücksetzen.

    Beim Erkennen eines Resets (current < last) wird ``current`` als Delta
    gezählt – die Energie seit dem letzten Reset. Beim allerersten Messwert
    (last=None) zählt der aktuelle Stand als heutiger Tageswert.
    """
    if current is None:
        return 0.0
    if last is None:
        return current  # Erster Wert: heutigen Teiltagswert direkt zählen
    if current < last:
        return current  # Reset erkannt: von 0 weiterzählen
    return current - last


def update(
    state: RoiState,
    *,
    investment: float,
    now: datetime,
    consumption: float | None = None,
    export: float | None = None,
    battery_discharge: float | None = None,
    grid_import: float | None = None,
    price_per_unit: float | None = None,
    reward_per_unit: float | None = None,
    cost_total: float | None = None,
    reward_total: float | None = None,
    baseline_rate: float | None = None,
    reset_daily: bool = False,
) -> RoiResult:
    """Aktualisiert ``state`` anhand neuer Messwerte und gibt das Ergebnis zurück.

    Eingaben (alle optional, je nach Vorlage/Konfiguration):
      consumption       – kumulierte selbst genutzte Menge (kWh/km/...)
      export            – kumulierte eingespeiste/abgegebene Menge
      battery_discharge – kumulierte aus der Batterie entnommene Menge (kWh)
      price_per_unit    – aktueller Bezugspreis €/Einheit (fester Wert ODER Sensor)
      reward_per_unit   – aktuelle Vergütung €/Einheit
      cost_total        – fertiger kumulierter €-Kostensensor (statt price*menge)
      reward_total      – fertiger kumulierter €-Ertragssensor (statt reward*menge)
      baseline_rate     – Kosten der Alt-Lösung €/Einheit (Vergleich, z. B. E-Auto)

    Batterie: Jede aus der Batterie entnommene kWh ersetzt eine kWh Netzbezug
    und wird daher mit dem Bezugspreis als zusätzliche Ersparnis gewertet. Die
    Ladung (battery_charge) verursacht keine direkten Kosten – sie stammt i. d. R.
    aus PV-Überschuss – und wird hier bewusst nicht als Ausgabe gerechnet.
    """
    if state.first_update is None:
        state.first_update = now.isoformat()

    # Wähle die passende Delta-Funktion je nach Sensor-Typ
    d = _delta_reset if reset_daily else _delta

    # --- Ersparnis durch Eigenverbrauch -------------------------------------
    if cost_total is not None:
        delta_cost = d(cost_total, state.last_cost_total)
        state.savings += delta_cost
        state.last_cost_total = cost_total
    elif consumption is not None:
        d_units = d(consumption, state.last_consumption)
        state.total_consumption += d_units
        rate = baseline_rate if baseline_rate is not None else price_per_unit
        if rate is not None:
            state.savings += d_units * rate
        state.last_consumption = consumption

    # --- Einnahmen durch Einspeisung/Abgabe ---------------------------------
    if reward_total is not None:
        delta_reward = d(reward_total, state.last_reward_total)
        state.revenue += delta_reward
        state.last_reward_total = reward_total
    elif export is not None:
        d_units = d(export, state.last_export)
        state.total_export += d_units
        if reward_per_unit is not None:
            state.revenue += d_units * reward_per_unit
        state.last_export = export

    # --- Netzbezug (optional, nur für Gesamtbilanz-Anzeige) -----------------
    # Wird NICHT vom total_return abgezogen – nur für transparente Anzeige.
    if grid_import is not None:
        d_grid = d(grid_import, state.last_grid_import)
        state.grid_import_kwh += d_grid
        if price_per_unit is not None:
            state.grid_import_cost += d_grid * price_per_unit
        state.last_grid_import = grid_import

    # --- Ersparnis durch Batterie-Entladung ---------------------------------
    if battery_discharge is not None and cost_total is None:
        d_units = d(battery_discharge, state.last_battery_discharge)
        state.total_battery_discharge += d_units
        rate = baseline_rate if baseline_rate is not None else price_per_unit
        if rate is not None:
            state.battery_savings += d_units * rate
        state.last_battery_discharge = battery_discharge

    # --- Kennzahlen ---------------------------------------------------------
    total_return = state.savings + state.battery_savings + state.revenue
    remaining = max(investment - total_return, 0.0)
    amortization = (total_return / investment * 100.0) if investment > 0 else 0.0
    roi_percent = (
        (total_return - investment) / investment * 100.0 if investment > 0 else 0.0
    )

    # Tagesdurchschnitt & Restlaufzeit
    daily_avg = 0.0
    breakeven_days: float | None = None
    breakeven_date: str | None = None
    if state.first_update:
        start = datetime.fromisoformat(state.first_update)
        elapsed_days = max((now - start).total_seconds() / 86400.0, 0.0)
        if elapsed_days > 0:
            daily_avg = total_return / elapsed_days
            if daily_avg > 0 and remaining > 0:
                breakeven_days = remaining / daily_avg
                breakeven_date = (
                    now + timedelta(days=breakeven_days)
                ).date().isoformat()
            elif remaining <= 0:
                breakeven_days = 0.0
                breakeven_date = now.date().isoformat()

    monthly_estimate = round(daily_avg * 30.44, 2)
    yearly_estimate = round(daily_avg * 365.0, 2)

    # Eigenverbrauchsquote (wie viel % der PV-Erzeugung selbst genutzt wird).
    # Batterie-Entladung zählt als selbst genutzte Energie.
    self_sufficiency: float | None = None
    self_used = state.total_consumption + state.total_battery_discharge
    denom = self_used + state.total_export
    if denom > 0:
        self_sufficiency = self_used / denom * 100.0

    grid_import_kwh = round(state.grid_import_kwh, 3)
    grid_import_cost = round(state.grid_import_cost, 2)
    total_consumption_kwh = round(state.total_consumption, 3)
    total_export_kwh = round(state.total_export, 3)
    total_battery_discharge_kwh = round(state.total_battery_discharge, 3)

    return RoiResult(
        savings=round(state.savings, 2),
        revenue=round(state.revenue, 2),
        battery_savings=round(state.battery_savings, 2),
        total_return=round(total_return, 2),
        remaining_investment=round(remaining, 2),
        amortization_percent=round(amortization, 1),
        roi_percent=round(roi_percent, 1),
        breakeven_days=round(breakeven_days, 1) if breakeven_days is not None else None,
        self_sufficiency_percent=(
            round(self_sufficiency, 1) if self_sufficiency is not None else None
        ),
        daily_average=round(daily_avg, 2),
        monthly_estimate=monthly_estimate,
        yearly_estimate=yearly_estimate,
        grid_import_kwh=grid_import_kwh,
        grid_import_cost=grid_import_cost,
        total_consumption_kwh=total_consumption_kwh,
        total_export_kwh=total_export_kwh,
        total_battery_discharge_kwh=total_battery_discharge_kwh,
        attributes={
            "investment": investment,
            "daily_average": round(daily_avg, 2),
            "monthly_estimate": monthly_estimate,
            "yearly_estimate": yearly_estimate,
            "breakeven_date": breakeven_date,
            "total_consumption": round(state.total_consumption, 3),
            "total_export": round(state.total_export, 3),
            "total_battery_discharge": round(state.total_battery_discharge, 3),
            "grid_import_kwh": grid_import_kwh,
            "grid_import_cost": grid_import_cost,
            "first_update": state.first_update,
        },
    )
