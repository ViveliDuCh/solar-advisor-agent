"""SizingSkill: "how many panels do I need" for new users.

Peak Sun Hours (PSH) methodology per thegreenwatt.com references:
    Daily panel output (Wh) = Panel rated W x PSH x system derate
    Panels needed = Target daily consumption (Wh) / Daily panel output (Wh)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from pydantic import Field

from solar_agent.skills.solar_output_skill import DEFAULT_SYSTEM_DERATE

DEFAULT_PANEL_RATED_W = 400.0  # common residential panel wattage today


@dataclass
class SizingResult:
    panels_needed: int
    total_system_w: float
    daily_output_kwh_per_panel: float
    explanation: str


def estimate_panels_needed(
    avg_daily_consumption_kwh: Annotated[
        float, Field(description="Average daily household electricity use in kWh, e.g. from a utility bill")
    ],
    peak_sun_hours: Annotated[
        float, Field(description="Peak sun hours/day for the location (from forecast/climate averages)")
    ],
    panel_rated_w: Annotated[float, Field(description="Rated wattage per panel (STC)")] = DEFAULT_PANEL_RATED_W,
    system_derate: Annotated[float, Field(description="System derate, 0.75-0.85 typical")] = DEFAULT_SYSTEM_DERATE,
    target_offset_pct: Annotated[
        float, Field(description="Fraction of consumption to offset with solar, e.g. 1.0 = 100%")
    ] = 1.0,
) -> dict:
    """Agent-callable tool: recommend a panel count and total system size."""
    daily_output_per_panel_kwh = (panel_rated_w * peak_sun_hours * system_derate) / 1000.0
    target_daily_kwh = avg_daily_consumption_kwh * target_offset_pct

    if daily_output_per_panel_kwh <= 0:
        raise ValueError("peak_sun_hours and panel_rated_w must be positive")

    panels_needed = max(1, round(target_daily_kwh / daily_output_per_panel_kwh + 0.49))
    total_system_w = panels_needed * panel_rated_w

    explanation = (
        f"Targeting {target_offset_pct:.0%} of {avg_daily_consumption_kwh:.1f} kWh/day average use "
        f"({target_daily_kwh:.1f} kWh/day) at {peak_sun_hours:.1f} peak sun hours/day. Each "
        f"{panel_rated_w:.0f}W panel produces about {daily_output_per_panel_kwh:.2f} kWh/day after a "
        f"{system_derate:.0%} system derate (wiring/inverter/soiling loss) -> "
        f"{panels_needed} panels ({total_system_w:.0f}W total)."
    )

    result = SizingResult(
        panels_needed=panels_needed,
        total_system_w=total_system_w,
        daily_output_kwh_per_panel=daily_output_per_panel_kwh,
        explanation=explanation,
    )
    return {
        "panels_needed": result.panels_needed,
        "total_system_w": result.total_system_w,
        "daily_output_kwh_per_panel": round(result.daily_output_kwh_per_panel, 2),
        "explanation": result.explanation,
    }
