"""HTTP response schemas for the read-only endpoints.

Implements SOLUTION.md section 29.2 and section 12.4.

These are the wire shapes, kept distinct from the internal contracts in
`pravaah.contracts.events`. An internal event carries provenance and full
precision; a passenger response carries only what a client needs plus the
freshness fields section 33.3 requires it to display.

Two invariants are structural here rather than left to view code:

* `age_s` and `is_stale` are always present, so a client renders the freshness
  badge without computing clock skew itself.
* `occupancy_class` is always present and is `"UNKNOWN"` when the vehicle
  reported nothing -- never omitted, never `"EMPTY"` (section 12.4 rule 3).
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from ..contracts.events import OccupancyClass, VehiclePositionEvent, VehicleStopStatus
from ..contracts.provenance import SourceType


class VehicleView(BaseModel):
    """One vehicle as the map sees it."""

    model_config = ConfigDict(frozen=True)

    vehicle_id: str
    trip_id: str | None = None
    route_id: str | None = None
    direction_id: int | None = None

    lat: float
    lon: float
    bearing: float | None = None
    speed_mps: float | None = None

    stop_id: str | None = None
    current_status: VehicleStopStatus | None = None

    occupancy_class: OccupancyClass = OccupancyClass.UNKNOWN
    occupancy_ratio: float | None = None

    ts: datetime
    age_s: int = Field(ge=0)
    is_stale: bool

    source_type: SourceType
    quality_score: float = Field(ge=0.0, le=1.0)

    @classmethod
    def from_event(
        cls,
        event: VehiclePositionEvent,
        now: datetime,
        stale_after_s: int,
        occupancy_class: OccupancyClass = OccupancyClass.UNKNOWN,
        occupancy_ratio: float | None = None,
    ) -> VehicleView:
        age = max(0, int((now - event.ts).total_seconds()))
        return cls(
            vehicle_id=event.vehicle_id,
            trip_id=event.trip_id,
            route_id=event.route_id,
            direction_id=event.direction_id,
            lat=event.lat,
            lon=event.lon,
            bearing=event.bearing,
            speed_mps=event.speed_mps,
            stop_id=event.stop_id,
            current_status=event.current_status,
            occupancy_class=occupancy_class,
            # A ratio without a known class would be a number the UI could show
            # for a vehicle that reported nothing. Tie them together.
            occupancy_ratio=occupancy_ratio if occupancy_class.is_known else None,
            ts=event.ts,
            age_s=age,
            is_stale=age > stale_after_s,
            source_type=event.provenance.source_type,
            quality_score=event.provenance.quality_score,
        )


class FleetResponse(BaseModel):
    """GET /v1/vehicles (SOLUTION.md section 29.2)."""

    model_config = ConfigDict(frozen=True)

    generated_at: datetime
    city_id: str
    count: int = Field(ge=0)
    vehicles: list[VehicleView]


class VehicleResponse(BaseModel):
    """GET /v1/vehicles/{vehicleId}."""

    model_config = ConfigDict(frozen=True)

    generated_at: datetime
    city_id: str
    vehicle: VehicleView


class DepartureView(BaseModel):
    """One upcoming departure from a stop.

    Until Slice B lands a forecast, `crowd_class` is `UNKNOWN` and `crowd` is
    null. That is the honest representation of "no forecast yet" and is exactly
    what section 12.4 rule 3 requires -- not a zero, and not an omission.
    """

    model_config = ConfigDict(frozen=True)

    trip_id: str
    route_id: str | None = None
    direction_id: int | None = None
    scheduled_departure: datetime
    headsign: str | None = None

    crowd_class: OccupancyClass = OccupancyClass.UNKNOWN
    crowd_p50: float | None = None
    is_forecast: bool = False


class DeparturesResponse(BaseModel):
    """GET /v1/stops/{stopId}/departures."""

    model_config = ConfigDict(frozen=True)

    generated_at: datetime
    city_id: str
    stop_id: str
    stop_name: str
    feed_version_id: int
    departures: list[DepartureView]


class HealthResponse(BaseModel):
    """GET /v1/health -- dependency reachability, for the deploy runbook (section 14.4)."""

    model_config = ConfigDict(frozen=True)

    status: str
    city_id: str
    generated_at: datetime
    database: bool
    redis: bool
    vehicles_tracked: int
    feed_version_id: int | None = None
