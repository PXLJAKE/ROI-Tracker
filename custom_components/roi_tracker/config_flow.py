"""Config- und Options-Flow für ROI Tracker.

Ablauf beim Hinzufügen:
  1. Vorlage wählen (PV / E-Auto / Heizung / Benutzerdefiniert)
  2. Felder ausfüllen – das angezeigte Formular hängt von der Vorlage ab
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
    CONF_BATTERY_CHARGE_SENSOR,
    CONF_BATTERY_DISCHARGE_SENSOR,
    CONF_CONSUMPTION_SENSOR,
    CONF_COST_SENSOR,
    CONF_EXPORT_SENSOR,
    CONF_INVESTMENT,
    CONF_NAME,
    CONF_PRICE_FIXED,
    CONF_PRICE_MODE,
    CONF_PRICE_SENSOR,
    CONF_PRODUCTION_SENSOR,
    CONF_REWARD_FIXED,
    CONF_REWARD_MODE,
    CONF_REWARD_SENSOR,
    CONF_TEMPLATE,
    DOMAIN,
    PRICE_MODE_COST_SENSOR,
    PRICE_MODE_FIXED,
    PRICE_MODE_NONE,
    PRICE_MODE_SENSOR,
    TEMPLATE_DEFAULTS,
    TEMPLATES,
)

# Wiederverwendbare Selektoren -----------------------------------------------

_SENSOR_SELECTOR = selector.EntitySelector(
    selector.EntitySelectorConfig(domain="sensor")
)
_PRICE_SELECTOR = selector.NumberSelector(
    selector.NumberSelectorConfig(
        min=0, step=0.0001, mode=selector.NumberSelectorMode.BOX
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
            mode=selector.SelectSelectorMode.DROPDOWN,
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


def _build_schema(template: str, defaults: dict[str, Any]) -> vol.Schema:
    """Erzeugt das Detail-Formular passend zur Vorlage."""
    tpl = TEMPLATE_DEFAULTS.get(template, TEMPLATE_DEFAULTS["custom"])
    fields: list[str] = tpl["fields"]
    has_reward: bool = tpl.get("has_reward", False)
    has_baseline: bool = tpl.get("has_baseline", False)

    schema: dict[Any, Any] = {
        vol.Required(
            CONF_NAME, default=defaults.get(CONF_NAME, "")
        ): selector.TextSelector(),
        vol.Required(
            CONF_INVESTMENT, default=defaults.get(CONF_INVESTMENT, 0)
        ): _INVEST_SELECTOR,
    }

    # Mengen-Sensoren je nach Vorlage
    if CONF_PRODUCTION_SENSOR in fields:
        schema[_opt(CONF_PRODUCTION_SENSOR, defaults)] = _SENSOR_SELECTOR
    if CONF_CONSUMPTION_SENSOR in fields:
        schema[_opt(CONF_CONSUMPTION_SENSOR, defaults)] = _SENSOR_SELECTOR
    if CONF_EXPORT_SENSOR in fields:
        schema[_opt(CONF_EXPORT_SENSOR, defaults)] = _SENSOR_SELECTOR
    if CONF_BATTERY_CHARGE_SENSOR in fields:
        schema[_opt(CONF_BATTERY_CHARGE_SENSOR, defaults)] = _SENSOR_SELECTOR
    if CONF_BATTERY_DISCHARGE_SENSOR in fields:
        schema[_opt(CONF_BATTERY_DISCHARGE_SENSOR, defaults)] = _SENSOR_SELECTOR

    # Bezugspreis / Kosten
    schema[
        vol.Required(
            CONF_PRICE_MODE, default=defaults.get(CONF_PRICE_MODE, PRICE_MODE_FIXED)
        )
    ] = _price_mode_selector(include_cost=True, include_none=False)
    schema[_opt(CONF_PRICE_FIXED, defaults)] = _PRICE_SELECTOR
    schema[_opt(CONF_PRICE_SENSOR, defaults)] = _SENSOR_SELECTOR
    schema[_opt(CONF_COST_SENSOR, defaults)] = _SENSOR_SELECTOR

    # Baseline (Vergleich mit Alt-Lösung) – E-Auto/Heizung/Custom
    if has_baseline:
        schema[_opt(CONF_BASELINE_RATE, defaults)] = _PRICE_SELECTOR

    # Einspeise-/Abgabe-Vergütung – PV/Custom
    if has_reward:
        schema[
            vol.Required(
                CONF_REWARD_MODE,
                default=defaults.get(CONF_REWARD_MODE, PRICE_MODE_FIXED),
            )
        ] = _price_mode_selector(include_cost=False, include_none=True)
        schema[_opt(CONF_REWARD_FIXED, defaults)] = _PRICE_SELECTOR
        schema[_opt(CONF_REWARD_SENSOR, defaults)] = _SENSOR_SELECTOR

    return vol.Schema(schema)


def _opt(key: str, defaults: dict[str, Any]) -> vol.Optional:
    """Optionales Feld mit ggf. vorbelegtem Default."""
    if key in defaults and defaults[key] not in (None, ""):
        return vol.Optional(key, default=defaults[key])
    return vol.Optional(key)


class RoiTrackerConfigFlow(ConfigFlow, domain=DOMAIN):
    """Geführter Dialog zum Anlegen einer Anlage."""

    VERSION = 1

    def __init__(self) -> None:
        self._template: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Schritt 1: Vorlage auswählen."""
        if user_input is not None:
            self._template = user_input[CONF_TEMPLATE]
            return await self.async_step_details()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required(CONF_TEMPLATE, default=TEMPLATES[0]): _template_selector()}
            ),
        )

    async def async_step_details(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Schritt 2: Detailfelder passend zur Vorlage."""
        assert self._template is not None

        if user_input is not None:
            data = {CONF_TEMPLATE: self._template, **user_input}
            return self.async_create_entry(title=user_input[CONF_NAME], data=data)

        return self.async_show_form(
            step_id="details",
            data_schema=_build_schema(self._template, {}),
            description_placeholders={"template": self._template},
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return RoiTrackerOptionsFlow()


class RoiTrackerOptionsFlow(OptionsFlow):
    """Nachträgliches Bearbeiten einer Anlage (Sensoren/Preise ändern)."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        template = self.config_entry.data.get(CONF_TEMPLATE, "custom")
        current = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(
            step_id="init",
            data_schema=_build_schema(template, current),
        )
