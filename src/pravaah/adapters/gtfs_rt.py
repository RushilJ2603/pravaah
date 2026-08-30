"""Generic GTFS-Realtime adapter.

Implements SOLUTION.md section 8 (Realtime Adapter) and section 6.4.

Any city publishing a standard GTFS-Realtime VehiclePositions feed is handled
here; a city subclass exists only for genuine quirks, not for configuration.

Two rules from the document are enforced in this file rather than left to
callers, because getting either wrong corrupts everything downstream:

* **`speed_mps` is left None.** The raw feed `speed` field is populated on ~9.8%
  of MBTA rows (section 6.2.1), so speed is derived from consecutive positions
  instead (section 28.4). An adapter that passes the feed value through would
  produce a feature that is present for one row in ten and absent for the rest.
* **Absent occupancy becomes `UNKNOWN`, never `EMPTY`.** GTFS-RT distinguishes a
  vehicle reported empty from one that reported nothing; collapsing the two is
  the single most damaging bug this system could ship (section 12.4 rule 3).
"""

from __future__ import annotations

import logging
import urllib.request
from datetime import UTC, datetime

from google.transit import gtfs_realtime_pb2 as rt

from ..contracts.events import (
    OccupancyClass,
    OccupancyObservation,
    VehiclePositionEvent,
    VehicleStopStatus,
)
from ..contracts.provenance import Provenance, SourceType
from .base import FeedSnapshot, RealtimeAdapter

log = logging.getLogger(__name__)

USER_AGENT = "pravaah/0.1 (SIH 2026; transit research)"

#: GTFS-Realtime OccupancyStatus -> our ladder (contracts/events.py).
#: NO_DATA_AVAILABLE and NOT_BOARDABLE carry no crowding information, so both
#: become UNKNOWN rather than being guessed at.
_OCCUPANCY_BY_NAME: dict[str, OccupancyClass] = {
    "EMPTY": OccupancyClass.EMPTY,
    "MANY_SEATS_AVAILABLE": OccupancyClass.MANY_SEATS_AVAILABLE,
    "FEW_SEATS_AVAILABLE": OccupancyClass.FEW_SEATS_AVAILABLE,
    "STANDING_ROOM_ONLY": OccupancyClass.STANDING_ROOM_ONLY,
    "CRUSHED_STANDING_ROOM_ONLY": OccupancyClass.CRUSHED_STANDING_ROOM_ONLY,
    "FULL": OccupancyClass.FULL,
    "NOT_ACCEPTING_PASSENGERS": OccupancyClass.NOT_ACCEPTING_PASSENGERS,
    "NO_DATA_AVAILABLE": OccupancyClass.UNKNOWN,
    "NOT_BOARDABLE": OccupancyClass.UNKNOWN,
}

_STATUS_BY_NAME: dict[str, VehicleStopStatus] = {
    "INCOMING_AT": VehicleStopStatus.INCOMING_AT,
    "STOPPED_AT": VehicleStopStatus.STOPPED_AT,
    "IN_TRANSIT_TO": VehicleStopStatus.IN_TRANSIT_TO,
}


def occupancy_from_name(name: str | None) -> OccupancyClass:
    """Map a GTFS-RT occupancy name onto our ladder.

    An unrecognised or absent value is UNKNOWN. It is never EMPTY, and it is
    never silently dropped.
    """
    if not name:
        return OccupancyClass.UNKNOWN
    return _OCCUPANCY_BY_NAME.get(name, OccupancyClass.UNKNOWN)


class GTFSRealtimeAdapter(RealtimeAdapter):
    """Decodes a standard GTFS-Realtime VehiclePositions feed."""

    @property
    def source_name(self) -> str:
        return f"{self.city.city_id}_gtfsrt"

    # -- I/O ---------------------------------------------------------------

    def fetch_vehicle_positions(self, timeout: float = 30.0) -> bytes:
        request = urllib.request.Request(
            self.city.feeds.vehicle_positions, headers={"User-Agent": USER_AGENT}
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read()

    # -- decoding ----------------------------------------------------------

    def decode_vehicle_positions(
        self, raw: bytes, ingest_ts: datetime | None = None
    ) -> FeedSnapshot:
        ingest_ts = ingest_ts or datetime.now(UTC)
        payload_sha = self.sha256(raw)

        message = rt.FeedMessage()
        message.ParseFromString(raw)
        feed_ts = datetime.fromtimestamp(message.header.timestamp or 0, tz=UTC)

        positions: list[VehiclePositionEvent] = []
        occupancies: list[OccupancyObservation] = []
        skipped: list[str] = []

        for entity in message.entity:
            if not entity.HasField("vehicle"):
                continue
            vehicle = entity.vehicle

            vehicle_id = vehicle.vehicle.id or entity.id
            if not vehicle_id:
                skipped.append(f"entity {entity.id!r}: no vehicle id")
                continue
            if not vehicle.HasField("position"):
                skipped.append(f"vehicle {vehicle_id}: no position")
                continue

            # The vehicle's own timestamp is what the observation is *about*.
            # Falling back to the feed header keeps the event usable while
            # making the substitution visible in the quality score below.
            has_own_ts = bool(vehicle.timestamp)
            observed_at = (
                datetime.fromtimestamp(vehicle.timestamp, tz=UTC) if has_own_ts else feed_ts
            )

            occupancy_name = (
                vehicle.OccupancyStatus.Name(vehicle.occupancy_status)
                if vehicle.HasField("occupancy_status")
                else None
            )
            occupancy_class = occupancy_from_name(occupancy_name)

            provenance = Provenance(
                source_type=SourceType.PUBLIC_FEED,
                source_name=self.source_name,
                source_timestamp=observed_at,
                ingest_timestamp=ingest_ts,
                quality_score=self._quality_score(vehicle, has_own_ts, observed_at, ingest_ts),
                raw_payload_ref=payload_sha,
            )

            try:
                positions.append(
                    VehiclePositionEvent(
                        city_id=self.city.city_id,
                        agency_id=self.city.agency_id,
                        vehicle_id=vehicle_id,
                        trip_id=vehicle.trip.trip_id or None,
                        route_id=vehicle.trip.route_id or None,
                        direction_id=(
                            vehicle.trip.direction_id
                            if vehicle.trip.HasField("direction_id")
                            else None
                        ),
                        ts=observed_at,
                        lat=vehicle.position.latitude,
                        lon=vehicle.position.longitude,
                        bearing=(
                            vehicle.position.bearing % 360.0
                            if vehicle.position.HasField("bearing")
                            else None
                        ),
                        # Deliberately None: derived later (section 28.4).
                        speed_mps=None,
                        stop_id=vehicle.stop_id or None,
                        current_stop_sequence=(
                            vehicle.current_stop_sequence
                            if vehicle.HasField("current_stop_sequence")
                            else None
                        ),
                        current_status=(
                            _STATUS_BY_NAME.get(
                                vehicle.VehicleStopStatus.Name(vehicle.current_status)
                            )
                            if vehicle.HasField("current_status")
                            else None
                        ),
                        provenance=provenance,
                    )
                )
            except ValueError as exc:
                # A contract violation is data we must not silently accept.
                skipped.append(f"vehicle {vehicle_id}: {exc}")
                continue

            observation = self._occupancy_observation(
                vehicle_id=vehicle_id,
                vehicle=vehicle,
                occupancy_class=occupancy_class,
                observed_at=observed_at,
                provenance=provenance,
            )
            if observation is not None:
                occupancies.append(observation)

        if skipped:
            log.info("decoded %d positions, skipped %d entities", len(positions), len(skipped))

        return FeedSnapshot(
            feed_timestamp=feed_ts,
            positions=positions,
            occupancies=occupancies,
            payload_sha256=payload_sha,
            skipped=skipped,
        )

    # -- hooks for city subclasses ----------------------------------------

    def _occupancy_observation(
        self,
        *,
        vehicle_id: str,
        vehicle,
        occupancy_class: OccupancyClass,
        observed_at: datetime,
        provenance: Provenance,
    ) -> OccupancyObservation | None:
        """Build an occupancy observation, or None when the feed reported nothing.

        Returning None is meaningful: it means this vehicle contributed no
        crowding evidence at this instant. Emitting an `UNKNOWN` observation
        instead would pad the record with rows asserting nothing, and
        `OccupancyObservation` rejects those by design (section 26.2).
        """
        has_percentage = vehicle.HasField("occupancy_percentage")
        if not occupancy_class.is_known and not has_percentage:
            return None

        ratio = min(vehicle.occupancy_percentage / 100.0, 1.0) if has_percentage else None

        # Occupancy travels with the position feed here, so it is the operator's
        # own report rather than a separate sensor stream (section 6.5).
        occupancy_provenance = Provenance(
            source_type=SourceType.REAL_OPERATOR,
            source_name=provenance.source_name,
            source_timestamp=provenance.source_timestamp,
            ingest_timestamp=provenance.ingest_timestamp,
            quality_score=provenance.quality_score,
            raw_payload_ref=provenance.raw_payload_ref,
        )

        return OccupancyObservation(
            city_id=self.city.city_id,
            vehicle_id=vehicle_id,
            trip_id=vehicle.trip.trip_id or None,
            ts=observed_at,
            occupancy_ratio=ratio,
            occupancy_class=occupancy_class,
            confidence=0.9 if occupancy_class.is_known else 0.5,
            provenance=occupancy_provenance,
        )

    def _quality_score(
        self,
        vehicle,
        has_own_ts: bool,
        observed_at: datetime,
        ingest_ts: datetime,
    ) -> float:
        """Confidence in this observation, in [0, 1] (section 6.8).

        A transparent deduction scheme rather than a learned score: models can
        learn source-specific reliability from it, and a human can explain why
        any given row scored what it did.
        """
        score = 1.0
        if not has_own_ts:
            score -= 0.15  # timestamp borrowed from the feed header
        if not vehicle.trip.trip_id:
            score -= 0.20  # cannot be tied to a scheduled trip
        if not vehicle.stop_id:
            score -= 0.05
        age = (ingest_ts - observed_at).total_seconds()
        if age > self.city.validation.stale_after_s:
            score -= 0.25
        return max(0.0, min(1.0, score))
