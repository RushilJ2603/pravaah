"""Focused acceptance tests for the chronological crowd baseline."""

from datetime import UTC, datetime, timedelta

import pytest

from pravaah.contracts.events import OccupancyClass
from pravaah.contracts.provenance import SourceType
from pravaah.models.baseline import (
    SIMULATOR_METRICS_LABEL,
    BaselineModel,
    TrainingRow,
    fit_rows,
)

START = datetime(2026, 8, 1, tzinfo=UTC)


def _rows(count: int = 100) -> list[TrainingRow]:
    rows = []
    for index in range(count):
        ratio = 0.2 if index < 80 else 0.9
        crowd_class = (
            OccupancyClass.MANY_SEATS_AVAILABLE
            if ratio < 0.5
            else OccupancyClass.CRUSHED_STANDING_ROOM_ONLY
        )
        rows.append(
            TrainingRow(
                ts=START + timedelta(minutes=index),
                route_id="R1",
                position=0.5,
                occupancy_ratio=ratio,
                occupancy_class=crowd_class,
                source_type=SourceType.SIMULATED,
                source_name="simulator_v1",
            )
        )
    return rows


def test_simulated_history_requires_explicit_opt_in():
    with pytest.raises(ValueError, match="allow_simulated=True"):
        fit_rows(_rows(), "test-city", "UTC")


def test_fit_is_chronological_and_metrics_are_disclosed_as_simulator_only():
    model = fit_rows(
        reversed(_rows()),
        "test-city",
        "UTC",
        allow_simulated=True,
    )

    assert model.train_rows == 80
    assert model.test_rows == 20
    assert model.train_end < model.test_start
    assert model.training_source_types == ["SIMULATED"]
    assert model.metrics_label == SIMULATOR_METRICS_LABEL
    assert model.real_world_accuracy is False
    assert model.metrics["mae"] == pytest.approx(0.7)
    assert "pinball_p10" in model.metrics
    assert "threshold_weighted_mae" in model.metrics


def test_prediction_keeps_quantiles_version_and_simulated_disclosure(tmp_path):
    model = fit_rows(_rows(200), "test-city", "UTC", allow_simulated=True)
    forecast = model.predict("R1", START + timedelta(minutes=10), 0.5)

    assert forecast.p10_ratio <= forecast.p50_ratio <= forecast.p90_ratio
    assert forecast.model_version == model.model_version
    assert forecast.training_source_types == ("SIMULATED",)
    assert forecast.metrics_label == SIMULATOR_METRICS_LABEL

    path = tmp_path / "baseline.json"
    path.write_text(model.to_json(), encoding="utf-8")
    loaded = BaselineModel.load(path)
    assert loaded.predict("R1", START, 0.5) == model.predict("R1", START, 0.5)
