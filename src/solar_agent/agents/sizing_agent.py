"""Sizing Agent: helps new users figure out how many panels they need."""

from __future__ import annotations

from agent_framework import Agent, SupportsChatGetResponse

from solar_agent.agent_client import create_chat_client
from solar_agent.skills.sizing_skill import estimate_panels_needed

INSTRUCTIONS = """
You help non-engineer homeowners figure out how many solar panels they need.
Always call the estimate_panels_needed tool to do the math - never compute
watt/kWh numbers yourself. Explain results in plain language, include the
tool's `explanation` field, and ask for any missing input (average daily kWh
usage, peak sun hours for their location, or a bill/location you can derive
those from) before estimating. This is an educational energy estimate, not
an electrical or structural design. Do not provide string layouts, wire or
breaker sizes, rooftop instructions, interconnection steps, or permission to
install. Direct the user to qualified local professionals for those decisions.
"""


def build_sizing_agent(client: SupportsChatGetResponse | None = None) -> Agent:
    return Agent(
        client=client or create_chat_client(),
        name="SizingAgent",
        description="Explains educational panel sizing estimates for new users.",
        instructions=INSTRUCTIONS,
        tools=[estimate_panels_needed],
        require_per_service_call_history_persistence=True,
    )
