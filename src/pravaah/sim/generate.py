"""Run a simulated Delhi service and emit canonical events (section 28.9).

Vehicles are placed on the synthetic network, advanced along their runs in real
time, and written into the same Redis latest-state the live worker uses. The API
cannot tell the difference between this and a real feed -- except by reading
provenance, which is exactly the point: `source_type=SIMULATED` travels with
every record and the client is required to show it (section 33.3 rule 6).

    python -m pravaah.sim.generate --interval 5
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import signal
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from ..contracts.events import (
    OccupancyObservation,
    VehiclePositionEvent,
    VehicleStopStatus,
)
from ..contracts.provenance import Provenance, SourceType
from . import network
from .demand import DemandProfile, simulate_trip

log = logging.getLogger(__name__)

CITY_ID = "delhi"
AGENCY_ID = "DTC"
SOURCE_NAME = "simulator_v1"
TIMEZONE = "Asia/Kolkata"

#: ASSUMPTION. Delhi arterial speeds are reported in the mid-20s km/h with
#: all-day congestion rather than a clean peak/off-peak split. Not sourced from
#: a primary document -- see the Slice H.2 gate.
SPEED_KMH_PEAK = 16.0
SPEED_KMH_OFFPEAK = 24.0

#: Dwell at each stop, seconds.
DWELL_S = 20


@dataclass
class SimVehicle:
    """One bus part-way through a run."""

    vehicle_id: str
    route: network.Route
    started_at: datetime
    trip_id: str
    onboard: list[int]
    boardings: list[int]
    alightings: list[int]
    direction_id: int

    def stop_index_at(self, now: datetime, seconds_per_stop: list[float]) -> tuple[int, float]:
        """Which stop the bus has passed, and how far to the next (0-1)."""
        elapsed = (now - self.started_at).total_seconds()
        total = 0.0
        for index, leg in enumerate(seconds_per_stop):
            if elapsed < total + leg:
                return index, (elapsed - total) / leg if leg > 0 else 0.0
            total += leg
        return len(seconds_per_stop), 1.0


def _is_peak(local: datetime) -> bool:
    return local.hour in (8, 9, 17, 18, 19)


def _leg_seconds(route: network.Route, local: datetime) -> list[float]:
    speed = SPEED_KMH_PEAK if _is_peak(local) else SPEED_KMH_OFFPEAK
    legs: list[float] = []
    for a, b in zip(route.stops, route.stops[1:], strict=False):
        km = network.haversine_km(a.lat, a.lon, b.lat, b.lon)
        legs.append((km / speed) * 3600.0 + DWELL_S)
    return legs


def _provenance(now: datetime) -> Provenance:
    """The only provenance this module may produce."""
    return Provenance(
        source_type=SourceType.SIMULATED,
        source_name=SOURCE_NAME,
        source_timestamp=now,
        ingest_timestamp=now,
        quality_score=1.0,
    )


class DelhiSimulator:
    """Keeps a fleet of simulated buses moving over the synthetic network."""

    def __init__(
        self,
        fleet_size: int = 300,
        seed: int = 20260830,
        load_profile: list[float] | None = None,
        profile: DemandProfile | None = None,
    ) -> None:
        self.rng = random.Random(seed)
        self.tz = ZoneInfo(TIMEZONE)
        self.stops, self.routes = network.build(seed=seed)
        self.profile = profile or DemandProfile.delhi()
        self.load_profile = load_profile
        self.fleet_size = fleet_size
        self.vehicles: list[SimVehicle] = []
        self._legs: dict[str, list[float]] = {}
        self._seed_fleet()

    def _seed_fleet(self) -> None:
        now = datetime.now(UTC)
        for i in range(self.fleet_size):
            route = self.routes[i % len(self.routes)]
            # Stagger starts so buses are spread along their routes rather than
            # all leaving the terminus together.
            offset = self.rng.uniform(0, 1) * self._run_seconds(route, now)
            self.vehicles.append(self._start(route, now - timedelta(seconds=offset), i))

    def _run_seconds(self, route: network.Route, now: datetime) -> float:
        return sum(_leg_seconds(route, now.astimezone(self.tz))) or 1.0

    def _start(self, route: network.Route, at: datetime, index: int) -> SimVehicle:
        local = at.astimezone(self.tz)
        load = simulate_trip(
            stop_count=len(route.stops),
            hour=local.hour,
            weekday=local.weekday(),
            profile=self.profile,
            load_profile=self.load_profile,
            rng=self.rng,
            route_demand=0.7 + self.rng.random() * 0.8,
        )
        return SimVehicle(
            vehicle_id=f"DL{index:04d}",
            route=route,
            started_at=at,
            trip_id=f"{route.route_id}-{int(at.timestamp())}",
            onboard=load.onboard,
            boardings=load.boardings,
            alightings=load.alightings,
            direction_id=index % 2,
        )

    def tick(
        self, now: datetime | None = None
    ) -> tuple[list[VehiclePositionEvent], list[OccupancyObservation]]:
        """Advance every vehicle and emit its current state."""
        now = now or datetime.now(UTC)
        local = now.astimezone(self.tz)
        positions: list[VehiclePositionEvent] = []
        occupancies: list[OccupancyObservation] = []

        for slot, vehicle in enumerate(self.vehicles):
            legs = self._legs.setdefault(vehicle.route.route_id, _leg_seconds(vehicle.route, local))
            index, fraction = vehicle.stop_index_at(now, legs)

            if index >= len(vehicle.route.stops) - 1:
                # Run complete; send it out again from the origin.
                self.vehicles[slot] = self._start(vehicle.route, now, slot)
                continue

            a = vehicle.route.stops[index]
            b = vehicle.route.stops[index + 1]
            lat = a.lat + (b.lat - a.lat) * fraction
            lon = a.lon + (b.lon - a.lon) * fraction
            onboard = vehicle.onboard[min(index, len(vehicle.onboard) - 1)]
            boardings = vehicle.boardings[min(index, len(vehicle.boardings) - 1)]
            alightings = vehicle.alightings[min(index, len(vehicle.alightings) - 1)]

            positions.append(
                VehiclePositionEvent(
                    city_id=CITY_ID,
                    agency_id=AGENCY_ID,
                    vehicle_id=vehicle.vehicle_id,
                    trip_id=vehicle.trip_id,
                    route_id=vehicle.route.route_id,
                    direction_id=vehicle.direction_id,
                    ts=now,
                    lat=round(lat, 6),
                    lon=round(lon, 6),
                    bearing=round(_bearing(a.lat, a.lon, b.lat, b.lon), 1),
                    speed_mps=None,  # derived downstream, never published raw
                    stop_id=b.stop_id,
                    current_stop_sequence=index + 1,
                    current_status=(
                        VehicleStopStatus.STOPPED_AT
                        if fraction < 0.08
                        else VehicleStopStatus.IN_TRANSIT_TO
                    ),
                    provenance=_provenance(now),
                )
            )
            occupancies.append(
                OccupancyObservation(
                    city_id=CITY_ID,
                    vehicle_id=vehicle.vehicle_id,
                    trip_id=vehicle.trip_id,
                    ts=now,
                    onboard=onboard,
                    capacity=self.profile.capacity.crush,
                    occupancy_ratio=self.profile.capacity.ratio(onboard),
                    occupancy_class=self.profile.capacity.occupancy_class(onboard),
                    boardings=boardings,
                    alightings=alightings,
                    confidence=1.0,
                    provenance=_provenance(now),
                )
            )

        return positions, occupancies


def _bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    import math

    dl = math.radians(lon2 - lon1)
    p1, p2 = math.radians(lat1), math.radians(lat2)
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(y, x)) + 360) % 360


def load_curve(path: Path | None) -> list[float] | None:
    """Read the fitted load curve, the one thing carried over from the corpus."""
    if path is None or not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    curve = data.get("load_profile")
    if curve:
        log.info("using fitted load curve from %s", path.name)
    return curve


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Delhi simulator into live state.")
    parser.add_argument("--interval", type=float, default=5, help="seconds between ticks")
    parser.add_argument("--fleet", type=int, default=300)
    parser.add_argument("--seed", type=int, default=20260830)
    parser.add_argument("--ticks", type=int, default=None, help="stop after N ticks")
    parser.add_argument(
        "--calibration",
        type=Path,
        default=Path("../config/calibration/delhi_v1.json"),
        help="fitted profile supplying the load curve only",
    )
    parser.add_argument(
        "--persist-history",
        action="store_true",
        help="append position and occupancy ticks to canonical database history",
    )
    parser.add_argument(
        "--step-seconds",
        type=float,
        default=None,
        help="advance event time by this amount per tick (for offline accumulation)",
    )
    parser.add_argument("--dry-run", action="store_true", help="do not write to Redis")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

    sim = DelhiSimulator(
        fleet_size=args.fleet, seed=args.seed, load_profile=load_curve(args.calibration)
    )
    log.info(
        "simulating %d vehicles over %d routes, %d stops",
        len(sim.vehicles), len(sim.routes), len(sim.stops),
    )

    state = occupancy_state = None
    client = None
    history = None
    if not args.dry_run:
        import redis as redis_lib

        from ..config import load_settings
        from ..state.redis_state import LatestOccupancyState, LatestVehicleState

        client = redis_lib.Redis.from_url(load_settings().redis_url, socket_connect_timeout=5)
        client.ping()
        state = LatestVehicleState(client, CITY_ID)
        occupancy_state = LatestOccupancyState(client, CITY_ID)
    if args.persist_history:
        from ..config import load_settings
        from .persist import TelemetryHistory

        history = TelemetryHistory(load_settings().database_dsn)

    running = True

    def stop(signum, frame):  # noqa: ARG001
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    ticks = 0
    virtual_start = datetime.now(UTC)
    while running:
        tick_time = (
            virtual_start + timedelta(seconds=ticks * args.step_seconds)
            if args.step_seconds is not None
            else None
        )
        positions, occupancies = sim.tick(tick_time)
        if state is not None:
            state.put_many(positions)
            occupancy_state.put_many(occupancies)
        if history is not None:
            history.put_tick(positions, occupancies)

        ticks += 1
        if ticks % 12 == 1 or args.dry_run:
            classes: dict[str, int] = {}
            for obs in occupancies:
                classes[obs.occupancy_class.value] = classes.get(obs.occupancy_class.value, 0) + 1
            log.info("tick %d: %d vehicles | %s", ticks, len(positions), classes)

        if args.ticks is not None and ticks >= args.ticks:
            break
        time.sleep(args.interval)

    if client is not None:
        client.close()
    if history is not None:
        history.close()
    log.info("stopped after %d ticks", ticks)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
