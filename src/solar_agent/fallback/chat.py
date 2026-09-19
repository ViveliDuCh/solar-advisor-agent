from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class AdvisorContext:
    annual_consumption_kwh: float
    annual_production_kwh: float
    system_capacity_kw: float
    electricity_rate: float
    simple_payback_years: float | None
    forecast_confidence: str


def _freezer_scenario(context: AdvisorContext, include_costs: bool) -> str:
    added_kwh = 500
    revised_consumption = context.annual_consumption_kwh + added_kwh
    before_grid_kwh = max(
        context.annual_consumption_kwh - context.annual_production_kwh,
        0,
    )
    after_grid_kwh = max(revised_consumption - context.annual_production_kwh, 0)
    added_grid_kwh = after_grid_kwh - before_grid_kwh
    annual_cost_change = added_grid_kwh * context.electricity_rate
    monthly_cost_change = annual_cost_change / 12
    revised_coverage = context.annual_production_kwh / revised_consumption * 100

    if include_costs:
        return (
            f"Using the demo assumptions of **{added_kwh} kWh/year** for one additional freezer "
            f"and **${context.electricity_rate:.2f}/kWh**, estimated purchased electricity rises "
            f"by about **{added_grid_kwh:,.0f} kWh/year**. That is approximately "
            f"**${annual_cost_change:,.0f}/year**, or **${monthly_cost_change:,.2f}/month**. "
            f"Household use becomes **{revised_consumption:,.0f} kWh/year**, and annual solar "
            f"coverage changes to roughly **{revised_coverage:.0f}%**. This simplified comparison "
            "values only energy; it excludes fixed utility charges, rate tiers, taxes, and the "
            "freezer purchase price. Replace 500 kWh with the product's EnergyGuide value for a "
            "product-specific estimate."
        )

    return (
        f"For a scenario, not a product estimate, I used **{added_kwh} kWh/year** for one "
        f"additional refrigeration appliance. Annual consumption becomes about "
        f"**{revised_consumption:,.0f} kWh** and the current solar estimate would equal roughly "
        f"**{revised_coverage:.0f}%** of annual use. Opening a refrigerator can increase "
        "compressor run time, while startup current is a short electrical event. Use the "
        "product's EnergyGuide kWh/year and nameplate amps for a real result; the solar model "
        "does not validate the branch circuit. Ask **“How would that change my costs?”** for the "
        "illustrative bill effect."
    )


def answer_question(
    question: str,
    context: AdvisorContext,
    previous_question: str | None = None,
) -> str:
    normalized = question.lower().strip()
    previous = (previous_question or "").lower().strip()
    cost_terms = ("cost", "bill", "price", "spend", "save", "financial", "money")
    refrigeration_terms = ("freezer", "fridge", "refrigerator")
    asks_about_cost = any(term in normalized for term in cost_terms)
    asks_about_refrigeration = any(term in normalized for term in refrigeration_terms)
    follows_refrigeration_scenario = (
        asks_about_cost
        and not asks_about_refrigeration
        and any(term in previous for term in refrigeration_terms)
    )

    if asks_about_cost and (asks_about_refrigeration or follows_refrigeration_scenario):
        return _freezer_scenario(context, include_costs=True)

    if any(term in normalized for term in ("heatmap", "green square", "colors")):
        return (
            "**The heatmap answers one question: when is solar most likely to be available?** "
            "Bright green means the model expects meaningful solar after the home's normal load. "
            "Yellow means partial solar coverage, and dark/red means the grid will likely provide "
            "most energy. Hover over a square to see expected solar, home load, and uncertainty."
        )

    if any(term in normalized for term in ("sankey", "energy flow", "where does")):
        return (
            "**The flow graphic follows each kWh.** Wider paths mean more energy. Solar can flow "
            "to the home, grid, or battery; the grid and battery can flow to the home. Compare the "
            "three examples to see whether scheduling or storage reduces grid imports."
        )

    if "solar used directly" in normalized or "direct solar" in normalized:
        return (
            "**Solar used directly is solar energy generated during the same hours that the home "
            "is consuming electricity.** For each hour, the model takes the smaller of solar "
            "generation and household load. That amount flows from Solar to Home; any remaining "
            "solar is exported, and any remaining household need comes from the grid or battery. "
            "It does not mean an appliance is wired directly to the panels."
        )

    if "deploy" in normalized or "deployment" in normalized:
        return (
            "**Deploy means make something available on another computer or cloud service.** "
            "Deploying the dashboard means hosting the Streamlit app so teammates and judges can "
            "open a web address. Deploying Aurora means creating a cloud endpoint that runs the "
            "weather model when our code sends it atmospheric input. These are separate "
            "deployments."
        )

    if any(term in normalized for term in ("confidence", "uncertain", "assumed")):
        return (
            f"The overall forecast confidence is **{context.forecast_confidence}**. The largest "
            "uncertainties are weather, shading, the synthetic hourly household profile, and "
            "unknown appliance nameplate information. Panel count, watts, orientation, and "
            "inverter capacity are explicit inputs. Open **Confidence and assumptions** for the "
            "calculation-by-calculation breakdown."
        )

    if "underperformance" in normalized or "inverter" in normalized:
        return (
            "**Simulated inverter underperformance is a demo fault, not an inverter setting.** "
            "A value such as 12% means the synthetic inverter reports 12% less daylight energy "
            "than the weather-adjusted model expected. The app watches the difference over time; "
            "it does not conclude from one cloudy hour that panels need cleaning."
        )

    if "different" in normalized and ("panel" in normalized or "watt" in normalized):
        return (
            "Describe the system as **array sections**. Each section has its own panel count, "
            "panel wattage, tilt, direction, and shading. The model calculates every section "
            "separately and then combines their DC output before applying the shared inverter "
            "limit. Mixed panel or inverter compatibility still requires installer documentation."
        )

    if any(term in normalized for term in ("current", "circuit", "electrical damage", "amps")):
        return (
            "**Solar availability is not a circuit-safety test.** In a normal grid-connected "
            "home, an appliance can use solar and grid energy at the same time; insufficient "
            "solar does not force the panel array to provide unsafe current. Circuit overload "
            "depends on wiring, breaker, receptacle, appliance nameplate, and other loads. The "
            "advisor schedules high-draw examples sequentially but never certifies a circuit."
        )

    if "water heater" in normalized and "gas" in normalized:
        reduction = 3_000
        revised = max(context.annual_consumption_kwh - reduction, 0)
        coverage = context.annual_production_kwh / max(revised, 1) * 100
        return (
            f"Using a clearly labeled **example reduction of {reduction:,} kWh/year**, switching "
            f"the modeled electric water heater to gas would reduce household electricity from "
            f"{context.annual_consumption_kwh:,.0f} to about **{revised:,.0f} kWh/year**. The "
            f"solar system could then equal roughly **{coverage:.0f}%** of annual "
            "electricity use. This does not include gas cost, combustion safety, emissions, "
            "installation cost, or the actual EnergyGuide rating."
        )

    if asks_about_refrigeration:
        return _freezer_scenario(context, include_costs=False)

    if "payback" in normalized or "financial" in normalized or "money" in normalized:
        payback = (
            f"{context.simple_payback_years:.1f} years"
            if context.simple_payback_years is not None
            else "not available"
        )
        return (
            f"The displayed simple payback is **{payback}**. It divides the illustrative installed "
            "cost by one year of modeled energy value. It intentionally excludes financing, fixed "
            "charges, detailed PSE tiers, incentives, degradation, maintenance, and future rate "
            "changes. Those are presentation stretch goals, not hidden assumptions."
        )

    number_words = {
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
    }
    number_token = r"\d+|one|two|three|four|five|six|seven|eight|nine|ten"
    panel_pattern = (
        rf"(?:add|buy)\s+({number_token}).{{0,12}}?(\d{{3}})?"
        r"\s*(?:w|watt)?\s*panels?"
    )
    panel_match = re.search(panel_pattern, normalized)
    if panel_match:
        raw_count = panel_match.group(1)
        count = int(raw_count) if raw_count.isdigit() else number_words[raw_count]
        watts = int(panel_match.group(2) or 400)
        added_kw = count * watts / 1000
        approximate_gain = context.annual_production_kwh * added_kw / context.system_capacity_kw
        return (
            f"Adding **{count} x {watts} W panels** adds **{added_kw:.1f} kW DC**. If orientation "
            f"and shading were similar, a first-pass estimate is about **{approximate_gain:,.0f} "
            "additional kWh/year**. The agent needs the new section's direction, tilt, shading, "
            "and inverter arrangement before treating that estimate as more than low confidence."
        )

    if "stretch" in normalized or "future" in normalized or "next step" in normalized:
        return (
            "**Stretch goals:** real Aurora initialized from operational weather data; vendor "
            "inverter OAuth; smart-meter imports; personalized tariff and incentives; proactive "
            "mobile notifications; longer-term fault classification; roof imagery; multilingual "
            "education; accessibility testing; and privacy-preserving community benchmarks."
        )

    return (
        "I can explain the heatmap, energy-flow graphic, confidence, finance, inverter health, "
        "mixed panel arrays, and electrical-safety boundary. I can also simulate questions such "
        'as **"What if I switch my water heater to gas?"**, **"What if I add a freezer?"**, or '
        '**"What if I add four 430 W panels?"**'
    )
