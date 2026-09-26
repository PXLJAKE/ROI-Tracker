"""Reine ROI-Berechnung – ohne Home-Assistant-Abhängigkeiten, damit testbar.

Grundidee: Die HA-Langzeitstatistik liefert pro Stunde, wie viele kWh jeder
Zähler gezählt hat (``change``). Resets, Ausfälle und Neustarts sind darin
bereits korrekt behandelt. Pro Stunde gilt:

    Eigenverbrauch = Σ Plus-Sensoren − Σ Minus-Sensoren   (je nach Modus)
    Ersparnis      = Eigenverbrauch × Strompreis dieser Stunde
    Vergütung      = Einspeisung × Einspeisevergütung

Die Stundenwerte werden zu Tagen aufsummiert und persistiert. Monate, Jahre,
ROI und Hochrechnung werden daraus abgeleitet.
"""

from __future__ import annotations

import calendar
import math
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime, timedelta

HOUR = timedelta(hours=1)
DAY_FIELDS = ("self_kwh", "export_kwh", "savings", "revenue")


@dataclass
class Amounts:
    """Energie- und Geldbeträge eines Zeitraums."""

    self_kwh: float = 0.0
    export_kwh: float = 0.0
    savings: float = 0.0
    revenue: float = 0.0

    @property
    def total(self) -> float:
        return self.savings + self.revenue

    def add(self, other: "Amounts | dict | None") -> None:
        if other is None:
            return
        if isinstance(other, dict):
            other = Amounts.from_dict(other)
        self.self_kwh += other.self_kwh
        self.export_kwh += other.export_kwh
        self.savings += other.savings
        self.revenue += other.revenue

    @classmethod
    def from_dict(cls, data: dict) -> "Amounts":
        return cls(**{f: float(data.get(f) or 0.0) for f in DAY_FIELDS})

    def to_store(self) -> dict:
        return {f: round(getattr(self, f), 5) for f in DAY_FIELDS}

    def to_dict(self) -> dict:
        """Gerundete Ausgabe inkl. Summe und Ø-Preis (für Sensoren/Karte)."""
        return {
            "self_kwh": round(self.self_kwh, 2),
            "export_kwh": round(self.export_kwh, 2),
            "savings": round(self.savings, 2),
            "revenue": round(self.revenue, 2),
            "total": round(self.total, 2),
            "avg_price": (
                round(self.savings / self.self_kwh, 4) if self.self_kwh > 0 else None
            ),
        }


# ── Preise ────────────────────────────────────────────────────────────────────


def price_factor(unit: str | None) -> float:
    """Umrechnungsfaktor der Preis-Einheit nach €/kWh (ct/kWh, €/MWh, ...)."""
    u = (unit or "").lower().replace(" ", "")
    if "mwh" in u:
        return 0.001
    if u.startswith(("ct", "cent", "c/")) or "ct/" in u or "cent" in u:
        return 0.01
    return 1.0


def floor_hour(ts: datetime) -> datetime:
    return ts.replace(minute=0, second=0, microsecond=0)


def time_weighted_hourly(
    points: list[tuple[datetime, float | None]], start: datetime, end: datetime
) -> dict[datetime, float]:
    """Zeitgewichteter Stunden-Mittelwert aus Zustandsänderungen.

    ``points`` sind (Zeitpunkt, Wert) chronologisch; ein Wert gilt bis zum
    nächsten Punkt. ``None`` (unavailable) zählt als Lücke. Wird genutzt, wenn
    der Preis-Sensor keine Langzeitstatistik hat.
    """
    acc: dict[datetime, float] = {}
    weight: dict[datetime, float] = {}
    for i, (ts, value) in enumerate(points):
        seg_end = points[i + 1][0] if i + 1 < len(points) else end
        seg_start = max(ts, start)
        seg_end = min(seg_end, end)
        if value is None:
            continue
        while seg_start < seg_end:
            hour = floor_hour(seg_start)
            part_end = min(hour + HOUR, seg_end)
            secs = (part_end - seg_start).total_seconds()
            acc[hour] = acc.get(hour, 0.0) + value * secs
            weight[hour] = weight.get(hour, 0.0) + secs
            seg_start = part_end
    return {h: acc[h] / weight[h] for h in acc if weight[h] > 0}


def fill_prices(
    hours: Iterable[datetime],
    known: dict[datetime, float],
    previous: float | None = None,
    fallback: float | None = None,
) -> dict[datetime, float | None]:
    """Ordnet jeder Stunde einen Preis zu.

    Reihenfolge: bekannter Stundenpreis → zuletzt bekannter Preis (auch aus
    einem früheren Abschnitt, ``previous``) → erster bekannter Preis danach →
    ``fallback`` (Festpreis) → None.
    """
    ordered = sorted(hours)
    first_known = next((known[h] for h in ordered if h in known), None)
    last = previous
    out: dict[datetime, float | None] = {}
    for hour in ordered:
        if hour in known:
            last = known[hour]
            out[hour] = last
        elif last is not None:
            out[hour] = last
        elif first_known is not None:
            out[hour] = first_known
        else:
            out[hour] = fallback
    return out


# ── Stunden → Tage ────────────────────────────────────────────────────────────


def hour_amounts(
    changes: dict[str, float],
    *,
    plus: Iterable[str],
    minus: Iterable[str],
    export_id: str | None,
    price: float | None,
    feed_in: float,
) -> Amounts:
    """Berechnet Eigenverbrauch, Einspeisung und Geldwerte einer Stunde.

    Der Eigenverbrauch darf negativ sein (z. B. Batterie wird bei billigem
    dynamischem Preis aus dem Netz geladen) – das ist korrekt und wird beim
    späteren Entladen zum dann höheren Preis wieder gutgeschrieben.
    """
    self_kwh = sum(changes.get(s, 0.0) for s in plus) - sum(
        changes.get(s, 0.0) for s in minus
    )
    export_kwh = max(changes.get(export_id, 0.0), 0.0) if export_id else 0.0
    return Amounts(
        self_kwh=self_kwh,
        export_kwh=export_kwh,
        savings=self_kwh * price if price is not None else 0.0,
        revenue=export_kwh * feed_in,
    )


def add_to_day(days: dict[str, dict], day_key: str, amounts: Amounts) -> None:
    day = Amounts.from_dict(days.get(day_key, {}))
    day.add(amounts)
    days[day_key] = day.to_store()


def aggregate(
    days: dict[str, dict],
    key_len: int,
    live: Amounts | None = None,
    live_day: str | None = None,
) -> dict[str, Amounts]:
    """Fasst Tage zu Monaten (key_len=7) oder Jahren (key_len=4) zusammen."""
    out: dict[str, Amounts] = {}
    for day_key, values in days.items():
        out.setdefault(day_key[:key_len], Amounts()).add(values)
    if live is not None and live_day:
        out.setdefault(live_day[:key_len], Amounts()).add(live)
    return dict(sorted(out.items()))


def period_list(periods: dict[str, Amounts]) -> list[dict]:
    return [{"period": key, **value.to_dict()} for key, value in periods.items()]


# ── Kennzahlen & Hochrechnung ─────────────────────────────────────────────────


def _has_data(values: dict) -> bool:
    return any(abs(float(values.get(f) or 0.0)) > 1e-9 for f in DAY_FIELDS)


def compute(
    days: dict[str, dict],
    *,
    investment: float,
    today: date,
    live: Amounts | None = None,
) -> dict:
    """Berechnet alle Kennzahlen aus den Tageswerten (+ laufender Stunde)."""
    today_key = today.isoformat()
    totals = Amounts()
    for values in days.values():
        totals.add(values)
    totals.add(live)
    total_return = totals.total

    today_amounts = Amounts.from_dict(days.get(today_key, {}))
    today_amounts.add(live)

    remaining = max(investment - total_return, 0.0)
    amortization = total_return / investment * 100.0 if investment > 0 else 0.0
    roi = (total_return - investment) / investment * 100.0 if investment > 0 else 0.0

    # Datenbeginn = erster Tag mit Werten (nicht das konfigurierte Startdatum:
    # reicht die HA-Statistik nicht so weit zurück, wäre der Ø sonst zu niedrig).
    active = sorted(k for k, v in days.items() if _has_data(v))
    first_day = date.fromisoformat(active[0]) if active else today
    full_days = (today - first_day).days  # abgeschlossene Tage vor heute

    # Hochrechnung: Mit ≥ 365 Tagen Daten die tatsächliche Summe der letzten
    # 365 Tage (saisonal korrekt). Sonst Tagesdurchschnitt × 365 (vorläufig).
    if full_days >= 365:
        lo = (today - timedelta(days=365)).isoformat()
        yearly = sum(
            Amounts.from_dict(v).total for k, v in days.items() if lo <= k < today_key
        )
        provisional = False
    else:
        before_today = total_return - today_amounts.total
        daily = before_today / full_days if full_days > 0 else today_amounts.total
        yearly = daily * 365.0
        provisional = True
    daily_average = yearly / 365.0

    # Break-Even
    breakeven_date: date | None = None
    years_to_breakeven: float | None = None
    reached = investment > 0 and remaining <= 0
    if reached:
        cumulative = 0.0
        for key in sorted(days):
            cumulative += Amounts.from_dict(days[key]).total
            if cumulative >= investment:
                breakeven_date = date.fromisoformat(key)
                break
        if breakeven_date is None:
            breakeven_date = today
        years_to_breakeven = 0.0
    elif investment > 0 and daily_average > 0:
        days_left = remaining / daily_average
        years_to_breakeven = days_left / 365.0
        if days_left < 365 * 200:
            breakeven_date = today + timedelta(days=math.ceil(days_left))

    # Laufender Monat + Prognose für den Rest des Monats
    month = aggregate(days, 7, live, today_key).get(today_key[:7], Amounts())
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    month_forecast = month.total + daily_average * (days_in_month - today.day)

    return {
        "investment": round(investment, 2),
        **{k: v for k, v in totals.to_dict().items() if k != "total"},
        "total_return": round(total_return, 2),
        "remaining": round(remaining, 2),
        "amortization": round(amortization, 1),
        "roi": round(roi, 1),
        "daily_average": round(daily_average, 2),
        "yearly_estimate": round(yearly, 2),
        "projection_provisional": provisional,
        "breakeven_reached": reached,
        "breakeven_date": breakeven_date.isoformat() if breakeven_date else None,
        "years_to_breakeven": (
            round(years_to_breakeven, 2) if years_to_breakeven is not None else None
        ),
        "today": today_amounts.to_dict(),
        "month": month.to_dict(),
        "month_forecast": round(month_forecast, 2),
        "data_since": first_day.isoformat() if active else None,
    }
