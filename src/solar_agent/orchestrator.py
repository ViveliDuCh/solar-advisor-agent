from __future__ import annotations

import asyncio

from agent_framework import Agent, AgentSession, SupportsChatGetResponse
from agent_framework.orchestrations import HandoffBuilder

from solar_agent.agent_client import create_chat_client
from solar_agent.agents.financial_agent import build_financial_agent
from solar_agent.agents.forecast_agent import build_forecast_agent
from solar_agent.agents.maintenance_agent import build_maintenance_agent
from solar_agent.agents.safety_agent import build_safety_agent
from solar_agent.agents.sizing_agent import build_sizing_agent
from solar_agent.security.pii_middleware import redact_text

TRIAGE_INSTRUCTIONS = """
You are the user-facing Solar Advisor. Determine which specialist should answer and hand off:
- ForecastAgent: weather, hourly solar output, appliance timing, and dashboard forecast questions.
- FinancialAgent: cost, bills, payback, savings, and household consumption changes.
- MaintenanceAgent: inverter telemetry, cleaning, faults, and underperformance.
- SafetyAgent: electrical safety boundaries and battery tradeoffs.
- SizingAgent: educational estimates for panel count or added array capacity.

Do not calculate watts, kWh, dollars, or safety limits yourself. Hand the request to the
specialist with the appropriate deterministic tools. Preserve prior conversational context.
Never request a real utility bill, account number, exact street address, or payment information.
"""


def build_advisor_workflow(client: SupportsChatGetResponse | None = None):
    shared_client = client or create_chat_client()
    triage = Agent(
        client=shared_client,
        name="SolarAdvisor",
        description="Routes household solar questions to the appropriate specialist.",
        instructions=TRIAGE_INSTRUCTIONS,
        require_per_service_call_history_persistence=True,
    )
    specialists = [
        build_forecast_agent(shared_client),
        build_financial_agent(shared_client),
        build_maintenance_agent(shared_client),
        build_safety_agent(shared_client),
        build_sizing_agent(shared_client),
    ]
    builder = HandoffBuilder(
        name="SolarAdvisorWorkflow",
        participants=[triage, *specialists],
        description="Routes solar questions to calculation-grounded specialists.",
        output_from="all",
    ).with_start_agent(triage)
    builder.add_handoff(
        triage,
        specialists,
        description="Choose the specialist whose scope best matches the user's request.",
    )
    for specialist in specialists:
        builder.add_handoff(
            specialist,
            [triage],
            description="Return to SolarAdvisor when a different specialist is required.",
        )
    return builder.build()


def build_advisor_agent(client: SupportsChatGetResponse | None = None):
    return build_advisor_workflow(client).as_agent(
        name="SolarAdvisor",
        description="Multi-agent household solar advisor.",
    )


async def handle_message(
    message: str,
    *,
    dashboard_context: str = "",
    session: AgentSession | None = None,
) -> str:
    safe_message = redact_text(message)
    prompt = (
        f"Current dashboard context:\n{dashboard_context}\n\nHomeowner question:\n{safe_message}"
    )
    result = await build_advisor_agent().run(prompt, session=session)
    return result.text


async def _demo() -> None:
    print(await handle_message("How many panels do I need? I use about 28 kWh/day."))


if __name__ == "__main__":
    asyncio.run(_demo())
