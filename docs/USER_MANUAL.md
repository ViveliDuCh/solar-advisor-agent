# Solar Advisor — User Manual

This covers running the demo, what you'll see, and fixes for the setup
issues we've hit so far. See `docs/ARCHITECTURE.md` for the full technical
design (agents, skills, Aurora integration, security).

## 1. What this is

A prototype AI assistant that helps homeowners size, optimize, and maintain
a solar panel system. Two ways to run it:

| Mode | Needs a key? | What you get |
|---|---|---|
| **Demo dashboard/chat** (`solar_agent.web.app`) | No | Graphical dashboard + chat, rule-based replies, real computed numbers (live weather → watts → sizing/payback) |
| **Full LLM chat** (`devui ui_agents`) | Yes (OpenAI or Azure OpenAI) | The 5 real `agent_framework.Agent`s reasoning over the same skills |

Start with the demo dashboard — it needs nothing but Python and internet
access, and is the fastest way to see the product.

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
py -3.14 -m venv .venv
.venv\Scripts\activate
```

Install dependencies:
```powershell
cd C:\Users\vivianad\HACKATHON2026\solar-agent
python -m pip install --pre -r requirements.txt
python -m pip install fastapi uvicorn agent-framework-devui --pre
```
If your machine routes pip through a corporate proxy
(`packagefeedproxy.microsoft.io`) and it can't find these (pre-release)
packages, fall back to public PyPI for just these:
```powershell
python -m pip install --pre --index-url https://pypi.org/simple agent-framework agent-framework-foundry agent-framework-devui
```

## 3. Run the demo dashboard (recommended first run)

```powershell
cd C:\Users\vivianad\HACKATHON2026\solar-agent
$env:PYTHONPATH = "src"
python -m solar_agent.web.app
```
Open **http://127.0.0.1:8000**. You'll see:
- **4 summary cards**: System Health, Current Output, Panels Recommended, Payback Estimate
- **A 24h forecast chart** with a P10–P90 uncertainty band around the expected (P50) output
- **A chat panel** with 5 selectable agents (Sizing, Forecast, Maintenance, Financial, Safety) for Q&A

All numbers come from a synthetic demo household ("Alex Rivera", Redmond WA
— see `src/solar_agent/data/sample_user.json`), and from a **live** call to
Open-Meteo for the weather forecast, so the chart/cards change run to run.

Chat replies here are rule-based templates, not an LLM — clearly labeled as
demo mode. Every number shown is still a genuine computation, not fabricated.

**`ModuleNotFoundError: No module named 'solar_agent'`?** You forgot
`$env:PYTHONPATH = "src"` — the package lives under `src/`, which isn't on
Python's path by default.

**Port already in use?** Something else is bound to 8000 (maybe a previous
run you didn't stop). Find and stop it:
```powershell
Get-NetTCPConnection -LocalPort 8000 | Select OwningProcess
Stop-Process -Id <that PID>
```

## 4. Run the full LLM chat UI (needs a key)

```powershell
copy ui_agents\.env.example ui_agents\.env
notepad ui_agents\.env    # set OPENAI_API_KEY (or Azure OpenAI vars) + OPENAI_MODEL
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

## 5. Run the tests (no key needed)
```powershell
python -m pytest tests -q
```

## 6. Demo household & data used

Synthetic, no real PII (`src/solar_agent/data/sample_user.json`):
Alex Rivera, Redmond WA, 12×400W panels (4800W total), 30° tilt/south-facing,
~28 kWh/day usage, remote-worker occupancy, time-of-use tariff, $15,600
system cost.

Fields the real app would collect from an actual user: location, roof
tilt/azimuth, existing system size (or "none yet"), inverter capacity,
average daily kWh + tariff type (never a real bill upload), occupancy
pattern, appliance list, shading.

## 7. Weather / Aurora status

Default provider is **Open-Meteo** (free, live, no auth). Microsoft Aurora
(via Azure AI Foundry, or open MIT-licensed weights on Hugging Face) is
wired as a second provider behind the same interface
(`src/solar_agent/skills/weather_forecast_skill.py`) but not yet active —
see `docs/ARCHITECTURE.md` section 2 for the setup steps and trade-offs.

## 8. Repo & docs map

- `docs/ARCHITECTURE.md` — full design: Aurora decision gate, solar math,
  agents/skills, security, task split
- `src/solar_agent/skills/` — deterministic math (tested, no LLM)
- `src/solar_agent/agents/` — LLM agent definitions
- `src/solar_agent/web/` — demo dashboard (FastAPI + static JS/CSS)
- `ui_agents/` — DevUI-discoverable entities for the full LLM chat UI
- `tests/` — run with `pytest tests -q`
