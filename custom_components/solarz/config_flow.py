from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SolarZApi
from .const import (
    DOMAIN,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_PLANT_ID,
    CONF_PLANT_UUID,
    CONF_PLANT_NAME,
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._username: str | None = None
        self._password: str | None = None
        self._plants: list[dict] | None = None

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            self._username = user_input[CONF_USERNAME]
            self._password = user_input[CONF_PASSWORD]

            try:
                api = SolarZApi(async_get_clientsession(self.hass))
                await api.authenticate(self._username, self._password)
                self._plants = await api.list_plants()
            except Exception:
                errors["base"] = "cannot_connect"
            else:
                if not self._plants:
                    errors["base"] = "no_plants"
                else:
                    return await self.async_step_select_plant()

        schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_select_plant(self, user_input=None):
        errors = {}

        assert self._username is not None
        assert self._password is not None
        assert self._plants is not None

        # Monta opções: "ID - Nome"
        options: dict[str, str] = {}
        for p in self._plants:
            pid = p.get("id")
            puuid = p.get("uuid")
            # tenta vários campos de nome comuns
            pname = (
                p.get("nome")
                or p.get("name")
                or p.get("descricao")
                or p.get("description")
                or f"Planta {pid}"
            )
            if pid is None:
                continue
            key = str(pid)
            options[key] = f"{pid} — {pname}"

        if user_input is not None:
            selected_id = int(user_input[CONF_PLANT_ID])

            selected = next((p for p in self._plants if int(p.get("id", -1)) == selected_id), None)
            if not selected:
                errors["base"] = "invalid_plant"
            else:
                plant_uuid = selected.get("uuid") or ""
                plant_name = (
                    selected.get("nome")
                    or selected.get("name")
                    or selected.get("descricao")
                    or selected.get("description")
                    or f"Planta {selected_id}"
                )

                # Permite múltiplas entries (uma por planta). Unique ID por planta.
                await self.async_set_unique_id(f"{DOMAIN}_{selected_id}")
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"SolarZ — {plant_name} ({selected_id})",
                    data={
                        CONF_USERNAME: self._username,
                        CONF_PASSWORD: self._password,
                        CONF_PLANT_ID: selected_id,
                        CONF_PLANT_UUID: plant_uuid,
                        CONF_PLANT_NAME: plant_name,
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_PLANT_ID): vol.In(options)
            }
        )
        return self.async_show_form(step_id="select_plant", data_schema=schema, errors=errors)
