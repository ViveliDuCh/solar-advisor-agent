"""Safety/Education Agent: plain-language electrical safety & battery tradeoffs.

No deterministic "skill" backs this agent - it must stay grounded in a small,
vetted reference set (RAG) rather than freelancing electrical rules. The
reference content below is a placeholder; replace with vetted NEC-adjacent
guidance and manufacturer safety docs before using this for real advice.
"""
from __future__ import annotations

from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient

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

# Placeholder reference set - replace with vetted, cited sources before demo.
SAFETY_REFERENCE_NOTES = [
    "AC-side work (past the main disconnect) may be within reach for an "
    "experienced DIYer in some jurisdictions; DC combiner/inverter wiring and "
    "grid interconnection require a licensed electrician and utility permit "
    "in virtually all US jurisdictions.",
    "Lithium-ion battery storage: higher cost, longer cycle life, requires "
    "thermal management and fire-safety clearances; lead-acid: lower upfront "
    "cost, shorter life, more toxic to dispose of, needs ventilation.",
    "Panels should be de-energized (covered) before any physical inspection "
    "or cleaning work near wiring; panels still generate voltage in daylight "
    "even when 'off'.",
]


def build_safety_agent(client: OpenAIChatClient | None = None) -> Agent:
    return Agent(
        client=client or OpenAIChatClient(),
        name="SafetyAgent",
        instructions=INSTRUCTIONS + "\n\nReference notes:\n" + "\n".join(SAFETY_REFERENCE_NOTES),
        tools=[],
    )
