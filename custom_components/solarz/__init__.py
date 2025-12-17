from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SolarZApi
from .const import DOMAIN, CONF_USERNAME, CONF_PASSWORD, CONF_PLANT_ID
from .coordinator import SolarZCoordinator

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session = async_get_clientsession(hass)
    api = SolarZApi(session)

    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    plant_id = int(entry.data[CONF_PLANT_ID])

    coordinator = SolarZCoordinator(hass, api, username, password, plant_id)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unloaded
