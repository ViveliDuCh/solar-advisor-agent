"""Forecast/Optimization Agent: hourly output + appliance-timing suggestions."""
from __future__ import annotations

from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient

from solar_agent.skills.appliance_scheduler_skill import suggest_appliance_windows
from solar_agent.skills.solar_output_skill import estimate_hourly_output
from solar_agent.skills.weather_forecast_skill import get_hourly_forecast

INSTRUCTIONS = """
You turn a weather forecast into concrete hour-by-hour solar output and
appliance-timing advice for a household (e.g. "run the dishwasher at 1pm,
you'll get ~80% of its power from solar that hour").

Always call get_hourly_forecast first, then estimate_hourly_output with the
household's panel wattage/tilt/azimuth, then suggest_appliance_windows with
their appliance list. Report the P10/P50/P90 range, not a single number, and
say plainly that estimates get less certain further into the future. Never
invent wattage or irradiance figures yourself.
"""


def build_forecast_agent(client: OpenAIChatClient | None = None) -> Agent:
    return Agent(
        client=client or OpenAIChatClient(),
        name="ForecastAgent",
        instructions=INSTRUCTIONS,
        tools=[get_hourly_forecast, estimate_hourly_output, suggest_appliance_windows],
    )
