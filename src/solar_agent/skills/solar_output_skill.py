"""SolarOutputSkill: irradiance -> watts, with an uncertainty band.

Formulas per docs/ARCHITECTURE.md section 3:

    Instant Power (W) = Panel rated W (STC)
                       x (irradiance / 1000 W/m^2)
                       x system derate            # 0.75-0.85
                       x tilt/azimuth factor
                       x temp_derate(ambient, irradiance)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from pydantic import Field

STC_IRRADIANCE_W_M2 = 1000.0
DEFAULT_SYSTEM_DERATE = 0.80  # wiring/inverter/soiling/mismatch losses, 0.75-0.85 typical
NOCT_C = 45.0  # nominal operating cell temp at 800 W/m2, 20C ambient, 1 m/s wind
TEMP_COEFF_PCT_PER_C = 0.4  # % power loss per degree C above 25C cell temp


@dataclass
class OutputEstimate:
    p10_w: float
    p50_w: float
    p90_w: float
    explanation: str


def _cell_temp_c(ambient_c: float, irradiance_w_m2: float) -> float:
    """Estimate cell temperature from ambient temp + irradiance (NOCT model)."""
    return ambient_c + (irradiance_w_m2 / 800.0) * (NOCT_C - 20.0)


def _temp_derate(ambient_c: float, irradiance_w_m2: float) -> float:
    cell_temp = _cell_temp_c(ambient_c, irradiance_w_m2)
    delta = max(0.0, cell_temp - 25.0)
    return max(0.5, 1.0 - (TEMP_COEFF_PCT_PER_C / 100.0) * delta)


def tilt_azimuth_factor(panel_tilt_deg: float, panel_azimuth_deg: float) -> float:
    """Simplified orientation factor, 1.0 = ideal (tilt = latitude, due south).

    Hackathon-grade approximation: cosine falloff from true south (180deg)
    and from a 30deg reference tilt. Good enough to differentiate "south
    facing, 30deg roof" from "west facing, flat roof" in the UI; swap for a
    proper solar-position model (pvlib) post-hackathon.
    """
    import math

    azimuth_penalty = math.cos(math.radians(panel_azimuth_deg - 180.0))
    tilt_penalty = math.cos(math.radians(panel_tilt_deg - 30.0))
    factor = max(0.4, 0.6 + 0.4 * azimuth_penalty) * max(0.6, 0.8 + 0.2 * tilt_penalty)
    return min(1.0, factor)


def estimate_output_w(
    panel_rated_w: float,
    irradiance_w_m2: float,
    ambient_temp_c: float,
    panel_tilt_deg: float = 30.0,
    panel_azimuth_deg: float = 180.0,
    system_derate: float = DEFAULT_SYSTEM_DERATE,
    irradiance_uncertainty_pct: float = 15.0,
) -> OutputEstimate:
    """Core deterministic calc, P10/P50/P90 via a simple irradiance band.

    ``irradiance_uncertainty_pct`` should widen with forecast lead time
    (tighter for tomorrow, wider for day+5) - callers pick the band.
    """
    orientation = tilt_azimuth_factor(panel_tilt_deg, panel_azimuth_deg)

    def power_at(irr: float) -> float:
        irr = max(0.0, irr)
        derate_t = _temp_derate(ambient_temp_c, irr)
        return (
            panel_rated_w
            * (irr / STC_IRRADIANCE_W_M2)
            * system_derate
            * orientation
            * derate_t
        )

    band = irradiance_uncertainty_pct / 100.0
    p10 = power_at(irradiance_w_m2 * (1 - band))
    p50 = power_at(irradiance_w_m2)
    p90 = power_at(irradiance_w_m2 * (1 + band))

    explanation = (
        f"Assumes {panel_rated_w:.0f}W rated panel(s), {system_derate:.0%} system "
        f"derate (wiring/inverter/soiling loss), orientation factor {orientation:.2f} "
        f"(tilt {panel_tilt_deg:.0f} deg, azimuth {panel_azimuth_deg:.0f} deg), and "
        f"+/-{irradiance_uncertainty_pct:.0f}% irradiance uncertainty from the forecast."
    )
    return OutputEstimate(p10_w=p10, p50_w=p50, p90_w=p90, explanation=explanation)


def estimate_hourly_output(
    panel_rated_w: Annotated[float, Field(description="Total rated wattage of installed panels (STC)")],
    hourly_forecast: Annotated[
        list[dict], Field(description="Output of get_hourly_forecast: list of {ghi_w_m2, temp_c, timestamp}")
    ],
    panel_tilt_deg: Annotated[float, Field(description="Roof/panel tilt in degrees")] = 30.0,
    panel_azimuth_deg: Annotated[float, Field(description="Panel azimuth, 180=south")] = 180.0,
) -> list[dict]:
    """Agent-callable tool: turn an hourly forecast into hourly power estimates."""
    out = []
    for i, hour in enumerate(hourly_forecast):
        # Uncertainty widens with lead time: +-10% for hour 0, capped at +-40%.
        uncertainty_pct = min(40.0, 10.0 + i * 0.6)
        est = estimate_output_w(
            panel_rated_w=panel_rated_w,
            irradiance_w_m2=hour["ghi_w_m2"],
            ambient_temp_c=hour["temp_c"],
            panel_tilt_deg=panel_tilt_deg,
            panel_azimuth_deg=panel_azimuth_deg,
            irradiance_uncertainty_pct=uncertainty_pct,
        )
        out.append(
            {
                "timestamp": hour["timestamp"],
                "p10_w": round(est.p10_w, 1),
                "p50_w": round(est.p50_w, 1),
                "p90_w": round(est.p90_w, 1),
                "explanation": est.explanation,
            }
        )
    return out
