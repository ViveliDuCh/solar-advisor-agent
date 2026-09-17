"""Rule-based (no-LLM) reply generators for the demo web UI.

Each function calls the real deterministic skills and formats a plain-
language reply, mirroring what the corresponding LLM agent in
solar_agent.agents is instructed to do - so the demo UI shows genuine
computed numbers even with zero API keys configured.
"""
from __future__ import annotations

import json
from pathlib import Path

from solar_agent.adapters.simulated_inverter_adapter import SimulatedInverterAdapter
from solar_agent.agents.safety_agent import SAFETY_REFERENCE_NOTES
from solar_agent.skills.appliance_scheduler_skill import suggest_appliance_windows
from solar_agent.skills.sizing_skill import estimate_panels_needed
from solar_agent.skills.solar_output_skill import estimate_hourly_output
from solar_agent.skills.tariff_payback_skill import estimate_payback
from solar_agent.skills.weather_forecast_skill import get_hourly_forecast

_DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def load_sample_user() -> dict:
    with open(_DATA_DIR / "sample_user.json", encoding="utf-8") as f:
        return json.load(f)


async def sizing_reply(user_message: str, household: dict) -> str:
    forecast = await get_hourly_forecast(
        lat=household["user"]["lat"], lon=household["user"]["lon"], hours=24
    )
    daylight = [h for h in forecast if h["ghi_w_m2"] > 0]
    peak_sun_hours = (sum(h["ghi_w_m2"] for h in daylight) / 1000.0) if daylight else 4.0

    result = estimate_panels_needed(
        avg_daily_consumption_kwh=household["consumption"]["avg_daily_kwh"],
        peak_sun_hours=max(peak_sun_hours, 2.5),
        panel_rated_w=household["existing_system"]["panel_rated_w"],
    )
    return (
        f"For {household['user']['name']} in {household['user']['location_label']} "
        f"(~{household['consumption']['avg_daily_kwh']:.0f} kWh/day, "
        f"~{peak_sun_hours:.1f} peak sun hours today):\n\n"
        f"**{result['panels_needed']} panels** ({result['total_system_w']:.0f}W total) "
        f"would offset that usage.\n\n{result['explanation']}\n\n"
        "DIY note: panel mounting/wiring on the DC side and grid interconnection "
        "require a licensed electrician and utility permit in virtually all US "
        "jurisdictions - see the Safety agent for details."
    )


async def forecast_reply(user_message: str, household: dict) -> str:
    forecast = await get_hourly_forecast(
        lat=household["user"]["lat"], lon=household["user"]["lon"], hours=12
    )
    total_w = household["existing_system"]["panel_count"] * household["existing_system"]["panel_rated_w"]
    hourly = estimate_hourly_output(
        panel_rated_w=total_w,
        hourly_forecast=forecast,
        panel_tilt_deg=household["roof"]["tilt_deg"],
        panel_azimuth_deg=household["roof"]["azimuth_deg"],
    )
    suggestions = suggest_appliance_windows(hourly, household["appliances"], top_n_windows=1)

    best_hour = max(hourly, key=lambda h: h["p50_w"])
    lines = [
        f"Next 12h for your {total_w:.0f}W system: peak output ~{best_hour['p50_w']:.0f}W "
        f"(range {best_hour['p10_w']:.0f}-{best_hour['p90_w']:.0f}W) around {best_hour['timestamp']}.",
        "",
        "Best times to run appliances:",
    ]
    for s in suggestions:
        if s["recommended_windows"]:
            w = s["recommended_windows"][0]
            lines.append(
                f"- {s['appliance'].replace('_', ' ').title()}: around {w['timestamp']} "
                f"(~{w['solar_coverage_pct']:.0f}% covered by solar)"
            )
    return "\n".join(lines)


async def maintenance_reply(user_message: str, household: dict) -> str:
    total_w = household["existing_system"]["panel_count"] * household["existing_system"]["panel_rated_w"]
    adapter = SimulatedInverterAdapter(panel_rated_w=total_w)
    readings = await adapter.get_current_telemetry()
    reading = readings[0]
    expected_w = await adapter.get_expected_power_w(reading.timestamp)
    shortfall_pct = max(0.0, (expected_w - reading.power_w) / expected_w * 100.0) if expected_w > 0 else 0.0

    if reading.fault_code or shortfall_pct > 20.0:
        return (
            f"⚠️ Your system is producing {reading.power_w:.0f}W vs. an expected "
            f"~{expected_w:.0f}W ({shortfall_pct:.0f}% shortfall)"
            + (f", flagged as **{reading.fault_code}**." if reading.fault_code else ".")
            + " Common causes: soiling (dust/pollen) or partial shading - check for "
            "shadows from new tree growth or debris. If cleaning doesn't help within "
            "a few days, contact a licensed installer; do not open the inverter enclosure yourself."
        )
    return (
        f"✅ Producing {reading.power_w:.0f}W vs. an expected ~{expected_w:.0f}W - "
        "within normal range, no maintenance needed right now."
    )


async def financial_reply(user_message: str, household: dict) -> str:
    total_w = household["existing_system"]["panel_count"] * household["existing_system"]["panel_rated_w"]
    # Rough annual estimate from a representative peak-sun-hours figure; a full
    # implementation would sum a year of hourly estimates.
    annual_kwh = (total_w / 1000.0) * 4.2 * 365 * 0.8
    result = estimate_payback(
        tariff_profile_id=household["tariff_profile_id"],
        system_cost_usd=household["system_cost_usd"],
        estimated_annual_generation_kwh=annual_kwh,
    )
    return (
        f"Estimated **{annual_kwh:.0f} kWh/year** from your {total_w:.0f}W system.\n\n"
        f"{result['explanation']}"
    )


_SAFETY_KEYWORDS = {
    "battery": 1,
    "batteries": 1,
    "toxic": 1,
    "diy": 0,
    "electrician": 0,
    "clean": 2,
    "cleaning": 2,
    "shock": 2,
}


async def safety_reply(user_message: str, household: dict) -> str:
    lowered = user_message.lower()
    idx = next((i for kw, i in _SAFETY_KEYWORDS.items() if kw in lowered), None)
    if idx is not None:
        return SAFETY_REFERENCE_NOTES[idx]
    return " ".join(SAFETY_REFERENCE_NOTES)


REPLY_FUNCS = {
    "sizing": sizing_reply,
    "forecast": forecast_reply,
    "maintenance": maintenance_reply,
    "financial": financial_reply,
    "safety": safety_reply,
}
