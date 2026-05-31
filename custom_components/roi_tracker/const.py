"""Konstanten für die ROI-Tracker-Integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "roi_tracker"

# --- Config-/Options-Flow Schlüssel -----------------------------------------

CONF_NAME: Final = "name"
CONF_TEMPLATE: Final = "template"
CONF_INVESTMENT: Final = "investment"
CONF_START_DATE: Final = "start_date"

# Energie-/Mengen-Sensoren (kWh)
CONF_PRODUCTION_SENSOR: Final = "production_sensor"      # erzeugte PV-Energie
CONF_CONSUMPTION_SENSOR: Final = "consumption_sensor"    # Eigenverbrauch (PV direkt + Batterie)
CONF_EXPORT_SENSOR: Final = "export_sensor"              # eingespeiste Energie
CONF_BATTERY_CHARGE_SENSOR: Final = "battery_charge_sensor"
CONF_BATTERY_DISCHARGE_SENSOR: Final = "battery_discharge_sensor"
CONF_GRID_IMPORT_SENSOR: Final = "grid_import_sensor"    # Netzbezug (optional, Gesamtbilanz)

# Preise / Erträge -----------------------------------------------------------
CONF_PRICE_MODE: Final = "price_mode"      # fixed | sensor | cost_sensor
CONF_PRICE_FIXED: Final = "price_fixed"    # €/kWh (fester Wert)
CONF_PRICE_SENSOR: Final = "price_sensor"  # €/kWh (z. B. Tibber)
CONF_COST_SENSOR: Final = "cost_sensor"    # € (fertiger kumulierter Kosten-Sensor)

CONF_REWARD_MODE: Final = "reward_mode"    # fixed | sensor | none
CONF_REWARD_FIXED: Final = "reward_fixed"  # €/kWh
CONF_REWARD_SENSOR: Final = "reward_sensor"

# Nur für TEMPLATE_CUSTOM: manueller Vergleichswert
CONF_BASELINE_RATE: Final = "baseline_rate"  # €/Einheit Alt-Lösung
CONF_UNIT: Final = "unit"

# --- Preis-Modi -------------------------------------------------------------

PRICE_MODE_FIXED: Final = "fixed"
PRICE_MODE_SENSOR: Final = "sensor"
PRICE_MODE_COST_SENSOR: Final = "cost_sensor"
PRICE_MODE_NONE: Final = "none"

# --- Vorlagen ---------------------------------------------------------------

TEMPLATE_PV: Final = "pv"
TEMPLATE_CUSTOM: Final = "custom"

TEMPLATES: Final = [
    TEMPLATE_PV,
    TEMPLATE_CUSTOM,
]

TEMPLATE_DEFAULTS: Final = {
    TEMPLATE_PV: {
        "unit": "kWh",
        "currency_unit": "€/kWh",
        "fields": [
            CONF_PRODUCTION_SENSOR,
            CONF_CONSUMPTION_SENSOR,
            CONF_EXPORT_SENSOR,
            CONF_BATTERY_CHARGE_SENSOR,
            CONF_BATTERY_DISCHARGE_SENSOR,
            CONF_GRID_IMPORT_SENSOR,
        ],
        "has_reward": True,
    },
    TEMPLATE_CUSTOM: {
        "unit": "kWh",
        "currency_unit": "€",
        "fields": [
            CONF_PRODUCTION_SENSOR,
            CONF_CONSUMPTION_SENSOR,
            CONF_EXPORT_SENSOR,
            CONF_GRID_IMPORT_SENSOR,
        ],
        "has_reward": True,
        "has_baseline": True,
    },
}

# --- Sensor-Kennungen (entity suffixes) -------------------------------------

SENSOR_SAVINGS: Final = "savings"
SENSOR_BATTERY_SAVINGS: Final = "battery_savings"
SENSOR_REVENUE: Final = "revenue"
SENSOR_TOTAL_RETURN: Final = "total_return"
SENSOR_AMORTIZATION: Final = "amortization"
SENSOR_REMAINING: Final = "remaining_investment"
SENSOR_BREAKEVEN_DAYS: Final = "breakeven_days"
SENSOR_SELF_SUFFICIENCY: Final = "self_sufficiency"
SENSOR_ROI_PERCENT: Final = "roi_percent"
SENSOR_DAILY_AVERAGE: Final = "daily_average"
SENSOR_MONTHLY_ESTIMATE: Final = "monthly_estimate"
SENSOR_GRID_IMPORT_COST: Final = "grid_import_cost"

# --- Sonstiges --------------------------------------------------------------

DEFAULT_UPDATE_INTERVAL_MINUTES: Final = 5

# --- Services ---------------------------------------------------------------

SERVICE_RESET: Final = "reset"
SERVICE_RECALCULATE: Final = "recalculate"
ATTR_START_DATE: Final = "start_date"

STORAGE_VERSION: Final = 1
STORAGE_KEY: Final = "roi_tracker_{entry_id}"
