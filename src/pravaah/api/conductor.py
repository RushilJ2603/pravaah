"""Authenticated conductor shift and live-state write endpoints.

Implements SOLUTION.md sections 12.5, 15.3 and 29.5. Database row locks make
ownership checks and writes one transaction; the partial unique index in
``005_auth.sql`` is the final concurrency guard for vehicle claims.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from ..contracts.api import ErrorCode
from ..contracts.events import OccupancyObservation, VehiclePositionEvent
from ..contracts.provenance import Provenance, SourceType
from .auth import StaffIdentity, optional_staff, require_conductor
from .deps import AppResources
from .schemas import (
    OccupancyReportRequest,
    ShiftPositionRequest,
    ShiftStartRequest,
    ShiftStartResponse,
)

router = APIRouter(prefix="/v1", tags=["conductor"])
log = logging.getLogger(__name__)


@router.post("/shifts/start", response_model=ShiftStartResponse)
def start_shift(
    body: ShiftStartRequest,
    request: Request,
    identity: Annotated[StaffIdentity, Depends(require_conductor)],
) -> ShiftStartResponse:
    """Claim one vehicle for the authenticated conductor and device."""
    resources = _resources(request, identity)
    _require_database(resources)

    try:
        with resources.db_pool.connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO conductor_shift (
                    user_id, city_id, vehicle_id, trip_id, route_id, device_id
                ) VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING shift_id, started_at
                """,
                (
                    identity.user_id,
                    identity.city_id,
                    body.vehicle_id,
                    body.trip_id,
                    body.route_id,
                    body.device_id,
                ),
            )
            row = cur.fetchone()
            conn.commit()
    except Exception as exc:  # database-specific class is deliberately not leaked here
        if getattr(exc, "sqlstate", None) == "23505":
            raise _fail(
                ErrorCode.VEHICLE_ALREADY_CLAIMED,
                "vehicle already has an active shift",
                409,
            ) from exc
        raise

    return ShiftStartResponse(shift_id=row[0], started_at=row[1])


@router.post("/shifts/{shift_id}/position", status_code=204)
def report_position(
    shift_id: int,
    body: ShiftPositionRequest,
    request: Request,
    identity: Annotated[StaffIdentity, Depends(require_conductor)],
) -> Response:
    """Append and publish a position only for the caller's active shift."""
    resources = _resources(request, identity)
    _require_database(resources)
    if resources.redis is None:
        raise _fail(ErrorCode.FEED_UNAVAILABLE, "live state is unavailable", 503)
    if not resources.city.bounds.contains(body.lat, body.lon):
        raise _fail(ErrorCode.OUT_OF_SERVICE_AREA, "position is outside city bounds", 400)

    ingest_time = datetime.now(UTC)
    _validate_live_timestamp(body.timestamp, ingest_time, resources)
    if (
        body.speed_mps is not None
        and body.speed_mps > resources.city.validation.max_plausible_speed_mps
    ):
        raise _fail(ErrorCode.INTERNAL, "reported speed is implausible", 400)
    with resources.db_pool.connection() as conn, conn.cursor() as cur:
        vehicle_id, trip_id, route_id = _lock_owned_shift(
            cur, shift_id, identity.user_id, identity.city_id
        )
        event = VehiclePositionEvent(
            city_id=identity.city_id,
            agency_id=resources.city.agency_id,
            vehicle_id=vehicle_id,
            trip_id=trip_id,
            route_id=route_id,
            ts=body.timestamp,
            lat=body.lat,
            lon=body.lon,
            # Device speed is raw evidence. The canonical field is populated
            # only by consecutive-position derivation (section 28.4).
            speed_mps=None,
            provenance=Provenance(
                source_type=SourceType.REAL_OPERATOR,
                source_name="conductor_app",
                source_timestamp=body.timestamp,
                ingest_timestamp=ingest_time,
                quality_score=1.0,
            ),
        )
        _insert_position(cur, event)
        conn.commit()

    resources.state.put(event)
    return Response(status_code=204)


@router.post("/shifts/{shift_id}/end", status_code=204)
def end_shift(
    shift_id: int,
    request: Request,
    identity: Annotated[StaffIdentity, Depends(require_conductor)],
) -> Response:
    """End only the caller's own active shift."""
    resources = _resources(request, identity)
    _require_database(resources)
    with resources.db_pool.connection() as conn, conn.cursor() as cur:
        _lock_owned_shift(cur, shift_id, identity.user_id, identity.city_id)
        cur.execute(
            """
            UPDATE conductor_shift SET ended_at = now()
             WHERE shift_id = %s AND user_id = %s AND ended_at IS NULL
            """,
            (shift_id, identity.user_id),
        )
        conn.commit()
    return Response(status_code=204)


@router.post("/occupancy/report", status_code=202)
def report_occupancy(
    body: OccupancyReportRequest,
    request: Request,
    identity: Annotated[StaffIdentity | None, Depends(optional_staff)],
) -> Response:
    """Use the single crowd write path for anonymous and conductor reports."""
    resources: AppResources = request.app.state.resources
    _require_database(resources)
    if resources.redis is None:
        raise _fail(ErrorCode.FEED_UNAVAILABLE, "live state is unavailable", 503)
    if not body.occupancy_class.is_known:
        raise _fail(ErrorCode.INTERNAL, "occupancy_class must be known", 400)

    if identity is not None:
        if identity.role != "CONDUCTOR" or identity.city_id != resources.city.city_id:
            raise _fail(ErrorCode.SHIFT_NOT_ACTIVE, "active conductor shift required", 403)
        source_type = SourceType.REAL_OPERATOR
        source_name = "conductor_app"
        confidence = 1.0
    else:
        source_type = SourceType.CROWDSOURCED
        source_name = "passenger_app"
        confidence = 0.5

    ingest_time = datetime.now(UTC)
    _validate_live_timestamp(body.reported_at, ingest_time, resources)
    observation = OccupancyObservation(
        city_id=resources.city.city_id,
        vehicle_id=body.vehicle_id,
        trip_id=body.trip_id,
        ts=body.reported_at,
        occupancy_class=body.occupancy_class,
        confidence=confidence,
        provenance=Provenance(
            source_type=source_type,
            source_name=source_name,
            source_timestamp=body.reported_at,
            ingest_timestamp=ingest_time,
            quality_score=confidence,
        ),
    )

    with resources.db_pool.connection() as conn, conn.cursor() as cur:
        if identity is not None:
            cur.execute(
                """
                SELECT shift_id FROM conductor_shift
                 WHERE user_id = %s AND city_id = %s AND vehicle_id = %s
                   AND ended_at IS NULL
                   AND (trip_id IS NULL OR trip_id = %s)
                 FOR UPDATE
                """,
                (identity.user_id, identity.city_id, body.vehicle_id, body.trip_id),
            )
            if cur.fetchone() is None:
                log.warning(
                    "rejected conductor occupancy write user_id=%s city_id=%s vehicle_id=%s",
                    identity.user_id,
                    identity.city_id,
                    body.vehicle_id,
                )
                raise _fail(
                    ErrorCode.SHIFT_NOT_ACTIVE,
                    "no owned active shift matches this vehicle and trip",
                    409,
                )
        _insert_occupancy(cur, observation)
        conn.commit()

    current = resources.occupancy.get(body.vehicle_id, now=ingest_time)
    if _may_publish_occupancy(current, observation):
        resources.occupancy.put_many([observation])
    return Response(status_code=202)


def _resources(request: Request, identity: StaffIdentity) -> AppResources:
    resources: AppResources = request.app.state.resources
    if identity.city_id != resources.city.city_id:
        raise _fail(ErrorCode.SHIFT_NOT_ACTIVE, "shift is not active in this city", 403)
    return resources


def _require_database(resources: AppResources) -> None:
    if resources.db_pool is None:
        raise _fail(ErrorCode.FEED_UNAVAILABLE, "database is unavailable", 503)


def _validate_live_timestamp(
    reported_at: datetime, current: datetime, resources: AppResources
) -> None:
    age_s = (current - reported_at.astimezone(UTC)).total_seconds()
    if age_s < -60:
        raise _fail(ErrorCode.INTERNAL, "reported timestamp is in the future", 400)
    if age_s > resources.city.validation.stale_after_s:
        raise _fail(ErrorCode.INTERNAL, "reported timestamp is too old for live state", 400)


def _lock_owned_shift(
    cur, shift_id: int, user_id: int, city_id: str
) -> tuple[str, str | None, str | None]:
    cur.execute(
        """
        SELECT vehicle_id, trip_id, route_id
          FROM conductor_shift
         WHERE shift_id = %s AND user_id = %s AND city_id = %s
           AND ended_at IS NULL
         FOR UPDATE
        """,
        (shift_id, user_id, city_id),
    )
    row = cur.fetchone()
    if row is None:
        log.warning(
            "rejected shift write user_id=%s city_id=%s shift_id=%s",
            user_id,
            city_id,
            shift_id,
        )
        raise _fail(
            ErrorCode.SHIFT_NOT_ACTIVE,
            "shift is not active or is not owned by this conductor",
            409,
        )
    return row[0], row[1], row[2]


def _insert_position(cur, event: VehiclePositionEvent) -> None:
    cur.execute(
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
        ),
    )


def _insert_occupancy(cur, observation: OccupancyObservation) -> None:
    cur.execute(
        """
        INSERT INTO occupancy_observation (
            city_id, vehicle_id, trip_id, ts, onboard, capacity,
            occupancy_ratio, occupancy_class, boardings, alightings,
            confidence, source_type, source_name, ingest_ts
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            observation.city_id,
            observation.vehicle_id,
            observation.trip_id,
            observation.ts,
            observation.onboard,
            observation.capacity,
            observation.occupancy_ratio,
            observation.occupancy_class.value,
            observation.boardings,
            observation.alightings,
            observation.confidence,
            observation.provenance.source_type.value,
            observation.provenance.source_name,
            observation.provenance.ingest_timestamp,
        ),
    )


def _may_publish_occupancy(
    current: OccupancyObservation | None, incoming: OccupancyObservation
) -> bool:
    """Apply the explicit section 6.5 precedence rules to latest state.

    Every accepted report still enters immutable history. This decision only
    prevents the materialized latest value from hiding a fresh higher-trust
    observation.
    """
    if current is None:
        return True
    machine_sources = {SourceType.APC, SourceType.AFC}
    current_source = current.provenance.source_type
    incoming_source = incoming.provenance.source_type
    if incoming_source is SourceType.CROWDSOURCED and current_source in {
        *machine_sources,
        SourceType.REAL_OPERATOR,
    }:
        return False
    if (
        incoming_source is SourceType.REAL_OPERATOR
        and current_source in machine_sources
        and current.ts >= incoming.ts
    ):
        return False
    return True


def _fail(code: ErrorCode, message: str, status: int) -> HTTPException:
    return HTTPException(status_code=status, detail={"code": code.value, "message": message})
