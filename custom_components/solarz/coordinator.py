from __future__ import annotations

from datetime import timedelta, date
from typing import Any, Dict

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import SolarZApi
from .const import DEFAULT_SCAN_SECONDS, DOMAIN


class SolarZCoordinator(DataUpdateCoordinator[Dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, api: SolarZApi, username: str, password: str, plant_id: int) -> None:
        super().__init__(
            hass,
            logger=__import__("logging").getLogger(__name__),
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_SECONDS),
        )
        self._api = api
        self._username = username
        self._password = password
        self._plant_id = plant_id

    async def _async_update_data(self) -> Dict[str, Any]:
        try:
            # reautentica sempre antes (simples e robusto)
            await self._api.authenticate(self._username, self._password)

            status = await self._api.get_status(self._plant_id)
            gen_day = await self._api.get_generation_day(self._plant_id, date.today(), unite_portals=True)

            return {
                "status": status,
                "generation_day": gen_day,
            }
        except Exception as err:
            raise UpdateFailed(str(err)) from err
