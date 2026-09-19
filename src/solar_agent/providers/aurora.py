from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class AuroraRunRequest:
    initialization_time: datetime
    mode: str
    forecast_hours: int = 48
    location_zip: str = "98052"


class AuroraPipeline:
    """Production boundary for ERA5 -> Aurora Foundry -> validated local artifact."""

    def __init__(self, artifact_directory: Path) -> None:
        self.artifact_directory = artifact_directory

    def validate_environment(self) -> list[str]:
        import os

        required = [
            "AURORA_FOUNDRY_ENDPOINT",
            "AURORA_FOUNDRY_TOKEN",
            "AURORA_BLOB_SAS_URL",
            "CDS_API_KEY",
        ]
        return [name for name in required if not os.getenv(name)]

    def run(self, request: AuroraRunRequest) -> Path:
        missing = self.validate_environment()
        if missing:
            raise RuntimeError(
                "Aurora pipeline is not configured. Missing environment variables: "
                + ", ".join(missing)
            )
        raise NotImplementedError(
            "Complete the exact ERA5 variable mapping from the deployed Aurora 1.5 example "
            "after Azure and CDS access are confirmed. Synthetic values must never fill "
            "missing fields."
        )
