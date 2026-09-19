import pandas as pd

from solar_agent.domain.maintenance import diagnose_maintenance, simulate_inverter_telemetry


def test_detects_sustained_underperformance() -> None:
    expected = pd.Series([1.0, 2.0, 3.0, 2.0])
    telemetry = simulate_inverter_telemetry(expected, 25)
    diagnosis = diagnose_maintenance(telemetry)
    assert diagnosis["status"] == "investigate"
    assert diagnosis["loss_percent"] >= 20
