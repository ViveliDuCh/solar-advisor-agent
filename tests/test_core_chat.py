from solar_agent.core.chat import AdvisorContext, answer_question


def context() -> AdvisorContext:
    return AdvisorContext(
        annual_consumption_kwh=10_800,
        annual_production_kwh=8_800,
        system_capacity_kw=8.0,
        electricity_rate=0.14,
        simple_payback_years=19.5,
        forecast_confidence="medium",
    )


def test_water_heater_scenario_explains_assumption() -> None:
    answer = answer_question("What if I replace my water heater with gas?", context())
    assert "example reduction" in answer
    assert "gas cost" in answer


def test_circuit_answer_does_not_claim_safety() -> None:
    answer = answer_question("Could an appliance cause electrical damage?", context())
    assert "not a circuit-safety test" in answer
    assert "never certifies a circuit" in answer


def test_add_panel_scenario_reports_added_capacity() -> None:
    answer = answer_question("What if I add four 430 W panels?", context())
    assert "1.7 kW DC" in answer
    assert "low confidence" in answer


def test_freezer_cost_question_calculates_bill_change() -> None:
    answer = answer_question("How would my costs change if I add a freezer?", context())
    assert "$70/year" in answer
    assert "$5.83/month" in answer
    assert "fixed utility charges" in answer


def test_cost_follow_up_uses_previous_freezer_scenario() -> None:
    answer = answer_question(
        "How would that change my bill?",
        context(),
        previous_question="What if I add a freezer?",
    )
    assert "$70/year" in answer
    assert "500 kWh/year" in answer
