from __future__ import annotations

import numpy as np
import pandas as pd


def simulate_inverter_telemetry(
    expected_kw: pd.Series,
    underperformance_percent: float,
) -> pd.DataFrame:
    daylight = expected_kw > 0.05
    actual = expected_kw.copy()
    actual.loc[daylight] *= 1 - underperformance_percent / 100
    actual.loc[daylight] *= 1 + 0.015 * np.sin(np.arange(daylight.sum()))
    return pd.DataFrame(
        {
            "expected_kw": expected_kw,
            "actual_kw": actual.clip(lower=0),
            "communication_ok": True,
        }
    )


def diagnose_maintenance(telemetry: pd.DataFrame) -> dict[str, object]:
    valid = telemetry[
        telemetry["communication_ok"]
        & (telemetry["expected_kw"] >= 0.25)
    ]
    if valid.empty:
        return {
            "status": "insufficient_data",
            "severity": "info",
            "loss_percent": None,
            "message": "Not enough valid daylight telemetry to diagnose performance.",
        }

    expected = float(valid["expected_kw"].sum())
    actual = float(valid["actual_kw"].sum())
    loss = max(0.0, (expected - actual) / expected * 100)

    if loss >= 20:
        status = "investigate"
        severity = "warning"
        message = (
            "Production is materially below the weather-adjusted estimate. Possible causes include "
            "soiling, persistent shading, an inverter issue, or incorrect system assumptions."
        )
    elif loss >= 10:
        status = "watch"
        severity = "caution"
        message = (
            "Production is moderately below expectation. Continue monitoring before concluding "
            "that cleaning or service is required."
        )
    else:
        status = "normal"
        severity = "success"
        message = "Production is within the expected modeled range."

    return {
        "status": status,
        "severity": severity,
        "loss_percent": round(loss, 1),
        "message": message,
        "safe_action": (
            "Review monitoring alerts and visually inspect from ground level. Do not open the "
            "inverter, disconnect DC wiring, or access the roof."
        ),
    }

