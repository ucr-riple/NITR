from __future__ import annotations

import os


class Tmp26Sensor:
    def read_temperature(self) -> float:
        env_temp = os.getenv("TMP26_SIMULATOR_TEMP")
        if env_temp is not None:
            return float(env_temp)
        return 22.5
