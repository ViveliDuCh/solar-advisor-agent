"""DeviceAdapter interface.

Any real inverter integration (SolarEdge, Enphase, SMA, ...) implements this
same Protocol, so Maintenance/Notification agents never know whether they're
talking to a simulator or real hardware. See docs/ARCHITECTURE.md section 5.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass
class Telemetry:
    timestamp: datetime
    power_w: float
    panel_id: str | None = None
    fault_code: str | None = None


class DeviceAdapter(Protocol):
    async def get_current_telemetry(self) -> list[Telemetry]: ...

    async def get_expected_power_w(self, timestamp: datetime) -> float:
        """Expected power at this timestamp per solar_output_skill, for
        comparison against actual telemetry to flag underperformance."""
        ...
