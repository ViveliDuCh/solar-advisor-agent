"""Financial Agent: payback/ROI using example tariff profiles (never a real bill)."""
from __future__ import annotations

from agent_framework import Agent, SupportsChatGetResponse

from solar_agent.agent_client import create_chat_client
from solar_agent.skills.household_scenario_skill import simulate_household_change
from solar_agent.skills.tariff_payback_skill import estimate_payback, list_tariff_profiles

INSTRUCTIONS = """
You explain financial payback for a solar system in plain language. Always
call list_tariff_profiles to show the homeowner example rate structures (do
not ask them to upload a real bill - this app never stores real bill data),
then call estimate_payback with their chosen profile, system cost, and
estimated annual generation. Report the explanation field verbatim so the
simplifying assumptions (no degradation, no incentives) are visible, and
answer "what if" questions with simulate_household_change when it supports
the requested scenario. Never perform energy or cost arithmetic yourself.
State every demonstration assumption.
"""


def build_financial_agent(client: SupportsChatGetResponse | None = None) -> Agent:
    return Agent(
        client=client or create_chat_client(),
        name="FinancialAgent",
        description="Explains payback and household cost scenarios.",
        instructions=INSTRUCTIONS,
        tools=[list_tariff_profiles, estimate_payback, simulate_household_change],
        require_per_service_call_history_persistence=True,
    )
