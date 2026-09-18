"""SizingSkill: "how many panels do I need" for new users.

Peak Sun Hours (PSH) methodology per thegreenwatt.com references:
    Daily panel output (Wh) = Panel rated W x PSH x system derate
    Panels needed = Target daily consumption (Wh) / Daily panel output (Wh)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from pydantic import Field


@dataclass
class SizingResult:
    panels_needed: int
    total_system_w: float
    daily_output_kwh_per_panel: float
    explanation: str


def estimate_panels_needed(
    avg_daily_consumption_kwh: Annotated[
        float,
        Field(
            description="Average daily household electricity use in kWh, e.g. from a utility bill"
        ),
    ],
    peak_sun_hours: Annotated[
        float,
        Field(description="Peak sun hours/day for the location (from forecast/climate averages)"),
    ],
    panel_rated_w: Annotated[float, Field(description="Rated wattage per panel (STC)")],
    system_derate: Annotated[
        float,
        Field(description="Explicit modeled efficiency after system losses, expressed 0 to 1"),
    ],
    target_offset_pct: Annotated[
        float, Field(description="Fraction of consumption to offset with solar, e.g. 1.0 = 100%")
    ],
) -> dict:
    """Agent-callable tool: recommend a panel count and total system size."""
    daily_output_per_panel_kwh = (panel_rated_w * peak_sun_hours * system_derate) / 1000.0
    target_daily_kwh = avg_daily_consumption_kwh * target_offset_pct

    if daily_output_per_panel_kwh <= 0:
        raise ValueError("peak_sun_hours, panel_rated_w, and system_derate must be positive")
    if not 0 < target_offset_pct <= 1.5:
        raise ValueError("target_offset_pct must be greater than 0 and no more than 1.5")

    panels_needed = max(1, round(target_daily_kwh / daily_output_per_panel_kwh + 0.49))
    total_system_w = panels_needed * panel_rated_w

    explanation = (
        f"Targeting {target_offset_pct:.0%} of {avg_daily_consumption_kwh:.1f} kWh/day average use "
        f"({target_daily_kwh:.1f} kWh/day) at {peak_sun_hours:.1f} peak sun hours/day. Each "
        f"{panel_rated_w:.0f}W panel produces about "
        f"{daily_output_per_panel_kwh:.2f} kWh/day after a {system_derate:.0%} system derate "
        "(wiring/inverter/soiling loss) -> "
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
