from __future__ import annotations


def simple_financial_estimate(
    annual_production_kwh: float,
    self_consumption_fraction: float,
    electricity_rate_per_kwh: float,
    installed_cost: float,
) -> dict[str, float | None]:
    directly_used = annual_production_kwh * self_consumption_fraction
    exported = annual_production_kwh - directly_used
    # Simplified demo: exports are valued at the same illustrative rate.
    annual_value = (directly_used + exported) * electricity_rate_per_kwh
    payback = installed_cost / annual_value if annual_value > 0 else None
    return {
        "annual_production_kwh": round(annual_production_kwh),
        "annual_value": round(annual_value),
        "simple_payback_years": round(payback, 1) if payback else None,
    }

