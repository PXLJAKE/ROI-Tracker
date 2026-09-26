"""Konstanten für die ROI-Tracker-Integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "roi_tracker"

# --- Config-/Options-Flow Schlüssel -----------------------------------------

CONF_NAME: Final = "name"
CONF_INVESTMENT: Final = "investment"
CONF_START_DATE: Final = "start_date"
CONF_MODE: Final = "calc_mode"

# Energie-Sensoren (kumulierte kWh-Zähler mit state_class)
CONF_CONSUMPTION_SENSOR: Final = "consumption_sensor"  # Hausverbrauch bzw. Eigenverbrauch
CONF_GRID_IMPORT_SENSOR: Final = "grid_import_sensor"  # Netzbezug
CONF_EXPORT_SENSOR: Final = "export_sensor"  # Einspeisung
CONF_PRODUCTION_SENSOR: Final = "production_sensor"  # PV-Erzeugung
CONF_BATTERY_CHARGE_SENSOR: Final = "battery_charge_sensor"
CONF_BATTERY_DISCHARGE_SENSOR: Final = "battery_discharge_sensor"

# Preise
CONF_PRICE_SENSOR: Final = "price_sensor"  # dynamischer Strompreis (€/kWh, ct/kWh, €/MWh)
CONF_PRICE_FIXED: Final = "price_fixed"  # fester Strompreis €/kWh (bzw. Fallback)
CONF_FEED_IN_TARIFF: Final = "reward_fixed"  # Einspeisevergütung €/kWh (Schlüssel aus v1)

ENERGY_SENSOR_KEYS: Final = (
    CONF_CONSUMPTION_SENSOR,
    CONF_GRID_IMPORT_SENSOR,
    CONF_EXPORT_SENSOR,
    CONF_PRODUCTION_SENSOR,
    CONF_BATTERY_CHARGE_SENSOR,
    CONF_BATTERY_DISCHARGE_SENSOR,
)

# Alle Schlüssel, die das Rechenergebnis beeinflussen (Investition nicht:
# die ändert nur ROI/Amortisation, nicht die Tageswerte).
CALC_KEYS: Final = (
    CONF_START_DATE,
    CONF_MODE,
    *ENERGY_SENSOR_KEYS,
    CONF_PRICE_SENSOR,
    CONF_PRICE_FIXED,
    CONF_FEED_IN_TARIFF,
)

# --- Berechnungsarten ---------------------------------------------------------

# Eigenverbrauch = Hausverbrauch − Netzbezug
MODE_HOUSE: Final = "house"
# Eigenverbrauch = PV-Erzeugung − Einspeisung + Batterie-Entladung − Batterie-Ladung
MODE_PV: Final = "pv"
# Eigenverbrauch = fertiger Eigenverbrauchs-Sensor (+ Batterie-Entladung)
MODE_DIRECT: Final = "direct"

MODES: Final = [MODE_HOUSE, MODE_PV, MODE_DIRECT]

# Welche Sensoren in welchem Modus abgefragt werden: (Schlüssel, Pflicht)
MODE_SENSORS: Final = {
    MODE_HOUSE: (
        (CONF_CONSUMPTION_SENSOR, True),
        (CONF_GRID_IMPORT_SENSOR, True),
        (CONF_EXPORT_SENSOR, False),
    ),
    MODE_PV: (
        (CONF_PRODUCTION_SENSOR, True),
        (CONF_EXPORT_SENSOR, True),
        (CONF_BATTERY_CHARGE_SENSOR, False),
        (CONF_BATTERY_DISCHARGE_SENSOR, False),
    ),
    MODE_DIRECT: (
        (CONF_CONSUMPTION_SENSOR, True),
        (CONF_BATTERY_DISCHARGE_SENSOR, False),
        (CONF_EXPORT_SENSOR, False),
    ),
}

# --- Sensor-Kennungen (unique_id-Suffixe) -------------------------------------
# Die ersten sechs existierten schon in v1 → Historie bleibt erhalten.

SENSOR_SAVINGS: Final = "savings"
SENSOR_REVENUE: Final = "revenue"
SENSOR_TOTAL_RETURN: Final = "total_return"
SENSOR_REMAINING: Final = "remaining_investment"
SENSOR_AMORTIZATION: Final = "amortization"
SENSOR_ROI_PERCENT: Final = "roi_percent"
SENSOR_YEARLY_ESTIMATE: Final = "yearly_estimate"
SENSOR_BREAKEVEN_DATE: Final = "breakeven_date"
SENSOR_SELF_KWH: Final = "total_consumption_kwh"
SENSOR_EXPORT_KWH: Final = "total_export_kwh"

# --- Sonstiges ----------------------------------------------------------------

DEFAULT_UPDATE_INTERVAL_MINUTES: Final = 5

SERVICE_RECALCULATE: Final = "recalculate"
ATTR_START_DATE: Final = "start_date"

STORAGE_VERSION: Final = 1
STORAGE_KEY: Final = "roi_tracker_v2_{entry_id}"
LEGACY_STORAGE_KEY: Final = "roi_tracker_{entry_id}"
