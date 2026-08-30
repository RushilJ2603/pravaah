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
from pravaah.contracts.events import VehiclePositionEvent
from pravaah.contracts.provenance import Provenance, SourceType

redis_lib = pytest.importorskip("redis", reason="redis client not installed")

BOSTON_BBOX = "42.30,-71.20,42.45,-70.95"


def position(vehicle_id: str, lat: float, lon: float, ts: datetime) -> VehiclePositionEvent:
    return VehiclePositionEvent(
        city_id="mbta",
        agency_id="MBTA",
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
            source_type=SourceType.PUBLIC_FEED,
            source_name="mbta_cdn",
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
    """Two fresh vehicles in Boston, one stale, one far outside the viewport."""
    state = client.app.state.resources.state
    state.clear()
    now = datetime.now(UTC)
    state.put_many(
        [
            position("fresh-1", 42.3601, -71.0589, now),
            position("fresh-2", 42.3701, -71.0620, now - timedelta(seconds=20)),
            position("stale-1", 42.3650, -71.0600, now - timedelta(seconds=300)),
            position("far-1", 42.4400, -70.9600, now),
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
    assert body["city_id"] == "mbta"
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
        "42.30,-71.20,42.45",           # too few parts
        "not,a,bounding,box",           # non-numeric
        "42.45,-71.20,42.30,-70.95",    # min >= max
        "99.0,-71.20,101.0,-70.95",     # latitude out of range
    ],
)
def test_malformed_bbox_is_rejected(client, bbox):
    response = client.get("/v1/vehicles", params={"bbox": bbox})
    assert response.status_code in (400, 422)
    assert response.json()["error"]["code"] == "INVALID_COORDINATES"


def test_fleet_returns_only_vehicles_in_the_viewport(client, seeded):
    body = client.get("/v1/vehicles", params={"bbox": "42.35,-71.07,42.38,-71.05"}).json()
    ids = {v["vehicle_id"] for v in body["vehicles"]}
    assert "fresh-1" in ids
    assert "far-1" not in ids
    assert body["count"] == len(body["vehicles"])


def test_fleet_response_carries_generated_at_and_city(client, seeded):
    body = client.get("/v1/vehicles", params={"bbox": BOSTON_BBOX}).json()
    assert "generated_at" in body
    assert body["city_id"] == "mbta"


def test_every_vehicle_carries_freshness(client, seeded):
    """The gate: a client must render the badge without computing clock skew."""
    body = client.get("/v1/vehicles", params={"bbox": BOSTON_BBOX}).json()
    assert body["vehicles"]

    for vehicle in body["vehicles"]:
        assert "age_s" in vehicle and vehicle["age_s"] >= 0
        assert "is_stale" in vehicle and isinstance(vehicle["is_stale"], bool)
        assert "ts" in vehicle
        assert "quality_score" in vehicle


def test_stale_vehicle_is_flagged_but_still_returned(client, seeded):
    """Section 16.1: degraded data stays visible rather than vanishing."""
    body = client.get("/v1/vehicles", params={"bbox": BOSTON_BBOX}).json()
    by_id = {v["vehicle_id"]: v for v in body["vehicles"]}

    assert by_id["stale-1"]["is_stale"] is True
    assert by_id["fresh-1"]["is_stale"] is False


def test_occupancy_is_present_and_unknown_never_absent(client, seeded):
    """Section 12.4 rule 3, on the wire.

    Slice A has no occupancy join yet, so every vehicle reports UNKNOWN. The
    field must still be present, and the ratio must be null rather than 0.
    """
    body = client.get("/v1/vehicles", params={"bbox": BOSTON_BBOX}).json()

    for vehicle in body["vehicles"]:
        assert "occupancy_class" in vehicle, "the field must never be omitted"
        assert vehicle["occupancy_class"] == "UNKNOWN"
        assert vehicle["occupancy_ratio"] is None, "unknown must not become 0"
        assert vehicle["occupancy_class"] != "EMPTY"


def test_fleet_limit_is_capped_server_side(client, seeded):
    assert client.get(
        "/v1/vehicles", params={"bbox": BOSTON_BBOX, "limit": 99999}
    ).status_code == 422
    body = client.get("/v1/vehicles", params={"bbox": BOSTON_BBOX, "limit": 1}).json()
    assert len(body["vehicles"]) == 1


def test_speed_is_the_derived_value(client, seeded):
    body = client.get("/v1/vehicles", params={"bbox": BOSTON_BBOX}).json()
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

    response = client.get("/v1/stops/1064/departures", params={"window_min": 240})
    if response.status_code == 503:
        pytest.skip("no GTFS feed imported")
    if response.status_code == 404:
        pytest.skip("stop 1064 absent from the imported feed")

    body = response.json()
    assert body["stop_id"] == "1064"
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
