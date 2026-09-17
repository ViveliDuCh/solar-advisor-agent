from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class ArraySection:
    panel_count: int = 20
    panel_watts: int = 400
    tilt_degrees: float = 30.0
    azimuth_degrees: float = 180.0
    shading_percent: float = 5.0

    @property
    def dc_capacity_kw(self) -> float:
        return self.panel_count * self.panel_watts / 1000


@dataclass(frozen=True)
class SolarSystem:
    sections: tuple[ArraySection, ...] = field(
        default_factory=lambda: (ArraySection(),)
    )
    inverter_ac_kw: float = 7.6
    other_losses_percent: float = 9.0

    @property
    def dc_capacity_kw(self) -> float:
        return sum(section.dc_capacity_kw for section in self.sections)

    @property
    def panel_count(self) -> int:
        return sum(section.panel_count for section in self.sections)

    def section_losses_fraction(self, section: ArraySection) -> float:
        total = section.shading_percent + self.other_losses_percent
        return min(max(total / 100, 0), 0.9)


@dataclass(frozen=True)
class Household:
    zip_code: str = "98052"
    annual_consumption_kwh: float = 10_800
    occupants: int = 2
    work_from_home: bool = True


@dataclass(frozen=True)
class Appliance:
    name: str
    power_kw: float
    duration_hours: float
    earliest_hour: int
    latest_hour: int
    flexible: bool = True

    @property
    def energy_kwh(self) -> float:
        return self.power_kw * self.duration_hours


@dataclass(frozen=True)
class Battery:
    usable_capacity_kwh: float = 10.0
    max_power_kw: float = 5.0
    round_trip_efficiency: float = 0.90
    reserve_fraction: float = 0.20


@dataclass(frozen=True)
class ForecastMetadata:
    provider: str
    mode: str
    initialized_at: datetime
    generated_at: datetime
    is_live: bool
    limitations: list[str] = field(default_factory=list)
