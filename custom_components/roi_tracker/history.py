"""Liest historische Sensor-Zählerstände aus dem Recorder.

Wird genutzt, um die ROI-Berechnung rückwirkend ab einem gewählten Startdatum
zu starten: Der Zählerstand eines Sensors zu diesem Datum dient als Basislinie.

Primär werden die Langzeit-Statistiken genutzt (bleiben für Sensoren mit
state_class praktisch unbegrenzt erhalten). Fällt das aus, gibt es einen
Fallback auf die rohe Zustands-Historie (nur für jüngere Daten verfügbar, da
diese nach der Recorder-Aufbewahrungszeit gelöscht wird).

Alles defensiv: Bei jedem Problem wird ``None`` zurückgegeben, sodass die
Berechnung einfach „ab jetzt" startet, statt das Setup zu blockieren.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


async def async_get_sensor_value_at(
    hass: HomeAssistant, entity_id: str | None, when: datetime
) -> float | None:
    """Ermittelt den numerischen Wert von ``entity_id`` zum Zeitpunkt ``when``.

    Gibt ``None`` zurück, wenn kein Wert gefunden wird oder der Recorder fehlt.
    """
    if not entity_id:
        return None

    value = await _async_from_statistics(hass, entity_id, when)
    if value is not None:
        return value
    return await _async_from_history(hass, entity_id, when)


async def _async_from_statistics(
    hass: HomeAssistant, entity_id: str, when: datetime
) -> float | None:
    try:
        from homeassistant.components.recorder import get_instance
        from homeassistant.components.recorder.statistics import (
            statistics_during_period,
        )
    except ImportError:
        return None

    end = when + timedelta(days=3)

    def _run() -> float | None:
        stats = statistics_during_period(
            hass, when, end, {entity_id}, "hour", None, {"state"}
        )
        rows = stats.get(entity_id)
        if not rows:
            return None
        # Erste Stunde ab dem Startdatum: deren Mess-State ist der Zählerstand.
        state = rows[0].get("state")
        try:
            return float(state) if state is not None else None
        except (ValueError, TypeError):
            return None

    try:
        return await get_instance(hass).async_add_executor_job(_run)
    except Exception as err:  # noqa: BLE001 - defensiv
        _LOGGER.debug("Statistik-Abfrage für %s fehlgeschlagen: %s", entity_id, err)
        return None


async def _async_from_history(
    hass: HomeAssistant, entity_id: str, when: datetime
) -> float | None:
    try:
        from homeassistant.components.recorder import get_instance
        from homeassistant.components.recorder.history import (
            state_changes_during_period,
        )
    except ImportError:
        return None

    end = when + timedelta(days=3)

    def _run() -> float | None:
        result = state_changes_during_period(
            hass,
            when,
            end,
            entity_id,
            include_start_time_state=True,
            no_attributes=True,
        )
        states = result.get(entity_id)
        if not states:
            return None
        for state in states:
            try:
                return float(state.state)
            except (ValueError, TypeError):
                continue
        return None

    try:
        return await get_instance(hass).async_add_executor_job(_run)
    except Exception as err:  # noqa: BLE001 - defensiv
        _LOGGER.debug("Historie-Abfrage für %s fehlgeschlagen: %s", entity_id, err)
        return None
