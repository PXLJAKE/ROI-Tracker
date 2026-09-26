"""Sensor-Entitäten einer Anlage."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import RoiConfigEntry
from .const import (
    CONF_EXPORT_SENSOR,
    DOMAIN,
    SENSOR_AMORTIZATION,
    SENSOR_BREAKEVEN_DATE,
    SENSOR_EXPORT_KWH,
    SENSOR_REMAINING,
    SENSOR_REVENUE,
    SENSOR_ROI_PERCENT,
    SENSOR_SAVINGS,
    SENSOR_SELF_KWH,
    SENSOR_TOTAL_RETURN,
    SENSOR_YEARLY_ESTIMATE,
)
from .coordinator import RoiTrackerCoordinator


@dataclass(frozen=True, kw_only=True)
class RoiSensorDescription(SensorEntityDescription):
    value_fn: Callable[[dict], Any]
    currency: bool = False
    required_conf: str | None = None


def _date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


SENSOR_DESCRIPTIONS: tuple[RoiSensorDescription, ...] = (
    RoiSensorDescription(
        key=SENSOR_TOTAL_RETURN,
        translation_key=SENSOR_TOTAL_RETURN,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:cash-multiple",
        currency=True,
        value_fn=lambda d: d["total_return"],
    ),
    RoiSensorDescription(
        key=SENSOR_SAVINGS,
        translation_key=SENSOR_SAVINGS,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:piggy-bank",
        currency=True,
        value_fn=lambda d: d["savings"],
    ),
    RoiSensorDescription(
        key=SENSOR_REVENUE,
        translation_key=SENSOR_REVENUE,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:transmission-tower-export",
        currency=True,
        value_fn=lambda d: d["revenue"],
        required_conf=CONF_EXPORT_SENSOR,
    ),
    RoiSensorDescription(
        key=SENSOR_REMAINING,
        translation_key=SENSOR_REMAINING,
        device_class=SensorDeviceClass.MONETARY,
        icon="mdi:cash-clock",
        currency=True,
        value_fn=lambda d: d["remaining"],
    ),
    RoiSensorDescription(
        key=SENSOR_AMORTIZATION,
        translation_key=SENSOR_AMORTIZATION,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:progress-check",
        value_fn=lambda d: d["amortization"],
    ),
    RoiSensorDescription(
        key=SENSOR_ROI_PERCENT,
        translation_key=SENSOR_ROI_PERCENT,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:chart-line",
        value_fn=lambda d: d["roi"],
    ),
    RoiSensorDescription(
        key=SENSOR_YEARLY_ESTIMATE,
        translation_key=SENSOR_YEARLY_ESTIMATE,
        device_class=SensorDeviceClass.MONETARY,
        icon="mdi:calendar-range",
        currency=True,
        value_fn=lambda d: d["yearly_estimate"],
    ),
    RoiSensorDescription(
        key=SENSOR_BREAKEVEN_DATE,
        translation_key=SENSOR_BREAKEVEN_DATE,
        device_class=SensorDeviceClass.DATE,
        icon="mdi:calendar-check",
        value_fn=lambda d: _date(d["breakeven_date"]),
    ),
    RoiSensorDescription(
        key=SENSOR_SELF_KWH,
        translation_key=SENSOR_SELF_KWH,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:home-lightning-bolt-outline",
        value_fn=lambda d: d["self_kwh"],
    ),
    RoiSensorDescription(
        key=SENSOR_EXPORT_KWH,
        translation_key=SENSOR_EXPORT_KWH,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:transmission-tower-export",
        value_fn=lambda d: d["export_kwh"],
        required_conf=CONF_EXPORT_SENSOR,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: RoiConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    cfg = coordinator.config
    descriptions = [
        d for d in SENSOR_DESCRIPTIONS if d.required_conf is None or cfg.get(d.required_conf)
    ]

    # Entitäten, die es nicht mehr gibt (v1 hatte 16 Sensoren, oder ein Sensor
    # wurde abgewählt), aus der Registry entfernen statt „nicht verfügbar“ zu zeigen.
    wanted = {f"{entry.entry_id}_{d.key}" for d in descriptions}
    ent_reg = er.async_get(hass)
    for reg_entry in er.async_entries_for_config_entry(ent_reg, entry.entry_id):
        if reg_entry.unique_id not in wanted:
            ent_reg.async_remove(reg_entry.entity_id)

    async_add_entities(RoiSensor(coordinator, entry, d) for d in descriptions)


class RoiSensor(CoordinatorEntity[RoiTrackerCoordinator], SensorEntity):
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
        if description.currency:
            self._attr_native_unit_of_measurement = coordinator.hass.config.currency
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="ROI Tracker",
            model="PV-Amortisation",
        )

    @property
    def native_value(self) -> Any:
        if not self.coordinator.data:
            return None
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict | None:
        data = self.coordinator.data
        if self.entity_description.key != SENSOR_TOTAL_RETURN or not data:
            return None
        return {
            "investment": data["investment"],
            "data_since": data["data_since"],
            "daily_average": data["daily_average"],
            "month_total": data["month"]["total"],
            "month_forecast": data["month_forecast"],
            "today_total": data["today"]["total"],
            "avg_price": data["avg_price"],
            "years_to_breakeven": data["years_to_breakeven"],
            "projection_provisional": data["projection_provisional"],
        }
