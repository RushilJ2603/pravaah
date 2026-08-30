"""Seasonal-median crowd baseline trained from canonical occupancy history.

The baseline deliberately learns only route/hour/position quantiles. It is
fitted on the chronological head of history and scored on the held-out tail;
random splitting is not supported. Synthetic labels require explicit opt-in
and remain disclosed on the model artifact and every prediction.

Run from ``src/`` (see PROJECT_STATE.md):

    python -m pravaah.models.baseline fit --allow-simulated
"""

from __future__ import annotations

import argparse
import json
import logging
import math
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from ..contracts.events import OccupancyClass
from ..contracts.provenance import SourceType

log = logging.getLogger(__name__)

MODEL_KIND = "seasonal_median"
MODEL_VERSION = "seasonal_median_v1"
PROFILE_BUCKETS = 10
MIN_GROUP_OBSERVATIONS = 30
FALLBACK_LEVELS = ("route_hour_pos", "route_hour", "hour", "global")
SIMULATOR_METRICS_LABEL = "SIMULATOR_PERFORMANCE_ONLY_NOT_REAL_WORLD_ACCURACY"

_LADDER = [
    OccupancyClass.EMPTY,
    OccupancyClass.MANY_SEATS_AVAILABLE,
    OccupancyClass.FEW_SEATS_AVAILABLE,
    OccupancyClass.STANDING_ROOM_ONLY,
    OccupancyClass.CRUSHED_STANDING_ROOM_ONLY,
    OccupancyClass.FULL,
]


@dataclass(frozen=True)
class TrainingRow:
    """One joined history row, already normalized to position along its route."""

    ts: datetime
    route_id: str
    position: float
    occupancy_ratio: float
    occupancy_class: OccupancyClass
    source_type: SourceType
    source_name: str


@dataclass(frozen=True)
class CrowdForecast:
    """A historical crowd prediction with its training provenance attached."""

    p10: OccupancyClass
    p50: OccupancyClass
    p90: OccupancyClass
    p10_ratio: float | None
    p50_ratio: float | None
    p90_ratio: float | None
    basis: str
    is_fallback: bool
    observations: int
    model_version: str
    training_source_types: tuple[str, ...]
    metrics_label: str

    @classmethod
    def unknown(
        cls,
        model_version: str,
        training_source_types: Iterable[str],
        metrics_label: str,
        basis: str = "none",
    ) -> CrowdForecast:
        return cls(
            p10=OccupancyClass.UNKNOWN,
            p50=OccupancyClass.UNKNOWN,
            p90=OccupancyClass.UNKNOWN,
            p10_ratio=None,
            p50_ratio=None,
            p90_ratio=None,
            basis=basis,
            is_fallback=True,
            observations=0,
            model_version=model_version,
            training_source_types=tuple(training_source_types),
            metrics_label=metrics_label,
        )


@dataclass
class BaselineModel:
    """Fitted quantile tables plus the audit data needed to describe the fit."""

    model_version: str
    kind: str
    fitted_at: str
    timezone: str
    city_id: str
    train_rows: int
    test_rows: int
    train_end: str
    test_start: str
    training_source_types: list[str]
    training_source_names: list[str]
    metrics_label: str
    real_world_accuracy: bool
    tables: dict[str, dict[str, list[float]]] = field(default_factory=dict)
    metrics: dict[str, float] = field(default_factory=dict)
    fit_warnings: list[str] = field(default_factory=list)

    def predict(
        self,
        route_id: str | None,
        when: datetime,
        position: float | None = None,
    ) -> CrowdForecast:
        if when.tzinfo is None:
            raise ValueError("forecast timestamp must be timezone-aware")

        hour = when.astimezone(ZoneInfo(self.timezone)).hour
        bucket = None if position is None else _position_bucket(position)
        candidates: list[tuple[str, str]] = []
        if route_id and bucket is not None:
            candidates.append(("route_hour_pos", f"{route_id}|{hour}|{bucket}"))
        if route_id:
            candidates.append(("route_hour", f"{route_id}|{hour}"))
        candidates.append(("hour", str(hour)))
        candidates.append(("global", "all"))

        for index, (level, key) in enumerate(candidates):
            row = self.tables.get(level, {}).get(key)
            if row:
                return self._to_forecast(row, level, is_fallback=index > 0)
        return CrowdForecast.unknown(
            self.model_version,
            self.training_source_types,
            self.metrics_label,
        )

    def _to_forecast(
        self, row: list[float], basis: str, is_fallback: bool
    ) -> CrowdForecast:
        p10_ratio, p50_ratio, p90_ratio, p10_class, p50_class, p90_class, count = row
        return CrowdForecast(
            p10=_class_from_ordinal(p10_class),
            p50=_class_from_ordinal(p50_class),
            p90=_class_from_ordinal(p90_class),
            p10_ratio=p10_ratio,
            p50_ratio=p50_ratio,
            p90_ratio=p90_ratio,
            basis=basis,
            is_fallback=is_fallback,
            observations=int(count),
            model_version=self.model_version,
            training_source_types=tuple(self.training_source_types),
            metrics_label=self.metrics_label,
        )

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True)

    @classmethod
    def load(cls, path: Path) -> BaselineModel:
        return cls(**json.loads(path.read_text(encoding="utf-8")))


def _class_from_ordinal(value: float) -> OccupancyClass:
    index = max(0, min(int(round(value)), len(_LADDER) - 1))
    return _LADDER[index]


def _position_bucket(position: float) -> int:
    return max(0, min(int(position * PROFILE_BUCKETS), PROFILE_BUCKETS - 1))


def _quantile(values: list[float], q: float) -> float:
    """Linear quantile matching pandas' default, without a dataframe dependency."""
    if not values:
        raise ValueError("cannot calculate a quantile of no values")
    ordered = sorted(values)
    index = (len(ordered) - 1) * q
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return float(ordered[lower])
    weight = index - lower
    return float(ordered[lower] * (1 - weight) + ordered[upper] * weight)


def fit_rows(
    rows: Iterable[TrainingRow],
    city_id: str,
    timezone: str,
    test_fraction: float = 0.2,
    *,
    allow_simulated: bool = False,
) -> BaselineModel:
    """Fit from canonical rows using the only accepted split: chronological."""
    if not 0 < test_fraction < 1:
        raise ValueError("test_fraction must be between 0 and 1")

    ordered = sorted(rows, key=lambda row: row.ts)
    if len(ordered) < 2:
        raise ValueError("at least two labelled observations are required")

    source_types = sorted({row.source_type.value for row in ordered})
    if SourceType.SIMULATED.value in source_types and not allow_simulated:
        raise ValueError("SIMULATED training requires allow_simulated=True")
    if source_types != [SourceType.SIMULATED.value]:
        raise ValueError("this demo baseline must be fitted only on SIMULATED history")

    cutoff = max(1, min(int(len(ordered) * (1 - test_fraction)), len(ordered) - 1))
    train, test = ordered[:cutoff], ordered[cutoff:]
    tz = ZoneInfo(timezone)

    grouped: dict[str, dict[str, list[TrainingRow]]] = {
        level: {} for level in FALLBACK_LEVELS
    }
    for row in train:
        hour = row.ts.astimezone(tz).hour
        bucket = _position_bucket(row.position)
        keys = {
            "route_hour_pos": f"{row.route_id}|{hour}|{bucket}",
            "route_hour": f"{row.route_id}|{hour}",
            "hour": str(hour),
            "global": "all",
        }
        for level, key in keys.items():
            grouped[level].setdefault(key, []).append(row)

    tables: dict[str, dict[str, list[float]]] = {level: {} for level in FALLBACK_LEVELS}
    for level, groups in grouped.items():
        for key, values in groups.items():
            if len(values) < MIN_GROUP_OBSERVATIONS:
                continue
            ratios = [row.occupancy_ratio for row in values]
            ordinals = [float(row.occupancy_class.ordinal) for row in values]
            tables[level][key] = [
                round(_quantile(ratios, 0.1), 4),
                round(_quantile(ratios, 0.5), 4),
                round(_quantile(ratios, 0.9), 4),
                _quantile(ordinals, 0.1),
                _quantile(ordinals, 0.5),
                _quantile(ordinals, 0.9),
                float(len(values)),
            ]

    simulated = source_types == [SourceType.SIMULATED.value]
    model = BaselineModel(
        model_version=MODEL_VERSION,
        kind=MODEL_KIND,
        fitted_at=datetime.now(UTC).isoformat(),
        timezone=timezone,
        city_id=city_id,
        train_rows=len(train),
        test_rows=len(test),
        train_end=train[-1].ts.isoformat(),
        test_start=test[0].ts.isoformat(),
        training_source_types=source_types,
        training_source_names=sorted({row.source_name for row in ordered}),
        metrics_label=(SIMULATOR_METRICS_LABEL if simulated else "HISTORICAL_HOLDOUT"),
        real_world_accuracy=not simulated,
        tables=tables,
    )
    model.metrics = _evaluate(model, test)
    for level in FALLBACK_LEVELS:
        if not tables[level]:
            model.fit_warnings.append(f"level '{level}' is empty; it can never answer")
    if len(test) < 1000:
        model.fit_warnings.append(
            f"held-out set has only {len(test)} rows; metrics are indicative, not reliable"
        )
    return model


def _history_rows(dsn: str, city_id: str, source_type: SourceType) -> list[TrainingRow]:
    """Read de-duplicated occupancy joined to route position from TimescaleDB."""
    import psycopg

    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        spans = dict(
            cur.execute(
                """
                SELECT t.route_id, MAX(st.stop_sequence)
                FROM trip t JOIN stop_time st
                  ON st.feed_version_id = t.feed_version_id AND st.trip_id = t.trip_id
                WHERE t.feed_version_id = (
                    SELECT feed_version_id FROM feed_version
                    WHERE city_id = %s ORDER BY imported_at DESC LIMIT 1
                )
                GROUP BY t.route_id
                """,
                (city_id,),
            ).fetchall()
        )
        position_records = cur.execute(
            """
            SELECT vehicle_id, trip_id, ts, route_id, current_stop_sequence
            FROM vehicle_position
            WHERE city_id = %s AND source_type = %s AND route_id IS NOT NULL
              AND trip_id IS NOT NULL AND current_stop_sequence IS NOT NULL
            """,
            (city_id, source_type.value),
        ).fetchall()
        occupancy_records = cur.execute(
            """
            SELECT vehicle_id, trip_id, ts, occupancy_ratio, occupancy_class,
                   source_type, source_name
            FROM occupancy_observation
            WHERE city_id = %s AND source_type = %s
              AND trip_id IS NOT NULL AND occupancy_ratio IS NOT NULL
              AND occupancy_class <> 'UNKNOWN'
            """,
            (city_id, source_type.value),
        ).fetchall()

    positions = {
        (vehicle_id, trip_id, ts): (route_id, sequence)
        for vehicle_id, trip_id, ts, route_id, sequence in position_records
    }
    rows: dict[tuple[str, str, datetime], TrainingRow] = {}
    for vehicle_id, trip_id, ts, ratio, crowd_class, record_source, source_name in (
        occupancy_records
    ):
        matched = positions.get((vehicle_id, trip_id, ts))
        if matched is None:
            continue
        route_id, sequence = matched
        max_sequence = spans.get(route_id)
        if max_sequence is None or max_sequence <= 1:
            continue
        position = min(1.0, max(0.0, (sequence - 1) / (max_sequence - 1)))
        rows[(vehicle_id, trip_id, ts)] = TrainingRow(
            ts=ts,
            route_id=route_id,
            position=position,
            occupancy_ratio=float(ratio),
            occupancy_class=OccupancyClass(crowd_class),
            source_type=SourceType(record_source),
            source_name=source_name,
        )
    return sorted(rows.values(), key=lambda row: row.ts)


def fit_database(
    dsn: str,
    city_id: str,
    timezone: str,
    test_fraction: float = 0.2,
    *,
    allow_simulated: bool = False,
) -> BaselineModel:
    rows = _history_rows(dsn, city_id, SourceType.SIMULATED)
    if not rows:
        raise ValueError("no joined SIMULATED occupancy history found")
    return fit_rows(
        rows, city_id, timezone, test_fraction, allow_simulated=allow_simulated
    )


def _pinball(actual: float, predicted: float, q: float) -> float:
    error = actual - predicted
    return max(q * error, (q - 1) * error)


def _evaluate(model: BaselineModel, test: list[TrainingRow]) -> dict[str, float]:
    scored: list[tuple[float, CrowdForecast]] = []
    for row in test:
        forecast = model.predict(row.route_id, row.ts, row.position)
        if forecast.p50_ratio is not None:
            scored.append((row.occupancy_ratio, forecast))
    if not scored:
        return {}

    absolute_errors = [abs(actual - forecast.p50_ratio) for actual, forecast in scored]
    squared_errors = [(actual - forecast.p50_ratio) ** 2 for actual, forecast in scored]
    covered = sum(
        forecast.p10_ratio <= actual <= forecast.p90_ratio for actual, forecast in scored
    )
    threshold_weights = [2.0 if actual >= 0.65 else 1.0 for actual, _ in scored]
    weighted_error = sum(
        weight * error for weight, error in zip(threshold_weights, absolute_errors, strict=True)
    ) / sum(threshold_weights)

    result = {
        "scored_rows": float(len(scored)),
        "mae": sum(absolute_errors) / len(scored),
        "rmse": math.sqrt(sum(squared_errors) / len(scored)),
        "threshold_weighted_mae": weighted_error,
        "band_coverage": covered / len(scored),
    }
    for q, attribute in ((0.1, "p10_ratio"), (0.5, "p50_ratio"), (0.9, "p90_ratio")):
        result[f"pinball_p{int(q * 100)}"] = sum(
            _pinball(actual, getattr(forecast, attribute), q)
            for actual, forecast in scored
        ) / len(scored)
    return {key: round(value, 6) for key, value in result.items()}


def main(argv: list[str] | None = None) -> int:
    from ..config import CONFIG_DIR, active_city, load_city, load_settings

    parser = argparse.ArgumentParser(description="Fit the seasonal-median crowd baseline.")
    parser.add_argument("command", choices=["fit"], nargs="?", default="fit")
    parser.add_argument("--city", default=None)
    parser.add_argument("--timezone", default=None)
    parser.add_argument("--dsn", default=None)
    parser.add_argument("--test-fraction", type=float, default=0.2)
    parser.add_argument("--allow-simulated", action="store_true")
    parser.add_argument("--out", type=Path, default=CONFIG_DIR / "models" / "baseline_v1.json")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    settings = load_settings()
    city = active_city() if args.city is None else load_city(args.city)
    model = fit_database(
        args.dsn or settings.database_dsn,
        city.city_id,
        args.timezone or city.timezone,
        args.test_fraction,
        allow_simulated=args.allow_simulated,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(model.to_json(), encoding="utf-8")

    log.info("wrote %s", args.out)
    log.info(
        "train %d / test %d rows, split at %s",
        model.train_rows, model.test_rows, model.train_end,
    )
    log.info("%s metrics: %s", model.metrics_label, model.metrics)
    for level in FALLBACK_LEVELS:
        log.info("  %-16s %d groups", level, len(model.tables[level]))
    for warning in model.fit_warnings:
        log.warning("FIT WARNING: %s", warning)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
