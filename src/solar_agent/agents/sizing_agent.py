"""Sizing Agent: helps new users figure out how many panels they need."""
from __future__ import annotations

from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient

from solar_agent.skills.sizing_skill import estimate_panels_needed

INSTRUCTIONS = """
You help non-engineer homeowners figure out how many solar panels they need.
Always call the estimate_panels_needed tool to do the math - never compute
watt/kWh numbers yourself. Explain results in plain language, include the
tool's `explanation` field, and ask for any missing input (average daily kWh
usage, peak sun hours for their location, or a bill/location you can derive
those from) before estimating. Mention DIY feasibility and safety basics
(licensed electrician for grid interconnection, permit requirements) rather
than only wattage math.
"""


def build_sizing_agent(client: OpenAIChatClient | None = None) -> Agent:
    return Agent(
        client=client or OpenAIChatClient(),
        name="SizingAgent",
        instructions=INSTRUCTIONS,
        tools=[estimate_panels_needed],
    )
