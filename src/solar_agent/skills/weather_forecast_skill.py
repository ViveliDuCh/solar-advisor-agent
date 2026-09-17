"""WeatherForecastSkill: provider-agnostic hourly forecast.

Two providers implement the same contract so the rest of the system never
cares which one is active:

- ``OpenMeteoProvider``: zero-auth REST, hourly GHI + cloud cover. Used by
  default so the app is demoable on day one.
- ``AuroraFoundryProvider``: calls Microsoft Aurora on Azure AI Foundry.
  Requires FOUNDRY_ENDPOINT / FOUNDRY_TOKEN / a blob SAS URL and a prepared
  initial-condition batch (see docs/ARCHITECTURE.md section 2). Stubbed here
  pending Foundry access approval.

Switch providers with the ``SOLAR_AGENT_WEATHER_PROVIDER`` env var
("open-meteo" | "aurora"); defaults to "open-meteo".
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Annotated, Protocol

import httpx
from pydantic import Field

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


@dataclass
class HourlyForecast:
    """One hour of forecast data at a location."""

    timestamp: datetime
    ghi_w_m2: float  # global horizontal irradiance, W/m^2
    cloud_cover_pct: float
    temp_c: float
    wind_speed_ms: float


class WeatherProvider(Protocol):
    async def get_forecast(
        self, lat: float, lon: float, hours: int
    ) -> list[HourlyForecast]: ...


class OpenMeteoProvider:
    """Default provider: no auth required, good enough for a live demo."""

    async def get_forecast(
        self, lat: float, lon: float, hours: int = 48
    ) -> list[HourlyForecast]:
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "shortwave_radiation,cloud_cover,temperature_2m,wind_speed_10m",
            "forecast_days": max(1, hours // 24 + 1),
        }
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(OPEN_METEO_URL, params=params)
            resp.raise_for_status()
            data = resp.json()["hourly"]

        results = []
        for i, ts in enumerate(data["time"][:hours]):
            results.append(
                HourlyForecast(
                    timestamp=datetime.fromisoformat(ts),
                    ghi_w_m2=data["shortwave_radiation"][i],
                    cloud_cover_pct=data["cloud_cover"][i],
                    temp_c=data["temperature_2m"][i],
                    wind_speed_ms=data["wind_speed_10m"][i],
                )
            )
        return results


class AuroraFoundryProvider:
    """Microsoft Aurora via Azure AI Foundry.

    TODO (backend/AI owner):
      1. pip install agent-framework-foundry
      2. Build the initial-condition batch from ECMWF Open Data / NOAA HRRR
         (see docs/ARCHITECTURE.md) and upload to the blob SAS URL.
      3. Call ``aurora.foundry.submit(...)``, poll for completion, and map
         the returned grid's ssrd/cloud-cover/2m-temp channels onto
         ``HourlyForecast`` for the nearest grid cell to (lat, lon).
    """

    def __init__(self) -> None:
        self.endpoint = os.environ.get("FOUNDRY_ENDPOINT")
        self.token = os.environ.get("FOUNDRY_TOKEN")
        self.blob_url = os.environ.get("BLOB_URL_WITH_SAS")

    async def get_forecast(
        self, lat: float, lon: float, hours: int = 48
    ) -> list[HourlyForecast]:
        raise NotImplementedError(
            "Aurora Foundry provider not wired yet - see TODO in this class "
            "and docs/ARCHITECTURE.md section 2. Falls back to OpenMeteoProvider "
            "until implemented."
        )


def get_provider() -> WeatherProvider:
    name = os.environ.get("SOLAR_AGENT_WEATHER_PROVIDER", "open-meteo")
    if name == "aurora":
        return AuroraFoundryProvider()
    return OpenMeteoProvider()


async def get_hourly_forecast(
    lat: Annotated[float, Field(description="Latitude of the house")],
    lon: Annotated[float, Field(description="Longitude of the house")],
    hours: Annotated[int, Field(description="Number of hours to forecast")] = 48,
) -> list[dict]:
    """Agent-callable tool: hourly weather forecast for a location.

    Returns a list of dicts (timestamp, ghi_w_m2, cloud_cover_pct, temp_c,
    wind_speed_ms) so it can be passed directly as an LLM tool result.
    """
    provider = get_provider()
    try:
        forecast = await provider.get_forecast(lat, lon, hours)
    except NotImplementedError:
        forecast = await OpenMeteoProvider().get_forecast(lat, lon, hours)

    return [
        {
            "timestamp": f.timestamp.isoformat(),
            "ghi_w_m2": f.ghi_w_m2,
            "cloud_cover_pct": f.cloud_cover_pct,
            "temp_c": f.temp_c,
            "wind_speed_ms": f.wind_speed_ms,
        }
        for f in forecast
    ]
