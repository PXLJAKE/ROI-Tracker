"""Config- und Options-Flow für ROI Tracker.

Zwei Schritte:
  1. Grunddaten: Name, Investition, Startdatum, Berechnungsart, Preise
  2. Energie-Sensoren passend zur Berechnungsart
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector
from homeassistant.util import dt as dt_util

from .const import (
    CONF_BATTERY_CHARGE_SENSOR,
    CONF_BATTERY_DISCHARGE_SENSOR,
    CONF_FEED_IN_TARIFF,
    CONF_INVESTMENT,
    CONF_MODE,
    CONF_NAME,
    CONF_PRICE_FIXED,
    CONF_PRICE_SENSOR,
    CONF_PRODUCTION_SENSOR,
    CONF_START_DATE,
    DOMAIN,
    ENERGY_SENSOR_KEYS,
    MODE_HOUSE,
    MODE_SENSORS,
    MODES,
)

_ENERGY_SENSOR = selector.EntitySelector(
    selector.EntitySelectorConfig(domain="sensor", device_class="energy")
)
# Mehrere PV-Strings / Wechselrichter werden addiert.
_ENERGY_SENSOR_MULTI = selector.EntitySelector(
    selector.EntitySelectorConfig(domain="sensor", device_class="energy", multiple=True)
)
MULTI_KEYS = (CONF_PRODUCTION_SENSOR,)
# So weit reicht die Zustands-Historie des Recorders standardmäßig zurück.
HISTORY_DAYS = 10
_PRICE_SENSOR = selector.EntitySelector(
    selector.EntitySelectorConfig(domain=["sensor", "input_number"])
)
_PRICE = selector.NumberSelector(
    selector.NumberSelectorConfig(
        min=0, step="any", mode=selector.NumberSelectorMode.BOX,
        unit_of_measurement="€/kWh",
    )
)
_EURO = selector.NumberSelector(
    selector.NumberSelectorConfig(
        min=0, step=0.01, mode=selector.NumberSelectorMode.BOX, unit_of_measurement="€"
    )
)
_MODE = selector.SelectSelector(
    selector.SelectSelectorConfig(
        options=MODES, translation_key="calc_mode", mode=selector.SelectSelectorMode.LIST
    )
)

BASIC_KEYS = (
    CONF_NAME, CONF_INVESTMENT, CONF_START_DATE, CONF_MODE,
    CONF_PRICE_SENSOR, CONF_PRICE_FIXED, CONF_FEED_IN_TARIFF,
)


def _opt(key: str, defaults: dict[str, Any]) -> vol.Optional:
    if defaults.get(key) not in (None, ""):
        return vol.Optional(key, default=defaults[key])
    return vol.Optional(key)


def _schema_basic(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, "PV-Anlage")):
                selector.TextSelector(),
            vol.Required(CONF_INVESTMENT, default=defaults.get(CONF_INVESTMENT, 0)): _EURO,
            vol.Required(
                CONF_START_DATE,
                default=defaults.get(CONF_START_DATE) or dt_util.now().date().isoformat(),
            ): selector.DateSelector(),
            vol.Required(CONF_MODE, default=defaults.get(CONF_MODE, MODE_HOUSE)): _MODE,
            _opt(CONF_PRICE_SENSOR, defaults): _PRICE_SENSOR,
            _opt(CONF_PRICE_FIXED, defaults): _PRICE,
            vol.Required(
                CONF_FEED_IN_TARIFF, default=defaults.get(CONF_FEED_IN_TARIFF) or 0
            ): _PRICE,
        }
    )


def _schema_sensors(mode: str, defaults: dict[str, Any]) -> vol.Schema:
    schema: dict[Any, Any] = {}
    # Alte Einträge speichern die Erzeugung als einzelnen String.
    defaults = {
        **defaults,
        **{k: _as_list(defaults.get(k)) for k in MULTI_KEYS if defaults.get(k)},
    }
    for key, required in MODE_SENSORS[mode]:
        if required:
            marker = (
                vol.Required(key, default=defaults[key]) if defaults.get(key)
                else vol.Required(key)
            )
        else:
            marker = _opt(key, defaults)
        schema[marker] = _ENERGY_SENSOR_MULTI if key in MULTI_KEYS else _ENERGY_SENSOR
    return vol.Schema(schema)


def _as_list(value: Any) -> list[str]:
    if isinstance(value, (list, tuple)):
        return [v for v in value if v]
    return [value] if value else []


def _validate_basic(hass: HomeAssistant, user_input: dict[str, Any]) -> dict[str, str]:
    price_sensor = user_input.get(CONF_PRICE_SENSOR)
    has_fixed = user_input.get(CONF_PRICE_FIXED) not in (None, "")
    if not price_sensor and not has_fixed:
        return {"base": "price_required"}
    # Preis-Sensor ohne Langzeitstatistik: Für Zeiträume vor der Zustands-
    # Historie (~10 Tage) gibt es keinen Stundenpreis. Ohne Festpreis als
    # Ersatz würde die Ersparnis dort mit 0 € gerechnet.
    if price_sensor and not has_fixed:
        state = hass.states.get(price_sensor)
        start = dt_util.parse_date(str(user_input.get(CONF_START_DATE) or ""))
        old_start = start is not None and start < dt_util.now().date() - timedelta(days=HISTORY_DAYS)
        if state is not None and not state.attributes.get("state_class") and old_start:
            return {CONF_PRICE_FIXED: "price_fallback_required"}
    return {}


def _validate_sensors(hass: HomeAssistant, mode: str, user_input: dict[str, Any]) -> dict[str, str]:
    errors: dict[str, str] = {}
    chosen = [e for k, _ in MODE_SENSORS[mode] for e in _as_list(user_input.get(k))]
    if len(chosen) != len(set(chosen)):
        return {"base": "duplicate_sensor"}
    for key, required in MODE_SENSORS[mode]:
        entity_ids = _as_list(user_input.get(key))
        if required and not entity_ids:
            errors[key] = "sensor_required"
        for entity_id in entity_ids:
            state = hass.states.get(entity_id)
            if state is not None and not state.attributes.get("state_class"):
                errors[key] = "no_state_class"
    has_charge = bool(user_input.get(CONF_BATTERY_CHARGE_SENSOR))
    has_discharge = bool(user_input.get(CONF_BATTERY_DISCHARGE_SENSOR))
    if any(k == CONF_BATTERY_CHARGE_SENSOR for k, _ in MODE_SENSORS[mode]) and (
        has_charge != has_discharge
    ):
        errors["base"] = "battery_pair"
    return errors


def _full_config(basic: dict[str, Any], sensors: dict[str, Any]) -> dict[str, Any]:
    """Alle Schlüssel explizit setzen – geleerte Felder werden zu None.

    Wichtig für den Options-Flow: sonst würde ein gelöschtes optionales Feld
    auf den alten Wert aus ``entry.data`` zurückfallen.
    """
    mode = basic[CONF_MODE]
    allowed = {k for k, _ in MODE_SENSORS[mode]}
    data = {k: basic.get(k) for k in BASIC_KEYS}
    data.update({k: (sensors.get(k) if k in allowed else None) for k in ENERGY_SENSOR_KEYS})
    return data


class RoiTrackerConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 2

    def __init__(self) -> None:
        self._basic: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = _validate_basic(self.hass, user_input)
            if not errors:
                self._basic = user_input
                return await self.async_step_sensors()
        return self.async_show_form(
            step_id="user",
            data_schema=_schema_basic(user_input or {}),
            errors=errors,
        )

    async def async_step_sensors(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        mode = self._basic[CONF_MODE]
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = _validate_sensors(self.hass, mode, user_input)
            if not errors:
                return self.async_create_entry(
                    title=self._basic[CONF_NAME],
                    data=_full_config(self._basic, user_input),
                )
        return self.async_show_form(
            step_id=f"sensors_{mode}",
            data_schema=_schema_sensors(mode, user_input or {}),
            errors=errors,
        )

    # Jede Berechnungsart hat eigene Texte → eigene step_ids, gleiche Logik.
    async_step_sensors_house = async_step_sensors
    async_step_sensors_pv = async_step_sensors
    async_step_sensors_direct = async_step_sensors

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return RoiTrackerOptionsFlow()


class RoiTrackerOptionsFlow(OptionsFlow):
    def __init__(self) -> None:
        self._basic: dict[str, Any] = {}

    @property
    def _current(self) -> dict[str, Any]:
        return {**self.config_entry.data, **self.config_entry.options}

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = _validate_basic(self.hass, user_input)
            if not errors:
                self._basic = user_input
                return await self.async_step_sensors()
        return self.async_show_form(
            step_id="init",
            data_schema=_schema_basic(user_input or self._current),
            errors=errors,
        )

    async def async_step_sensors(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        mode = self._basic[CONF_MODE]
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = _validate_sensors(self.hass, mode, user_input)
            if not errors:
                if self._basic[CONF_NAME] != self.config_entry.title:
                    self.hass.config_entries.async_update_entry(
                        self.config_entry, title=self._basic[CONF_NAME]
                    )
                return self.async_create_entry(
                    title="", data=_full_config(self._basic, user_input)
                )
        return self.async_show_form(
            step_id=f"sensors_{mode}",
            data_schema=_schema_sensors(mode, user_input or self._current),
            errors=errors,
        )

    async_step_sensors_house = async_step_sensors
    async_step_sensors_pv = async_step_sensors
    async_step_sensors_direct = async_step_sensors
