"""TariffPaybackSkill: financial payback using example tariff profiles.

Deliberately does NOT accept a real uploaded bill (see docs/ARCHITECTURE.md
section 6, Security & privacy) - callers pass a tariff profile name from
data/tariff_profiles.json, or synthetic numbers of their own choosing.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

from pydantic import Field

TARIFF_PROFILES_PATH = Path(__file__).resolve().parents[1] / "data" / "tariff_profiles.json"


def _load_profiles() -> dict:
    with open(TARIFF_PROFILES_PATH, encoding="utf-8") as f:
        return json.load(f)


def list_tariff_profiles() -> list[dict]:
    """Agent-callable tool: list example tariff profiles the user can pick from."""
    return list(_load_profiles().values())


def estimate_payback(
    tariff_profile_id: Annotated[
        str, Field(description="One of the ids returned by list_tariff_profiles, e.g. 'flat_rate'")
    ],
    system_cost_usd: Annotated[float, Field(description="Total installed cost of the system, e.g. from a quote")],
    estimated_annual_generation_kwh: Annotated[
        float, Field(description="Estimated annual kWh generated (sum of hourly/daily estimates)")
    ],
) -> dict:
    """Agent-callable tool: simple payback estimate in years.

    This is a hackathon-grade estimate (no degradation curve, no net-metering
    escalation, no incentives) - flagged explicitly in the explanation so the
    Financial Agent doesn't overstate precision.
    """
    profiles = _load_profiles()
    if tariff_profile_id not in profiles:
        raise ValueError(f"Unknown tariff_profile_id: {tariff_profile_id}")

    profile = profiles[tariff_profile_id]
    avg_rate_usd_per_kwh = profile["avg_rate_usd_per_kwh"]
    annual_savings_usd = estimated_annual_generation_kwh * avg_rate_usd_per_kwh
    payback_years = system_cost_usd / annual_savings_usd if annual_savings_usd > 0 else float("inf")

    explanation = (
        f"Using the '{profile['name']}' example tariff (${avg_rate_usd_per_kwh:.2f}/kWh avg), "
        f"{estimated_annual_generation_kwh:.0f} kWh/year generation saves about "
        f"${annual_savings_usd:,.0f}/year, paying back a ${system_cost_usd:,.0f} system in "
        f"~{payback_years:.1f} years. This is a simplified estimate: it ignores panel "
        f"degradation, rate escalation, and incentives/rebates."
    )

    return {
        "annual_savings_usd": round(annual_savings_usd, 2),
        "payback_years": round(payback_years, 1),
        "explanation": explanation,
    }
