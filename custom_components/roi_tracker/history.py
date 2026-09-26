"""Zugriff auf den HA-Recorder: Langzeitstatistik und Zustands-Historie.

Alles defensiv: Bei Problemen wird ein leeres Ergebnis geliefert, damit die
Integration nicht abstürzt, sondern beim nächsten Update erneut versucht.
"""

from __future__ import annotations

import logging
from datetime import datetime

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)


def _row_start(value) -> datetime | None:
    """Statistik-Zeilen liefern ``start`` je nach HA-Version als Timestamp oder datetime."""
    if isinstance(value, (int, float)):
        return dt_util.utc_from_timestamp(value)
    if isinstance(value, datetime):
        return dt_util.as_utc(value)
    return None


async def async_get_statistics(
    hass: HomeAssistant,
    start: datetime,
    end: datetime,
    statistic_ids: set[str],
    period: str,
    stat_type: str,
) -> dict[str, dict[datetime, float]]:
    """Liefert {statistic_id: {Periodenbeginn (UTC): Wert}} für ``change`` oder ``mean``."""
    if not statistic_ids or start >= end:
        return {}
    try:
        from homeassistant.components.recorder import get_instance
        from homeassistant.components.recorder.statistics import (
            statistics_during_period,
        )

        raw = await get_instance(hass).async_add_executor_job(
            statistics_during_period,
            hass,
            start,
            end,
            statistic_ids,
            period,
            None,
            {stat_type},
        )
    except Exception as err:  # noqa: BLE001 - defensiv
        _LOGGER.warning("Statistik konnte nicht gelesen werden: %s", err)
        return {}

    out: dict[str, dict[datetime, float]] = {}
    for stat_id, rows in raw.items():
        series: dict[datetime, float] = {}
        for row in rows:
            ts = _row_start(row.get("start"))
            value = row.get(stat_type)
            if ts is not None and value is not None:
                series[ts] = float(value)
        out[stat_id] = series
    return out


async def async_get_state_points(
    hass: HomeAssistant, entity_id: str, start: datetime, end: datetime
) -> list[tuple[datetime, float | None]]:
    """Zustandsänderungen eines Sensors als (Zeitpunkt, Zahl oder None).

    Enthält den Zustand zum Startzeitpunkt. Nur für die letzten Tage verfügbar
    (Recorder-Aufbewahrung, Standard 10 Tage).
    """
    try:
        from homeassistant.components.recorder import get_instance
        from homeassistant.components.recorder.history import (
            state_changes_during_period,
        )

        def _run():
            return state_changes_during_period(
                hass,
                start,
                end,
                entity_id,
                no_attributes=True,
                include_start_time_state=True,
            )

        result = await get_instance(hass).async_add_executor_job(_run)
    except Exception as err:  # noqa: BLE001 - defensiv
        _LOGGER.debug("Historie für %s nicht lesbar: %s", entity_id, err)
        return []

    points: list[tuple[datetime, float | None]] = []
    for state in result.get(entity_id, []):
        try:
            value: float | None = float(state.state)
        except (ValueError, TypeError):
            value = None
        points.append((max(dt_util.as_utc(state.last_changed), start), value))
    return points
