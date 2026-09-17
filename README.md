# Solar Advisor Agent

AI agent system that helps homeowners size, optimize, and maintain solar panel
systems — for the "Hack for Industry: Energy & Resources" challenge.

Built on [Microsoft Agent Framework](https://github.com/microsoft/agent-framework)
(Python), with forecasts from [Microsoft Aurora](https://github.com/microsoft/aurora)
(via Azure AI Foundry) falling back to Open-Meteo when Aurora access/setup isn't
ready.

See `docs/ARCHITECTURE.md` for the full design doc (agents, skills, data flow,
security, and the Aurora integration decision gate), and `docs/USER_MANUAL.md`
for step-by-step run instructions and troubleshooting.

## Requirements

- **Python 3.10+** (`agent-framework` will not install on older versions).
  On Windows, plain `python`/`py` often resolves to an old bundled interpreter
  (e.g. a Visual Studio-installed Python 3.9) even if a newer one is present.
  Check what's available with:
  ```powershell
  py -0p
  ```
  If you see a 3.10+ entry (e.g. `-3.14-64`) alongside an older default, pin it
  explicitly in every command below (`py -3.14 ...`), or better, create the
  venv with it once so plain `python`/`pip` resolve correctly afterwards.

## Quick start

```powershell
py -3.13 -m venv .venv
.venv\Scripts\activate
python -m pip install -e ".[dev]"
streamlit run app.py
```

The dashboard runs immediately with an explicitly labeled deterministic
fallback. To activate the real Microsoft Agent Framework workflow, deploy a
chat model in Microsoft Foundry, authenticate with Azure CLI, and create a
local `.env`:

```powershell
az login
copy .env.example .env
notepad .env
```

Set:

```dotenv
FOUNDRY_PROJECT_ENDPOINT=https://<resource>.services.ai.azure.com/api/projects/<project>
FOUNDRY_MODEL=<chat-model-deployment-name>
```

The dashboard then uses a real Agent Framework handoff workflow:
`SolarAdvisor` routes to Forecast, Financial, Maintenance, Safety, or Sizing.
The specialists call deterministic Python skills for watts, kWh, cost, and
maintenance calculations. Aurora is a separate weather-model integration and
is not required for conversational chat.

### Run the tests (no API key needed)
```powershell
python -m pytest tests -q
```

### Legacy FastAPI demo (no model needed)
```powershell
python -m pip install fastapi uvicorn
python -m solar_agent.web.app
```
Opens `http://127.0.0.1:8000` - a graphical dashboard (all power figures in
**kW**) plus a chat panel with the same 5 agents (Sizing, Forecast,
Maintenance, Financial, Safety), against a made-up demo household
("Alex Rivera", Redmond WA - synthetic, no real data):
- 4 stat cards (System Health, Current Output, Panels Recommended, Payback)
- a color-coded **bar chart** of the next 24h expected output per hour -
  green = peak sun hour, amber = medium, gray = low/night - hover a bar for
  the low/high estimate range
- an **Appliances** section with 3-4 common devices, their draw in kW, and a
  colored Low/Medium/High usage tag
- hover the **ⓘ** icon next to any card, chart, or section heading for a
  plain-language explanation of that term

Replies are **rule-based templates, not an LLM** - but every number
(forecast, kW, sizing, payback) is a genuine live call to the real skills
(Open-Meteo + solar math), not fabricated. This is the fastest way to see
what the product looks like; swap to the LLM-backed agents below once a key
is available.

### Optional Agent Framework DevUI
```powershell
python -m pip install -e ".[devui]"
devui ui_agents --port 8080
```
If `devui` isn't recognized (its console-script exe isn't on PATH), call the
CLI's `main()` directly instead - this always works once the package is
installed:
```powershell
python -c "import sys; sys.argv=['devui','ui_agents','--port','8080']; from agent_framework_devui._cli import main; main()"
```
Opens `http://localhost:8080` with all 5 agents (Sizing, Forecast,
Maintenance, Financial, Safety) selectable in the sidebar. DevUI prints an
auth token at startup - pass it as `Authorization: Bearer <token>` for direct
API calls, or use `--no-auth` for local-only loopback testing.

## Layout

```
src/solar_agent/
  agents/        # LLM-backed reasoning units (Sizing, Forecast, Maintenance, Financial, Safety)
  skills/        # Deterministic Python functions agents call as tools (no LLM math)
  adapters/      # Device adapter interface + simulated inverter telemetry
  security/      # PII redaction middleware
  data/          # Sample household + tariff profiles (synthetic, no real user data)
  orchestrator.py
tests/
docs/ARCHITECTURE.md
```

## Status

The repository contains a working Agent Framework handoff workflow and a
Streamlit dashboard. Without Foundry configuration the UI uses an explicit
local fallback; with `FOUNDRY_PROJECT_ENDPOINT` and `FOUNDRY_MODEL`, the same
chat invokes the live multi-agent workflow. Forecast data remains synthetic
in the dashboard until a live provider is enabled, and Aurora remains a
documented future integration.
