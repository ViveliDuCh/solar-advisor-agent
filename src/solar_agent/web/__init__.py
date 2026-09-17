"""Zero-dependency demo web UI.

Runs without any LLM API key: "agent" replies here are rule-based templates
that still call the real deterministic skills (live Open-Meteo forecast,
solar output math, sizing, payback, simulated inverter telemetry) - so every
number shown is genuinely computed, just phrased by templates instead of an
LLM. Swap in solar_agent.agents / orchestrator.handle_message for real
LLM-backed replies once a key is available; the skills underneath are shared.
"""
