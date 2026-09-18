# Solar Advisor Agent — Demo Data & Assumptions

This documents every piece of synthetic data used in the no-LLM demo
dashboard/chat (`python -m solar_agent.web.app`), and the assumptions/formulas
behind each computed number. **Nothing here is real user data** — it's a
made-up household used only so the UI has something to show.

Source: `src/solar_agent/data/sample_user.json`

## Demo user: "Alex Rivera"

| Field | Value | Notes |
|---|---|---|
| Name / email | Alex Rivera / alex.rivera@example.com | Fictional, not a real person |
| Location | Redmond, WA (47.6740, -122.1215) | Real coordinates, used only to fetch a **real, live** Open-Meteo forecast for those coordinates |
| Roof tilt | 30° | Typical residential roof pitch |
| Roof azimuth | 180° (true south) | Optimal orientation in the northern hemisphere |
| Shading | none | Simplifying assumption — no tree/building shade modeled |
| Existing system | 12 panels × 400 W = 4.8 kW rated (STC) | Mid-size residential system |
| Inverter capacity | 5,000 W | Sized above panel rating (normal practice) |
| Avg daily consumption | 28.0 kWh/day | ~2x the US average household (855 kWh/mo vs. ~893 kWh/mo national avg used as base, then bumped up) |
| Occupancy | Full-time remote work | Drives the higher-than-average consumption assumption |
| Tariff profile | `time_of_use` | See `src/solar_agent/data/tariff_profiles.json` |
| System cost | $15,600 | Rough US market rate for a 4.8 kW installed system (~$3.25/W before incentives) |
| Appliances | Dishwasher 1,800 W, Washing machine 500 W, Clothes dryer 3,000 W, EV charger (Level 2) 7,200 W | Manufacturer-typical nameplate draws, not measured |

## Computed values shown on the dashboard, and how

All of these are **real function calls to the deterministic skills** — the
"dummy" part is only that a template, not an LLM, phrases the chat replies.
The math itself is genuine and re-runs live every request.

### Current Output / 24h forecast chart (kW)
- **Weather input**: live call to Open-Meteo's free forecast API for
  Redmond's lat/lon (no Aurora yet — see "Aurora status" below).
- **Formula** (`solar_output_skill.py`):
  `Power (W) = panel_rated_w_total × (irradiance / 1000) × system_derate × tilt/azimuth_factor × temp_derate`
  - `system_derate` = 0.80 (assumed wiring/inverter/soiling losses)
  - `temp_derate` = NOCT-based estimate, ~0.4%/°C loss above 25°C cell temp
  - P10/P50/P90 = ±10% / center / +10% band around the point estimate, to
    represent forecast uncertainty (not a real quantile regression — a
    simple symmetric spread placeholder)
- **Bar color tiers**: relative to that day's max P50 hour — ≥66% = "peak"
  (green), 33–66% = "medium" (amber), below that but non-zero = "low" (gray),
  zero = "none".

### System Health card
- Simulated inverter telemetry (`SimulatedInverterAdapter`) generates a
  plausible current reading (with occasional injected faults) and compares
  it to an "expected" output for that timestamp. >20% shortfall or a fault
  code ⇒ "Needs attention", otherwise "Healthy". This is **not real hardware
  telemetry** — there's no physical inverter connected in the demo.

### Panels Recommended card
- `sizing_skill.py`: `panels_needed = ceil(avg_daily_kwh / (peak_sun_hours × panel_rated_kw × system_derate))`
  using the day's actual peak sun hours from the live forecast (floored at
  2.5h so a very cloudy day doesn't wildly inflate the number).

### Payback Estimate card
- `tariff_payback_skill.py`: `payback_years = system_cost_usd / annual_savings_usd`
  - `annual_savings_usd` derived from `estimated_annual_generation_kwh` (a
    simplified `rated_kw × 4.2 avg sun-hours × 365 days × 0.8 derate`
    estimate — not the live forecast) × the `time_of_use` tariff's blended
    rate.
  - **Ignores**: panel degradation (~0.5%/yr), future rate changes,
    financing/interest, net-metering vs. self-consumption differences.
  - Demo result: **~13.9 years**, ~$1,118/yr savings.

### Appliance usage tags
- Thresholds on nameplate wattage only (not actual runtime/duty cycle):
  ≥2,500 W = High (red), 800–2,499 W = Medium (amber), <800 W = Low (green).

## What's real vs. simulated in this demo

| Component | Real | Simulated / placeholder |
|---|---|---|
| Weather forecast | ✅ Live Open-Meteo API call | Aurora integration not yet connected (pending Azure Foundry access — architecture + fallback documented in `docs/ARCHITECTURE.md`) |
| Solar output math | ✅ Real formulas, real skill code | Uncertainty band (P10/P90) is a simple ±10% placeholder, not a trained model |
| Sizing / payback math | ✅ Real formulas, real skill code | Cost, tariff rate, and consumption are hand-entered assumptions, not billing data |
| Inverter telemetry | ❌ | Fully simulated (`SimulatedInverterAdapter`) — no physical device |
| Chat replies | ❌ (demo mode) | Rule-based templates; the LLM-backed agents (`ui_agents/`) exist and use the same skills but need an API key to actually reason |
| User profile | ❌ | Fully fictional ("Alex Rivera") |

## Related docs in the repo
- `docs/ARCHITECTURE.md` — full system design, Aurora decision gate, agent/skill breakdown
- `docs/USER_MANUAL.md` — how to run both the demo and the full LLM chat UI
- `src/solar_agent/data/tariff_profiles.json` — the rate assumptions behind payback math
