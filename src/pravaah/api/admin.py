"""Operator endpoints (SOLUTION.md section 12.2).

The operator's value is **lead time**. A dashboard that reports crowding already
happening is the status quo this project exists to beat, so every hotspot here
carries how many minutes of warning it comes with, and the ranking is by
severity weighted by how soon it lands.

Read-only over the fleet. Nothing in this module writes vehicle state.
"""

from __future__ import annotations

import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, Query, Request

from ..contracts.api import ErrorCode
from ..contracts.events import OccupancyClass
from .auth import require_operator
from .deps import AppResources, now
from .passenger import (
    _band,
    _fail,
    _latest_feed_version,
    _service_midnight,
    _zoneinfo,
)
from .schemas import (
    DataHealthResponse,
    FleetResponse,
    HotspotsResponse,
    HotspotView,
    RouteForecastResponse,
    RouteHourForecast,
)

log = logging.getLogger(__name__)

router = APIRouter(
    prefix="/v1/admin",
    tags=["operator"],
    dependencies=[Depends(require_operator)],
)

#: A stop only counts as a hotspot at or above this crowding level.
HOTSPOT_THRESHOLD = OccupancyClass.STANDING_ROOM_ONLY


def _resources(request: Request) -> AppResources:
    return request.app.state.resources


@router.get("/hotspots", response_model=HotspotsResponse)
def hotspots(
    request: Request,
    horizon_min: int = Query(60, ge=10, le=240),
    limit: int = Query(20, ge=1, le=100),
) -> HotspotsResponse:
    """Predicted crowding hotspots, ranked by severity and urgency.

    This is the operator's core screen: problems that have not happened yet,
    with enough lead time to act on them (section 3.2).
    """
    resources = _resources(request)
    if resources.db_pool is None:
        raise _fail(ErrorCode.FEED_UNAVAILABLE, "schedule database unavailable", status=503)
    if resources.forecaster is None:
        raise _fail(ErrorCode.FEED_UNAVAILABLE, "forecast model unavailable", status=503)

    current = now()
    tz = _zoneinfo(resources.city.timezone)
    midnight = _service_midnight(current, tz)
    local = current.astimezone(tz)
    from_s = local.hour * 3600 + local.minute * 60
    to_s = from_s + horizon_min * 60

    with resources.db_pool.connection() as conn, conn.cursor() as cur:
        feed_version_id = _latest_feed_version(cur, resources.city.city_id)
        # Trip lengths first, as their own cheap grouped scan. Joining this as a
        # correlated CTE inside the window query made the planner choose a plan
        # that did not return within five minutes; two simple queries and a
        # dictionary join in Python are milliseconds.
        cur.execute(
            """
            SELECT trip_id, max(stop_sequence) FROM stop_time
             WHERE feed_version_id = %s GROUP BY trip_id
            """,
            (feed_version_id,),
        )
        totals = {trip_id: total for trip_id, total in cur.fetchall()}

        cur.execute(
            """
            SELECT st.trip_id, st.stop_id, s.name, t.route_id, r.short_name,
                   st.stop_sequence, st.arrival_seconds
              FROM stop_time st
              JOIN trip t ON t.feed_version_id = st.feed_version_id AND t.trip_id = st.trip_id
              JOIN route r ON r.feed_version_id = st.feed_version_id AND r.route_id = t.route_id
              JOIN stop s ON s.feed_version_id = st.feed_version_id AND s.stop_id = st.stop_id
             WHERE st.feed_version_id = %s
               AND st.arrival_seconds BETWEEN %s AND %s
             ORDER BY st.arrival_seconds
             LIMIT 6000
            """,
            (feed_version_id, from_s, to_s),
        )
        rows = cur.fetchall()

    # Collapse to one entry per (stop, route): the soonest service and how many
    # run in the window.
    grouped: dict[tuple[str, str], dict] = {}
    for trip_id, stop_id, stop_name, route_id, short_name, sequence, arrival_s in rows:
        key = (stop_id, route_id)
        total = totals.get(trip_id) or 1
        entry = grouped.setdefault(
            key,
            {
                "stop_name": stop_name,
                "short_name": short_name,
                "soonest": arrival_s,
                "services": 0,
                "positions": [],
            },
        )
        entry["services"] += 1
        entry["soonest"] = min(entry["soonest"], arrival_s)
        entry["positions"].append(sequence / total)

    found: list[HotspotView] = []
    for (stop_id, route_id), entry in grouped.items():
        arrival = midnight + timedelta(seconds=int(entry["soonest"]))
        position = sum(entry["positions"]) / len(entry["positions"])
        quantiles = resources.forecaster.predict(
            arrival.astimezone(tz).hour, position, route_id
        )

        severity = quantiles.p50_class.ordinal
        if severity is None or severity < (HOTSPOT_THRESHOLD.ordinal or 3):
            continue

        lead_min = max(0, int((arrival - current).total_seconds() / 60))
        found.append(
            HotspotView(
                stop_id=stop_id,
                stop_name=entry["stop_name"],
                route_id=route_id,
                route_short_name=entry["short_name"],
                predicted_at=arrival,
                lead_time_min=lead_min,
                services_in_window=entry["services"],
                severity=severity,
                crowd=_band(quantiles),
                reason=(
                    f"{entry['stop_name']} on route {entry['short_name']} is predicted "
                    f"{quantiles.p50_class.value.replace('_', ' ').lower()} "
                    f"in {lead_min} min ({quantiles.p50_onboard} of {quantiles.capacity} onboard)"
                ),
            )
        )

    # Most severe first; among equals, the one landing soonest.
    found.sort(key=lambda h: (-h.severity, h.lead_time_min))

    return HotspotsResponse(
        generated_at=current,
        city_id=resources.city.city_id,
        horizon_min=horizon_min,
        model_version=resources.forecaster.model_version,
        count=len(found[:limit]),
        hotspots=found[:limit],
    )


@router.get("/routes/{route_id}/forecast", response_model=RouteForecastResponse)
def route_forecast(
    request: Request,
    route_id: str,
    hours: int = Query(12, ge=1, le=24),
) -> RouteForecastResponse:
    """Hour-by-hour predicted load for one route (section 12.2)."""
    resources = _resources(request)
    if resources.db_pool is None:
        raise _fail(ErrorCode.FEED_UNAVAILABLE, "schedule database unavailable", status=503)
    if resources.forecaster is None:
        raise _fail(ErrorCode.FEED_UNAVAILABLE, "forecast model unavailable", status=503)

    current = now()
    tz = _zoneinfo(resources.city.timezone)
    start_hour = current.astimezone(tz).hour

    with resources.db_pool.connection() as conn, conn.cursor() as cur:
        feed_version_id = _latest_feed_version(cur, resources.city.city_id)
        cur.execute(
            "SELECT 1 FROM route WHERE feed_version_id = %s AND route_id = %s",
            (feed_version_id, route_id),
        )
        if cur.fetchone() is None:
            raise _fail(
                ErrorCode.NO_ROUTE_FOUND, f"unknown route {route_id}", status=404
            )

    series = []
    for offset in range(hours):
        hour = (start_hour + offset) % 24
        # Mid-run is where a route carries its heaviest load, so it is the
        # honest single number for a route-level summary.
        quantiles = resources.forecaster.predict(hour, 0.5, route_id)
        series.append(
            RouteHourForecast(hour=hour, crowd=_band(quantiles))
        )

    return RouteForecastResponse(
        generated_at=current,
        city_id=resources.city.city_id,
        route_id=route_id,
        model_version=resources.forecaster.model_version,
        hours=series,
    )


@router.get("/vehicles", response_model=FleetResponse)
def admin_vehicles(
    request: Request,
    limit: int = Query(2000, ge=1, le=5000),
) -> FleetResponse:
    """Whole-fleet live state. No bbox -- an operator sees the network.

    This is the one place a full-fleet read is legitimate; the passenger API
    requires a viewport (section 12.4 rule 5).
    """
    resources = _resources(request)
    if not resources.redis_ok():
        raise _fail(ErrorCode.FEED_UNAVAILABLE, "live state is unavailable", status=503)

    current = now()
    events = resources.state.all(now=current)[:limit]
    crowd = resources.occupancy.get_many([e.vehicle_id for e in events], now=current)
    stale_after = resources.city.validation.stale_after_s

    from .passenger import _view

    return FleetResponse(
        generated_at=current,
        city_id=resources.city.city_id,
        count=len(events),
        vehicles=[_view(e, current, stale_after, crowd.get(e.vehicle_id)) for e in events],
    )


@router.get("/data-health", response_model=DataHealthResponse)
def data_health(request: Request) -> DataHealthResponse:
    """Feed freshness and coverage (section 12.2).

    Occupancy coverage is reported explicitly because a silent drop in it is the
    failure most likely to go unnoticed -- the map keeps moving while the crowd
    layer quietly becomes all-unknown.
    """
    resources = _resources(request)
    current = now()

    tracked = 0
    stale = 0
    with_occupancy = 0
    oldest_age_s = 0
    source_types: dict[str, int] = {}

    if resources.redis_ok():
        events = resources.state.all(now=current)
        tracked = len(events)
        stale_after = resources.city.validation.stale_after_s
        crowd = resources.occupancy.get_many([e.vehicle_id for e in events], now=current)
        with_occupancy = sum(
            1 for vehicle_id in crowd if crowd[vehicle_id].occupancy_class.is_known
        )
        for event in events:
            age = int((current - event.ts).total_seconds())
            oldest_age_s = max(oldest_age_s, age)
            if age > stale_after:
                stale += 1
            name = event.provenance.source_type.value
            source_types[name] = source_types.get(name, 0) + 1

    feed_version_id = None
    if resources.db_pool is not None:
        try:
            with resources.db_pool.connection() as conn, conn.cursor() as cur:
                feed_version_id = _latest_feed_version(cur, resources.city.city_id)
        except Exception:  # noqa: BLE001 -- health reports, never raises
            feed_version_id = None

    return DataHealthResponse(
        generated_at=current,
        city_id=resources.city.city_id,
        database=resources.database_ok(),
        redis=resources.redis_ok(),
        feed_version_id=feed_version_id,
        vehicles_tracked=tracked,
        vehicles_stale=stale,
        vehicles_with_occupancy=with_occupancy,
        occupancy_coverage=round(with_occupancy / tracked, 4) if tracked else 0.0,
        oldest_position_age_s=oldest_age_s,
        source_types=source_types,
        forecast_model=(
            resources.forecaster.model_version if resources.forecaster else None
        ),
    )
