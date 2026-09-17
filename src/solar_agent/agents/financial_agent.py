"""Financial Agent: payback/ROI using example tariff profiles (never a real bill)."""
from __future__ import annotations

from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient

from solar_agent.skills.tariff_payback_skill import estimate_payback, list_tariff_profiles

INSTRUCTIONS = """
You explain financial payback for a solar system in plain language. Always
call list_tariff_profiles to show the homeowner example rate structures (do
not ask them to upload a real bill - this app never stores real bill data),
then call estimate_payback with their chosen profile, system cost, and
estimated annual generation. Report the explanation field verbatim so the
simplifying assumptions (no degradation, no incentives) are visible, and
answer "what if" questions (consumption rises, more panels, WFH full time)
by re-deriving generation/consumption first, then re-calling estimate_payback.
"""


def build_financial_agent(client: OpenAIChatClient | None = None) -> Agent:
    return Agent(
        client=client or OpenAIChatClient(),
        name="FinancialAgent",
        instructions=INSTRUCTIONS,
        tools=[list_tariff_profiles, estimate_payback],
    )
