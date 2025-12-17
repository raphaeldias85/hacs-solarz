from __future__ import annotations

from typing import Any, Dict, Optional

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    add_entities(
        [
            SolarZGenerationTodaySensor(coordinator),
            SolarZForecastTodaySensor(coordinator),
            SolarZStatusSensor(coordinator),
        ]
    )


class SolarZBaseSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)


class SolarZGenerationTodaySensor(SolarZBaseSensor):
    _attr_name = "Geração hoje"
    _attr_unique_id = "solarz_generation_today"
    _attr_unit_of_measurement = "kWh"
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    @property
    def native_value(self) -> float:
        data = self.coordinator.data.get("generation_day", {}) if self.coordinator.data else {}
        return float(data.get("totalGerado", 0) or 0)

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        data = self.coordinator.data.get("generation_day", {}) if self.coordinator.data else {}
        # cuidado com atributos gigantes; mantenho os principais
        return {
            "erros": data.get("erros"),
            "status": data.get("status"),
            "prognosticos": data.get("prognosticos"),
        }


class SolarZForecastTodaySensor(SolarZBaseSensor):
    _attr_name = "Previsão hoje"
    _attr_unique_id = "solarz_forecast_today"
    _attr_unit_of_measurement = "kWh"

    @property
    def native_value(self) -> float:
        data = self.coordinator.data.get("generation_day", {}) if self.coordinator.data else {}
        forecasts = data.get("prognosticos") or {}
        if isinstance(forecasts, dict) and forecasts:
            # pega o primeiro valor
            return float(next(iter(forecasts.values())) or 0)
        return 0.0


class SolarZStatusSensor(SolarZBaseSensor):
    _attr_name = "Status"
    _attr_unique_id = "solarz_status"

    @property
    def native_value(self) -> str:
        data = self.coordinator.data.get("status", {}) if self.coordinator.data else {}
        # pelo seu print, o endpoint retorna algo como dict com fields; se houver status direto, usa
        if isinstance(data, dict):
            if "status" in data and isinstance(data["status"], str):
                return data["status"]
            # se vier dict dentro, cai pra string
            return "ok"
        return "unknown"

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        return self.coordinator.data.get("status", {}) if self.coordinator.data else {}
