"""Canonical event contracts.

Implements SOLUTION.md section 26.2.

These are the stable schemas every plane downstream of ingestion speaks. City
adapters translate into these types; nothing past `adapters/` sees a
city-specific payload (SOLUTION.md section 25, layout rules).

Changing a model here is a document-level change, not a refactor.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .provenance import Provenance


class OccupancyClass(str, Enum):
    """GTFS-Realtime occupancy ladder, preserved verbatim so the mapping is lossless.

    UNKNOWN is a real member of this enum, distinct from both `None` and EMPTY.
    SOLUTION.md section 12.4 rule 3: missing occupancy must never silently become
    zero or "empty bus". Coercing UNKNOWN to EMPTY is a defect.
    """

    EMPTY = "EMPTY"
    MANY_SEATS_AVAILABLE = "MANY_SEATS_AVAILABLE"
    FEW_SEATS_AVAILABLE = "FEW_SEATS_AVAILABLE"
    STANDING_ROOM_ONLY = "STANDING_ROOM_ONLY"
    CRUSHED_STANDING_ROOM_ONLY = "CRUSHED_STANDING_ROOM_ONLY"
    FULL = "FULL"
    NOT_ACCEPTING_PASSENGERS = "NOT_ACCEPTING_PASSENGERS"
    UNKNOWN = "UNKNOWN"

    @property
    def is_known(self) -> bool:
        return self is not OccupancyClass.UNKNOWN

    @property
    def ordinal(self) -> int | None:
        """Position on the crowding ladder, or None when unknown.

        NOT_ACCEPTING_PASSENGERS shares the top of the ladder with FULL: it is an
        operational state, not a distinct crowding level.
        """
        return _OCCUPANCY_ORDINAL.get(self)


_OCCUPANCY_ORDINAL: dict[OccupancyClass, int] = {
    OccupancyClass.EMPTY: 0,
    OccupancyClass.MANY_SEATS_AVAILABLE: 1,
    OccupancyClass.FEW_SEATS_AVAILABLE: 2,
    OccupancyClass.STANDING_ROOM_ONLY: 3,
    OccupancyClass.CRUSHED_STANDING_ROOM_ONLY: 4,
    OccupancyClass.FULL: 5,
    OccupancyClass.NOT_ACCEPTING_PASSENGERS: 5,
}


class VehicleStopStatus(str, Enum):
    """GTFS-Realtime VehicleStopStatus."""

    INCOMING_AT = "INCOMING_AT"
    STOPPED_AT = "STOPPED_AT"
    IN_TRANSIT_TO = "IN_TRANSIT_TO"


class VehiclePositionEvent(BaseModel):
    """One vehicle observation, normalized across cities.

    `speed_mps` is DERIVED from consecutive positions (SOLUTION.md section 28.4).
    The raw GTFS-RT speed field is populated on only ~9.8% of MBTA rows and must
    not be used (SOLUTION.md section 6.2.1); adapters leave this None and the
    stream processor fills it.
    """

    model_config = ConfigDict(frozen=True)

    city_id: str = Field(min_length=1)
    agency_id: str = Field(min_length=1)
    vehicle_id: str = Field(min_length=1)

    trip_id: str | None = None
    route_id: str | None = None
    direction_id: int | None = Field(default=None, ge=0, le=1)

    ts: datetime
    lat: float = Field(ge=-90.0, le=90.0)
    lon: float = Field(ge=-180.0, le=180.0)
    bearing: float | None = Field(default=None, ge=0.0, lt=360.0)
    speed_mps: float | None = Field(default=None, ge=0.0)

    stop_id: str | None = None
    current_stop_sequence: int | None = Field(default=None, ge=0)
    current_status: VehicleStopStatus | None = None
    matched_segment_id: str | None = None

    provenance: Provenance


class OccupancyObservation(BaseModel):
    """One crowding observation, from any source in the hierarchy.

    At least one of `onboard`, `occupancy_ratio` or `occupancy_class` must carry
    information. An observation asserting nothing is rejected rather than stored
    as an implicit "empty".
    """

    model_config = ConfigDict(frozen=True)

    city_id: str = Field(min_length=1)
    vehicle_id: str = Field(min_length=1)
    trip_id: str | None = None

    ts: datetime
    onboard: int | None = Field(default=None, ge=0)
    capacity: int | None = Field(default=None, gt=0)
    occupancy_ratio: float | None = Field(default=None, ge=0.0, le=1.0)
    occupancy_class: OccupancyClass = OccupancyClass.UNKNOWN
    boardings: int | None = Field(default=None, ge=0)
    alightings: int | None = Field(default=None, ge=0)

    confidence: float = Field(ge=0.0, le=1.0)
    provenance: Provenance

    @model_validator(mode="after")
    def _assert_something_known(self) -> OccupancyObservation:
        if (
            self.onboard is None
            and self.occupancy_ratio is None
            and not self.occupancy_class.is_known
        ):
            raise ValueError(
                "occupancy observation carries no information: set onboard, "
                "occupancy_ratio or a known occupancy_class"
            )
        return self

    @model_validator(mode="after")
    def _assert_onboard_within_capacity(self) -> OccupancyObservation:
        if self.onboard is not None and self.capacity is not None:
            if self.onboard > self.capacity:
                raise ValueError(
                    f"onboard {self.onboard} exceeds capacity {self.capacity}"
                )
        return self


class StopPassageEvent(BaseModel):
    """A vehicle passing a stop.

    These are the stable labels for segment travel-time learning
    (SOLUTION.md section 8.1), so they are emitted deliberately rather than
    inferred ad hoc at query time.
    """

    model_config = ConfigDict(frozen=True)

    city_id: str = Field(min_length=1)
    vehicle_id: str = Field(min_length=1)
    trip_id: str = Field(min_length=1)
    stop_id: str = Field(min_length=1)
    stop_sequence: int = Field(ge=0)

    arrival_ts: datetime | None = None
    departure_ts: datetime | None = None
    dwell_seconds: float | None = Field(default=None, ge=0.0)
    schedule_deviation_seconds: float | None = None

    provenance: Provenance

    @model_validator(mode="after")
    def _assert_has_a_time(self) -> StopPassageEvent:
        if self.arrival_ts is None and self.departure_ts is None:
            raise ValueError("stop passage needs arrival_ts or departure_ts")
        if self.arrival_ts and self.departure_ts and self.departure_ts < self.arrival_ts:
            raise ValueError("departure_ts precedes arrival_ts")
        return self

    @property
    def ts(self) -> datetime:
        """Canonical time for the hypertable partition key (SOLUTION.md section 27)."""
        return self.arrival_ts or self.departure_ts  # type: ignore[return-value]


class SegmentTravelTime(BaseModel):
    """Observed traversal of one stop-to-stop segment."""

    model_config = ConfigDict(frozen=True)

    city_id: str = Field(min_length=1)
    segment_id: str = Field(min_length=1)
    vehicle_id: str = Field(min_length=1)
    trip_id: str | None = None
    start_ts: datetime
    end_ts: datetime
    seconds: float = Field(gt=0.0)

    provenance: Provenance

    @model_validator(mode="after")
    def _assert_ordered(self) -> SegmentTravelTime:
        if self.end_ts <= self.start_ts:
            raise ValueError("end_ts must be after start_ts")
        return self
