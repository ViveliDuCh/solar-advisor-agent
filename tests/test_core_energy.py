import pandas as pd

from solar_agent.core.demo import demo_appliances, demo_battery, demo_household, demo_system
from solar_agent.core.energy import (
    TIMEZONE,
    energy_flows,
    estimate_solar_power,
    household_load_profile,
    schedule_appliances,
)
from solar_agent.core.forecast import SyntheticForecastProvider
from solar_agent.core.models import ArraySection, SolarSystem


def test_demo_system_is_eight_kw() -> None:
    assert demo_system().dc_capacity_kw == 8.0


def test_energy_pipeline_produces_bounded_forecast() -> None:
    start = pd.Timestamp("2026-09-16 08:00", tz=TIMEZONE)
    weather, _ = SyntheticForecastProvider().get_hourly(start, 48)
    frame = estimate_solar_power(weather, demo_system())
    assert frame["solar_expected_kw"].min() >= 0
    assert frame["solar_expected_kw"].max() <= demo_system().inverter_ac_kw
    assert frame["solar_expected_kw"].sum() > 0


def test_scheduler_and_battery_conserve_positive_flows() -> None:
    start = pd.Timestamp("2026-09-16 08:00", tz=TIMEZONE)
    weather, _ = SyntheticForecastProvider().get_hourly(start, 48)
    frame = estimate_solar_power(weather, demo_system())
    frame["base_load_kw"] = household_load_profile(frame.index, demo_household())
    scheduled, recommendations = schedule_appliances(frame, demo_appliances())
    assert recommendations
    flows = energy_flows(
        frame["solar_expected_kw"],
        frame["base_load_kw"] + scheduled,
        demo_battery(),
    )
    assert all(value >= 0 for value in flows.values())


def test_mixed_panel_sections_are_combined() -> None:
    system = SolarSystem(
        sections=(
            ArraySection(panel_count=10, panel_watts=400),
            ArraySection(panel_count=4, panel_watts=430, azimuth_degrees=225),
        )
    )
    assert system.panel_count == 14
    assert system.dc_capacity_kw == 5.72


def test_high_draw_appliances_do_not_overlap() -> None:
    start = pd.Timestamp("2026-09-16 08:00", tz=TIMEZONE)
    weather, _ = SyntheticForecastProvider().get_hourly(start, 48)
    frame = estimate_solar_power(weather, demo_system())
    frame["base_load_kw"] = household_load_profile(frame.index, demo_household())
    scheduled, _ = schedule_appliances(frame, demo_appliances())
    assert scheduled.max() <= 7.2
