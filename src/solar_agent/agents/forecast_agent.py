"""Forecast/Optimization Agent: hourly output + appliance-timing suggestions."""

from __future__ import annotations

from agent_framework import Agent, SupportsChatGetResponse

from solar_agent.agent_client import create_chat_client
from solar_agent.skills.appliance_scheduler_skill import suggest_appliance_windows
from solar_agent.skills.solar_output_skill import estimate_hourly_output
from solar_agent.skills.weather_forecast_skill import get_hourly_forecast

INSTRUCTIONS = """
You turn a weather forecast into concrete hour-by-hour solar output and
appliance-timing advice for a household (e.g. "run the dishwasher at 1pm,
you'll get ~80% of its power from solar that hour").

Always call get_hourly_forecast first, then estimate_hourly_output with the
household's explicit panel wattage, tilt, azimuth, inverter limit, and loss
assumption, then suggest_appliance_windows with an explicit appliance list.
If any required value is absent, ask the user rather than using a hidden
default. Report the P10/P50/P90 range, not a single number, and say plainly
that estimates get less certain further into the future. Never invent
wattage or irradiance figures yourself.
"""


def build_forecast_agent(client: SupportsChatGetResponse | None = None) -> Agent:
    return Agent(
        client=client or create_chat_client(),
        name="ForecastAgent",
        description="Forecasts solar output and recommends appliance timing.",
        instructions=INSTRUCTIONS,
        tools=[get_hourly_forecast, estimate_hourly_output, suggest_appliance_windows],
        require_per_service_call_history_persistence=True,
    )
