import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from solar_agent.agents.financial_agent import build_financial_agent  # noqa: E402

agent = build_financial_agent()
