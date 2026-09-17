# Solar Advisor — User Manual

This covers running the demo, what you'll see, and fixes for the setup
issues we've hit so far. See `docs/ARCHITECTURE.md` for the full technical
design (agents, skills, Aurora integration, security).

## 1. What this is

A prototype AI assistant that helps homeowners understand, optimize, and maintain
a solar panel system. There are three local interfaces:

| Interface | Address | Purpose |
|---|---|---|
| **Primary Streamlit product UI** (`app.py`) | `http://localhost:8501` | Main household dashboard, 48-hour opportunity heatmap, recommendations, confidence, finance, maintenance, and Agent Framework chat |
| **Upstream FastAPI prototype** (`solar_agent.web.app`) | `http://127.0.0.1:8000` | Secondary graphical demo retained from the base repository |
| **Agent Framework DevUI** (`devui ui_agents`) | `http://localhost:8080` | Developer interface for inspecting individual specialist agents |

Start with the Streamlit product UI. Without Foundry configuration it clearly
uses a local deterministic chat fallback; with Foundry configured it invokes
the multi-agent handoff workflow.

## 2. One-time setup

**Requirement: Python 3.10+.** On Windows, `python`/`py` may default to an
older bundled interpreter. Check what's installed:
```powershell
py -0p
```
If you see both an old default (e.g. 3.9) and a newer one (e.g. 3.14), pin
the newer one explicitly in every command below, or create a venv with it
once so plain `python` resolves correctly afterwards:
```powershell
py -3.13 -m venv .venv
.venv\Scripts\activate
```

Install dependencies:
```powershell
cd C:\Users\ebeltrnreyes\source\repos\solar-advisor-agent
python -m pip install -e ".[dev]"
```

## 3. Run the primary product UI

```powershell
cd C:\Users\ebeltrnreyes\source\repos\solar-advisor-agent
.\.venv\Scripts\python.exe -m streamlit run app.py
```
Open **http://localhost:8501**. The current product UI shows:

- Editable household and mixed-array assumptions
- One 48-hour solar-opportunity heatmap
- Appliance schedules with running kW and Low/Medium/High usage relative to
  that household's average hourly demand
- Explicit confidence definitions and missing data
- Simulated maintenance and simple financial examples
- Agent Framework chat, or a clearly labeled deterministic fallback

The current Streamlit weather is synthetic and is never labeled as Aurora.

**Port already in use?** Something else is bound to 8501 (maybe a previous
run you didn't stop). Find and stop it:
```powershell
Get-NetTCPConnection -LocalPort 8501 | Select OwningProcess
Stop-Process -Id <that PID>
```

## 4. Run the merged upstream FastAPI prototype

```powershell
python -m solar_agent.web.app
```

Open **http://127.0.0.1:8000**. The September 17 upstream merge added a
graphical dashboard, kW unit corrections, hover explanations, a 24-hour
peak-sun-hours chart, appliance usage tags, and this user manual. It remains
a secondary prototype; the Streamlit UI is the integration target.

## 5. Activate live Agent Framework chat

Authenticate with Azure CLI, then create `.env` from `.env.example`:

```dotenv
FOUNDRY_PROJECT_ENDPOINT=https://<resource>.services.ai.azure.com/api/projects/<project>
FOUNDRY_MODEL=<chat-model-deployment-name>
```

Restart Streamlit. The status banner should change from **Offline fallback**
to **Live multi-agent mode**.

## 6. Optional Agent Framework DevUI

```powershell
python -m pip install -e ".[devui]"
copy ui_agents\.env.example ui_agents\.env
devui ui_agents --port 8080
```
If `devui` isn't recognized (its console-script exe isn't on PATH), call the
CLI's `main()` directly instead:
```powershell
python -c "import sys; sys.argv=['devui','ui_agents','--port','8080']; from agent_framework_devui._cli import main; main()"
```
Open **http://localhost:8080**. If prompted for an auth token, scroll up in
the terminal to a line like `DEV TOKEN (localhost only, shown once): abc...`
and paste that in — it's a session token DevUI generates each run, not your
LLM key. Use `--no-auth` to skip this for local-only testing.

If it loads but shows **"No agents or workflows found"**: you're either not
running the command from the `solar-agent` folder (so it scanned an empty
directory instead of `ui_agents`), or `ui_agents/.env` is missing a valid
`OPENAI_API_KEY`/`OPENAI_MODEL` (each agent fails to construct and is
silently skipped).

## 7. Run the tests (no key needed)
```powershell
python -m pytest tests -q
```

## 8. Demo household & data used

Synthetic, no real PII (`src/solar_agent/data/sample_user.json`):
Alex Rivera, Redmond WA, 12×400W panels (4800W total), 30° tilt/south-facing,
~28 kWh/day usage, remote-worker occupancy, time-of-use tariff, $15,600
system cost.

Fields the real app would collect from an actual user: location, roof
tilt/azimuth, existing system size (or "none yet"), inverter capacity,
average daily kWh + tariff type (never a real bill upload), occupancy
pattern, appliance list, shading.

## 9. Weather / Aurora status

The primary Streamlit dashboard currently uses an explicitly labeled synthetic
48-hour provider for repeatable demonstrations. The merged FastAPI prototype
uses Open-Meteo. Microsoft Aurora remains preserved behind provider boundaries
and in `docs/AURORA_FUTURE_WORK.md`; it is not yet active or claimed as the
source of any displayed forecast.

## 10. Repo & docs map

- `docs/ARCHITECTURE.md` — full design: Aurora decision gate, solar math,
  agents/skills, security, task split
- `src/solar_agent/skills/` — deterministic math (tested, no LLM)
- `src/solar_agent/agents/` — LLM agent definitions
- `app.py` — primary Streamlit product UI
- `src/solar_agent/web/` — demo dashboard (FastAPI + static JS/CSS)
- `ui_agents/` — DevUI-discoverable entities for the full LLM chat UI
- `tests/` — run with `pytest tests -q`
