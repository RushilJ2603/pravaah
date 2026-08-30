"""Passenger read endpoints.

Implements SOLUTION.md section 12.1 and the schemas in section 29.2.

Slice A is read-only: live fleet state and scheduled departures. Forecasting
arrives in Slice B, and until then crowd fields are `UNKNOWN` rather than absent
or zero -- the API tells the truth about what it does not yet know.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query, Request

from ..contracts.api import ErrorCode
from ..contracts.events import OccupancyClass
from .deps import AppResources, now
from .schemas import (
    DeparturesResponse,
    DepartureView,
    FleetResponse,
    VehicleResponse,
    VehicleView,
)

log = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["passenger"])

#: Server-side cap from section 29.2. A client asking for more gets this many.
MAX_FLEET_LIMIT = 2000
DEFAULT_FLEET_LIMIT = 500

#: How far ahead `/departures` looks when the caller does not say.
DEFAULT_DEPARTURE_WINDOW_MIN = 60


def _resources(request: Request) -> AppResources:
    return request.app.state.resources


def _fail(code: ErrorCode, message: str, status: int = 400) -> HTTPException:
    return HTTPException(status_code=status, detail={"code": code.value, "message": message})


def parse_bbox(raw: str) -> tuple[float, float, float, float]:
    """Parse `minLat,minLon,maxLat,maxLon`.

    Required by section 29.2: omitting it is an error, never a full-fleet
    response, so a city-wide payload is not reachable by accident.
    """
    parts = raw.split(",")
    if len(parts) != 4:
        raise _fail(
            ErrorCode.INVALID_COORDINATES,
            "bbox must be minLat,minLon,maxLat,maxLon",
        )
    try:
        min_lat, min_lon, max_lat, max_lon = (float(p) for p in parts)
    except ValueError:
        raise _fail(ErrorCode.INVALID_COORDINATES, "bbox values must be numbers") from None

    if not (-90 <= min_lat <= 90 and -90 <= max_lat <= 90):
        raise _fail(ErrorCode.INVALID_COORDINATES, "latitude out of range")
    if not (-180 <= min_lon <= 180 and -180 <= max_lon <= 180):
        raise _fail(ErrorCode.INVALID_COORDINATES, "longitude out of range")
    if min_lat >= max_lat or min_lon >= max_lon:
        raise _fail(ErrorCode.INVALID_COORDINATES, "bbox min must be less than max")

    return min_lat, min_lon, max_lat, max_lon


@router.get("/vehicles", response_model=FleetResponse)
def list_vehicles(
    request: Request,
    bbox: str = Query(..., description="minLat,minLon,maxLat,maxLon"),
    limit: int = Query(DEFAULT_FLEET_LIMIT, ge=1, le=MAX_FLEET_LIMIT),
) -> FleetResponse:
    """Fleet inside a viewport (section 29.2)."""
    resources = _resources(request)
    min_lat, min_lon, max_lat, max_lon = parse_bbox(bbox)

    if not resources.redis_ok():
        raise _fail(ErrorCode.FEED_UNAVAILABLE, "live state is unavailable", status=503)

    current = now()
    events = resources.state.in_viewport(
        min_lat, min_lon, max_lat, max_lon, now=current, limit=limit
    )
    stale_after = resources.city.validation.stale_after_s

    return FleetResponse(
        generated_at=current,
        city_id=resources.city.city_id,
        count=len(events),
        vehicles=[VehicleView.from_event(e, current, stale_after) for e in events[:limit]],
    )


@router.get("/vehicles/{vehicle_id}", response_model=VehicleResponse)
def get_vehicle(request: Request, vehicle_id: str) -> VehicleResponse:
    """Current state of one vehicle, with freshness (section 12.1)."""
    resources = _resources(request)
    if not resources.redis_ok():
        raise _fail(ErrorCode.FEED_UNAVAILABLE, "live state is unavailable", status=503)

    current = now()
    event = resources.state.get(vehicle_id, now=current)
    if event is None:
        raise _fail(
            ErrorCode.NO_ROUTE_FOUND, f"no live state for vehicle {vehicle_id}", status=404
        )

    return VehicleResponse(
        generated_at=current,
        city_id=resources.city.city_id,
        vehicle=VehicleView.from_event(
            event, current, resources.city.validation.stale_after_s
        ),
    )


@router.get("/stops/{stop_id}/departures", response_model=DeparturesResponse)
def stop_departures(
    request: Request,
    stop_id: str,
    window_min: int = Query(DEFAULT_DEPARTURE_WINDOW_MIN, ge=1, le=240),
    limit: int = Query(20, ge=1, le=100),
) -> DeparturesResponse:
    """Upcoming scheduled departures from a stop.

    Crowd fields are `UNKNOWN` until Slice B adds forecasting. They are present
    and explicitly unknown rather than omitted, so a client never has to infer
    that a missing field means an empty vehicle (section 12.4 rule 3).
    """
    resources = _resources(request)
    if resources.db_pool is None:
        raise _fail(ErrorCode.FEED_UNAVAILABLE, "schedule database unavailable", status=503)

    current = now()
    with resources.db_pool.connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT feed_version_id FROM feed_version
             WHERE city_id = %s ORDER BY imported_at DESC LIMIT 1
            """,
            (resources.city.city_id,),
        )
        row = cur.fetchone()
        if row is None:
            raise _fail(
                ErrorCode.FEED_UNAVAILABLE, "no GTFS feed imported", status=503
            )
        feed_version_id = row[0]

        cur.execute(
            "SELECT name FROM stop WHERE feed_version_id = %s AND stop_id = %s",
            (feed_version_id, stop_id),
        )
        stop_row = cur.fetchone()
        if stop_row is None:
            raise _fail(
                ErrorCode.NO_ROUTE_FOUND, f"unknown stop {stop_id}", status=404
            )

        # Seconds past service midnight, so the comparison stays in the same
        # units GTFS uses and overnight trips past 24:00 are not lost.
        local = current.astimezone(_zoneinfo(resources.city.timezone))
        seconds_now = local.hour * 3600 + local.minute * 60 + local.second

        cur.execute(
            """
            SELECT st.trip_id, t.route_id, t.direction_id, st.departure_seconds
              FROM stop_time st
              JOIN trip t
                ON t.feed_version_id = st.feed_version_id AND t.trip_id = st.trip_id
             WHERE st.feed_version_id = %s
               AND st.stop_id = %s
               AND st.departure_seconds BETWEEN %s AND %s
             ORDER BY st.departure_seconds
             LIMIT %s
            """,
            (feed_version_id, stop_id, seconds_now, seconds_now + window_min * 60, limit),
        )
        rows = cur.fetchall()

    departures = [
        DepartureView(
            trip_id=trip_id,
            route_id=route_id,
            direction_id=direction_id,
            scheduled_departure=_at_service_seconds(local, departure_seconds),
            crowd_class=OccupancyClass.UNKNOWN,
            crowd_p50=None,
            is_forecast=False,
        )
        for trip_id, route_id, direction_id, departure_seconds in rows
    ]

    return DeparturesResponse(
        generated_at=current,
        city_id=resources.city.city_id,
        stop_id=stop_id,
        stop_name=stop_row[0],
        feed_version_id=feed_version_id,
        departures=departures,
    )


def _zoneinfo(name: str):
    from zoneinfo import ZoneInfo

    return ZoneInfo(name)


def _at_service_seconds(local_now, seconds: int):
    """Turn seconds-past-service-midnight into an absolute local timestamp."""
    from datetime import timedelta

    midnight = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    return midnight + timedelta(seconds=seconds)
