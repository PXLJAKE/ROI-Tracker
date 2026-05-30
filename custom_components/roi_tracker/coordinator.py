"""DataUpdateCoordinator: liest Quell-Sensoren, rechnet ROI, persistiert Zustand."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from . import calculator
from .calculator import RoiResult, RoiState
from .const import (
    CONF_BASELINE_RATE,
    CONF_CONSUMPTION_SENSOR,
    CONF_COST_SENSOR,
    CONF_EXPORT_SENSOR,
    CONF_INVESTMENT,
    CONF_PRICE_FIXED,
    CONF_PRICE_MODE,
    CONF_PRICE_SENSOR,
    CONF_REWARD_FIXED,
    CONF_REWARD_MODE,
    CONF_REWARD_SENSOR,
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

    @property
    def config(self) -> dict:
        """Effektive Konfiguration (Options haben Vorrang vor Daten)."""
        return {**self.entry.data, **self.entry.options}

    async def async_load_state(self) -> None:
        """Persistenten Zustand beim Setup laden."""
        stored = await self._store.async_load()
        self._state = RoiState.from_dict(stored)

    async def _async_save_state(self) -> None:
        await self._store.async_save(self._state.to_dict())

    def _read_number(self, entity_id: str | None) -> float | None:
        """Liest einen numerischen Sensorwert; None bei fehlend/unverfügbar."""
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
        baseline_rate = cfg.get(CONF_BASELINE_RATE)
        baseline_rate = float(baseline_rate) if baseline_rate not in (None, "") else None

        # Bezugspreis je nach Modus
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

        # Vergütung je nach Modus
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
            price_per_unit=price_per_unit,
            reward_per_unit=reward_per_unit,
            cost_total=cost_total,
            reward_total=reward_total,
            baseline_rate=baseline_rate,
        )

        await self._async_save_state()
        return result

    async def async_reset(self) -> None:
        """Setzt den Rechner auf null zurück (z. B. via Service/Button später)."""
        self._state = RoiState()
        await self._store.async_remove()
        await self.async_request_refresh()
