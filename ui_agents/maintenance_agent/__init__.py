import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from solar_agent.agents.maintenance_agent import build_maintenance_agent  # noqa: E402

agent = build_maintenance_agent()
