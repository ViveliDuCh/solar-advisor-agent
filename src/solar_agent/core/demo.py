import json
from pathlib import Path

from solar_agent.core.models import (
    Appliance,
    ArraySection,
    Battery,
    Household,
    SolarSystem,
)

DEMO_ASSUMPTIONS_PATH = Path(__file__).resolve().parents[1] / "data" / "demo_assumptions.json"


def load_demo_assumptions() -> dict:
    with open(DEMO_ASSUMPTIONS_PATH, encoding="utf-8") as file:
        return json.load(file)


def demo_household(work_from_home: bool = True) -> Household:
    values = load_demo_assumptions()["household"]
    return Household(
        zip_code=values["zip_code"],
        annual_consumption_kwh=values["annual_consumption_kwh"],
        occupants=values["occupants"],
        work_from_home=work_from_home,
    )


def demo_system(
    sections: tuple[ArraySection, ...] | None = None,
) -> SolarSystem:
    values = load_demo_assumptions()["solar_system"]
    return SolarSystem(
        sections=sections
        or tuple(
            ArraySection(
                panel_count=section["panel_count"],
                panel_watts=section["panel_watts"],
                tilt_degrees=section["tilt_degrees"],
                azimuth_degrees=section["azimuth_degrees"],
                shading_percent=section["shading_percent"],
            )
            for section in values["sections"]
        ),
        inverter_ac_kw=values["inverter_ac_kw"],
        other_losses_percent=values["other_losses_percent"],
    )


def demo_appliances(include_ev: bool = True) -> list[Appliance]:
    values = load_demo_assumptions()["appliances"]
    appliances = [
        Appliance(
            name=item["name"],
            power_kw=item["power_kw"],
            duration_hours=item["duration_hours"],
            earliest_hour=item["earliest_hour"],
            latest_hour=item["latest_hour"],
        )
        for item in values
        if include_ev or item["name"] != "EV charging"
    ]
    return appliances


def demo_battery() -> Battery:
    return Battery()
