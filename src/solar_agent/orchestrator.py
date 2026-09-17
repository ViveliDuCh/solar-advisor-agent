"""Orchestrator: user-facing router ("Solar Advisor").

Routes a user message to the right specialist agent. Hackathon-grade: simple
keyword routing stub, upgrade to agent-framework's handoff/group-chat
orchestration (see python README "Multi-Agent Orchestration") once all
specialist agents are wired to a real LLM client.
"""
from __future__ import annotations

import asyncio

from solar_agent.agents.financial_agent import build_financial_agent
from solar_agent.agents.forecast_agent import build_forecast_agent
from solar_agent.agents.maintenance_agent import build_maintenance_agent
from solar_agent.agents.safety_agent import build_safety_agent
from solar_agent.agents.sizing_agent import build_sizing_agent

_ROUTES = {
    "sizing": ("how many panels", "size", "new system", "diy"),
    "forecast": ("today", "tomorrow", "schedule", "when should i", "forecast"),
    "maintenance": ("underperform", "dirty", "clean", "fault", "maintenance"),
    "financial": ("payback", "cost", "save", "roi", "bill"),
    "safety": ("safe", "battery", "shock", "electrocut", "toxic"),
}


def route(message: str) -> str:
    lowered = message.lower()
    for agent_name, keywords in _ROUTES.items():
        if any(kw in lowered for kw in keywords):
            return agent_name
    return "forecast"  # default: most common "what should I do today" question


async def handle_message(message: str) -> str:
    agent_name = route(message)
    builders = {
        "sizing": build_sizing_agent,
        "forecast": build_forecast_agent,
        "maintenance": build_maintenance_agent,
        "financial": build_financial_agent,
        "safety": build_safety_agent,
    }
    agent = builders[agent_name]()
    result = await agent.run(message)
    return str(result)


async def _demo() -> None:
    print(await handle_message("How many panels do I need? I use about 28 kWh/day."))


if __name__ == "__main__":
    asyncio.run(_demo())
