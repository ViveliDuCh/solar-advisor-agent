import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from solar_agent.agents.safety_agent import build_safety_agent  # noqa: E402

agent = build_safety_agent()
