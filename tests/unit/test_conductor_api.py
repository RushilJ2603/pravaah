"""Focused Slice G gates: authentication, claims, ownership and provenance."""

from __future__ import annotations

from contextlib import nullcontext
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from pravaah.api.auth import (
    StaffIdentity,
    decode_access_token,
    hash_password,
    issue_access_token,
    login,
    verify_password,
)
from pravaah.api.conductor import (
    end_shift,
    report_occupancy,
    report_position,
    start_shift,
)
from pravaah.api.schemas import (
    LoginRequest,
    OccupancyReportRequest,
    ShiftPositionRequest,
    ShiftStartRequest,
)
from pravaah.contracts.events import OccupancyClass, OccupancyObservation
from pravaah.contracts.provenance import Provenance, SourceType

SECRET = b"test-only-secret-that-is-at-least-32-bytes"
NOW = datetime.now(UTC).replace(microsecond=0)


class UniqueViolation(Exception):
    sqlstate = "23505"


class FakeCursor:
    def __init__(self, database):
        self.database = database
        self.row = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def execute(self, query, params=()):
        sql = " ".join(query.split())
        self.row = None
        if "FROM app_user" in sql:
            user = self.database.users.get(params[0])
            if user and user[4]:
                self.row = user[:4]
        elif sql.startswith("INSERT INTO conductor_shift"):
            user_id, city_id, vehicle_id, trip_id, route_id, device_id = params
            if any(
                s["city_id"] == city_id
                and s["vehicle_id"] == vehicle_id
                and not s["ended"]
                for s in self.database.shifts.values()
            ):
                raise UniqueViolation
            shift_id = len(self.database.shifts) + 1
            self.database.shifts[shift_id] = {
                "user_id": user_id,
                "city_id": city_id,
                "vehicle_id": vehicle_id,
                "trip_id": trip_id,
                "route_id": route_id,
                "device_id": device_id,
                "ended": False,
            }
            self.row = (shift_id, NOW)
        elif sql.startswith("SELECT vehicle_id, trip_id, route_id"):
            shift_id, user_id, city_id = params
            shift = self.database.shifts.get(shift_id)
            if (
                shift
                and shift["user_id"] == user_id
                and shift["city_id"] == city_id
                and not shift["ended"]
            ):
                self.row = (shift["vehicle_id"], shift["trip_id"], shift["route_id"])
        elif sql.startswith("UPDATE conductor_shift"):
            shift_id, user_id = params
            shift = self.database.shifts[shift_id]
            if shift["user_id"] == user_id:
                shift["ended"] = True
        elif sql.startswith("SELECT shift_id FROM conductor_shift"):
            user_id, city_id, vehicle_id, trip_id = params
            for shift_id, shift in self.database.shifts.items():
                if (
                    shift["user_id"] == user_id
                    and shift["city_id"] == city_id
                    and shift["vehicle_id"] == vehicle_id
                    and not shift["ended"]
                    and (shift["trip_id"] is None or shift["trip_id"] == trip_id)
                ):
                    self.row = (shift_id,)
                    break
        elif sql.startswith("INSERT INTO vehicle_position"):
            self.database.positions.append(params)
        elif sql.startswith("INSERT INTO occupancy_observation"):
            self.database.occupancies.append(params)
        else:  # pragma: no cover - a changed SQL path should fail loudly
            raise AssertionError(sql)

    def fetchone(self):
        return self.row


class FakeConnection:
    def __init__(self, database):
        self.database = database

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def cursor(self):
        return FakeCursor(self.database)

    def commit(self):
        self.database.commits += 1


class FakePool:
    def __init__(self, database):
        self.database = database

    def connection(self):
        return nullcontext(FakeConnection(self.database))


class CaptureState:
    def __init__(self):
        self.values = []

    def put(self, value):
        self.values.append(value)

    def put_many(self, values):
        self.values.extend(values)

    def get(self, vehicle_id, now=None):
        return next(
            (value for value in reversed(self.values) if value.vehicle_id == vehicle_id),
            None,
        )


@pytest.fixture
def harness(monkeypatch):
    monkeypatch.setenv("PRAVAAH_AUTH_SECRET", SECRET.decode())
    database = SimpleNamespace(
        users={"crew": (7, hash_password("correct"), "CONDUCTOR", "test-city", True)},
        shifts={},
        positions=[],
        occupancies=[],
        commits=0,
    )
    position_state = CaptureState()
    occupancy_state = CaptureState()
    city = SimpleNamespace(
        city_id="test-city",
        agency_id="test-agency",
        bounds=SimpleNamespace(contains=lambda lat, lon: 10 <= lat <= 40 and 60 <= lon <= 100),
        validation=SimpleNamespace(
            stale_after_s=120,
            max_plausible_speed_mps=30.0,
        ),
    )
    resources = SimpleNamespace(
        db_pool=FakePool(database),
        redis=object(),
        city=city,
        state=position_state,
        occupancy=occupancy_state,
    )
    request = SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(resources=resources))
    )
    return database, position_state, occupancy_state, request


def test_password_hash_is_salted_and_verifies():
    first = hash_password("secret")
    second = hash_password("secret")
    assert first != second
    assert verify_password("secret", first)
    assert not verify_password("wrong", first)


def test_token_is_signed_and_expires():
    identity = StaffIdentity(7, "CONDUCTOR", "test-city")
    token = issue_access_token(identity, secret=SECRET, issued_at=NOW)
    assert decode_access_token(
        token, secret=SECRET, current_time=NOW + timedelta(hours=1)
    ) == identity
    with pytest.raises(HTTPException) as expired:
        decode_access_token(token, secret=SECRET, current_time=NOW + timedelta(hours=8))
    assert expired.value.status_code == 401


def test_login_rejects_bad_password_and_returns_eight_hour_token(harness):
    _, _, _, request = harness
    response = login(LoginRequest(username="crew", password="correct"), request)
    assert response.role == "CONDUCTOR"
    assert response.expires_in == 28_800
    assert decode_access_token(response.access_token).user_id == 7

    with pytest.raises(HTTPException) as rejected:
        login(LoginRequest(username="crew", password="wrong"), request)
    assert rejected.value.status_code == 401


def test_vehicle_claim_is_unique_and_owned_position_is_real_operator(harness):
    database, position_state, _, request = harness
    owner = StaffIdentity(7, "CONDUCTOR", "test-city")
    other = StaffIdentity(8, "CONDUCTOR", "test-city")
    body = ShiftStartRequest(
        vehicle_id="bus-1", trip_id="trip-1", route_id="route-1", device_id="phone-1"
    )
    shift = start_shift(body, request, owner)

    with pytest.raises(HTTPException) as claimed:
        start_shift(body.model_copy(update={"device_id": "phone-2"}), request, other)
    assert claimed.value.detail["code"] == "VEHICLE_ALREADY_CLAIMED"

    position = ShiftPositionRequest(
        lat=28.6,
        lon=77.2,
        accuracy_m=8.0,
        speed_mps=9.0,
        timestamp=NOW,
    )
    with pytest.raises(HTTPException) as not_owned:
        report_position(shift.shift_id, position, request, other)
    assert not_owned.value.detail["code"] == "SHIFT_NOT_ACTIVE"

    response = report_position(shift.shift_id, position, request, owner)
    assert response.status_code == 204
    event = position_state.values[-1]
    assert event.vehicle_id == "bus-1"
    assert event.speed_mps is None
    assert event.provenance.source_type is SourceType.REAL_OPERATOR
    assert event.provenance.source_name == "conductor_app"
    assert database.positions


def test_conductor_occupancy_needs_active_shift_and_end_stops_writes(harness):
    _, _, occupancy_state, request = harness
    owner = StaffIdentity(7, "CONDUCTOR", "test-city")
    report = OccupancyReportRequest(
        trip_id="trip-1",
        vehicle_id="bus-1",
        occupancy_class=OccupancyClass.STANDING_ROOM_ONLY,
        reported_at=NOW,
    )
    with pytest.raises(HTTPException) as inactive:
        report_occupancy(report, request, owner)
    assert inactive.value.detail["code"] == "SHIFT_NOT_ACTIVE"

    shift = start_shift(
        ShiftStartRequest(
            vehicle_id="bus-1",
            trip_id="trip-1",
            route_id="route-1",
            device_id="phone-1",
        ),
        request,
        owner,
    )
    assert report_occupancy(report, request, owner).status_code == 202
    observation = occupancy_state.values[-1]
    assert observation.provenance.source_type is SourceType.REAL_OPERATOR
    assert observation.provenance.source_name == "conductor_app"

    assert end_shift(shift.shift_id, request, owner).status_code == 204
    with pytest.raises(HTTPException) as ended:
        report_position(
            shift.shift_id,
            ShiftPositionRequest(
                lat=28.6,
                lon=77.2,
                accuracy_m=8.0,
                speed_mps=None,
                timestamp=NOW,
            ),
            request,
            owner,
        )
    assert ended.value.detail["code"] == "SHIFT_NOT_ACTIVE"


def test_anonymous_occupancy_remains_crowdsourced(harness):
    _, _, occupancy_state, request = harness
    response = report_occupancy(
        OccupancyReportRequest(
            trip_id="trip-1",
            vehicle_id="bus-1",
            occupancy_class=OccupancyClass.FEW_SEATS_AVAILABLE,
            reported_at=NOW,
        ),
        request,
        None,
    )
    assert response.status_code == 202
    observation = occupancy_state.values[-1]
    assert observation.provenance.source_type is SourceType.CROWDSOURCED
    assert observation.provenance.source_name == "passenger_app"


def test_live_write_timestamps_must_be_aware_and_recent(harness):
    _, _, _, request = harness
    owner = StaffIdentity(7, "CONDUCTOR", "test-city")
    shift = start_shift(
        ShiftStartRequest(
            vehicle_id="bus-1",
            trip_id="trip-1",
            route_id="route-1",
            device_id="phone-1",
        ),
        request,
        owner,
    )

    with pytest.raises(ValidationError):
        ShiftPositionRequest(
            lat=28.6,
            lon=77.2,
            accuracy_m=8.0,
            timestamp=NOW.replace(tzinfo=None),
        )

    for timestamp in (NOW + timedelta(minutes=2), NOW - timedelta(minutes=3)):
        with pytest.raises(HTTPException):
            report_position(
                shift.shift_id,
                ShiftPositionRequest(
                    lat=28.6,
                    lon=77.2,
                    accuracy_m=8.0,
                    timestamp=timestamp,
                ),
                request,
                owner,
            )


def test_conductor_report_does_not_hide_fresher_machine_count(harness):
    _, _, occupancy_state, request = harness
    owner = StaffIdentity(7, "CONDUCTOR", "test-city")
    start_shift(
        ShiftStartRequest(
            vehicle_id="bus-1",
            trip_id="trip-1",
            route_id="route-1",
            device_id="phone-1",
        ),
        request,
        owner,
    )
    machine_time = NOW + timedelta(minutes=1)
    machine = OccupancyObservation(
        city_id="test-city",
        vehicle_id="bus-1",
        trip_id="trip-1",
        ts=machine_time,
        occupancy_class=OccupancyClass.FULL,
        confidence=1.0,
        provenance=Provenance(
            source_type=SourceType.APC,
            source_name="vehicle_counter",
            source_timestamp=machine_time,
            ingest_timestamp=machine_time,
            quality_score=1.0,
        ),
    )
    occupancy_state.put_many([machine])

    report_occupancy(
        OccupancyReportRequest(
            trip_id="trip-1",
            vehicle_id="bus-1",
            occupancy_class=OccupancyClass.EMPTY,
            reported_at=NOW,
        ),
        request,
        owner,
    )
    assert occupancy_state.values[-1] is machine
