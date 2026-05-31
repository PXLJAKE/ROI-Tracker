"""Konstanten für die ROI-Tracker-Integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "roi_tracker"

# --- Config-/Options-Flow Schlüssel -----------------------------------------

CONF_NAME: Final = "name"
CONF_TEMPLATE: Final = "template"
CONF_INVESTMENT: Final = "investment"
CONF_START_DATE: Final = "start_date"

# Energie-/Mengen-Sensoren (kWh, km, m³ ...)
CONF_PRODUCTION_SENSOR: Final = "production_sensor"  # erzeugte/erbrachte Menge
CONF_CONSUMPTION_SENSOR: Final = "consumption_sensor"  # Eigenverbrauch
CONF_EXPORT_SENSOR: Final = "export_sensor"  # eingespeiste/abgegebene Menge

# Batterie (optional, vor allem für PV)
CONF_BATTERY_CHARGE_SENSOR: Final = "battery_charge_sensor"
CONF_BATTERY_DISCHARGE_SENSOR: Final = "battery_discharge_sensor"

# Preise / Erträge -----------------------------------------------------------
# "Bezug" = Geld, das man spart, weil man nicht aus dem Netz kauft
# "Vergütung" = Geld, das man für Einspeisung/Abgabe bekommt
CONF_PRICE_MODE: Final = "price_mode"  # fixed | sensor | cost_sensor
CONF_PRICE_FIXED: Final = "price_fixed"  # €/Einheit (fester Wert)
CONF_PRICE_SENSOR: Final = "price_sensor"  # €/Einheit (dynamischer Sensor, z. B. Tibber)
CONF_COST_SENSOR: Final = "cost_sensor"  # € (fertiger Kosten-Sensor, "accumulated cost")

CONF_REWARD_MODE: Final = "reward_mode"  # fixed | sensor | none
CONF_REWARD_FIXED: Final = "reward_fixed"  # €/Einheit
CONF_REWARD_SENSOR: Final = "reward_sensor"  # € (fertiger Ertrags-Sensor)

# Vergleich/Referenz (z. B. bei E-Auto: alter Verbrenner-Verbrauch)
CONF_BASELINE_RATE: Final = "baseline_rate"  # Kosten der Alt-Lösung pro Einheit (manuell)
CONF_UNIT: Final = "unit"  # Anzeige-Einheit der Menge

# Altlösungs-Vergleich (zerlegt, nur für EV und Heizung)
CONF_LEGACY_CONSUMPTION: Final = "legacy_consumption"  # z. B. 8,5 L/100km oder L/m²/Jahr
CONF_LEGACY_FUEL_TYPE: Final = "legacy_fuel_type"      # Kraftstoff-/Heizmittelart
CONF_FUEL_PRICE_FIXED: Final = "fuel_price_fixed"      # Kraftstoffpreis fester Wert (€/Einheit)
CONF_FUEL_PRICE_SENSOR: Final = "fuel_price_sensor"    # Sensor für Kraftstoffpreis

# --- Kraftstoff-/Heizmittelarten --------------------------------------------

FUEL_DIESEL: Final = "diesel"
FUEL_BENZIN: Final = "benzin"
FUEL_LPG: Final = "lpg"
FUEL_CNG: Final = "cng"
FUEL_ERDGAS: Final = "erdgas"
FUEL_OEL: Final = "oel"
FUEL_PELLETS: Final = "pellets"
FUEL_FERNWAERME: Final = "fernwaerme"

FUEL_TYPES: Final = [
    FUEL_DIESEL,
    FUEL_BENZIN,
    FUEL_LPG,
    FUEL_CNG,
    FUEL_ERDGAS,
    FUEL_OEL,
    FUEL_PELLETS,
    FUEL_FERNWAERME,
]

# --- Preis-Modi -------------------------------------------------------------

PRICE_MODE_FIXED: Final = "fixed"
PRICE_MODE_SENSOR: Final = "sensor"
PRICE_MODE_COST_SENSOR: Final = "cost_sensor"
PRICE_MODE_NONE: Final = "none"

# --- Vorlagen ---------------------------------------------------------------

TEMPLATE_PV: Final = "pv"
TEMPLATE_EV: Final = "ev"
TEMPLATE_HEATING: Final = "heating"
TEMPLATE_CUSTOM: Final = "custom"

TEMPLATES: Final = [
    TEMPLATE_PV,
    TEMPLATE_EV,
    TEMPLATE_HEATING,
    TEMPLATE_CUSTOM,
]

# Pro Vorlage: welche Felder im Flow sinnvoll/sichtbar sind und Standard-Einheit.
# "fields" steuert, welche optionalen Sensorfelder angeboten werden.
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
        ],
        "has_reward": True,
    },
    TEMPLATE_EV: {
        "unit": "km",
        "currency_unit": "€/km",
        "fields": [
            CONF_CONSUMPTION_SENSOR,
        ],
        "has_reward": False,
        "has_baseline": False,
        "has_legacy": True,   # Vergleich mit altem Verbrenner (zerlegt)
    },
    TEMPLATE_HEATING: {
        "unit": "kWh",
        "currency_unit": "€/kWh",
        "fields": [
            CONF_CONSUMPTION_SENSOR,
        ],
        "has_reward": False,
        "has_baseline": False,
        "has_legacy": True,   # Vergleich mit alter Heizung (zerlegt)
    },
    TEMPLATE_CUSTOM: {
        "unit": "kWh",
        "currency_unit": "€",
        "fields": [
            CONF_PRODUCTION_SENSOR,
            CONF_CONSUMPTION_SENSOR,
            CONF_EXPORT_SENSOR,
        ],
        "has_reward": True,
        "has_baseline": True,
    },
}

# --- Sensor-Kennungen (entity suffixes) -------------------------------------

SENSOR_SAVINGS: Final = "savings"  # Ersparnis durch Eigenverbrauch (€)
SENSOR_BATTERY_SAVINGS: Final = "battery_savings"  # Ersparnis durch Batterie (€)
SENSOR_REVENUE: Final = "revenue"  # Einnahmen Einspeisung/Abgabe (€)
SENSOR_TOTAL_RETURN: Final = "total_return"  # kumulierter Rückfluss (€)
SENSOR_AMORTIZATION: Final = "amortization"  # Amortisation (%)
SENSOR_REMAINING: Final = "remaining_investment"  # offener Restbetrag (€)
SENSOR_BREAKEVEN_DAYS: Final = "breakeven_days"  # Restlaufzeit bis Break-Even (Tage)
SENSOR_SELF_SUFFICIENCY: Final = "self_sufficiency"  # Eigenverbrauchsquote (%)
SENSOR_ROI_PERCENT: Final = "roi_percent"  # ROI (%) inkl. Gewinn über Investition
SENSOR_DAILY_AVERAGE: Final = "daily_average"      # Ø täglicher Rückfluss (€/Tag)
SENSOR_MONTHLY_ESTIMATE: Final = "monthly_estimate"  # Monatsprognose (€/Monat)

# --- Sonstiges --------------------------------------------------------------

DEFAULT_UPDATE_INTERVAL_MINUTES: Final = 5

# --- Services ---------------------------------------------------------------

SERVICE_RESET: Final = "reset"
SERVICE_RECALCULATE: Final = "recalculate"
ATTR_START_DATE: Final = "start_date"

# Persistenter Zustand im ConfigEntry (runtime-data / store)
STORAGE_VERSION: Final = 1
STORAGE_KEY: Final = "roi_tracker_{entry_id}"
