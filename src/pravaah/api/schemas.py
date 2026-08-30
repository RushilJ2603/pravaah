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

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

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


class CrowdBand(BaseModel):
    """A crowd prediction as a band, never a point (section 12.4 rule 2)."""

    # `model_version` is required by section 12.4 rule 1; pydantic reserves the
    # `model_` prefix, so the namespace guard is opened deliberately here.
    model_config = ConfigDict(frozen=True, protected_namespaces=())

    p10_class: OccupancyClass
    p50_class: OccupancyClass
    p90_class: OccupancyClass
    p10_onboard: int | None
    p50_onboard: int | None
    p90_onboard: int | None
    p50_ratio: float | None
    capacity: int | None
    model_version: str
    is_fallback: bool = False


class StopForecast(BaseModel):
    """Predicted crowd when the vehicle reaches one upcoming stop."""

    model_config = ConfigDict(frozen=True)

    stop_id: str
    stop_name: str
    stop_sequence: int
    scheduled_arrival: datetime
    crowd: CrowdBand


class TripForecastResponse(BaseModel):
    """GET /v1/trips/{tripId}/forecast (section 12.1)."""

    model_config = ConfigDict(frozen=True, protected_namespaces=())

    generated_at: datetime
    city_id: str
    trip_id: str
    route_id: str | None
    model_version: str
    stops: list[StopForecast]


class JourneyLeg(BaseModel):
    model_config = ConfigDict(frozen=True)

    route_id: str
    route_name: str | None
    board_stop_id: str
    board_stop_name: str
    alight_stop_id: str
    alight_stop_name: str
    departure: datetime
    arrival: datetime
    stops: int
    crowd: CrowdBand


class JourneyOption(BaseModel):
    """One ranked itinerary. `reasons` is mandatory (section 21)."""

    model_config = ConfigDict(frozen=True)

    option_id: str
    total_minutes: int
    transfers: int
    departure: datetime
    arrival: datetime
    legs: list[JourneyLeg]
    score: float
    reasons: list[str]
    is_recommended: bool = False


class PlanResponse(BaseModel):
    """GET /v1/plan (section 29.1)."""

    model_config = ConfigDict(frozen=True)

    generated_at: datetime
    city_id: str
    profile: str
    options: list[JourneyOption]


class HotspotView(BaseModel):
    """One predicted crowding hotspot, with its lead time."""

    model_config = ConfigDict(frozen=True)

    stop_id: str
    stop_name: str
    route_id: str
    route_short_name: str | None
    predicted_at: datetime
    lead_time_min: int
    services_in_window: int
    severity: int
    crowd: CrowdBand
    reason: str


class HotspotsResponse(BaseModel):
    """GET /v1/admin/hotspots (section 12.2)."""

    model_config = ConfigDict(frozen=True, protected_namespaces=())

    generated_at: datetime
    city_id: str
    horizon_min: int
    model_version: str
    count: int
    hotspots: list[HotspotView]


class RouteHourForecast(BaseModel):
    model_config = ConfigDict(frozen=True)

    hour: int
    crowd: CrowdBand


class RouteForecastResponse(BaseModel):
    """GET /v1/admin/routes/{id}/forecast (section 12.2)."""

    model_config = ConfigDict(frozen=True, protected_namespaces=())

    generated_at: datetime
    city_id: str
    route_id: str
    model_version: str
    hours: list[RouteHourForecast]


class DataHealthResponse(BaseModel):
    """GET /v1/admin/data-health (section 12.2)."""

    model_config = ConfigDict(frozen=True)

    generated_at: datetime
    city_id: str
    database: bool
    redis: bool
    feed_version_id: int | None
    vehicles_tracked: int
    vehicles_stale: int
    vehicles_with_occupancy: int
    occupancy_coverage: float
    oldest_position_age_s: int
    source_types: dict[str, int]
    forecast_model: str | None


class LoginRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=1024)


class LoginResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    access_token: str
    role: str
    expires_in: int = Field(gt=0)


class ShiftStartRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    vehicle_id: str = Field(min_length=1, max_length=128)
    trip_id: str | None = Field(default=None, max_length=256)
    route_id: str | None = Field(default=None, max_length=128)
    device_id: str = Field(min_length=1, max_length=256)


class ShiftStartResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    shift_id: int
    started_at: datetime


class ShiftPositionRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    lat: float = Field(ge=-90.0, le=90.0)
    lon: float = Field(ge=-180.0, le=180.0)
    accuracy_m: float = Field(ge=0.0, le=500.0)
    speed_mps: float | None = Field(default=None, ge=0.0)
    timestamp: AwareDatetime


class OccupancyReportRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    trip_id: str | None = Field(default=None, max_length=256)
    vehicle_id: str = Field(min_length=1, max_length=128)
    occupancy_class: OccupancyClass
    reported_at: AwareDatetime


class StopPoint(BaseModel):
    """One stop on a trip's path, with the coordinates a client draws."""

    model_config = ConfigDict(frozen=True)

    stop_id: str
    name: str
    lat: float
    lon: float
    stop_sequence: int
    scheduled_arrival: datetime | None = None


class TripDetailResponse(BaseModel):
    """GET /v1/trips/{tripId} (section 29.6)."""

    model_config = ConfigDict(frozen=True)

    generated_at: datetime
    city_id: str
    trip_id: str
    route_id: str | None
    route_name: str | None
    direction_id: int | None
    origin: StopPoint
    destination: StopPoint
    stops: list[StopPoint]
