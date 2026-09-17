"""ApplianceSchedulerSkill: turn hourly output estimates into "do X at hour Y".

Consumes the output of solar_output_skill.estimate_hourly_output plus a list
of appliance loads and suggests the best windows to run high-draw appliances.
"""
from __future__ import annotations

from typing import Annotated

from pydantic import Field

DEFAULT_APPLIANCE_LIBRARY = {
    "dishwasher": 1800,
    "washing_machine": 500,
    "clothes_dryer": 3000,
    "ev_charger_level2": 7200,
    "water_heater": 4000,
    "air_conditioner": 3500,
}


def suggest_appliance_windows(
    hourly_output: Annotated[
        list[dict], Field(description="Output of estimate_hourly_output: list of {timestamp, p50_w, ...}")
    ],
    appliance_watts: Annotated[
        dict[str, float],
        Field(description="Appliance name -> running watts, defaults to DEFAULT_APPLIANCE_LIBRARY if omitted"),
    ] = None,
    top_n_windows: Annotated[int, Field(description="How many best hours to suggest per appliance")] = 2,
) -> list[dict]:
    """Agent-callable tool: best hours to run each appliance this forecast window."""
    appliances = appliance_watts or DEFAULT_APPLIANCE_LIBRARY

    suggestions = []
    for name, watts in appliances.items():
        # Rank hours by how much of the appliance's draw is covered by p50 solar output.
        ranked = sorted(hourly_output, key=lambda h: h["p50_w"], reverse=True)[:top_n_windows]
        windows = []
        for hour in ranked:
            coverage_pct = min(100.0, (hour["p50_w"] / watts) * 100.0) if watts > 0 else 0.0
            windows.append({"timestamp": hour["timestamp"], "solar_coverage_pct": round(coverage_pct, 0)})
        suggestions.append(
            {
                "appliance": name,
                "watts": watts,
                "recommended_windows": windows,
                "explanation": (
                    f"{name.replace('_', ' ')} draws ~{watts:.0f}W; best forecast windows cover "
                    f"{windows[0]['solar_coverage_pct']:.0f}% of that from solar alone."
                    if windows
                    else "No forecast data available."
                ),
            }
        )
    return suggestions
