from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Optional

from aiohttp import ClientSession, ClientResponseError

from .const import BASE_URL, UA_CHROME


@dataclass
class SolarZAuth:
    token: str


class SolarZApi:
    def __init__(self, session: ClientSession) -> None:
        self._session = session
        self._token: Optional[str] = None

    def _headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": UA_CHROME,
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    async def authenticate(self, username: str, password: str) -> SolarZAuth:
        url = f"{BASE_URL}/cliente/authenticate"
        payload = {"username": username, "password": password}

        async with self._session.post(url, json=payload, headers=self._headers()) as resp:
            resp.raise_for_status()
            data = await resp.json()

        token = data.get("token")
        if not token:
            raise ClientResponseError(
                request_info=resp.request_info,
                history=resp.history,
                status=resp.status,
                message="Token not found in authenticate response",
                headers=resp.headers,
            )

        self._token = token
        return SolarZAuth(token=token)

    async def get_status(self, plant_id: int) -> Dict[str, Any]:
        url = f"{BASE_URL}/shareable/currently/usina"
        params = {"id": plant_id}
        async with self._session.get(url, params=params, headers=self._headers()) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def get_generation_day(self, plant_id: int, day: date, unite_portals: bool = True) -> Dict[str, Any]:
        url = f"{BASE_URL}/api-sz/generation/day"
        params = {
            "usinaId": plant_id,
            "day": day.isoformat(),
            "unitePortals": str(unite_portals).lower(),
        }
        async with self._session.get(url, params=params, headers=self._headers()) as resp:
            resp.raise_for_status()
            return await resp.json()
    async def get_client_context(self) -> Dict[str, Any]:
        url = f"{BASE_URL}/cliente/context"
        async with self._session.get(url, headers=self._headers()) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def list_plants(self) -> list[dict]:
        """Retorna lista de usinas do /cliente/context no formato bruto."""
        ctx = await self.get_client_context()
        usinas = ctx.get("usinas") or []
        # cada item costuma ter id, uuid, nome/descricao (varia), etc.
        return usinas
