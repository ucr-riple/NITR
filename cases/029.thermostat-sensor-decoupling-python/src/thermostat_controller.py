from __future__ import annotations

from enum import Enum


class Command(Enum):
    HEATING = "Heating"
    COOLING = "Cooling"
    IDLE = "Idle"


class ThermostatController:
    TEMPERATURE_DELTA_THRESHOLD = 2.0

    def __init__(self, target_temperature: float) -> None:
        self._target_temperature = target_temperature

    def evaluate(self, current_temperature: float) -> Command:
        if current_temperature <= (
            self._target_temperature - self.TEMPERATURE_DELTA_THRESHOLD
        ):
            return Command.HEATING
        if current_temperature >= (
            self._target_temperature + self.TEMPERATURE_DELTA_THRESHOLD
        ):
            return Command.COOLING
        return Command.IDLE

    def target_temperature(self) -> float:
        return self._target_temperature
