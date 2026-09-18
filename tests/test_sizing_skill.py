import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest  # noqa: E402

from solar_agent.skills.sizing_skill import estimate_panels_needed  # noqa: E402
from solar_agent.skills.tariff_payback_skill import (  # noqa: E402
    estimate_payback,
    list_tariff_profiles,
)


def test_sizing_reasonable_panel_count():
    result = estimate_panels_needed(
        avg_daily_consumption_kwh=28.0,
        peak_sun_hours=4.5,
        panel_rated_w=400,
        system_derate=0.8,
        target_offset_pct=1.0,
    )
    assert result["panels_needed"] > 0
    assert "explanation" in result


def test_sizing_rejects_zero_sun_hours():
    with pytest.raises(ValueError):
        estimate_panels_needed(
            avg_daily_consumption_kwh=28.0,
            peak_sun_hours=0,
            panel_rated_w=400,
            system_derate=0.8,
            target_offset_pct=1.0,
        )


def test_tariff_profiles_listed():
    profiles = list_tariff_profiles()
    ids = {p["id"] for p in profiles}
    assert "flat_rate" in ids and "time_of_use" in ids


def test_payback_estimate_positive():
    result = estimate_payback(
        tariff_profile_id="flat_rate",
        system_cost_usd=15000,
        estimated_annual_generation_kwh=6000,
    )
    assert result["payback_years"] > 0
