"""Crowd forecast as a distribution (SOLUTION.md sections 9, 12.4 rule 2).

The product claim is "how crowded will this bus be **when it reaches your
stop**", not "how crowded is it now". That means a forecast keyed by where the
passenger boards, and it means a distribution rather than a number: section 12.4
rule 2 and section 33.3 rule 2 both require the uncertainty to reach the screen.

The forecast is built by Monte Carlo over the same behavioural demand model that
drives the simulator: for a given hour and a given position along a run, sample
many trips and take the p10/p50/p90 of the onboard count. That is an honest
distribution over the world the system is modelling, and it is reproducible from
a seed.

Two properties this deliberately keeps:

* **A forecast is never a point.** Every response carries all three quantiles.
* **A missing forecast is UNKNOWN, not zero.** Section 12.4 rule 3 applies to
  predictions exactly as it applies to observations.
"""

from __future__ import annotations

import json
import logging
import random
from dataclasses import dataclass, field
from pathlib import Path

from ..contracts.events import OccupancyClass
from ..sim.demand import DemandProfile, simulate_trip

log = logging.getLogger(__name__)

MODEL_VERSION = "crowd_mc_v1"

#: Position buckets along a run, matching the calibration profile.
BUCKETS = 10

#: Monte Carlo samples per (hour, bucket) cell.
SAMPLES = 240

#: Representative run length, in stops, for the sampling pass.
NOMINAL_STOPS = 30


@dataclass(frozen=True)
class CrowdQuantiles:
    """p10/p50/p90 for one (hour, position) cell."""

    p10_class: OccupancyClass
    p50_class: OccupancyClass
    p90_class: OccupancyClass
    p10_onboard: int | None
    p50_onboard: int | None
    p90_onboard: int | None
    p50_ratio: float | None
    capacity: int | None
    model_version: str = MODEL_VERSION
    is_fallback: bool = False

    @classmethod
    def unknown(cls, model_version: str = MODEL_VERSION) -> CrowdQuantiles:
        return cls(
            p10_class=OccupancyClass.UNKNOWN,
            p50_class=OccupancyClass.UNKNOWN,
            p90_class=OccupancyClass.UNKNOWN,
            p10_onboard=None,
            p50_onboard=None,
            p90_onboard=None,
            p50_ratio=None,
            capacity=None,
            model_version=model_version,
            is_fallback=True,
        )


@dataclass
class CrowdForecaster:
    """Precomputed quantile table, keyed `hour|bucket`."""

    table: dict[str, list[int]] = field(default_factory=dict)
    capacity: int = 100
    model_version: str = MODEL_VERSION
    samples: int = SAMPLES
    profile: DemandProfile | None = None

    # -- build -------------------------------------------------------------

    @classmethod
    def build(
        cls,
        profile: DemandProfile | None = None,
        load_profile: list[float] | None = None,
        seed: int = 20260830,
        samples: int = SAMPLES,
    ) -> CrowdForecaster:
        """Monte Carlo the demand model across every hour and position."""
        profile = profile or DemandProfile.delhi()
        rng = random.Random(seed)
        table: dict[str, list[int]] = {}

        for hour in range(24):
            # Samples of the onboard count at each bucket, across many trips.
            per_bucket: list[list[int]] = [[] for _ in range(BUCKETS)]
            for _ in range(samples):
                load = simulate_trip(
                    stop_count=NOMINAL_STOPS,
                    hour=hour,
                    weekday=rng.randint(0, 4),  # a representative working day
                    profile=profile,
                    load_profile=load_profile,
                    rng=rng,
                    route_demand=0.7 + rng.random() * 0.8,
                )
                for index, onboard in enumerate(load.onboard):
                    bucket = min(
                        int((index / max(NOMINAL_STOPS - 1, 1)) * BUCKETS), BUCKETS - 1
                    )
                    per_bucket[bucket].append(onboard)

            for bucket, values in enumerate(per_bucket):
                if not values:
                    continue
                values.sort()
                table[f"{hour}|{bucket}"] = [
                    _quantile(values, 0.10),
                    _quantile(values, 0.50),
                    _quantile(values, 0.90),
                ]

        log.info("built crowd forecast table: %d cells, %d samples each", len(table), samples)
        return cls(
            table=table,
            capacity=profile.capacity.crush,
            samples=samples,
            profile=profile,
        )

    # -- predict -----------------------------------------------------------

    def predict(
        self, hour: int, position: float, route_id: str | None = None
    ) -> CrowdQuantiles:
        """Forecast for a boarding at `position` along a run at `hour`.

        `position` is 0.0 at the origin and 1.0 at the terminus. An unseen cell
        returns UNKNOWN rather than a guess.
        """
        del route_id  # the cold-start table predates route-specific history
        bucket = max(0, min(int(position * BUCKETS), BUCKETS - 1))
        row = self.table.get(f"{hour % 24}|{bucket}")
        if not row:
            return CrowdQuantiles.unknown()

        capacity_model = (self.profile or DemandProfile.delhi()).capacity
        p10, p50, p90 = row
        return CrowdQuantiles(
            p10_class=capacity_model.occupancy_class(p10),
            p50_class=capacity_model.occupancy_class(p50),
            p90_class=capacity_model.occupancy_class(p90),
            p10_onboard=p10,
            p50_onboard=p50,
            p90_onboard=p90,
            p50_ratio=capacity_model.ratio(p50),
            capacity=self.capacity,
            model_version=self.model_version,
        )

    # -- persistence -------------------------------------------------------

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "model_version": self.model_version,
                    "capacity": self.capacity,
                    "samples": self.samples,
                    "buckets": BUCKETS,
                    "table": self.table,
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: Path) -> CrowdForecaster:
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            table=data["table"],
            capacity=data.get("capacity", 100),
            model_version=data.get("model_version", MODEL_VERSION),
            samples=data.get("samples", SAMPLES),
        )


def _quantile(sorted_values: list[int], q: float) -> int:
    if not sorted_values:
        return 0
    index = max(0, min(int(q * (len(sorted_values) - 1)), len(sorted_values) - 1))
    return int(sorted_values[index])


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Build the crowd forecast table.")
    parser.add_argument("--out", type=Path, default=Path("config/models/crowd_v1.json"))
    parser.add_argument("--calibration", type=Path, default=None)
    parser.add_argument("--samples", type=int, default=SAMPLES)
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

    curve = None
    if args.calibration and args.calibration.exists():
        curve = json.loads(args.calibration.read_text(encoding="utf-8")).get("load_profile")

    forecaster = CrowdForecaster.build(load_profile=curve, samples=args.samples)
    forecaster.save(args.out)
    log.info("wrote %s", args.out)

    for hour in (5, 9, 13, 18, 22):
        q = forecaster.predict(hour, 0.5)
        log.info(
            "  %02d:00 mid-run  p10=%s p50=%s p90=%s  (%d/%d/%d onboard)",
            hour, q.p10_class.value, q.p50_class.value, q.p90_class.value,
            q.p10_onboard, q.p50_onboard, q.p90_onboard,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
