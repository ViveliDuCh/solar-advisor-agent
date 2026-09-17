"""Maintenance Agent: flags underperformance vs. expected output curve.

Reads telemetry through the DeviceAdapter interface, so it works identically
against SimulatedInverterAdapter today and a real vendor adapter later.
"""
from __future__ import annotations

from typing import Annotated

from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient
from pydantic import Field

from solar_agent.adapters.simulated_inverter_adapter import SimulatedInverterAdapter

INSTRUCTIONS = """
You monitor a household's solar system and tell the homeowner, in plain
language, when something looks off (underperformance, a fault code) and what
to do about it (e.g. "check for shading/dirt on the panels", "call an
electrician" for anything involving live wiring). Always call
check_inverter_health first. Never suggest the homeowner open the inverter
enclosure or touch DC wiring themselves - that's a licensed-electrician task.
"""


async def check_inverter_health(
    panel_rated_w: Annotated[float, Field(description="Total rated wattage of the installed system")],
) -> dict:
    """Agent-callable tool: compare current telemetry to expected output.

    Backed by SimulatedInverterAdapter today; swap for a Real*Adapter behind
    the same DeviceAdapter interface once vendor API credentials exist.
    """
    adapter = SimulatedInverterAdapter(panel_rated_w=panel_rated_w)
    readings = await adapter.get_current_telemetry()
    reading = readings[0]
    expected_w = await adapter.get_expected_power_w(reading.timestamp)

    shortfall_pct = 0.0
    if expected_w > 0:
        shortfall_pct = max(0.0, (expected_w - reading.power_w) / expected_w * 100.0)

    return {
        "actual_power_w": reading.power_w,
        "expected_power_w": round(expected_w, 1),
        "shortfall_pct": round(shortfall_pct, 1),
        "fault_code": reading.fault_code,
        "needs_attention": reading.fault_code is not None or shortfall_pct > 20.0,
    }


def build_maintenance_agent(client: OpenAIChatClient | None = None) -> Agent:
    return Agent(
        client=client or OpenAIChatClient(),
        name="MaintenanceAgent",
        instructions=INSTRUCTIONS,
        tools=[check_inverter_health],
    )
