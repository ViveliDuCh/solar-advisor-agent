from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from solar_agent.demo.assumptions import load_demo_assumptions


def simulate_household_change(
    change: Annotated[
        Literal["add_freezer", "switch_electric_water_heater_to_gas"],
        Field(description="Supported household change to simulate"),
    ],
    annual_consumption_kwh: Annotated[
        float,
        Field(description="Current annual household electricity consumption in kWh"),
    ],
    annual_production_kwh: Annotated[
        float,
        Field(description="Current modeled annual solar production in kWh"),
    ],
    electricity_rate_per_kwh: Annotated[
        float,
        Field(description="Illustrative electricity energy rate in dollars per kWh"),
    ],
    appliance_annual_kwh: Annotated[
        float | None,
        Field(
            description=(
                "Product EnergyGuide annual kWh if known. Omit to use a clearly labeled "
                "demonstration assumption."
            )
        ),
    ] = None,
) -> dict[str, float | str | list[str]]:
    """Calculate supported household changes without LLM arithmetic."""
    if annual_consumption_kwh < 0 or annual_production_kwh < 0:
        raise ValueError("Annual consumption and production must be non-negative")
    if electricity_rate_per_kwh < 0:
        raise ValueError("Electricity rate must be non-negative")

    assumptions: list[str] = []
    scenario_defaults = load_demo_assumptions()["scenario_defaults"]
    if change == "add_freezer":
        default_kwh = scenario_defaults["add_freezer_kwh_per_year"]
        delta_kwh = appliance_annual_kwh if appliance_annual_kwh is not None else default_kwh
        if appliance_annual_kwh is None:
            assumptions.append(
                f"Uses {default_kwh:,.0f} kWh/year from the versioned demo assumption catalog "
                "for one additional freezer."
            )
    else:
        default_kwh = scenario_defaults["electric_water_heater_kwh_per_year"]
        delta_kwh = -(appliance_annual_kwh if appliance_annual_kwh is not None else default_kwh)
        if appliance_annual_kwh is None:
            assumptions.append(
                f"Uses {default_kwh:,.0f} kWh/year from the versioned demo assumption catalog "
                "for electric water heating."
            )

    revised_consumption = max(annual_consumption_kwh + delta_kwh, 0)
    current_grid_kwh = max(annual_consumption_kwh - annual_production_kwh, 0)
    revised_grid_kwh = max(revised_consumption - annual_production_kwh, 0)
    grid_change_kwh = revised_grid_kwh - current_grid_kwh
    annual_cost_change = grid_change_kwh * electricity_rate_per_kwh
    solar_coverage_pct = annual_production_kwh / max(revised_consumption, 1) * 100
    assumptions.extend(
        [
            "Uses annual energy balance rather than interval utility billing.",
            "Excludes fixed charges, taxes, tariff tiers, equipment price, and fuel costs.",
        ]
    )

    return {
        "change": change,
        "current_consumption_kwh": round(annual_consumption_kwh),
        "revised_consumption_kwh": round(revised_consumption),
        "grid_energy_change_kwh": round(grid_change_kwh),
        "annual_cost_change_usd": round(annual_cost_change, 2),
        "monthly_cost_change_usd": round(annual_cost_change / 12, 2),
        "revised_solar_coverage_pct": round(solar_coverage_pct, 1),
        "assumptions": assumptions,
    }
