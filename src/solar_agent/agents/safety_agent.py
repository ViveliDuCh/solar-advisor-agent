"""Safety/Education Agent: plain-language electrical safety & battery tradeoffs.

No deterministic "skill" backs this agent - it must stay grounded in a small,
vetted reference set (RAG) rather than freelancing electrical rules. The
reference content below is a placeholder; replace with vetted NEC-adjacent
guidance and manufacturer safety docs before using this for real advice.
"""
from __future__ import annotations

from agent_framework import Agent, SupportsChatGetResponse

from solar_agent.agent_client import create_chat_client

INSTRUCTIONS = """
You explain electrical safety, DIY feasibility limits, and battery-storage
tradeoffs to non-engineer homeowners in plain language. Ground every safety
claim in the reference material provided (never invent electrical code
requirements). Always flag when a task requires a licensed electrician
(anything past the AC disconnect / grid interconnection, working on live DC
combiner wiring, roof-mounting work). When discussing batteries, cover cost,
thermal/toxicity handling, and cycle-life tradeoffs honestly rather than
oversimplifying - the app pitches "skip the battery" savings, so batteries
must still get an unbiased explanation when asked about.
"""

# Conservative demo boundaries. Replace with a vetted, cited knowledge source.
SAFETY_REFERENCE_NOTES = [
    "Solar availability is not a circuit-capacity test. Breakers, wiring, "
    "receptacles, nameplate current, and simultaneous loads determine circuit safety.",
    "Do not open an inverter, disconnect solar DC wiring, enter a battery enclosure, "
    "or access a roof based on this application's advice.",
    "Battery comparisons must disclose usable capacity, power limits, efficiency, "
    "reserve assumptions, cost, warranty, thermal-management needs, and end-of-life handling.",
    "Follow equipment documentation and use qualified local professionals for electrical, "
    "structural, permitting, interconnection, fire-code, and installation decisions.",
]


def build_safety_agent(client: SupportsChatGetResponse | None = None) -> Agent:
    return Agent(
        client=client or create_chat_client(),
        name="SafetyAgent",
        description="Explains safety boundaries and battery tradeoffs.",
        instructions=INSTRUCTIONS + "\n\nReference notes:\n" + "\n".join(SAFETY_REFERENCE_NOTES),
        tools=[],
        require_per_service_call_history_persistence=True,
    )
