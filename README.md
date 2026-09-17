# Solar Advisor Agent

AI agent system that helps homeowners size, optimize, and maintain solar panel
systems — for the "Hack for Industry: Energy & Resources" challenge.

Built on [Microsoft Agent Framework](https://github.com/microsoft/agent-framework)
(Python), with forecasts from [Microsoft Aurora](https://github.com/microsoft/aurora)
(via Azure AI Foundry) falling back to Open-Meteo when Aurora access/setup isn't
ready.

See `docs/ARCHITECTURE.md` for the full design doc (agents, skills, data flow,
security, and the Aurora integration decision gate).

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m solar_agent.orchestrator
```

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
