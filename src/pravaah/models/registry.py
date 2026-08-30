"""Serving-model selection with an explicit historical-baseline preference.

The simulator-derived Monte Carlo table remains a cold-start fallback. Once a
chronological baseline artifact exists, requests are served from learned
history and its SIMULATED training provenance remains visible in the model
version returned by every forecast endpoint.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Protocol
from zoneinfo import ZoneInfo

from .baseline import BaselineModel
from .crowd import CrowdForecaster, CrowdQuantiles


class ServingForecaster(Protocol):
    model_version: str

    def predict(
        self, hour: int, position: float, route_id: str | None = None
    ) -> CrowdQuantiles: ...


class HistoricalBaselineForecaster:
    """Adapt the fitted seasonal baseline to the API's serving contract."""

    def __init__(self, model: BaselineModel, capacity: int) -> None:
        self.model = model
        self.capacity = capacity
        disclosure = (
            "+simulated"
            if "SIMULATED" in model.training_source_types
            else "+historical"
        )
        self.model_version = f"{model.model_version}{disclosure}"

    @classmethod
    def load(cls, path: Path, capacity: int) -> HistoricalBaselineForecaster:
        return cls(BaselineModel.load(path), capacity)

    def predict(
        self, hour: int, position: float, route_id: str | None = None
    ) -> CrowdQuantiles:
        local_time = datetime(2000, 1, 3, hour=hour % 24, tzinfo=ZoneInfo(self.model.timezone))
        forecast = self.model.predict(route_id, local_time, position)
        if forecast.p50_ratio is None:
            return CrowdQuantiles.unknown(model_version=self.model_version)

        return CrowdQuantiles(
            p10_class=forecast.p10,
            p50_class=forecast.p50,
            p90_class=forecast.p90,
            p10_onboard=round((forecast.p10_ratio or 0.0) * self.capacity),
            p50_onboard=round(forecast.p50_ratio * self.capacity),
            p90_onboard=round((forecast.p90_ratio or 0.0) * self.capacity),
            p50_ratio=forecast.p50_ratio,
            capacity=self.capacity,
            model_version=self.model_version,
            is_fallback=forecast.is_fallback,
        )


def load_serving_forecaster(models_dir: Path, capacity: int) -> ServingForecaster:
    """Prefer learned history; retain the simulator table for cold start."""
    baseline_path = models_dir / "baseline_v1.json"
    if baseline_path.exists():
        return HistoricalBaselineForecaster.load(baseline_path, capacity)
    return CrowdForecaster.load(models_dir / "crowd_v1.json")
