from solar_agent.core.models import (
    Appliance,
    ArraySection,
    Battery,
    Household,
    SolarSystem,
)


def demo_household(work_from_home: bool = True) -> Household:
    return Household(work_from_home=work_from_home)


def demo_system(
    sections: tuple[ArraySection, ...] | None = None,
) -> SolarSystem:
    return SolarSystem(
        sections=sections
        or (
            ArraySection(
                panel_count=12,
                panel_watts=400,
                tilt_degrees=30,
                azimuth_degrees=180,
                shading_percent=4,
            ),
            ArraySection(
                panel_count=8,
                panel_watts=400,
                tilt_degrees=24,
                azimuth_degrees=225,
                shading_percent=7,
            ),
        )
    )


def demo_appliances(include_ev: bool = True) -> list[Appliance]:
    appliances = [
        Appliance("Washer", 0.5, 1.0, 8, 20),
        Appliance("Dryer", 4.5, 0.75, 9, 21),
        Appliance("Dishwasher", 1.2, 1.5, 10, 22),
    ]
    if include_ev:
        appliances.append(Appliance("EV charging", 7.2, 2.0, 0, 23))
    return appliances


def demo_battery() -> Battery:
    return Battery()
