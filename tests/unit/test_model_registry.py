"""Serving selection keeps learned history ahead of the simulator fallback."""

from datetime import UTC, datetime, timedelta

from pravaah.contracts.events import OccupancyClass
from pravaah.contracts.provenance import SourceType
from pravaah.models.baseline import TrainingRow, fit_rows
from pravaah.models.registry import HistoricalBaselineForecaster, load_serving_forecaster


def _fitted_model():
    start = datetime(2026, 8, 30, tzinfo=UTC)
    rows = [
        TrainingRow(
            ts=start + timedelta(seconds=index),
            route_id="R1",
            position=0.5,
            occupancy_ratio=0.7,
            occupancy_class=OccupancyClass.STANDING_ROOM_ONLY,
            source_type=SourceType.SIMULATED,
            source_name="simulator_v1",
        )
        for index in range(100)
    ]
    return fit_rows(rows, "delhi", "UTC", allow_simulated=True)


def test_historical_adapter_exposes_simulated_disclosure_and_quantiles():
    forecaster = HistoricalBaselineForecaster(_fitted_model(), capacity=100)

    forecast = forecaster.predict(0, 0.5, "R1")

    assert forecaster.model_version.endswith("+simulated")
    assert forecast.model_version == forecaster.model_version
    assert forecast.p10_onboard <= forecast.p50_onboard <= forecast.p90_onboard
    assert forecast.p50_ratio == 0.7


def test_registry_prefers_fitted_baseline_when_both_artifacts_exist(tmp_path):
    (tmp_path / "baseline_v1.json").write_text(
        _fitted_model().to_json(), encoding="utf-8"
    )
    (tmp_path / "crowd_v1.json").write_text("not the selected model", encoding="utf-8")

    forecaster = load_serving_forecaster(tmp_path, capacity=100)

    assert isinstance(forecaster, HistoricalBaselineForecaster)
    assert forecaster.model_version.endswith("+simulated")
