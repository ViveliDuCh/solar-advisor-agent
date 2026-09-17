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
py -3.14 -m venv .venv
.venv\Scripts\activate
python -m pip install --pre -r requirements.txt
python -m pip install agent-framework-devui --pre
python -m solar_agent.orchestrator
```

Corporate/proxied pip index (e.g. `packagefeedproxy.microsoft.io`) may not
mirror these pre-release packages yet. If install fails with
"No matching distribution found", fall back to public PyPI for just these
packages:
```powershell
python -m pip install --pre --index-url https://pypi.org/simple agent-framework agent-framework-foundry agent-framework-devui
```

### Run the tests (no API key needed)
```powershell
python -m pytest tests -q
```

### See the UI right now (no API key needed)
```powershell
python -m pip install fastapi uvicorn
python -m solar_agent.web.app
```
Opens `http://127.0.0.1:8000` - a chat UI with the same 5 agents (Sizing,
Forecast, Maintenance, Financial, Safety) against a made-up demo household
("Alex Rivera", Redmond WA - synthetic, no real data). Replies are
**rule-based templates, not an LLM** - but every number (forecast, watts,
sizing, payback) is a genuine live call to the real skills (Open-Meteo +
solar math), not fabricated. This is the fastest way to see what the product
looks like; swap to the LLM-backed agents below once a key is available.

### Run the full LLM chat UI (needs an LLM key)
```powershell
copy ui_agents\.env.example ui_agents\.env
notepad ui_agents\.env    # set OPENAI_API_KEY (or Azure OpenAI vars) + OPENAI_MODEL
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

Hackathon scaffold — skills have working deterministic logic, agents are stubbed
with instructions + tool wiring pending an LLM client (Azure OpenAI / Foundry)
credential.
