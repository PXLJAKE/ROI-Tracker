"""Sensor-Entitäten für einen ROI-Rechner."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import RoiConfigEntry
from .calculator import RoiResult
from .const import (
    CONF_TEMPLATE,
    DOMAIN,
    SENSOR_AMORTIZATION,
    SENSOR_BATTERY_SAVINGS,
    SENSOR_BREAKEVEN_DAYS,
    SENSOR_DAILY_AVERAGE,
    SENSOR_GRID_IMPORT_COST,
    SENSOR_GRID_IMPORT_KWH,
    SENSOR_MONTHLY_ESTIMATE,
    SENSOR_REMAINING,
    SENSOR_REVENUE,
    SENSOR_ROI_PERCENT,
    SENSOR_SAVINGS,
    SENSOR_SELF_SUFFICIENCY,
    SENSOR_TOTAL_BATTERY_DISCHARGE_KWH,
    SENSOR_TOTAL_CONSUMPTION_KWH,
    SENSOR_TOTAL_EXPORT_KWH,
    SENSOR_TOTAL_RETURN,
)
from .coordinator import RoiTrackerCoordinator

CURRENCY = "€"


@dataclass(frozen=True, kw_only=True)
class RoiSensorDescription(SensorEntityDescription):
    """Beschreibung eines ROI-Sensors inkl. Wert-Extraktor."""

    value_fn: Callable[[RoiResult], float | None]


SENSOR_DESCRIPTIONS: tuple[RoiSensorDescription, ...] = (
    RoiSensorDescription(
        key=SENSOR_TOTAL_RETURN,
        translation_key=SENSOR_TOTAL_RETURN,
        native_unit_of_measurement=CURRENCY,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:cash-multiple",
        value_fn=lambda r: r.total_return,
    ),
    RoiSensorDescription(
        key=SENSOR_SAVINGS,
        translation_key=SENSOR_SAVINGS,
        native_unit_of_measurement=CURRENCY,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:piggy-bank",
        value_fn=lambda r: r.savings,
    ),
    RoiSensorDescription(
        key=SENSOR_BATTERY_SAVINGS,
        translation_key=SENSOR_BATTERY_SAVINGS,
        native_unit_of_measurement=CURRENCY,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:battery-charging",
        value_fn=lambda r: r.battery_savings,
    ),
    RoiSensorDescription(
        key=SENSOR_REVENUE,
        translation_key=SENSOR_REVENUE,
        native_unit_of_measurement=CURRENCY,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:transmission-tower-export",
        value_fn=lambda r: r.revenue,
    ),
    RoiSensorDescription(
        key=SENSOR_REMAINING,
        translation_key=SENSOR_REMAINING,
        native_unit_of_measurement=CURRENCY,
        device_class=SensorDeviceClass.MONETARY,
        icon="mdi:cash-clock",
        value_fn=lambda r: r.remaining_investment,
    ),
    RoiSensorDescription(
        key=SENSOR_AMORTIZATION,
        translation_key=SENSOR_AMORTIZATION,
        native_unit_of_measurement="%",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:progress-check",
        value_fn=lambda r: r.amortization_percent,
    ),
    RoiSensorDescription(
        key=SENSOR_ROI_PERCENT,
        translation_key=SENSOR_ROI_PERCENT,
        native_unit_of_measurement="%",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:chart-line",
        value_fn=lambda r: r.roi_percent,
    ),
    RoiSensorDescription(
        key=SENSOR_BREAKEVEN_DAYS,
        translation_key=SENSOR_BREAKEVEN_DAYS,
        native_unit_of_measurement="d",
        icon="mdi:calendar-clock",
        value_fn=lambda r: r.breakeven_days,
    ),
    RoiSensorDescription(
        key=SENSOR_SELF_SUFFICIENCY,
        translation_key=SENSOR_SELF_SUFFICIENCY,
        native_unit_of_measurement="%",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:home-lightning-bolt",
        value_fn=lambda r: r.self_sufficiency_percent,
    ),
    # Durchschnitts-/Prognosewerte: bewusst OHNE device_class monetary –
    # monetary erlaubt nur state_class total, measurement wäre ungültig.
    RoiSensorDescription(
        key=SENSOR_DAILY_AVERAGE,
        translation_key=SENSOR_DAILY_AVERAGE,
        native_unit_of_measurement=CURRENCY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:calendar-today",
        value_fn=lambda r: r.daily_average,
    ),
    RoiSensorDescription(
        key=SENSOR_MONTHLY_ESTIMATE,
        translation_key=SENSOR_MONTHLY_ESTIMATE,
        native_unit_of_measurement=CURRENCY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:calendar-month",
        value_fn=lambda r: r.monthly_estimate,
    ),
    RoiSensorDescription(
        key=SENSOR_GRID_IMPORT_COST,
        translation_key=SENSOR_GRID_IMPORT_COST,
        native_unit_of_measurement=CURRENCY,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:transmission-tower-import",
        value_fn=lambda r: r.grid_import_cost if r.grid_import_cost else None,
    ),
    # ── Permanente kWh-Summier-Sensoren ──────────────────────────────────────
    # Diese Sensoren akkumulieren dauerhaft, auch wenn der Quell-Sensor täglich
    # oder monatlich zurücksetzt. Nützlich für Automationen und externe Karten.
    RoiSensorDescription(
        key=SENSOR_TOTAL_CONSUMPTION_KWH,
        translation_key=SENSOR_TOTAL_CONSUMPTION_KWH,
        native_unit_of_measurement="kWh",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:home-lightning-bolt-outline",
        value_fn=lambda r: r.total_consumption_kwh if r.total_consumption_kwh else None,
    ),
    RoiSensorDescription(
        key=SENSOR_TOTAL_EXPORT_KWH,
        translation_key=SENSOR_TOTAL_EXPORT_KWH,
        native_unit_of_measurement="kWh",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:transmission-tower-export",
        value_fn=lambda r: r.total_export_kwh if r.total_export_kwh else None,
    ),
    RoiSensorDescription(
        key=SENSOR_TOTAL_BATTERY_DISCHARGE_KWH,
        translation_key=SENSOR_TOTAL_BATTERY_DISCHARGE_KWH,
        native_unit_of_measurement="kWh",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:battery-arrow-down",
        value_fn=lambda r: r.total_battery_discharge_kwh if r.total_battery_discharge_kwh else None,
    ),
    RoiSensorDescription(
        key=SENSOR_GRID_IMPORT_KWH,
        translation_key=SENSOR_GRID_IMPORT_KWH,
        native_unit_of_measurement="kWh",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:transmission-tower-import",
        value_fn=lambda r: r.grid_import_kwh if r.grid_import_kwh else None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: RoiConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Legt die Sensoren für eine Anlage an."""
    coordinator = entry.runtime_data
    async_add_entities(
        RoiSensor(coordinator, entry, description)
        for description in SENSOR_DESCRIPTIONS
    )


class RoiSensor(CoordinatorEntity[RoiTrackerCoordinator], SensorEntity):
    """Ein einzelner ROI-Kennzahl-Sensor."""

    entity_description: RoiSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: RoiTrackerCoordinator,
        entry: RoiConfigEntry,
        description: RoiSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="ROI Tracker",
            model=entry.data.get(CONF_TEMPLATE, "custom"),
        )

    @property
    def native_value(self) -> float | None:
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict | None:
        # Nur am "Gesamtrückfluss"-Sensor die Detailwerte anhängen.
        if self.entity_description.key == SENSOR_TOTAL_RETURN and self.coordinator.data:
            return self.coordinator.data.attributes
        return None
