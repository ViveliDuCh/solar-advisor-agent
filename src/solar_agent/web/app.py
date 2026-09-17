"""Standalone demo web app - no LLM API key required.

Run with:
    python -m solar_agent.web.app
Then open http://127.0.0.1:8000
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from solar_agent.web.dummy_responses import REPLY_FUNCS, load_sample_user

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(title="Solar Advisor - Demo UI")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

AGENTS = [
    {"id": "sizing", "name": "Sizing Agent", "blurb": "How many panels do I need?"},
    {"id": "forecast", "name": "Forecast Agent", "blurb": "What should I run, and when?"},
    {"id": "maintenance", "name": "Maintenance Agent", "blurb": "Is my system healthy?"},
    {"id": "financial", "name": "Financial Agent", "blurb": "What's my payback?"},
    {"id": "safety", "name": "Safety Agent", "blurb": "Electrical safety & battery tradeoffs"},
]


class ChatRequest(BaseModel):
    agent: str
    message: str


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/agents")
async def list_agents() -> list[dict]:
    return AGENTS


@app.get("/api/user")
async def get_user() -> dict:
    """The synthetic demo household (Alex Rivera) - no real user data."""
    return load_sample_user()


@app.post("/api/chat")
async def chat(req: ChatRequest) -> dict:
    reply_fn = REPLY_FUNCS.get(req.agent)
    if reply_fn is None:
        return {"reply": f"Unknown agent '{req.agent}'."}
    household = load_sample_user()
    try:
        reply = await reply_fn(req.message, household)
    except Exception as exc:  # noqa: BLE001 - surface errors to the demo UI directly
        reply = f"(demo error calling live weather data: {exc})"
    return {"reply": reply}


def main() -> None:
    import uvicorn

    uvicorn.run("solar_agent.web.app:app", host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    main()
