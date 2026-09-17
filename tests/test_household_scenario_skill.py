from solar_agent.skills.household_scenario_skill import simulate_household_change


def test_freezer_scenario_reports_energy_and_cost_assumptions() -> None:
    result = simulate_household_change(
        change="add_freezer",
        annual_consumption_kwh=10_800,
        annual_production_kwh=8_800,
        electricity_rate_per_kwh=0.14,
    )

    assert result["revised_consumption_kwh"] == 11_300
    assert result["annual_cost_change_usd"] == 70
    assert any("demonstration assumption" in item for item in result["assumptions"])


def test_gas_water_heater_scenario_does_not_go_below_zero() -> None:
    result = simulate_household_change(
        change="switch_electric_water_heater_to_gas",
        annual_consumption_kwh=2_000,
        annual_production_kwh=1_000,
        electricity_rate_per_kwh=0.14,
    )

    assert result["revised_consumption_kwh"] == 0
    assert result["annual_cost_change_usd"] == -140
