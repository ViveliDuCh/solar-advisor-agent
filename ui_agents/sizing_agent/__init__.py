import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from solar_agent.agents.sizing_agent import build_sizing_agent  # noqa: E402

agent = build_sizing_agent()
