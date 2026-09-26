"""ROI Tracker – Ersparnis, Einspeiseertrag und Amortisation einer PV-Anlage."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import (
    CONF_BATTERY_DISCHARGE_SENSOR,
    CONF_CONSUMPTION_SENSOR,
    CONF_EXPORT_SENSOR,
    CONF_FEED_IN_TARIFF,
    CONF_INVESTMENT,
    CONF_MODE,
    CONF_NAME,
    CONF_PRICE_FIXED,
    CONF_PRICE_SENSOR,
    CONF_START_DATE,
    ENERGY_SENSOR_KEYS,
    MODE_DIRECT,
    STORAGE_KEY,
    STORAGE_VERSION,
)
from .coordinator import RoiTrackerCoordinator
from .frontend import async_register_card
from .services import async_setup_services, async_unload_services
from .websocket import async_register_websocket

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

type RoiConfigEntry = ConfigEntry[RoiTrackerCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: RoiConfigEntry) -> bool:
    """Richtet eine Anlage anhand des ConfigEntry ein."""
    await async_register_card(hass)
    async_register_websocket(hass)

    coordinator = RoiTrackerCoordinator(hass, entry)
    await coordinator.async_load()
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    async_setup_services(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: RoiConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        async_unload_services(hass, exclude=entry.entry_id)
    return unloaded


async def async_remove_entry(hass: HomeAssistant, entry: RoiConfigEntry) -> None:
    """Gespeicherte Tageswerte beim Löschen der Anlage entfernen."""
    await Store(hass, STORAGE_VERSION, STORAGE_KEY.format(entry_id=entry.entry_id)).async_remove()


async def _async_update_listener(hass: HomeAssistant, entry: RoiConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """v1 (Vorlagen, Delta-Rechnung) → v2 (Statistik-Rechnung).

    v1 erwartete einen reinen PV-Eigenverbrauchs-Sensor (+ optional Batterie-
    Entladung) → das entspricht der Berechnungsart „direct“. Der Netzbezug war
    in v1 nur Anzeige und wird nicht übernommen.
    """
    if entry.version > 2:
        return False
    if entry.version == 1:
        old = {**entry.data, **entry.options}
        new: dict = {k: None for k in ENERGY_SENSOR_KEYS}
        new.update(
            {
                CONF_NAME: old.get(CONF_NAME) or entry.title,
                CONF_INVESTMENT: old.get(CONF_INVESTMENT, 0),
                CONF_START_DATE: old.get(CONF_START_DATE) or None,
                CONF_MODE: MODE_DIRECT,
                CONF_CONSUMPTION_SENSOR: old.get(CONF_CONSUMPTION_SENSOR),
                CONF_BATTERY_DISCHARGE_SENSOR: old.get(CONF_BATTERY_DISCHARGE_SENSOR),
                CONF_EXPORT_SENSOR: old.get(CONF_EXPORT_SENSOR),
                CONF_PRICE_SENSOR: None,
                CONF_PRICE_FIXED: None,
                CONF_FEED_IN_TARIFF: (
                    old.get(CONF_FEED_IN_TARIFF) if old.get("reward_mode", "fixed") == "fixed" else 0
                ) or 0,
            }
        )
        price_mode = old.get("price_mode", "fixed")
        if price_mode == "sensor":
            new[CONF_PRICE_SENSOR] = old.get(CONF_PRICE_SENSOR)
        elif price_mode == "fixed":
            new[CONF_PRICE_FIXED] = old.get(CONF_PRICE_FIXED)
        if old.get("baseline_rate") not in (None, ""):
            new[CONF_PRICE_FIXED] = old.get("baseline_rate")
        if not new[CONF_PRICE_SENSOR] and new[CONF_PRICE_FIXED] in (None, ""):
            _LOGGER.warning(
                "ROI Tracker '%s': Der bisherige Preis-Modus wird nicht mehr "
                "unterstützt. Bitte in den Optionen einen Strompreis eintragen.",
                entry.title,
            )
        if not new[CONF_START_DATE]:
            created = getattr(entry, "created_at", None)
            new[CONF_START_DATE] = created.date().isoformat() if created else None
        hass.config_entries.async_update_entry(entry, data=new, options={}, version=2)
        _LOGGER.info("ROI Tracker '%s' auf Version 2 migriert", entry.title)
    return True
