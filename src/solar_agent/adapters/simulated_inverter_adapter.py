"""SimulatedInverterAdapter: realistic telemetry without real hardware/OAuth.

Generates telemetry from solar_output_skill's own model plus injected noise
and occasional faults, so Maintenance/Notification agents run against a
believable stream. Swap for a RealSolarEdgeAdapter (same DeviceAdapter
interface) once vendor developer credentials are available.
"""
from __future__ import annotations

import random
from datetime import datetime, timezone

from solar_agent.adapters.device_adapter import Telemetry
from solar_agent.skills.solar_output_skill import estimate_output_w


class SimulatedInverterAdapter:
    def __init__(
        self,
        panel_rated_w: float,
        panel_tilt_deg: float = 30.0,
        panel_azimuth_deg: float = 180.0,
        fault_probability: float = 0.05,
    ) -> None:
        self.panel_rated_w = panel_rated_w
        self.panel_tilt_deg = panel_tilt_deg
        self.panel_azimuth_deg = panel_azimuth_deg
        self.fault_probability = fault_probability

    async def get_current_telemetry(
        self, irradiance_w_m2: float = 600.0, ambient_temp_c: float = 22.0
    ) -> list[Telemetry]:
        expected = estimate_output_w(
            panel_rated_w=self.panel_rated_w,
            irradiance_w_m2=irradiance_w_m2,
            ambient_temp_c=ambient_temp_c,
            panel_tilt_deg=self.panel_tilt_deg,
            panel_azimuth_deg=self.panel_azimuth_deg,
        )

        fault_code = None
        actual_w = expected.p50_w * random.uniform(0.92, 1.03)
        if random.random() < self.fault_probability:
            fault_code = random.choice(["SOILING_SUSPECTED", "PARTIAL_SHADING", "INVERTER_DERATE"])
            actual_w *= random.uniform(0.4, 0.75)

        return [
            Telemetry(
                timestamp=datetime.now(timezone.utc),
                power_w=round(actual_w, 1),
                panel_id="array-1",
                fault_code=fault_code,
            )
        ]

    async def get_expected_power_w(self, timestamp: datetime) -> float:
        # Hackathon stub: reuse a flat mid-day irradiance assumption.
        # Real implementation would look up the forecast for `timestamp`.
        est = estimate_output_w(
            panel_rated_w=self.panel_rated_w,
            irradiance_w_m2=600.0,
            ambient_temp_c=22.0,
            panel_tilt_deg=self.panel_tilt_deg,
            panel_azimuth_deg=self.panel_azimuth_deg,
        )
        return est.p50_w
