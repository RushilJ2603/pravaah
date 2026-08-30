"""Passenger read endpoints.

Implements SOLUTION.md section 12.1 and the schemas in section 29.2.

Slice A is read-only: live fleet state and scheduled departures. Forecasting
arrives in Slice B, and until then crowd fields are `UNKNOWN` rather than absent
or zero -- the API tells the truth about what it does not yet know.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Query, Request

from ..contracts.api import ErrorCode
from ..contracts.events import (
    OccupancyClass,
    OccupancyObservation,
    VehiclePositionEvent,
)
from .deps import AppResources, now
from .schemas import (
    CrowdBand,
    DeparturesResponse,
    DepartureView,
    FleetResponse,
    JourneyLeg,
    JourneyOption,
    PlanResponse,
    StopForecast,
    TripForecastResponse,
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


def _view(
    event: VehiclePositionEvent,
    current: datetime,
    stale_after_s: int,
    crowd: OccupancyObservation | None,
) -> VehicleView:
    """Join a position with its latest crowd reading, if there is one.

    `crowd is None` covers three different situations -- the vehicle never
    reported occupancy, the feed does not publish it at all, or the last reading
    aged out. All three are `UNKNOWN`, and none of them is `EMPTY`
    (section 12.4 rule 3). Collapsing them into a zero is the single most
    damaging bug this system could ship, so the absence is handled here once
    rather than at each call site.
    """
    if crowd is None:
        return VehicleView.from_event(event, current, stale_after_s)
    return VehicleView.from_event(
        event,
        current,
        stale_after_s,
        occupancy_class=crowd.occupancy_class,
        occupancy_ratio=crowd.occupancy_ratio,
    )


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

    shown = events[:limit]
    crowd = resources.occupancy.get_many([e.vehicle_id for e in shown], now=current)

    return FleetResponse(
        generated_at=current,
        city_id=resources.city.city_id,
        count=len(shown),
        vehicles=[_view(e, current, stale_after, crowd.get(e.vehicle_id)) for e in shown],
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
        vehicle=_view(
            event,
            current,
            resources.city.validation.stale_after_s,
            resources.occupancy.get(vehicle_id, now=current),
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


# ---------------------------------------------------------------------------
# Forecast and journey planning
# ---------------------------------------------------------------------------


def _band(quantiles, is_fallback: bool | None = None) -> CrowdBand:
    """Wire shape for a crowd distribution. Never collapses to one number."""
    return CrowdBand(
        p10_class=quantiles.p10_class,
        p50_class=quantiles.p50_class,
        p90_class=quantiles.p90_class,
        p10_onboard=quantiles.p10_onboard,
        p50_onboard=quantiles.p50_onboard,
        p90_onboard=quantiles.p90_onboard,
        p50_ratio=quantiles.p50_ratio if quantiles.p50_class.is_known else None,
        capacity=quantiles.capacity,
        model_version=quantiles.model_version,
        is_fallback=(
            getattr(quantiles, "is_fallback", False)
            if is_fallback is None
            else is_fallback
        ),
    )


def _service_midnight(current: datetime, tz) -> datetime:
    local = current.astimezone(tz)
    return local.replace(hour=0, minute=0, second=0, microsecond=0)


@router.get("/trips/{trip_id}/forecast", response_model=TripForecastResponse)
def trip_forecast(request: Request, trip_id: str) -> TripForecastResponse:
    """Predicted crowd at each upcoming stop of a trip (section 12.1).

    This is the product's core claim: not how full the bus is now, but how full
    it will be when it reaches the stop the passenger is waiting at.
    """
    resources = _resources(request)
    if resources.db_pool is None:
        raise _fail(ErrorCode.FEED_UNAVAILABLE, "schedule database unavailable", status=503)
    if resources.forecaster is None:
        raise _fail(ErrorCode.FEED_UNAVAILABLE, "forecast model unavailable", status=503)

    current = now()
    tz = _zoneinfo(resources.city.timezone)
    midnight = _service_midnight(current, tz)

    with resources.db_pool.connection() as conn, conn.cursor() as cur:
        feed_version_id = _latest_feed_version(cur, resources.city.city_id)
        cur.execute(
            """
            SELECT st.stop_sequence, st.stop_id, s.name, st.arrival_seconds, t.route_id
              FROM stop_time st
              JOIN stop s ON s.feed_version_id = st.feed_version_id AND s.stop_id = st.stop_id
              JOIN trip t ON t.feed_version_id = st.feed_version_id AND t.trip_id = st.trip_id
             WHERE st.feed_version_id = %s AND st.trip_id = %s
             ORDER BY st.stop_sequence
            """,
            (feed_version_id, trip_id),
        )
        rows = cur.fetchall()

    if not rows:
        raise _fail(ErrorCode.NO_ROUTE_FOUND, f"unknown trip {trip_id}", status=404)

    total = len(rows)
    route_id = rows[0][4]
    stops: list[StopForecast] = []
    for index, (sequence, stop_id, name, arrival_s, _route) in enumerate(rows):
        position = index / max(total - 1, 1)
        arrival = midnight + timedelta(seconds=int(arrival_s))
        quantiles = resources.forecaster.predict(
            arrival.astimezone(tz).hour, position, route_id
        )
        stops.append(
            StopForecast(
                stop_id=stop_id,
                stop_name=name,
                stop_sequence=sequence,
                scheduled_arrival=arrival,
                crowd=_band(quantiles),
            )
        )

    return TripForecastResponse(
        generated_at=current,
        city_id=resources.city.city_id,
        trip_id=trip_id,
        route_id=route_id,
        model_version=resources.forecaster.model_version,
        stops=stops,
    )


#: Preference profiles (section 10.2). Weights are per-minute-equivalents: how
#: many minutes of travel a passenger will trade to avoid one unit of crowding
#: or one transfer.
PROFILES: dict[str, dict[str, float]] = {
    "fastest": {"crowd": 0.5, "transfer": 4.0, "wait": 1.0},
    "least_crowded": {"crowd": 14.0, "transfer": 6.0, "wait": 1.0},
    "most_reliable": {"crowd": 2.0, "transfer": 25.0, "wait": 1.0},
    "balanced": {"crowd": 6.0, "transfer": 8.0, "wait": 1.0},
}

#: How far a passenger will walk to a stop, metres.
WALK_RADIUS_M = 700

#: Minimum time to change vehicles at an interchange, seconds. A connection
#: tighter than this is not a journey a passenger can actually make.
MIN_TRANSFER_S = 180

#: An interchange is only worth considering if the wait there is reasonable.
MAX_TRANSFER_WAIT_S = 1800

#: Bounds on the transfer search. Without these the four-way join over the
#: timetable degrades badly; with them the search stays interactive.
MAX_BOARDINGS = 250
MAX_ARRIVALS = 500


@router.get("/plan", response_model=PlanResponse)
def plan(
    request: Request,
    from_lat: float = Query(..., ge=-90, le=90),
    from_lon: float = Query(..., ge=-180, le=180),
    to_lat: float = Query(..., ge=-90, le=90),
    to_lon: float = Query(..., ge=-180, le=180),
    profile: str = Query("balanced"),
    window_min: int = Query(60, ge=5, le=240),
) -> PlanResponse:
    """Ranked journeys using *predicted* crowd, with a reason for each.

    Routing itself is deterministic -- candidates come from the timetable, not
    from a model (section 5). The model only predicts the conditions each
    candidate will face, and the ranking is an explicit weighted cost so every
    option can say why it scored as it did.
    """
    resources = _resources(request)
    if resources.db_pool is None:
        raise _fail(ErrorCode.FEED_UNAVAILABLE, "schedule database unavailable", status=503)
    if profile not in PROFILES:
        raise _fail(
            ErrorCode.INVALID_COORDINATES,
            f"unknown profile '{profile}'; choose one of {sorted(PROFILES)}",
        )

    current = now()
    tz = _zoneinfo(resources.city.timezone)
    midnight = _service_midnight(current, tz)
    local = current.astimezone(tz)
    from_seconds = local.hour * 3600 + local.minute * 60
    to_seconds = from_seconds + window_min * 60

    with resources.db_pool.connection() as conn, conn.cursor() as cur:
        feed_version_id = _latest_feed_version(cur, resources.city.city_id)
        origins = _stops_near(cur, feed_version_id, from_lat, from_lon)
        destinations = _stops_near(cur, feed_version_id, to_lat, to_lon)
        if not origins or not destinations:
            raise _fail(
                ErrorCode.OUT_OF_SERVICE_AREA,
                "no stops within walking distance of both points",
                status=404,
            )

        cur.execute(
            """
            SELECT st1.trip_id, t.route_id, r.long_name,
                   st1.stop_id, so.name, st1.stop_sequence, st1.departure_seconds,
                   st2.stop_id, sd.name, st2.stop_sequence, st2.arrival_seconds,
                   (SELECT count(*) FROM stop_time stc
                     WHERE stc.feed_version_id = st1.feed_version_id
                       AND stc.trip_id = st1.trip_id) AS trip_stops
              FROM stop_time st1
              JOIN stop_time st2
                ON st2.feed_version_id = st1.feed_version_id
               AND st2.trip_id = st1.trip_id
               AND st2.stop_sequence > st1.stop_sequence
              JOIN trip t ON t.feed_version_id = st1.feed_version_id AND t.trip_id = st1.trip_id
              JOIN route r ON r.feed_version_id = st1.feed_version_id AND r.route_id = t.route_id
              JOIN stop so ON so.feed_version_id = st1.feed_version_id AND so.stop_id = st1.stop_id
              JOIN stop sd ON sd.feed_version_id = st1.feed_version_id AND sd.stop_id = st2.stop_id
             WHERE st1.feed_version_id = %s
               AND st1.stop_id = ANY(%s) AND st2.stop_id = ANY(%s)
               AND st1.departure_seconds BETWEEN %s AND %s
             ORDER BY st1.departure_seconds
             LIMIT 40
            """,
            (
                feed_version_id,
                [s[0] for s in origins],
                [s[0] for s in destinations],
                from_seconds,
                to_seconds,
            ),
        )
        rows = cur.fetchall()

    weights = PROFILES[profile]
    options: list[JourneyOption] = []
    seen_routes: set[str] = set()

    for row in rows:
        (
            trip_id, route_id, route_name,
            board_id, board_name, board_seq, depart_s,
            alight_id, alight_name, alight_seq, arrive_s,
            trip_stops,
        ) = row

        # One option per route: ten departures of the same bus is not choice.
        if route_id in seen_routes:
            continue
        seen_routes.add(route_id)

        departure = midnight + timedelta(seconds=int(depart_s))
        arrival = midnight + timedelta(seconds=int(arrive_s))
        ride_min = max(1, int((arrive_s - depart_s) / 60))
        wait_min = max(0, int((depart_s - from_seconds) / 60))

        position = (board_seq - 1) / max(trip_stops - 1, 1)
        quantiles = (
            resources.forecaster.predict(
                departure.astimezone(tz).hour, position, route_id
            )
            if resources.forecaster
            else None
        )
        crowd_ordinal = (
            quantiles.p50_class.ordinal
            if quantiles and quantiles.p50_class.ordinal is not None
            else 0
        )

        score = (
            ride_min
            + wait_min * weights["wait"]
            + crowd_ordinal * weights["crowd"]
        )

        reasons: list[str] = []
        if quantiles and quantiles.p50_class.is_known:
            reasons.append(f"predicted {_readable(quantiles.p50_class)} when you board")
            if quantiles.p90_class is not quantiles.p50_class:
                reasons.append(f"could be as busy as {_readable(quantiles.p90_class)}")
        else:
            reasons.append("no crowd forecast available for this departure")
        reasons.append(f"{ride_min} min on board, no transfers")
        if wait_min <= 3:
            reasons.append("leaves within 3 minutes")
        elif wait_min >= 20:
            reasons.append(f"{wait_min} min wait before departure")

        options.append(
            JourneyOption(
                option_id=f"{trip_id}:{board_seq}-{alight_seq}",
                total_minutes=ride_min + wait_min,
                transfers=0,
                departure=departure,
                arrival=arrival,
                legs=[
                    JourneyLeg(
                        route_id=route_id,
                        route_name=route_name,
                        board_stop_id=board_id,
                        board_stop_name=board_name,
                        alight_stop_id=alight_id,
                        alight_stop_name=alight_name,
                        departure=departure,
                        arrival=arrival,
                        stops=int(alight_seq - board_seq),
                        crowd=_band(quantiles) if quantiles else _band(_unknown_band()),
                    )
                ],
                score=round(score, 2),
                reasons=reasons,
            )
        )

    # Most origin/destination pairs in a real network have no single route
    # joining them, so a direct-only planner answers "no service" for journeys
    # that are perfectly possible with one change. Search for those whenever
    # direct results are thin.
    if len(options) < 3:
        with resources.db_pool.connection() as conn, conn.cursor() as cur:
            options.extend(
                _transfer_options(
                    cur,
                    feed_version_id=feed_version_id,
                    origins=[s[0] for s in origins],
                    destinations=[s[0] for s in destinations],
                    from_seconds=from_seconds,
                    to_seconds=to_seconds,
                    midnight=midnight,
                    tz=tz,
                    weights=weights,
                    forecaster=resources.forecaster,
                    seen_routes=seen_routes,
                )
            )

    if not options:
        raise _fail(
            ErrorCode.NO_ROUTE_FOUND,
            "no service found between these stops in the requested window",
            status=404,
        )

    options.sort(key=lambda o: o.score)
    ranked = [
        o.model_copy(update={"is_recommended": index == 0})
        for index, o in enumerate(options[:5])
    ]

    return PlanResponse(
        generated_at=current,
        city_id=resources.city.city_id,
        profile=profile,
        options=ranked,
    )


def _unknown_band():
    from ..models.crowd import CrowdQuantiles

    return CrowdQuantiles.unknown()


def _readable(occupancy: OccupancyClass) -> str:
    return {
        OccupancyClass.EMPTY: "empty",
        OccupancyClass.MANY_SEATS_AVAILABLE: "plenty of seats",
        OccupancyClass.FEW_SEATS_AVAILABLE: "a few seats left",
        OccupancyClass.STANDING_ROOM_ONLY: "standing room only",
        OccupancyClass.CRUSHED_STANDING_ROOM_ONLY: "very crowded",
        OccupancyClass.FULL: "full",
        OccupancyClass.NOT_ACCEPTING_PASSENGERS: "not accepting passengers",
    }.get(occupancy, "unknown crowding")


def _stops_near(cur, feed_version_id: int, lat: float, lon: float) -> list[tuple]:
    """Stops within walking distance, nearest first."""
    cur.execute(
        """
        SELECT stop_id, name,
               ST_Distance(geom, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography) AS m
          FROM stop
         WHERE feed_version_id = %s
           AND ST_DWithin(geom, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography, %s)
         ORDER BY m
         LIMIT 8
        """,
        (lon, lat, feed_version_id, lon, lat, WALK_RADIUS_M),
    )
    return cur.fetchall()


def _latest_feed_version(cur, city_id: str) -> int:
    cur.execute(
        """
        SELECT feed_version_id FROM feed_version
         WHERE city_id = %s ORDER BY imported_at DESC LIMIT 1
        """,
        (city_id,),
    )
    row = cur.fetchone()
    if row is None:
        raise _fail(ErrorCode.FEED_UNAVAILABLE, "no GTFS feed imported", status=503)
    return row[0]


def _transfer_options(
    cur,
    *,
    feed_version_id: int,
    origins: list[str],
    destinations: list[str],
    from_seconds: int,
    to_seconds: int,
    midnight: datetime,
    tz,
    weights: dict[str, float],
    forecaster,
    seen_routes: set[str],
) -> list[JourneyOption]:
    """Journeys made with exactly one change.

    A direct-only planner reports "no service" for the majority of origin and
    destination pairs in any real network, because few single routes happen to
    join two arbitrary points. That is a missing feature, not a missing stop.

    The search is two bounded queries joined in Python rather than a four-way
    self-join in SQL: the join predicate is a time comparison across two
    independent trip sets, which the planner handles badly, and the same
    shape already cost us a five-minute query on the hotspots endpoint.
    """
    # Leg 1: everywhere a bus leaving one of the origin stops can take you.
    cur.execute(
        """
        WITH board AS (
            SELECT trip_id, stop_id, stop_sequence, departure_seconds
              FROM stop_time
             WHERE feed_version_id = %s AND stop_id = ANY(%s)
               AND departure_seconds BETWEEN %s AND %s
             ORDER BY departure_seconds
             LIMIT %s
        )
        SELECT b.trip_id, t.route_id, b.stop_id, b.stop_sequence, b.departure_seconds,
               d.stop_id, d.stop_sequence, d.arrival_seconds
          FROM board b
          JOIN stop_time d
            ON d.feed_version_id = %s AND d.trip_id = b.trip_id
           AND d.stop_sequence > b.stop_sequence
          JOIN trip t ON t.feed_version_id = %s AND t.trip_id = b.trip_id
        """,
        (feed_version_id, origins, from_seconds, to_seconds, MAX_BOARDINGS,
         feed_version_id, feed_version_id),
    )
    leg1 = cur.fetchall()
    if not leg1:
        return []

    # Leg 2: everywhere a bus that reaches a destination stop has come from.
    cur.execute(
        """
        WITH arrive AS (
            SELECT trip_id, stop_id, stop_sequence, arrival_seconds
              FROM stop_time
             WHERE feed_version_id = %s AND stop_id = ANY(%s)
               AND arrival_seconds BETWEEN %s AND %s
             ORDER BY arrival_seconds
             LIMIT %s
        )
        SELECT a.trip_id, t.route_id, o.stop_id, o.stop_sequence, o.departure_seconds,
               a.stop_id, a.stop_sequence, a.arrival_seconds
          FROM arrive a
          JOIN stop_time o
            ON o.feed_version_id = %s AND o.trip_id = a.trip_id
           AND o.stop_sequence < a.stop_sequence
          JOIN trip t ON t.feed_version_id = %s AND t.trip_id = a.trip_id
        """,
        (feed_version_id, destinations, from_seconds, to_seconds + 3600, MAX_ARRIVALS,
         feed_version_id, feed_version_id),
    )
    leg2 = cur.fetchall()
    if not leg2:
        return []

    # Index leg 2 by the stop it can be boarded at, earliest departure first.
    from collections import defaultdict

    boardable: dict[str, list] = defaultdict(list)
    for row in leg2:
        boardable[row[2]].append(row)
    for rows in boardable.values():
        rows.sort(key=lambda r: r[4])

    names = _stop_names(cur, feed_version_id)
    route_names = _route_names(cur, feed_version_id)

    best: dict[tuple[str, str], JourneyOption] = {}
    for (t1, r1, board1, seq1, dep1, xfer, seq1b, arr1) in leg1:
        candidates = boardable.get(xfer)
        if not candidates:
            continue
        for (t2, r2, _b2, seq2, dep2, alight2, seq2b, arr2) in candidates:
            if r2 == r1:
                continue  # changing onto the same route is not a transfer
            wait = dep2 - arr1
            if wait < MIN_TRANSFER_S or wait > MAX_TRANSFER_WAIT_S:
                continue

            # One option per route pair: twenty departures of the same two
            # buses is not twenty choices.
            key = (r1, r2)
            if key in best or r1 in seen_routes:
                break

            departure = midnight + timedelta(seconds=int(dep1))
            arrival = midnight + timedelta(seconds=int(arr2))
            total_min = max(1, int((arr2 - from_seconds) / 60))
            ride_min = max(1, int(((arr1 - dep1) + (arr2 - dep2)) / 60))
            wait_min = int(wait / 60)

            crowd1 = _forecast_at(forecaster, departure, tz, seq1, cur, feed_version_id, t1)
            crowd2 = _forecast_at(
                forecaster, midnight + timedelta(seconds=int(dep2)), tz, seq2,
                cur, feed_version_id, t2,
            )
            ordinal = max(
                (c.p50_class.ordinal or 0) for c in (crowd1, crowd2) if c is not None
            )

            score = (
                total_min
                + ordinal * weights["crowd"]
                + weights["transfer"]  # one change
            )

            reasons = [f"change at {names.get(xfer, xfer)}"]
            if crowd1 is not None and crowd1.p50_class.is_known:
                reasons.append(f"predicted {_readable(crowd1.p50_class)} when you board")
            reasons.append(f"{ride_min} min riding, {wait_min} min to change")

            best[key] = JourneyOption(
                option_id=f"{t1}:{seq1}-{seq1b}|{t2}:{seq2}-{seq2b}",
                total_minutes=total_min,
                transfers=1,
                departure=departure,
                arrival=arrival,
                legs=[
                    JourneyLeg(
                        route_id=r1,
                        route_name=route_names.get(r1),
                        board_stop_id=board1,
                        board_stop_name=names.get(board1, board1),
                        alight_stop_id=xfer,
                        alight_stop_name=names.get(xfer, xfer),
                        departure=departure,
                        arrival=midnight + timedelta(seconds=int(arr1)),
                        stops=int(seq1b - seq1),
                        crowd=_band(crowd1) if crowd1 else _band(_unknown_band()),
                    ),
                    JourneyLeg(
                        route_id=r2,
                        route_name=route_names.get(r2),
                        board_stop_id=xfer,
                        board_stop_name=names.get(xfer, xfer),
                        alight_stop_id=alight2,
                        alight_stop_name=names.get(alight2, alight2),
                        departure=midnight + timedelta(seconds=int(dep2)),
                        arrival=arrival,
                        stops=int(seq2b - seq2),
                        crowd=_band(crowd2) if crowd2 else _band(_unknown_band()),
                    ),
                ],
                score=round(score, 2),
                reasons=reasons,
            )
            break  # earliest usable connection for this pair is enough

    return sorted(best.values(), key=lambda o: o.score)[:4]


def _forecast_at(forecaster, when, tz, sequence: int, cur, feed_version_id: int, trip_id: str):
    """Crowd band for boarding `trip_id` at `sequence`."""
    if forecaster is None:
        return None
    total = _trip_length(cur, feed_version_id, trip_id)
    position = (sequence - 1) / max(total - 1, 1)
    return forecaster.predict(when.astimezone(tz).hour, position)


_TRIP_LENGTHS: dict[tuple[int, str], int] = {}


def _trip_length(cur, feed_version_id: int, trip_id: str) -> int:
    key = (feed_version_id, trip_id)
    if key not in _TRIP_LENGTHS:
        cur.execute(
            "SELECT max(stop_sequence) FROM stop_time WHERE feed_version_id=%s AND trip_id=%s",
            (feed_version_id, trip_id),
        )
        row = cur.fetchone()
        _TRIP_LENGTHS[key] = int(row[0]) if row and row[0] else 1
    return _TRIP_LENGTHS[key]


_STOP_NAMES: dict[int, dict[str, str]] = {}


def _stop_names(cur, feed_version_id: int) -> dict[str, str]:
    if feed_version_id not in _STOP_NAMES:
        cur.execute(
            "SELECT stop_id, name FROM stop WHERE feed_version_id=%s", (feed_version_id,)
        )
        _STOP_NAMES[feed_version_id] = dict(cur.fetchall())
    return _STOP_NAMES[feed_version_id]


_ROUTE_NAMES: dict[int, dict[str, str]] = {}


def _route_names(cur, feed_version_id: int) -> dict[str, str]:
    if feed_version_id not in _ROUTE_NAMES:
        cur.execute(
            "SELECT route_id, long_name FROM route WHERE feed_version_id=%s", (feed_version_id,)
        )
        _ROUTE_NAMES[feed_version_id] = dict(cur.fetchall())
    return _ROUTE_NAMES[feed_version_id]
