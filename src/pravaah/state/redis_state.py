"""Latest vehicle state in Redis.

Implements SOLUTION.md section 6.4 ("materialize latest vehicle state in Redis"),
section 11.1 and section 11.3.

Redis holds only *derived, reconstructible* state. The immutable event history
lives in the time-series store, so losing Redis costs latency, never data --
section 16.1 requires the system to fall back to reading latest state from the
database, and `rebuild_from_database` is that path.

Two structures per city:

* a hash `pravaah:{city}:vehicles`, vehicle_id -> canonical event JSON;
* a geo set `pravaah:{city}:geo` for viewport queries, so the operator map can
  request a bounding box instead of the whole fleet (section 12.4 rule 5).

Entries carry no per-field TTL. Instead every read filters by age, and stale
entries are pruned as they are encountered -- which keeps behaviour identical
whether or not the deployment's Redis supports hash-field expiry.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from ..contracts.events import VehiclePositionEvent

log = logging.getLogger(__name__)

#: Entries older than this are treated as gone. Generous relative to the feed
#: cadence: a vehicle at the end of its trip should linger on the map briefly
#: rather than vanish mid-journey.
DEFAULT_MAX_AGE_S = 900


class LatestVehicleState:
    """Read/write the current position of every vehicle in a city."""

    def __init__(self, redis, city_id: str, max_age_s: int = DEFAULT_MAX_AGE_S) -> None:
        self.redis = redis
        self.city_id = city_id
        self.max_age_s = max_age_s

    # -- keys --------------------------------------------------------------

    @property
    def _hash_key(self) -> str:
        return f"pravaah:{self.city_id}:vehicles"

    @property
    def _geo_key(self) -> str:
        return f"pravaah:{self.city_id}:geo"

    # -- writes ------------------------------------------------------------

    def put_many(self, events: list[VehiclePositionEvent]) -> int:
        """Upsert a batch. One pipeline round trip regardless of batch size."""
        if not events:
            return 0

        pipe = self.redis.pipeline(transaction=False)
        for event in events:
            pipe.hset(self._hash_key, event.vehicle_id, event.model_dump_json())
            pipe.geoadd(self._geo_key, (event.lon, event.lat, event.vehicle_id))
        pipe.execute()
        return len(events)

    def put(self, event: VehiclePositionEvent) -> None:
        self.put_many([event])

    def clear(self) -> None:
        self.redis.delete(self._hash_key, self._geo_key)

    # -- reads -------------------------------------------------------------

    def get(self, vehicle_id: str, now: datetime | None = None) -> VehiclePositionEvent | None:
        raw = self.redis.hget(self._hash_key, vehicle_id)
        if raw is None:
            return None
        event = VehiclePositionEvent.model_validate_json(raw)
        if self._is_expired(event, now):
            self._prune([vehicle_id])
            return None
        return event

    def all(self, now: datetime | None = None) -> list[VehiclePositionEvent]:
        """Every non-expired vehicle, pruning what has aged out."""
        raw = self.redis.hgetall(self._hash_key)
        if not raw:
            return []

        fresh: list[VehiclePositionEvent] = []
        expired: list[str] = []
        for key, value in raw.items():
            event = VehiclePositionEvent.model_validate_json(value)
            if self._is_expired(event, now):
                expired.append(key.decode() if isinstance(key, bytes) else key)
            else:
                fresh.append(event)

        if expired:
            self._prune(expired)
        return fresh

    def in_viewport(
        self,
        min_lat: float,
        min_lon: float,
        max_lat: float,
        max_lon: float,
        now: datetime | None = None,
        limit: int = 2000,
    ) -> list[VehiclePositionEvent]:
        """Vehicles inside a bounding box.

        Uses Redis GEOSEARCH so a zoomed-in map does not transfer the whole
        fleet (section 12.4 rule 5, section 16.3).
        """
        centre_lat = (min_lat + max_lat) / 2
        centre_lon = (min_lon + max_lon) / 2
        height_m = _span_m(min_lat, centre_lon, max_lat, centre_lon)
        width_m = _span_m(centre_lat, min_lon, centre_lat, max_lon)

        ids = self.redis.geosearch(
            self._geo_key,
            longitude=centre_lon,
            latitude=centre_lat,
            width=max(width_m, 1.0),
            height=max(height_m, 1.0),
            unit="m",
            count=limit,
        )
        if not ids:
            return []

        decoded = [i.decode() if isinstance(i, bytes) else i for i in ids]
        raw = self.redis.hmget(self._hash_key, decoded)

        inside: list[VehiclePositionEvent] = []
        for value in raw:
            if value is None:
                continue
            event = VehiclePositionEvent.model_validate_json(value)
            if self._is_expired(event, now):
                continue
            # GEOSEARCH boxes are approximate near the poles and at the edges;
            # the exact test is cheap and keeps the contract honest.
            if min_lat <= event.lat <= max_lat and min_lon <= event.lon <= max_lon:
                inside.append(event)
        return inside

    def count(self) -> int:
        return int(self.redis.hlen(self._hash_key))

    # -- recovery ----------------------------------------------------------

    def rebuild_from_database(self, conn, since_s: int | None = None) -> int:
        """Repopulate from `vehicle_position` after a Redis restart.

        Section 11.3: latest-state keys are reconstructed from the database, so a
        cold cache is a latency event and never a data-loss event.
        """
        window = since_s if since_s is not None else self.max_age_s
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT ON (vehicle_id)
                       vehicle_id, trip_id, route_id, direction_id, ts,
                       ST_Y(geom::geometry), ST_X(geom::geometry),
                       bearing, speed_mps, stop_id, current_stop_sequence,
                       current_status, matched_segment_id,
                       source_type, source_name, quality_score, ingest_ts
                  FROM vehicle_position
                 WHERE city_id = %s AND ts > now() - make_interval(secs => %s)
                 ORDER BY vehicle_id, ts DESC
                """,
                (self.city_id, window),
            )
            rows = cur.fetchall()

        events = [self._event_from_row(row) for row in rows]
        written = self.put_many(events)
        log.info("rebuilt %d vehicles for %s from the database", written, self.city_id)
        return written

    def _event_from_row(self, row) -> VehiclePositionEvent:
        from ..contracts.provenance import Provenance, SourceType

        (
            vehicle_id, trip_id, route_id, direction_id, ts, lat, lon,
            bearing, speed_mps, stop_id, stop_sequence, status,
            segment_id, source_type, source_name, quality, ingest_ts,
        ) = row

        return VehiclePositionEvent(
            city_id=self.city_id,
            agency_id=source_name,
            vehicle_id=vehicle_id,
            trip_id=trip_id,
            route_id=route_id,
            direction_id=direction_id,
            ts=ts,
            lat=lat,
            lon=lon,
            bearing=bearing,
            speed_mps=speed_mps,
            stop_id=stop_id,
            current_stop_sequence=stop_sequence,
            current_status=status,
            matched_segment_id=segment_id,
            provenance=Provenance(
                source_type=SourceType(source_type),
                source_name=source_name,
                source_timestamp=ts,
                ingest_timestamp=ingest_ts,
                quality_score=quality,
            ),
        )

    # -- internals ---------------------------------------------------------

    def _is_expired(self, event: VehiclePositionEvent, now: datetime | None) -> bool:
        now = now or datetime.now(UTC)
        return (now - event.ts).total_seconds() > self.max_age_s

    def _prune(self, vehicle_ids: list[str]) -> None:
        if not vehicle_ids:
            return
        pipe = self.redis.pipeline(transaction=False)
        pipe.hdel(self._hash_key, *vehicle_ids)
        pipe.zrem(self._geo_key, *vehicle_ids)
        pipe.execute()


def _span_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    from ..ingest.validate import haversine_m

    return haversine_m(lat1, lon1, lat2, lon2)
