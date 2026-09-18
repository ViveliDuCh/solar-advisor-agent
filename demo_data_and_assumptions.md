# Solar Advisor demo data and assumptions

The dashboard uses a fictional household so the application can be demonstrated
without collecting a utility bill, address, account number, or inverter login.
All configurable demo values are stored in:

`src/solar_agent/data/demo_assumptions.json`

This catalog is the source of truth for the Streamlit dashboard and labeled
household scenarios. It replaces the former `sample_user.json` and
`sample_household.json` files.

## Household

| Field | Demonstration value |
|---|---:|
| ZIP code | 98052 |
| Annual electricity consumption | 10,800 kWh |
| Occupants | 2 |
| Work-from-home profile | Enabled |

The ZIP code is an approximate location input, not a complete street address.
Annual consumption is an example and is not presented as a national average or
as measured customer data.

## Existing solar array

The example is an 8.0 kW DC mixed-orientation array:

| Section | Panels | Panel rating | Tilt | Azimuth | Shading |
|---|---:|---:|---:|---:|---:|
| South | 12 | 400 W | 30 degrees | 180 degrees | 4% |
| Southwest | 8 | 400 W | 24 degrees | 225 degrees | 7% |

The shared inverter limit is 7.6 kW AC. The catalog also declares 9% for
non-shading system losses. These values are explicit inputs to the deterministic
`pvlib` calculation; GPT-4.1-mini does not invent them.

## Appliances

| Appliance | Running power | Demonstration duration |
|---|---:|---:|
| Washer | 0.5 kW | 1 hour |
| Dryer | 4.5 kW | 0.75 hour |
| Dishwasher | 1.2 kW | 1.5 hours |
| Level 2 EV charging | 7.2 kW | 2 hours |

The Low, Medium, and High labels shown in the UI are relative to the other
appliances in this demonstration household. They are not electrical safety
ratings. Actual power must come from the appliance nameplate or reliable
manufacturer documentation.

## Financial and scenario assumptions

| Field | Demonstration value |
|---|---:|
| Illustrative electricity rate | $0.14/kWh |
| Illustrative installed system cost | $24,000 |
| Added freezer consumption | 500 kWh/year |
| Electric water-heating consumption | 3,000 kWh/year |

The freezer and water-heating values are labeled scenario defaults used only
when the user does not provide measured or product-specific data. Financial
results exclude taxes, fixed charges, financing, tariff tiers, export credits,
future rate changes, and equipment fuel costs unless explicitly supplied.

Tariff examples are maintained separately in
`src/solar_agent/data/tariff_profiles.json`.

## Weather and confidence

The current dashboard uses a 48-hour synthetic weather series. It does not claim
to be a live forecast. Aurora remains a future provider described in
`docs/AURORA_FUTURE_WORK.md`.

Confidence describes the quality and completeness of inputs and data sources;
it is not a probability that a recommendation is correct. Synthetic weather,
catalog assumptions, missing interval load data, and missing inverter telemetry
all reduce confidence.

## What the model does

The Streamlit dashboard calculates charts and metrics directly through
deterministic Python code. A model request occurs only after the user submits a
chat message:

`app.py -> handle_message() -> HandoffBuilder -> specialist agent -> FoundryChatClient -> GPT-4.1-mini -> deterministic skill`

GPT-4.1-mini chooses the relevant specialist and tool and explains the result.
Python skills calculate watts, kWh, costs, schedules, and scenario changes. The
model is not trusted to invent numerical inputs or perform electrical design.

## Real versus simulated

| Component | Current state |
|---|---|
| Agent orchestration | Microsoft Agent Framework handoff workflow |
| Conversation model | Foundry deployment configured by `FOUNDRY_MODEL` |
| Solar calculations | Deterministic `pvlib` and Python functions |
| Household and appliances | Fictional catalog values |
| Weather | Synthetic 48-hour series |
| Inverter telemetry | Simulated adapter |
| Aurora | Documented future provider |
| Authentication and persistence | Not yet production-complete |

The application is advisory only. It must not provide wiring, breaker sizing,
code-compliance approval, rooftop work instructions, or permission to open
energized equipment.
