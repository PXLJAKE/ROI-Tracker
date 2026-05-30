"""ROI Tracker – universeller Return-on-Investment-Rechner für Home Assistant."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import RoiTrackerCoordinator
from .frontend import async_register_card

PLATFORMS: list[Platform] = [Platform.SENSOR]

type RoiConfigEntry = ConfigEntry[RoiTrackerCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: RoiConfigEntry) -> bool:
    """Richtet einen ROI-Rechner (eine Anlage) anhand des ConfigEntry ein."""
    # Dashboard-Karte einmalig als Frontend-Ressource registrieren.
    await async_register_card(hass)

    coordinator = RoiTrackerCoordinator(hass, entry)
    await coordinator.async_load_state()
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: RoiConfigEntry) -> bool:
    """Entlädt einen ROI-Rechner."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_update_listener(hass: HomeAssistant, entry: RoiConfigEntry) -> None:
    """Lädt den Eintrag neu, wenn Optionen geändert wurden."""
    await hass.config_entries.async_reload(entry.entry_id)
