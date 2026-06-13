"""Config- und Options-Flow für ROI Tracker.

Mehrstufiger Dialog, damit immer nur die wirklich benötigten Felder erscheinen:

  1. Vorlage wählen (PV / Benutzerdefiniert)
  2. Grunddaten: Name, Investition, Startdatum, Mengen-Sensoren, Modus-Auswahl
  3. Quellen-Details: passender Preis-/Vergütungs-Wert
"""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_BASELINE_RATE,
    CONF_BATTERY_DISCHARGE_SENSOR,
    CONF_CONSUMPTION_SENSOR,
    CONF_COST_SENSOR,
    CONF_EXPORT_SENSOR,
    CONF_GRID_IMPORT_SENSOR,
    CONF_INVESTMENT,
    CONF_NAME,
    CONF_PRICE_FIXED,
    CONF_PRICE_MODE,
    CONF_PRICE_SENSOR,
    CONF_REWARD_FIXED,
    CONF_REWARD_MODE,
    CONF_REWARD_SENSOR,
    CONF_SENSOR_RESET_DAILY,
    CONF_START_DATE,
    CONF_TEMPLATE,
    DOMAIN,
    PRICE_MODE_COST_SENSOR,
    PRICE_MODE_FIXED,
    PRICE_MODE_NONE,
    PRICE_MODE_SENSOR,
    TEMPLATE_DEFAULTS,
    TEMPLATES,
)

# ── Selektoren ────────────────────────────────────────────────────────────────

_ENERGY_SENSOR = selector.EntitySelector(
    selector.EntitySelectorConfig(domain="sensor")
)
_MONEY_SENSOR = selector.EntitySelector(
    selector.EntitySelectorConfig(domain="sensor", device_class="monetary")
)
_ANY_SENSOR = selector.EntitySelector(
    selector.EntitySelectorConfig(domain="sensor")
)
_PRICE_PER_UNIT = selector.NumberSelector(
    selector.NumberSelectorConfig(
        min=0, step="any", mode=selector.NumberSelectorMode.BOX,
        unit_of_measurement="€/kWh",
    )
)
_INVEST_SELECTOR = selector.NumberSelector(
    selector.NumberSelectorConfig(
        min=0, step=0.01, mode=selector.NumberSelectorMode.BOX, unit_of_measurement="€"
    )
)


def _price_mode_selector(include_cost: bool, include_none: bool) -> selector.Selector:
    options = [PRICE_MODE_FIXED, PRICE_MODE_SENSOR]
    if include_cost:
        options.append(PRICE_MODE_COST_SENSOR)
    if include_none:
        options.append(PRICE_MODE_NONE)
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=options,
            translation_key="price_mode",
            mode=selector.SelectSelectorMode.LIST,
        )
    )


def _template_selector() -> selector.Selector:
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=list(TEMPLATES),
            translation_key="template",
            mode=selector.SelectSelectorMode.LIST,
        )
    )


def _opt(key: str, defaults: dict[str, Any]) -> vol.Optional:
    if key in defaults and defaults[key] not in (None, ""):
        return vol.Optional(key, default=defaults[key])
    return vol.Optional(key)


def _req(key: str, defaults: dict[str, Any], fallback: Any) -> vol.Required:
    return vol.Required(key, default=defaults.get(key, fallback))


def _schema_setup(template: str, defaults: dict[str, Any]) -> vol.Schema:
    """Schritt 2: Grunddaten, Mengen-Sensoren und Modus-Auswahl."""
    tpl = TEMPLATE_DEFAULTS.get(template, TEMPLATE_DEFAULTS["custom"])
    fields: list[str] = tpl["fields"]
    has_reward: bool = tpl.get("has_reward", False)
    has_baseline: bool = tpl.get("has_baseline", False)

    schema: dict[Any, Any] = {
        _req(CONF_NAME, defaults, ""): selector.TextSelector(),
        _req(CONF_INVESTMENT, defaults, 0): _INVEST_SELECTOR,
        _opt(CONF_START_DATE, defaults): selector.DateSelector(),
    }

    if CONF_CONSUMPTION_SENSOR in fields:
        schema[_opt(CONF_CONSUMPTION_SENSOR, defaults)] = _ENERGY_SENSOR
    if CONF_EXPORT_SENSOR in fields:
        schema[_opt(CONF_EXPORT_SENSOR, defaults)] = _ENERGY_SENSOR
    if CONF_BATTERY_DISCHARGE_SENSOR in fields:
        schema[_opt(CONF_BATTERY_DISCHARGE_SENSOR, defaults)] = _ENERGY_SENSOR
    if CONF_GRID_IMPORT_SENSOR in fields:
        schema[_opt(CONF_GRID_IMPORT_SENSOR, defaults)] = _ENERGY_SENSOR

    schema[_req(CONF_PRICE_MODE, defaults, PRICE_MODE_FIXED)] = _price_mode_selector(
        include_cost=True, include_none=False
    )

    if has_baseline:
        schema[_opt(CONF_BASELINE_RATE, defaults)] = _PRICE_PER_UNIT

    if has_reward:
        schema[_req(CONF_REWARD_MODE, defaults, PRICE_MODE_FIXED)] = (
            _price_mode_selector(include_cost=False, include_none=True)
        )

    # Sensor-Typ: täglich/monatlich rücksetzend oder dauerhaft kumulativ
    schema[_req(CONF_SENSOR_RESET_DAILY, defaults, False)] = selector.BooleanSelector()

    return vol.Schema(schema)


def _schema_sources(
    price_mode: str,
    reward_mode: str | None,
    defaults: dict[str, Any],
) -> vol.Schema:
    """Schritt 3: nur die zum gewählten Modus passenden Wertfelder."""
    schema: dict[Any, Any] = {}

    if price_mode == PRICE_MODE_FIXED:
        schema[_opt(CONF_PRICE_FIXED, defaults)] = _PRICE_PER_UNIT
    elif price_mode == PRICE_MODE_SENSOR:
        schema[_opt(CONF_PRICE_SENSOR, defaults)] = _ANY_SENSOR
    elif price_mode == PRICE_MODE_COST_SENSOR:
        schema[_opt(CONF_COST_SENSOR, defaults)] = _MONEY_SENSOR

    if reward_mode == PRICE_MODE_FIXED:
        schema[_opt(CONF_REWARD_FIXED, defaults)] = _PRICE_PER_UNIT
    elif reward_mode == PRICE_MODE_SENSOR:
        schema[_opt(CONF_REWARD_SENSOR, defaults)] = _MONEY_SENSOR

    return vol.Schema(schema)


def _needs_sources_step(price_mode: str, reward_mode: str | None) -> bool:
    has_price = price_mode in (PRICE_MODE_FIXED, PRICE_MODE_SENSOR, PRICE_MODE_COST_SENSOR)
    has_reward = reward_mode in (PRICE_MODE_FIXED, PRICE_MODE_SENSOR)
    return has_price or has_reward


# ── Config Flow ───────────────────────────────────────────────────────────────

class RoiTrackerConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._template: str | None = None
        self._data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self._template = user_input[CONF_TEMPLATE]
            return await self.async_step_setup()
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required(CONF_TEMPLATE, default=TEMPLATES[0]): _template_selector()}
            ),
        )

    async def async_step_setup(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        assert self._template is not None
        if user_input is not None:
            self._data = {CONF_TEMPLATE: self._template, **user_input}
            if _needs_sources_step(
                user_input.get(CONF_PRICE_MODE, PRICE_MODE_FIXED),
                user_input.get(CONF_REWARD_MODE),
            ):
                return await self.async_step_sources()
            return self.async_create_entry(title=self._data[CONF_NAME], data=self._data)
        return self.async_show_form(
            step_id="setup",
            data_schema=_schema_setup(self._template, {}),
        )

    async def async_step_sources(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        assert self._template is not None
        price_mode = self._data.get(CONF_PRICE_MODE, PRICE_MODE_FIXED)
        reward_mode = self._data.get(CONF_REWARD_MODE)
        if user_input is not None:
            self._data.update(user_input)
            return self.async_create_entry(title=self._data[CONF_NAME], data=self._data)
        return self.async_show_form(
            step_id="sources",
            data_schema=_schema_sources(price_mode, reward_mode, {}),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return RoiTrackerOptionsFlow()


# ── Options Flow ──────────────────────────────────────────────────────────────

class RoiTrackerOptionsFlow(OptionsFlow):
    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    @property
    def _template(self) -> str:
        return self.config_entry.data.get(CONF_TEMPLATE, "custom")

    @property
    def _current(self) -> dict[str, Any]:
        return {**self.config_entry.data, **self.config_entry.options}

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self._data = dict(user_input)
            if _needs_sources_step(
                user_input.get(CONF_PRICE_MODE, PRICE_MODE_FIXED),
                user_input.get(CONF_REWARD_MODE),
            ):
                return await self.async_step_sources()
            return self.async_create_entry(title="", data=self._data)
        return self.async_show_form(
            step_id="init",
            data_schema=_schema_setup(self._template, self._current),
        )

    async def async_step_sources(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        price_mode = self._data.get(CONF_PRICE_MODE, PRICE_MODE_FIXED)
        reward_mode = self._data.get(CONF_REWARD_MODE)
        if user_input is not None:
            self._data.update(user_input)
            return self.async_create_entry(title="", data=self._data)
        return self.async_show_form(
            step_id="sources",
            data_schema=_schema_sources(price_mode, reward_mode, self._current),
        )
