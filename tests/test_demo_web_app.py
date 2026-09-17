"""Smoke tests for the no-LLM demo web app (dummy_responses)."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from solar_agent.web.dummy_responses import (  # noqa: E402
    financial_reply,
    load_sample_user,
    maintenance_reply,
    safety_reply,
    sizing_reply,
)


def _run(coro):
    return asyncio.run(coro)


def test_sample_user_has_expected_fields():
    household = load_sample_user()
    assert household["user"]["name"]
    assert household["existing_system"]["panel_count"] > 0


def test_sizing_reply_mentions_panels():
    household = load_sample_user()
    reply = _run(sizing_reply("how many panels do I need", household))
    assert "panels" in reply.lower()


def test_financial_reply_has_payback():
    household = load_sample_user()
    reply = _run(financial_reply("what's my payback", household))
    assert "kWh/year" in reply


def test_maintenance_reply_returns_status():
    household = load_sample_user()
    reply = _run(maintenance_reply("is my system ok", household))
    assert "Producing" in reply or "shortfall" in reply.lower()


def test_safety_reply_never_empty():
    household = load_sample_user()
    reply = _run(safety_reply("are batteries toxic", household))
    assert len(reply) > 0
