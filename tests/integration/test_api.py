"""Slice A.3 acceptance gate (SOLUTION.md section 31).

Gate: "Contract tests against section 29 shapes; every response carries
`generated_at` and freshness."

Runs against the real app with real Redis, seeded with known vehicles. The
database-backed departures endpoint is covered where the schedule is imported.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from pravaah.api.main import app
from pravaah.contracts.events import OccupancyClass, OccupancyObservation, VehiclePositionEvent
from pravaah.contracts.provenance import Provenance, SourceType

redis_lib = pytest.importorskip("redis", reason="redis client not installed")

DELHI_BBOX = "28.50,77.00,28.80,77.35"


def position(vehicle_id: str, lat: float, lon: float, ts: datetime) -> VehiclePositionEvent:
    return VehiclePositionEvent(
        city_id="delhi",
        agency_id="DTC",
        vehicle_id=vehicle_id,
        trip_id="76789790",
        route_id="64",
        direction_id=0,
        ts=ts,
        lat=lat,
        lon=lon,
        bearing=270.0,
        speed_mps=9.3,
        stop_id="1064",
        provenance=Provenance(
            source_type=SourceType.SIMULATED,
            source_name="test_simulator",
            source_timestamp=ts,
            ingest_timestamp=ts,
            quality_score=0.96,
        ),
    )


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        resources = c.app.state.resources
        if not resources.redis_ok():
            pytest.skip("redis unreachable; run: docker compose up -d")
        yield c


@pytest.fixture
def seeded(client):
    """Two fresh Delhi vehicles, one stale, one far outside the viewport."""
    state = client.app.state.resources.state
    state.clear()
    now = datetime.now(UTC)
    state.put_many(
        [
            position("fresh-1", 28.6139, 77.2090, now),
            position("fresh-2", 28.6200, 77.2150, now - timedelta(seconds=20)),
            position("stale-1", 28.6100, 77.2050, now - timedelta(seconds=300)),
            position("far-1", 28.8500, 77.4000, now),
        ]
    )
    yield state
    state.clear()


# --------------------------------------------------------------------------
# Health.
# --------------------------------------------------------------------------


def test_health_reports_dependencies(client):
    body = client.get("/v1/health").json()
    assert body["status"] in {"ok", "degraded"}
    assert body["city_id"] == "delhi"
    assert "generated_at" in body
    assert isinstance(body["redis"], bool)
    assert isinstance(body["database"], bool)


# --------------------------------------------------------------------------
# GET /v1/vehicles -- section 29.2.
# --------------------------------------------------------------------------


def test_fleet_requires_a_bbox(client):
    """Omitting bbox is an error, never a full-fleet response (section 29.2)."""
    response = client.get("/v1/vehicles")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_COORDINATES"


@pytest.mark.parametrize(
    "bbox",
    [
        "28.50,77.00,28.80",            # too few parts
        "not,a,bounding,box",           # non-numeric
        "28.80,77.00,28.50,77.35",      # min >= max
        "99.0,77.00,101.0,77.35",       # latitude out of range
    ],
)
def test_malformed_bbox_is_rejected(client, bbox):
    response = client.get("/v1/vehicles", params={"bbox": bbox})
    assert response.status_code in (400, 422)
    assert response.json()["error"]["code"] == "INVALID_COORDINATES"


def test_fleet_returns_only_vehicles_in_the_viewport(client, seeded):
    body = client.get("/v1/vehicles", params={"bbox": "28.58,77.18,28.65,77.24"}).json()
    ids = {v["vehicle_id"] for v in body["vehicles"]}
    assert "fresh-1" in ids
    assert "far-1" not in ids
    assert body["count"] == len(body["vehicles"])


def test_fleet_response_carries_generated_at_and_city(client, seeded):
    body = client.get("/v1/vehicles", params={"bbox": DELHI_BBOX}).json()
    assert "generated_at" in body
    assert body["city_id"] == "delhi"


def test_every_vehicle_carries_freshness(client, seeded):
    """The gate: a client must render the badge without computing clock skew."""
    body = client.get("/v1/vehicles", params={"bbox": DELHI_BBOX}).json()
    assert body["vehicles"]

    for vehicle in body["vehicles"]:
        assert "age_s" in vehicle and vehicle["age_s"] >= 0
        assert "is_stale" in vehicle and isinstance(vehicle["is_stale"], bool)
        assert "ts" in vehicle
        assert "quality_score" in vehicle


def test_stale_vehicle_is_flagged_but_still_returned(client, seeded):
    """Section 16.1: degraded data stays visible rather than vanishing."""
    body = client.get("/v1/vehicles", params={"bbox": DELHI_BBOX}).json()
    by_id = {v["vehicle_id"]: v for v in body["vehicles"]}

    assert by_id["stale-1"]["is_stale"] is True
    assert by_id["fresh-1"]["is_stale"] is False


def test_occupancy_is_present_and_unknown_never_absent(client, seeded):
    """Section 12.4 rule 3, on the wire.

    Slice A has no occupancy join yet, so every vehicle reports UNKNOWN. The
    field must still be present, and the ratio must be null rather than 0.
    """
    body = client.get("/v1/vehicles", params={"bbox": DELHI_BBOX}).json()

    for vehicle in body["vehicles"]:
        assert "occupancy_class" in vehicle, "the field must never be omitted"
        assert vehicle["occupancy_class"] == "UNKNOWN"
        assert vehicle["occupancy_ratio"] is None, "unknown must not become 0"
        assert vehicle["occupancy_class"] != "EMPTY"


def test_fleet_limit_is_capped_server_side(client, seeded):
    assert client.get(
        "/v1/vehicles", params={"bbox": DELHI_BBOX, "limit": 99999}
    ).status_code == 422
    body = client.get("/v1/vehicles", params={"bbox": DELHI_BBOX, "limit": 1}).json()
    assert len(body["vehicles"]) == 1


def test_speed_is_the_derived_value(client, seeded):
    body = client.get("/v1/vehicles", params={"bbox": DELHI_BBOX}).json()
    speeds = {v["vehicle_id"]: v["speed_mps"] for v in body["vehicles"]}
    assert speeds["fresh-1"] == pytest.approx(9.3)


# --------------------------------------------------------------------------
# GET /v1/vehicles/{id}.
# --------------------------------------------------------------------------


def test_single_vehicle_round_trip(client, seeded):
    body = client.get("/v1/vehicles/fresh-1").json()
    assert body["vehicle"]["vehicle_id"] == "fresh-1"
    assert body["vehicle"]["route_id"] == "64"
    assert "generated_at" in body
    assert "age_s" in body["vehicle"]


def test_unknown_vehicle_is_404_in_the_error_shape(client, seeded):
    response = client.get("/v1/vehicles/does-not-exist")
    assert response.status_code == 404
    body = response.json()
    assert set(body) == {"error"}
    assert set(body["error"]) >= {"code", "message"}


# --------------------------------------------------------------------------
# GET /v1/stops/{id}/departures.
# --------------------------------------------------------------------------


def test_departures_for_a_known_stop(client):
    """Needs an imported GTFS feed; skips when the schedule is absent."""
    resources = client.app.state.resources
    if resources.db_pool is None:
        pytest.skip("database unavailable")

    with resources.db_pool.connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT s.stop_id FROM stop s
            JOIN feed_version f ON f.feed_version_id = s.feed_version_id
            WHERE f.city_id = %s ORDER BY f.imported_at DESC, s.stop_id LIMIT 1
            """,
            (resources.city.city_id,),
        )
        row = cur.fetchone()
    if row is None:
        pytest.skip("no Delhi schedule imported")
    stop_id = row[0]
    response = client.get(f"/v1/stops/{stop_id}/departures", params={"window_min": 240})
    if response.status_code == 503:
        pytest.skip("no GTFS feed imported")
    if response.status_code == 404:
        pytest.skip("stop 1064 absent from the imported feed")

    body = response.json()
    assert body["stop_id"] == stop_id
    assert body["stop_name"]
    assert "generated_at" in body
    assert body["feed_version_id"] > 0

    for departure in body["departures"]:
        # No forecasts until Slice B, and that must be explicit on the wire.
        assert departure["crowd_class"] == "UNKNOWN"
        assert departure["crowd_p50"] is None
        assert departure["is_forecast"] is False


def test_unknown_stop_is_404(client):
    resources = client.app.state.resources
    if resources.db_pool is None:
        pytest.skip("database unavailable")

    response = client.get("/v1/stops/definitely-not-a-stop/departures")
    if response.status_code == 503:
        pytest.skip("no GTFS feed imported")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NO_ROUTE_FOUND"



@pytest.fixture
def seeded_with_occupancy(client, seeded):
    state = client.app.state.resources.occupancy
    state.clear()
    now = datetime.now(UTC)
    state.put_many([
        OccupancyObservation(
            city_id="delhi",
            vehicle_id="fresh-1",
            ts=now,
            occupancy_class=OccupancyClass.MANY_SEATS_AVAILABLE,
            occupancy_ratio=0.25,
            confidence=1.0,
            provenance=Provenance(
                source_type=SourceType.SIMULATED,
                source_name="test_simulator",
                source_timestamp=now,
                ingest_timestamp=now,
                quality_score=1.0,
            ),
        ),
        OccupancyObservation(
            city_id="delhi",
            vehicle_id="stale-1",
            ts=now - timedelta(hours=2),
            occupancy_class=OccupancyClass.FEW_SEATS_AVAILABLE,
            occupancy_ratio=0.85,
            confidence=1.0,
            provenance=Provenance(
                source_type=SourceType.SIMULATED,
                source_name="test_simulator",
                source_timestamp=now - timedelta(hours=2),
                ingest_timestamp=now - timedelta(hours=2),
                quality_score=1.0,
            ),
        ),
    ])
    yield state
    state.clear()

def test_vehicle_with_stored_occupancy_renders_it(client, seeded_with_occupancy):
    body = client.get("/v1/vehicles", params={"bbox": DELHI_BBOX}).json()
    by_id = {v["vehicle_id"]: v for v in body["vehicles"]}
    v = by_id["fresh-1"]
    assert v["occupancy_class"] == "MANY_SEATS_AVAILABLE"
    assert v["occupancy_ratio"] == 0.25

def test_vehicle_with_no_stored_occupancy_renders_unknown(client, seeded_with_occupancy):
    body = client.get("/v1/vehicles", params={"bbox": DELHI_BBOX}).json()
    by_id = {v["vehicle_id"]: v for v in body["vehicles"]}
    v = by_id["fresh-2"]
    assert v["occupancy_class"] == "UNKNOWN"
    assert v["occupancy_ratio"] is None
    assert v["occupancy_class"] != "EMPTY"
    assert v["occupancy_ratio"] != 0

def test_aged_out_occupancy_renders_unknown(client, seeded_with_occupancy):
    body = client.get("/v1/vehicles", params={"bbox": DELHI_BBOX}).json()
    by_id = {v["vehicle_id"]: v for v in body["vehicles"]}
    v = by_id["stale-1"]
    assert v["occupancy_class"] == "UNKNOWN"
    assert v["occupancy_ratio"] is None
