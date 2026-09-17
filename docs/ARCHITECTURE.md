# Solar Advisor — Architecture

Executive challenge: **Hack for Industry — Energy & Resources**.
Team: 2 people (hardware/electronics + backend/AI), Redmond WA.

## 1. Problem

~9% of US homes (~6M) have solar installed but most under-use it: no batteries,
no guidance on *when* to shift load to sun hours, no easy sizing help for new
buyers, and no plain-language safety/maintenance guidance. Goal: an AI agent
that turns weather + location + roof + consumption data into concrete hourly
actions ("run the dryer at 1pm"), sizing help for new users, maintenance
flags, and financial payback — all in plain, non-engineer language.

## 2. Forecast source — Aurora integration & decision gate

**Steps to call Aurora via Azure AI Foundry:**
1. Request access to `Aurora-1.5` in the Foundry model catalog
   (ai.azure.com/catalog/models/Aurora-1.5) — do this first; approval lag is
   the biggest schedule risk.
2. Collect `FOUNDRY_ENDPOINT`, `FOUNDRY_TOKEN`, and a Blob container + SAS URL
   (the Foundry Aurora API moves batches through blob storage, not inline).
3. Aurora needs an **initial atmospheric condition** grid (t=0 and t=-6h:
   temp, wind, pressure, etc.), not just a lat/lon. Sources:
   - **ECMWF Open Data** (free, 0.25°, closest to Aurora's native training grid)
   - **NOAA HRRR** (US-only, 3km, hourly) — best local precision
   - **Copernicus CDS ERA5** — reanalysis, ~5 day latency, backtesting only
4. Submit via `aurora.foundry.submit`, poll the 6-hourly output grid (to 10
   days out), extract the nearest cell, and read surface solar radiation
   (ssrd/shortwave flux), cloud cover, and 2m temp — the channels that feed
   the output model below.

**Decision gate:**

| | Aurora (Foundry) | Open-Meteo / NWS fallback |
|---|---|---|
| Setup risk | Access approval + shaping initial-condition tensors = real lift | Zero-auth REST, hourly GHI/cloud cover in minutes |
| Resolution | 0.25° global grid, 6h steps — coarse per rooftop | Already localized, hourly |
| Judge appeal | High — uses MSR's own foundation model | Lower but reliable |
| Demo latency | Foundry batch jobs aren't instant | Instant |

**Decision:** implement `WeatherForecastSkill` against Open-Meteo first (always
demoable), keep Aurora as a second provider behind the same interface, and
flip to it if ready by demo day.

## 3. Solar output model (per house), with uncertainty

```
Instant Power (W) = Panel rated W (STC)
                   × (irradiance / 1000 W/m²)
                   × system derate            # 0.75–0.85: wiring/inverter/soiling/mismatch loss
                   × tilt/azimuth factor
                   × temp_derate(ambient, irradiance)   # ~0.3–0.5%/°C above 25°C cell temp
```

Uncertainty band: run at P10/P50/P90 irradiance (ensemble spread if available,
else a cloud-cover-derived band), widening with forecast lead time. Output a
range + confidence, e.g. *"3.2–4.1 kWh between 12–2pm, P50 ≈ 3.6 kWh"* — never
a false-precision single number.

**Minimum user inputs:** location, roof orientation + tilt, existing system
size (or "none yet"), inverter capacity, sample monthly usage + tariff type
(synthetic, never a real bill), occupancy pattern, optional appliance list,
optional shading info.

## 4. Agents & Skills

Agent Framework concept: an **Agent** = LLM + instructions + tool access,
decides *when* to act. A **Skill** = a plain deterministic Python function —
all math (watts, dollars, safety limits) lives in skills, never freehand LLM
arithmetic.

| Agent | Role | Skills used |
|---|---|---|
| Orchestrator ("Solar Advisor") | User-facing router | — |
| Sizing Agent | "How many panels do I need" | `sizing_skill` |
| Forecast/Optimization Agent | Hourly output + appliance-timing suggestions | `weather_forecast_skill`, `solar_output_skill`, `appliance_scheduler_skill` |
| Maintenance Agent | Flags underperformance vs. expected curve | `inverter_sim_skill` (→ real adapter later) |
| Financial Agent | Payback/ROI | `tariff_payback_skill` |
| Safety/Education Agent | Plain-language electrical safety & battery tradeoffs, grounded in a small vetted reference set | — |

Wired as a workflow graph (sequential/handoff): Orchestrator routes →
specialist calls skill(s) → structured result → Orchestrator phrases the
answer in plain language.

## 5. Simulating hardware without giving anything up

Real inverter OAuth (SolarEdge/Enphase) needs vendor developer accounts that
can't be obtained mid-hackathon — an access blocker, not physics. Fix: a
`DeviceAdapter` interface with a `SimulatedInverterAdapter` that generates
realistic telemetry from `solar_output_skill` plus injected noise/faults, so
Maintenance/Notification logic runs on a stream indistinguishable from real
hardware in the demo. A `RealSolarEdgeAdapter` slots into the same interface
later (dependency inversion) — worth stating explicitly to judges.
Live notifications need no simulation: a scheduler runs the Optimization
Agent hourly and pushes real recommendation events. Tariff payback ships 2–3
real published rate-structure profiles (flat/tiered/TOU) as selectable
examples instead of requiring a bill upload.

## 6. Security & privacy

- Never persist raw utility bill uploads; only synthetic/example profiles are
  used in the demo.
- PII redaction middleware strips address/usage data from logs and traces
  before they reach any observability sink.
- Data at rest encrypted (Azure Key Vault + storage encryption), scoped per
  session, opt-in retention.
- In-app disclaimer: prototype — do not enter real personal financial data.

## 7. Repo & task split

Repo hosted on personal GitHub (github.com/ViveliDuCh) per current `gh` auth;
move to GitHub EMU or ADO if required by hackathon rules.

- **Backend/AI (C#/.NET runtime maintainer, Python for this project):**
  Agent Framework orchestration, `weather_forecast_skill` (Open-Meteo + Aurora
  swap-in), Forecast/Financial agents, chat API, PII middleware.
- **Hardware/electronics (Surface team):** `solar_output_skill` physics,
  `sizing_skill`, electrical-design/safety reference content,
  `inverter_sim_skill` fault model.
- **Shared:** web frontend, demo dataset/script, tariff profiles.
