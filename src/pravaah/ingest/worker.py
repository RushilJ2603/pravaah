"""Live ingestion worker.

Implements SOLUTION.md section 7.2 (streaming path) for Slice A:

    adapter.poll -> validate -> latest state (Redis) -> history (Postgres)

This is the process that makes the map move. It is deliberately a plain loop
rather than a stream framework: section 23 puts Kafka in production and Redis
Streams in the prototype, and Slice A needs neither to prove the path.

Failures are isolated per cycle. A feed hiccup, a Redis blip or a database
outage must not kill the loop -- section 16.1 requires the system to degrade,
and a worker that exits on the first error takes the live map down with it.
"""

from __future__ import annotations

import argparse
import logging
import signal
import time
from datetime import UTC, datetime

from ..adapters.base import RealtimeAdapter
from ..adapters.mbta import build as build_mbta
from ..config import CityProfile, active_city, load_settings
from ..contracts.events import OccupancyObservation, VehiclePositionEvent
from ..state.redis_state import LatestOccupancyState, LatestVehicleState
from .validate import PositionValidator

log = logging.getLogger(__name__)


class IngestWorker:
    """One poll-validate-store cycle, repeated."""

    def __init__(
        self,
        adapter: RealtimeAdapter,
        city: CityProfile,
        state: LatestVehicleState | None = None,
        db_pool=None,
        occupancy: LatestOccupancyState | None = None,
    ) -> None:
        self.adapter = adapter
        self.city = city
        self.state = state
        self.occupancy = occupancy
        self.db_pool = db_pool
        self.validator = PositionValidator(city)
        self.cycles = 0
        self.accepted_total = 0
        self.rejected_total = 0
        self.occupancy_total = 0
        self._running = True

    def stop(self) -> None:
        self._running = False

    def cycle(self) -> int:
        """One poll. Returns the number of accepted positions."""
        snapshot = self.adapter.poll()
        now = datetime.now(UTC)
        result = self.validator.validate(snapshot.positions, now=now)

        self.cycles += 1
        self.accepted_total += len(result.accepted)
        self.rejected_total += len(result.rejected)

        # Occupancy rides on the same payload, but only for vehicles whose
        # position survived validation. A position rejected as impossible must
        # not contribute a crowd reading to live state through the side door.
        accepted_ids = {e.vehicle_id for e in result.accepted}
        occupancies = [o for o in snapshot.occupancies if o.vehicle_id in accepted_ids]
        self.occupancy_total += len(occupancies)

        if result.accepted:
            if self.state is not None:
                try:
                    self.state.put_many(result.accepted)
                except Exception:  # noqa: BLE001 -- a cache blip is not fatal
                    log.exception("failed to write latest state")
            if self.db_pool is not None:
                try:
                    self._persist(result.accepted)
                except Exception:  # noqa: BLE001
                    log.exception("failed to persist history")

        if occupancies:
            if self.occupancy is not None:
                try:
                    self.occupancy.put_many(occupancies)
                except Exception:  # noqa: BLE001
                    log.exception("failed to write latest occupancy")
            if self.db_pool is not None:
                try:
                    self._persist_occupancy(occupancies)
                except Exception:  # noqa: BLE001
                    log.exception("failed to persist occupancy history")

        log.info(
            "cycle %d: %d accepted, %d rejected %s, %d stale, %d occupancy (%.0f%% coverage)",
            self.cycles,
            len(result.accepted),
            len(result.rejected),
            result.reasons() or "",
            len(result.stale),
            len(occupancies),
            snapshot.occupancy_coverage * 100,
        )
        return len(result.accepted)

    def run(self, interval_s: int | None = None, max_cycles: int | None = None) -> None:
        interval = interval_s or self.city.feeds.poll_interval_s
        log.info("polling %s every %ds", self.city.city_id, interval)

        while self._running:
            started = time.monotonic()
            try:
                self.cycle()
            except Exception:  # noqa: BLE001 -- never let one bad poll end the loop
                log.exception("poll failed; continuing")

            if max_cycles is not None and self.cycles >= max_cycles:
                break

            elapsed = time.monotonic() - started
            time.sleep(max(1.0, interval - elapsed))

    def _persist(self, events: list[VehiclePositionEvent]) -> None:
        """Append to the immutable history (section 11.1).

        Redis is a cache; this table is the record that makes a cold cache
        recoverable and the corpus reproducible.
        """
        rows = [
            (
                e.city_id, e.vehicle_id, e.trip_id, e.route_id, e.direction_id, e.ts,
                e.lon, e.lat, e.bearing, e.speed_mps, e.stop_id,
                e.current_stop_sequence,
                e.current_status.value if e.current_status else None,
                e.matched_segment_id,
                e.provenance.source_type.value, e.provenance.source_name,
                e.provenance.quality_score, e.provenance.ingest_timestamp,
            )
            for e in events
        ]
        with self.db_pool.connection() as conn, conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO vehicle_position (
                    city_id, vehicle_id, trip_id, route_id, direction_id, ts,
                    geom, bearing, speed_mps, stop_id, current_stop_sequence,
                    current_status, matched_segment_id,
                    source_type, source_name, quality_score, ingest_ts
                ) VALUES (
                    %s, %s, %s, %s, %s, %s,
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """,
                rows,
            )
            conn.commit()

    def _persist_occupancy(self, observations: list[OccupancyObservation]) -> None:
        """Append crowd observations to the immutable history (section 11.1).

        These are the training labels. Redis holds only the latest reading per
        vehicle; this table is the only place the history survives, and it
        cannot be re-recorded for elapsed time.
        """
        rows = [
            (
                o.city_id, o.vehicle_id, o.trip_id, o.ts,
                o.onboard, o.capacity, o.occupancy_ratio,
                o.occupancy_class.value, o.boardings, o.alightings, o.confidence,
                o.provenance.source_type.value, o.provenance.source_name,
                o.provenance.ingest_timestamp,
            )
            for o in observations
        ]
        with self.db_pool.connection() as conn, conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO occupancy_observation (
                    city_id, vehicle_id, trip_id, ts,
                    onboard, capacity, occupancy_ratio,
                    occupancy_class, boardings, alightings, confidence,
                    source_type, source_name, ingest_ts
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """,
                rows,
            )
            conn.commit()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Poll a realtime feed into live state.")
    parser.add_argument("--interval", type=int, default=None)
    parser.add_argument("--max-cycles", type=int, default=None)
    parser.add_argument("--no-persist", action="store_true", help="Redis only, no history")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    settings = load_settings()
    city = active_city()

    import redis as redis_lib

    client = redis_lib.Redis.from_url(settings.redis_url, socket_connect_timeout=5)
    client.ping()
    state = LatestVehicleState(client, city.city_id)
    occupancy = LatestOccupancyState(client, city.city_id)

    pool = None
    if not args.no_persist:
        from psycopg_pool import ConnectionPool

        pool = ConnectionPool(settings.database_dsn, min_size=1, max_size=2, open=True)
        pool.wait(timeout=10)

    worker = IngestWorker(
        build_mbta(city), city, state=state, db_pool=pool, occupancy=occupancy
    )

    def handle_signal(signum, frame):  # noqa: ARG001
        log.info("stopping after the current cycle")
        worker.stop()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        worker.run(interval_s=args.interval, max_cycles=args.max_cycles)
    finally:
        log.info(
            "stopped after %d cycles: %d accepted, %d rejected, %d occupancy",
            worker.cycles,
            worker.accepted_total,
            worker.rejected_total,
            worker.occupancy_total,
        )
        client.close()
        if pool is not None:
            pool.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
