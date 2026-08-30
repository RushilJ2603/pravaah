"""Persist the synthetic Delhi network as a GTFS feed version (section 28.9).

The simulator holds the network in memory, which is enough to move buses on a
map but not enough to answer "what departs from this stop next" or to plan a
journey. Those need the network in the same tables a real GTFS import would
populate, so every downstream consumer works identically whether the network
came from a real feed or from here.

The generated timetable is a real schedule: trips run at a headway across the
service day, and each stop time is derived from the actual distance between
stops at the configured speed. It is synthetic, but it is internally consistent
-- a bus cannot arrive at its third stop before its second.

    python -m pravaah.sim.persist
"""

from __future__ import annotations

import argparse
import hashlib
import logging
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING

from . import network
from .generate import CITY_ID, DWELL_S, SPEED_KMH_OFFPEAK, SPEED_KMH_PEAK

if TYPE_CHECKING:
    from ..contracts.events import OccupancyObservation, VehiclePositionEvent

log = logging.getLogger(__name__)

AGENCY_ID = "DTC"
SERVICE_ID = "ALLDAY"

#: Service span, local time. Delhi buses run long days.
FIRST_DEPARTURE_H = 5
LAST_DEPARTURE_H = 23

#: Headway in minutes by hour. Tighter during the broad peaks.
PEAK_HOURS = {8, 9, 10, 17, 18, 19}
HEADWAY_PEAK_MIN = 8
HEADWAY_OFFPEAK_MIN = 20


class TelemetryHistory:
    """Append simulator ticks to the canonical time-series history.

    Position and occupancy are written in one transaction with the same event
    timestamp. That exact join is what lets baseline training recover route and
    position without adding a city-specific column to the occupancy contract.
    """

    def __init__(self, dsn: str) -> None:
        import psycopg

        self._conn = psycopg.connect(dsn)

    def put_tick(
        self,
        positions: list[VehiclePositionEvent],
        occupancies: list[OccupancyObservation],
    ) -> int:
        with self._conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO vehicle_position (
                    city_id, vehicle_id, trip_id, route_id, direction_id, ts, geom,
                    bearing, speed_mps, stop_id, current_stop_sequence, current_status,
                    matched_segment_id, source_type, source_name, quality_score, ingest_ts
                ) VALUES (
                    %s, %s, %s, %s, %s, %s,
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """,
                [
                    (
                        event.city_id,
                        event.vehicle_id,
                        event.trip_id,
                        event.route_id,
                        event.direction_id,
                        event.ts,
                        event.lon,
                        event.lat,
                        event.bearing,
                        event.speed_mps,
                        event.stop_id,
                        event.current_stop_sequence,
                        event.current_status.value if event.current_status else None,
                        event.matched_segment_id,
                        event.provenance.source_type.value,
                        event.provenance.source_name,
                        event.provenance.quality_score,
                        event.provenance.ingest_timestamp,
                    )
                    for event in positions
                ],
            )
            cur.executemany(
                """
                INSERT INTO occupancy_observation (
                    city_id, vehicle_id, trip_id, ts, onboard, capacity,
                    occupancy_ratio, occupancy_class, boardings, alightings,
                    confidence, source_type, source_name, ingest_ts
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """,
                [
                    (
                        event.city_id,
                        event.vehicle_id,
                        event.trip_id,
                        event.ts,
                        event.onboard,
                        event.capacity,
                        event.occupancy_ratio,
                        event.occupancy_class.value,
                        event.boardings,
                        event.alightings,
                        event.confidence,
                        event.provenance.source_type.value,
                        event.provenance.source_name,
                        event.provenance.ingest_timestamp,
                    )
                    for event in occupancies
                ],
            )
        self._conn.commit()
        return len(occupancies)

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> TelemetryHistory:
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if exc_type is not None:
            self._conn.rollback()
        self.close()


def _leg_seconds(route: network.Route, hour: int) -> list[float]:
    speed = SPEED_KMH_PEAK if hour in PEAK_HOURS else SPEED_KMH_OFFPEAK
    return [
        (network.haversine_km(a.lat, a.lon, b.lat, b.lon) / speed) * 3600.0 + DWELL_S
        for a, b in zip(route.stops, route.stops[1:], strict=False)
    ]


def build_schedule(
    routes: list[network.Route],
) -> tuple[list[tuple], list[tuple]]:
    """Generate trips and stop_times for a service day.

    Returns (trip_rows, stop_time_rows) without feed_version_id, which the
    caller prepends once the feed version exists.
    """
    trips: list[tuple] = []
    stop_times: list[tuple] = []

    for route in routes:
        for direction in (0, 1):
            stops = route.stops if direction == 0 else list(reversed(route.stops))
            for hour in range(FIRST_DEPARTURE_H, LAST_DEPARTURE_H):
                headway = HEADWAY_PEAK_MIN if hour in PEAK_HOURS else HEADWAY_OFFPEAK_MIN
                legs = _leg_seconds(route, hour)
                if direction == 1:
                    legs = list(reversed(legs))

                for minute in range(0, 60, headway):
                    start_s = hour * 3600 + minute * 60
                    trip_id = f"{route.route_id}-{direction}-{hour:02d}{minute:02d}"
                    trips.append((trip_id, route.route_id, SERVICE_ID, direction, None))

                    elapsed = 0.0
                    for seq, stop in enumerate(stops):
                        arrival = int(start_s + elapsed)
                        departure = arrival + DWELL_S
                        stop_times.append((trip_id, seq + 1, stop.stop_id, arrival, departure))
                        if seq < len(legs):
                            elapsed += legs[seq]

    return trips, stop_times


def persist(dsn: str | None = None, seed: int = 20260830) -> int:
    """Write the synthetic network as a new feed version. Returns its id."""
    import psycopg

    from ..config import load_settings

    dsn = dsn or load_settings().database_dsn
    stops, routes = network.build(seed=seed)
    trips, stop_times = build_schedule(routes)

    # A hash over the generated content, so re-running with the same seed is
    # recognisably the same feed rather than silently creating a duplicate.
    digest = hashlib.sha256(
        f"{seed}|{len(stops)}|{len(routes)}|{len(trips)}|{len(stop_times)}".encode()
    ).hexdigest()

    today = date.today()
    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        existing = cur.execute(
            "SELECT feed_version_id FROM feed_version WHERE city_id=%s AND feed_hash=%s",
            (CITY_ID, digest),
        ).fetchone()
        if existing:
            log.info("feed already imported as version %d; nothing written", existing[0])
            return existing[0]

        cur.execute(
            """
            INSERT INTO feed_version (city_id, feed_hash, published_at, valid_from,
                                      valid_to, imported_at)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING feed_version_id
            """,
            (CITY_ID, digest, datetime.now(UTC), today, today, datetime.now(UTC)),
        )
        version = cur.fetchone()[0]

        cur.executemany(
            """
            INSERT INTO stop (feed_version_id, stop_id, name, geom)
            VALUES (%s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography)
            """,
            [(version, s.stop_id, s.name, s.lon, s.lat) for s in stops],
        )
        cur.executemany(
            """
            INSERT INTO route (feed_version_id, route_id, agency_id, short_name,
                               long_name, route_type)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            [(version, r.route_id, AGENCY_ID, r.short_name, r.long_name, 3) for r in routes],
        )
        cur.executemany(
            """
            INSERT INTO trip (feed_version_id, trip_id, route_id, service_id,
                              direction_id, shape_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            [(version, *t) for t in trips],
        )
        for start in range(0, len(stop_times), 50_000):
            batch = stop_times[start : start + 50_000]
            cur.executemany(
                """
                INSERT INTO stop_time (feed_version_id, trip_id, stop_sequence, stop_id,
                                       arrival_seconds, departure_seconds)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                [(version, *row) for row in batch],
            )
            log.info("stop_times %d/%d", min(start + 50_000, len(stop_times)), len(stop_times))
        conn.commit()

    log.info(
        "feed_version %d: %d stops, %d routes, %d trips, %d stop_times",
        version, len(stops), len(routes), len(trips), len(stop_times),
    )
    return version


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Persist the synthetic Delhi network.")
    parser.add_argument("--dsn", default=None)
    parser.add_argument("--seed", type=int, default=20260830)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    persist(args.dsn, args.seed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
