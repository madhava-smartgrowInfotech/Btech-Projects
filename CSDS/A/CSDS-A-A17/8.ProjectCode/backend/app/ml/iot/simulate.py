"""Simulated storage / transport sensor stream.

There is no physical sensor hardware in this project, so readings are
generated as a bounded random walk per shipment (seeded, so each
shipment has a stable "personality") with occasional injected anomalies
-- a cold-chain breach or a rough-handling shock event -- which the
dashboard surfaces as alerts. This keeps the live-monitoring UI honest
about being a simulation while still exercising a real streaming path
(WebSocket + history table) end to end.
"""

from __future__ import annotations

import random

SAFE_TEMP_RANGE = (2.0, 8.0)  # cold-chain target for perishables, C
SAFE_HUMIDITY_RANGE = (55.0, 75.0)
SHOCK_ALERT_THRESHOLD = 2.4  # g


class ShipmentSensorState:
    def __init__(self, seed: int):
        self._rng = random.Random(seed)
        self.temperature_c = self._rng.uniform(3.0, 6.0)
        self.humidity_pct = self._rng.uniform(58.0, 68.0)
        self.shock_g = 0.1
        self._anomaly_countdown = self._rng.randint(18, 40)

    def step(self) -> dict:
        self.temperature_c += self._rng.uniform(-0.35, 0.35)
        self.humidity_pct += self._rng.uniform(-1.2, 1.2)
        self.shock_g = max(0.0, self._rng.gauss(0.3, 0.25))

        self._anomaly_countdown -= 1
        is_anomaly = False
        if self._anomaly_countdown <= 0:
            kind = self._rng.choice(["temp_spike", "humidity_spike", "shock"])
            if kind == "temp_spike":
                self.temperature_c += self._rng.uniform(4.0, 8.0)
            elif kind == "humidity_spike":
                self.humidity_pct += self._rng.uniform(12.0, 20.0)
            else:
                self.shock_g += self._rng.uniform(2.2, 4.0)
            is_anomaly = True
            self._anomaly_countdown = self._rng.randint(25, 55)

        self.temperature_c = max(-5.0, min(35.0, self.temperature_c))
        self.humidity_pct = max(20.0, min(98.0, self.humidity_pct))

        out_of_range = not (SAFE_TEMP_RANGE[0] - 1.5 <= self.temperature_c <= SAFE_TEMP_RANGE[1] + 1.5) or not (
            SAFE_HUMIDITY_RANGE[0] - 8 <= self.humidity_pct <= SAFE_HUMIDITY_RANGE[1] + 8
        )
        is_anomaly = is_anomaly or out_of_range or self.shock_g >= SHOCK_ALERT_THRESHOLD

        return {
            "temperature_c": round(self.temperature_c, 2),
            "humidity_pct": round(self.humidity_pct, 2),
            "shock_g": round(self.shock_g, 2),
            "is_anomaly": is_anomaly,
        }
