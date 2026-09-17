"""Unit tests for deterministic skills (no LLM/network required)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from solar_agent.skills.solar_output_skill import estimate_output_w  # noqa: E402


def test_estimate_output_at_noon_full_sun():
    est = estimate_output_w(
        panel_rated_w=4800,  # 12 x 400W
        irradiance_w_m2=900,
        ambient_temp_c=25,
        panel_tilt_deg=30,
        panel_azimuth_deg=180,
    )
    assert est.p10_w < est.p50_w < est.p90_w
    assert est.p50_w > 0


def test_zero_irradiance_gives_zero_power():
    est = estimate_output_w(
        panel_rated_w=4800,
        irradiance_w_m2=0,
        ambient_temp_c=10,
    )
    assert est.p50_w == 0


def test_west_facing_steep_roof_worse_than_south_ideal():
    from solar_agent.skills.solar_output_skill import tilt_azimuth_factor

    south_ideal = tilt_azimuth_factor(30, 180)
    west_steep = tilt_azimuth_factor(45, 270)
    assert south_ideal > west_steep
