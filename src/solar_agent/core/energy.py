from __future__ import annotations

import math

import numpy as np
import pandas as pd
from pvlib import irradiance, location, pvsystem, temperature

from solar_agent.core.models import Appliance, ArraySection, Battery, Household, SolarSystem

REDMOND_LATITUDE = 47.6740
REDMOND_LONGITUDE = -122.1215
TIMEZONE = "America/Los_Angeles"


def estimate_solar_power(weather: pd.DataFrame, system: SolarSystem) -> pd.DataFrame:
    site = location.Location(REDMOND_LATITUDE, REDMOND_LONGITUDE, tz=TIMEZONE)
    solar_position = site.get_solarposition(weather.index)
    ghi = weather["ghi_wm2"].clip(lower=0)
    erbs = irradiance.erbs(ghi, solar_position["zenith"], weather.index)
    dc_after_losses = pd.Series(0.0, index=weather.index)
    for section in system.sections:
        dc_after_losses += _section_dc_power(
            weather,
            solar_position,
            ghi,
            erbs,
            section,
            system.section_losses_fraction(section),
        )

    ac_watts = pvsystem.inverter.pvwatts(
        dc_after_losses,
        pdc0=system.inverter_ac_kw * 1000 / 0.96,
        eta_inv_nom=0.96,
    )
    expected_kw = pd.Series(ac_watts, index=weather.index).clip(lower=0) / 1000

    output = weather.copy()
    output["solar_expected_kw"] = expected_kw
    output["solar_low_kw"] = expected_kw * 0.78
    output["solar_high_kw"] = np.minimum(expected_kw * 1.18, system.inverter_ac_kw)
    return output


def _section_dc_power(
    weather: pd.DataFrame,
    solar_position: pd.DataFrame,
    ghi: pd.Series,
    erbs: pd.DataFrame,
    section: ArraySection,
    losses_fraction: float,
) -> pd.Series:
    poa = irradiance.get_total_irradiance(
        surface_tilt=section.tilt_degrees,
        surface_azimuth=section.azimuth_degrees,
        solar_zenith=solar_position["apparent_zenith"],
        solar_azimuth=solar_position["azimuth"],
        dni=erbs["dni"].fillna(0),
        ghi=ghi,
        dhi=erbs["dhi"].fillna(0),
    )["poa_global"].fillna(0)
    cell_temperature = temperature.faiman(
        poa,
        weather["temperature_c"],
        weather["wind_speed_ms"],
    )
    dc_watts = pvsystem.pvwatts_dc(
        poa,
        cell_temperature,
        pdc0=section.dc_capacity_kw * 1000,
        gamma_pdc=-0.004,
    )
    return pd.Series(dc_watts, index=weather.index) * (1 - losses_fraction)


def household_load_profile(
    index: pd.DatetimeIndex,
    household: Household,
    flexible_energy_kwh: float = 0.0,
) -> pd.Series:
    period_days = len(index) / 24
    expected_period_energy = household.annual_consumption_kwh / 365 * period_days
    nonflexible_energy = max(
        expected_period_energy - flexible_energy_kwh,
        expected_period_energy * 0.35,
    )
    hourly_target = nonflexible_energy / len(index)
    hour = index.hour.to_numpy()
    morning = 0.75 * np.exp(-((hour - 7) / 2.1) ** 2)
    evening = 1.25 * np.exp(-((hour - 19) / 2.8) ** 2)
    overnight = 0.40
    daytime = 0.28 + (0.22 if household.work_from_home else 0)
    shape = overnight + daytime + morning + evening
    shape = shape / shape.mean() * hourly_target
    return pd.Series(shape, index=index, name="estimated_nonflexible_load_kw")


def schedule_appliances(
    frame: pd.DataFrame,
    appliances: list[Appliance],
) -> tuple[pd.Series, list[dict[str, object]]]:
    scheduled = pd.Series(0.0, index=frame.index, name="scheduled_appliance_kw")
    recommendations: list[dict[str, object]] = []
    surplus = frame["solar_expected_kw"] - frame["base_load_kw"]

    for appliance in sorted(appliances, key=lambda item: item.power_kw, reverse=True):
        candidate_positions: list[tuple[float, int]] = []
        slots = max(1, math.ceil(appliance.duration_hours))
        for position in range(0, len(frame) - slots + 1):
            window = frame.index[position : position + slots]
            if window[0].hour < appliance.earliest_hour or window[-1].hour > appliance.latest_hour:
                continue
            selection = slice(position, position + slots)
            available = surplus.iloc[selection] - scheduled.iloc[selection]
            # High-draw flexible loads are scheduled sequentially. This is an optimization
            # policy, not a circuit-capacity determination.
            if appliance.power_kw >= 1.5 and scheduled.iloc[selection].max() >= 1.5:
                continue
            solar_coverage = np.minimum(
                np.maximum(available.to_numpy(), 0),
                appliance.power_kw,
            ).sum()
            inconvenience = abs(window[0].hour - 13) * 0.03
            candidate_positions.append((float(solar_coverage - inconvenience), position))

        if not candidate_positions:
            continue
        _, best_position = max(candidate_positions)
        window = frame.index[best_position : best_position + slots]
        scheduled.loc[window] += appliance.power_kw
        available_at_start = max(float(surplus.iloc[best_position]), 0)
        recommendations.append(
            {
                "appliance": appliance.name,
                "start": window[0],
                "end": window[-1] + pd.Timedelta(hours=1),
                "energy_kwh": appliance.energy_kwh,
                "expected_solar_coverage_kwh": min(
                    appliance.energy_kwh,
                    available_at_start * appliance.duration_hours,
                ),
                "confidence": "medium",
                "safety_note": (
                    "Available solar does not prove that a circuit can carry this appliance. "
                    "In a grid-connected home, the grid supplies any shortfall. Use only an "
                    "existing properly installed circuit and follow the appliance instructions."
                ),
            }
        )
    return scheduled, recommendations


def energy_flows(
    solar_kw: pd.Series,
    load_kw: pd.Series,
    battery: Battery | None = None,
) -> dict[str, float]:
    flows = {
        "solar_to_home": 0.0,
        "solar_to_grid": 0.0,
        "solar_to_battery": 0.0,
        "battery_to_home": 0.0,
        "grid_to_home": 0.0,
    }
    state_of_charge = battery.usable_capacity_kwh * 0.5 if battery else 0.0
    reserve = battery.usable_capacity_kwh * battery.reserve_fraction if battery else 0.0
    charge_efficiency = math.sqrt(battery.round_trip_efficiency) if battery else 1.0

    for solar, load in zip(solar_kw, load_kw, strict=True):
        direct = min(solar, load)
        flows["solar_to_home"] += direct
        surplus = max(solar - direct, 0)
        deficit = max(load - direct, 0)

        if battery:
            charge_input = min(
                surplus,
                battery.max_power_kw,
                max((battery.usable_capacity_kwh - state_of_charge) / charge_efficiency, 0),
            )
            state_of_charge += charge_input * charge_efficiency
            flows["solar_to_battery"] += charge_input
            surplus -= charge_input

            discharge = min(
                deficit,
                battery.max_power_kw,
                max(state_of_charge - reserve, 0) * charge_efficiency,
            )
            state_of_charge -= discharge / charge_efficiency
            flows["battery_to_home"] += discharge
            deficit -= discharge

        flows["solar_to_grid"] += surplus
        flows["grid_to_home"] += deficit

    return {key: round(value, 2) for key, value in flows.items()}


def opportunity_score(frame: pd.DataFrame) -> pd.Series:
    surplus = frame["solar_expected_kw"] - frame["base_load_kw"]
    confidence_width = frame["solar_high_kw"] - frame["solar_low_kw"]
    raw = surplus - confidence_width * 0.15
    denominator = max(float(raw.max() - raw.min()), 0.1)
    return ((raw - raw.min()) / denominator * 100).clip(0, 100)
