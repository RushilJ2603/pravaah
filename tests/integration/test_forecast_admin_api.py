"""Contract coverage for forecast, planning, and operator endpoints.

The HTTP layer is exercised through the real FastAPI app.  Deterministic
in-memory resources keep the tests independent of Docker and wall-clock time;
database query shapes, response serialization, validation, and error handling
remain the production code paths.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from pravaah.api import admin, main, passenger
from pravaah.api.auth import StaffIdentity, require_operator
from pravaah.contracts.events import (
    OccupancyClass,
    OccupancyObservation,
    VehiclePositionEvent,
)
from pravaah.contracts.provenance import Provenance, SourceType
from pravaah.models.crowd import CrowdQuantiles

NOW = datetime(2026, 8, 30, 2, 30, tzinfo=UTC)  # 08:00 in Delhi
MODEL_VERSION = "test_quantiles_v1"


def _quantiles(
    p10: int,
    p50: int,
    p90: int,
    p10_class: OccupancyClass,
    p50_class: OccupancyClass,
    p90_class: OccupancyClass,
) -> CrowdQuantiles:
    return CrowdQuantiles(
        p10_class=p10_class,
        p50_class=p50_class,
        p90_class=p90_class,
        p10_onboard=p10,
        p50_onboard=p50,
        p90_onboard=p90,
        p50_ratio=p50 / 100,
        capacity=100,
        model_version=MODEL_VERSION,
    )


LOW = _quantiles(
    5,
    20,
    40,
    OccupancyClass.EMPTY,
    OccupancyClass.MANY_SEATS_AVAILABLE,
    OccupancyClass.FEW_SEATS_AVAILABLE,
)
CROWDED = _quantiles(
    45,
    72,
    91,
    OccupancyClass.FEW_SEATS_AVAILABLE,
    OccupancyClass.STANDING_ROOM_ONLY,
    OccupancyClass.CRUSHED_STANDING_ROOM_ONLY,
)
CRUSHED = _quantiles(
    65,
    88,
    100,
    OccupancyClass.STANDING_ROOM_ONLY,
    OccupancyClass.CRUSHED_STANDING_ROOM_ONLY,
    OccupancyClass.FULL,
)


class FakeForecaster:
    model_version = MODEL_VERSION

    def predict(
        self, hour: int, position: float, route_id: str | None = None
    ) -> CrowdQuantiles:
        del hour, route_id
        if position >= 0.7:
            return CRUSHED
        if position >= 0.3:
            return CROWDED
        return LOW


def _provenance(ts: datetime) -> Provenance:
    return Provenance(
        source_type=SourceType.SIMULATED,
        source_name="test_simulator",
        source_timestamp=ts,
        ingest_timestamp=ts,
        quality_score=0.9,
    )


def _position(vehicle_id: str, age_s: int) -> VehiclePositionEvent:
    ts = NOW - timedelta(seconds=age_s)
    return VehiclePositionEvent(
        city_id="delhi",
        agency_id="DTC",
        vehicle_id=vehicle_id,
        trip_id="trip-known",
        route_id="route-fast",
        direction_id=0,
        ts=ts,
        lat=28.6139,
        lon=77.2090,
        bearing=90.0,
        speed_mps=8.0,
        stop_id="origin",
        provenance=_provenance(ts),
    )


class FakeVehicleState:
    def __init__(self) -> None:
        self.events = [_position("sim-known", 30), _position("sim-unknown", 300)]

    def all(self, now: datetime | None = None) -> list[VehiclePositionEvent]:
        del now
        return list(self.events)


class FakeOccupancyState:
    def __init__(self) -> None:
        self.known = OccupancyObservation(
            city_id="delhi",
            vehicle_id="sim-known",
            trip_id="trip-known",
            ts=NOW - timedelta(seconds=30),
            occupancy_ratio=0.72,
            occupancy_class=OccupancyClass.STANDING_ROOM_ONLY,
            confidence=0.9,
            provenance=_provenance(NOW - timedelta(seconds=30)),
        )

    def get_many(
        self, vehicle_ids: list[str], now: datetime | None = None
    ) -> dict[str, OccupancyObservation]:
        del now
        return {"sim-known": self.known} if "sim-known" in vehicle_ids else {}


class FakeCursor:
    def __init__(self) -> None:
        self.rows: list[tuple] = []

    def __enter__(self) -> FakeCursor:
        return self

    def __exit__(self, *args) -> None:
        return None

    def execute(self, query: str, params: tuple | None = None) -> None:
        normalized = " ".join(query.split())
        params = params or ()

        if normalized.startswith("SELECT feed_version_id FROM feed_version"):
            self.rows = [(6,)]
        elif normalized.startswith("SELECT 1 FROM route"):
            self.rows = [(1,)] if params[1] == "route-fast" else []
        elif "SELECT st.stop_sequence" in normalized:
            trip_id = params[1]
            self.rows = (
                [
                    (1, "origin", "Origin Stop", 8 * 3600 + 5 * 60, "route-fast"),
                    (5, "middle", "Middle Stop", 8 * 3600 + 15 * 60, "route-fast"),
                    (10, "destination", "Destination Stop", 8 * 3600 + 30 * 60, "route-fast"),
                ]
                if trip_id == "trip-known"
                else []
            )
        elif "ST_Distance" in normalized:
            lon, lat = params[0], params[1]
            if (lat, lon) == pytest.approx((28.60, 77.10)):
                self.rows = [("origin", "Origin Stop", 15.0)]
            elif (lat, lon) == pytest.approx((28.70, 77.20)):
                self.rows = [("destination", "Destination Stop", 20.0)]
            else:
                self.rows = []
        elif "SELECT st1.trip_id" in normalized:
            self.rows = [
                (
                    "trip-fast",
                    "route-fast",
                    "Fast but busy",
                    "origin",
                    "Origin Stop",
                    6,
                    8 * 3600 + 5 * 60,
                    "destination",
                    "Destination Stop",
                    10,
                    8 * 3600 + 15 * 60,
                    11,
                ),
                (
                    "trip-calm",
                    "route-calm",
                    "Slower with seats",
                    "origin",
                    "Origin Stop",
                    2,
                    8 * 3600 + 10 * 60,
                    "destination",
                    "Destination Stop",
                    12,
                    8 * 3600 + 30 * 60,
                    21,
                ),
            ]
        elif "SELECT trip_id, max(stop_sequence)" in normalized:
            self.rows = [("trip-hot", 10), ("trip-crushed", 10)]
        elif "SELECT st.trip_id, st.stop_id" in normalized:
            self.rows = [
                (
                    "trip-hot",
                    "hot-stop",
                    "Hot Stop",
                    "route-hot",
                    "H1",
                    5,
                    8 * 3600 + 10 * 60,
                ),
                (
                    "trip-crushed",
                    "crushed-stop",
                    "Crushed Stop",
                    "route-crushed",
                    "C1",
                    8,
                    8 * 3600 + 20 * 60,
                ),
            ]
        else:  # pragma: no cover - makes new production queries fail loudly
            raise AssertionError(f"unexpected SQL in API test: {normalized}")

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self) -> list[tuple]:
        return list(self.rows)


class FakeConnection:
    def __enter__(self) -> FakeConnection:
        return self

    def __exit__(self, *args) -> None:
        return None

    def cursor(self) -> FakeCursor:
        return FakeCursor()


class FakePool:
    def connection(self) -> FakeConnection:
        return FakeConnection()


class FakeValidation:
    stale_after_s = 120


class FakeCity:
    city_id = "delhi"
    timezone = "Asia/Kolkata"
    validation = FakeValidation()


class FakeResources:
    def __init__(self) -> None:
        self.city = FakeCity()
        self.db_pool = FakePool()
        self.forecaster: FakeForecaster | None = FakeForecaster()
        self.state = FakeVehicleState()
        self.occupancy = FakeOccupancyState()

    def redis_ok(self) -> bool:
        return True

    def database_ok(self) -> bool:
        return self.db_pool is not None

    def close(self) -> None:
        return None


@pytest.fixture(scope="module")
def api():
    resources = FakeResources()
    main.app.dependency_overrides[require_operator] = lambda: StaffIdentity(
        user_id=99, role="OPERATOR", city_id="delhi"
    )
    with (
        patch.object(main, "build_resources", return_value=resources),
        patch.object(passenger, "now", return_value=NOW),
        patch.object(admin, "now", return_value=NOW),
        TestClient(main.app) as client,
    ):
        yield client, resources
    main.app.dependency_overrides.pop(require_operator, None)


def _assert_band(band: dict) -> None:
    assert set(band) == {
        "p10_class",
        "p50_class",
        "p90_class",
        "p10_onboard",
        "p50_onboard",
        "p90_onboard",
        "p50_ratio",
        "capacity",
        "model_version",
        "is_fallback",
    }
    assert band["p10_onboard"] <= band["p50_onboard"] <= band["p90_onboard"]
    assert band["model_version"] == MODEL_VERSION
    assert band["capacity"] == 100


def _plan_params(profile: str = "balanced") -> dict[str, str | float]:
    return {
        "from_lat": 28.60,
        "from_lon": 77.10,
        "to_lat": 28.70,
        "to_lon": 77.20,
        "profile": profile,
    }


def test_trip_forecast_returns_ordered_quantile_bands(api):
    client, _ = api
    response = client.get("/v1/trips/trip-known/forecast")

    assert response.status_code == 200
    body = response.json()
    assert body["city_id"] == "delhi"
    assert body["trip_id"] == "trip-known"
    assert body["route_id"] == "route-fast"
    assert body["model_version"] == MODEL_VERSION
    assert body["generated_at"] == NOW.isoformat().replace("+00:00", "Z")
    assert [stop["stop_sequence"] for stop in body["stops"]] == [1, 5, 10]
    for stop in body["stops"]:
        _assert_band(stop["crowd"])


def test_trip_forecast_unknown_trip_uses_error_contract(api):
    client, _ = api
    response = client.get("/v1/trips/not-a-trip/forecast")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NO_ROUTE_FOUND"


@pytest.mark.parametrize(
    "profile", ["fastest", "least_crowded", "most_reliable", "balanced"]
)
def test_plan_supports_every_contract_profile_with_reasons(api, profile):
    client, _ = api
    response = client.get("/v1/plan", params=_plan_params(profile))

    assert response.status_code == 200
    body = response.json()
    assert body["profile"] == profile
    assert body["options"]
    assert sum(option["is_recommended"] for option in body["options"]) == 1
    assert [option["score"] for option in body["options"]] == sorted(
        option["score"] for option in body["options"]
    )
    for option in body["options"]:
        assert option["reasons"]
        assert any("no transfers" in reason for reason in option["reasons"])
        _assert_band(option["legs"][0]["crowd"])


def test_plan_profiles_change_the_recommended_route(api):
    client, _ = api
    fastest = client.get("/v1/plan", params=_plan_params("fastest")).json()
    least_crowded = client.get(
        "/v1/plan", params=_plan_params("least_crowded")
    ).json()

    assert fastest["options"][0]["legs"][0]["route_id"] == "route-fast"
    assert least_crowded["options"][0]["legs"][0]["route_id"] == "route-calm"


def test_plan_rejects_unknown_profile(api):
    client, _ = api
    response = client.get("/v1/plan", params=_plan_params("teleport"))

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_COORDINATES"


def test_plan_rejects_non_contract_fewest_transfers_profile(api):
    client, _ = api
    response = client.get("/v1/plan", params=_plan_params("fewest_transfers"))

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_COORDINATES"


def test_plan_outside_service_area_uses_error_contract(api):
    client, _ = api
    params = _plan_params()
    params["from_lat"] = 10.0
    response = client.get("/v1/plan", params=params)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "OUT_OF_SERVICE_AREA"


def test_plan_without_forecaster_is_explicitly_unknown(api, monkeypatch):
    client, resources = api
    monkeypatch.setattr(resources, "forecaster", None)
    body = client.get("/v1/plan", params=_plan_params()).json()

    for option in body["options"]:
        crowd = option["legs"][0]["crowd"]
        assert crowd["p10_class"] == "UNKNOWN"
        assert crowd["p50_class"] == "UNKNOWN"
        assert crowd["p90_class"] == "UNKNOWN"
        assert crowd["p10_onboard"] is None
        assert crowd["p50_onboard"] is None
        assert crowd["p90_onboard"] is None
        assert crowd["p50_ratio"] is None
        assert crowd["capacity"] is None
        assert any("no crowd forecast" in reason for reason in option["reasons"])


def test_hotspots_have_severity_lead_time_and_supporting_quantiles(api):
    client, _ = api
    response = client.get("/v1/admin/hotspots", params={"horizon_min": 60})

    assert response.status_code == 200
    body = response.json()
    assert body["model_version"] == MODEL_VERSION
    assert body["count"] == len(body["hotspots"]) == 2
    assert [item["severity"] for item in body["hotspots"]] == [4, 3]
    for item in body["hotspots"]:
        assert item["lead_time_min"] >= 0
        assert item["services_in_window"] >= 1
        assert item["reason"]
        _assert_band(item["crowd"])


def test_route_forecast_is_hourly_and_wraps_midnight(api):
    client, _ = api
    response = client.get("/v1/admin/routes/route-fast/forecast", params={"hours": 24})

    assert response.status_code == 200
    body = response.json()
    assert body["route_id"] == "route-fast"
    assert body["model_version"] == MODEL_VERSION
    assert [item["hour"] for item in body["hours"]] == list(range(8, 24)) + list(range(8))
    for item in body["hours"]:
        _assert_band(item["crowd"])


def test_route_forecast_rejects_unknown_route(api):
    client, _ = api
    response = client.get("/v1/admin/routes/not-a-route/forecast")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NO_ROUTE_FOUND"


def test_admin_vehicles_preserve_simulated_provenance_and_unknown(api):
    client, _ = api
    response = client.get("/v1/admin/vehicles")

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 2
    by_id = {vehicle["vehicle_id"]: vehicle for vehicle in body["vehicles"]}
    assert {vehicle["source_type"] for vehicle in body["vehicles"]} == {"SIMULATED"}
    assert by_id["sim-known"]["occupancy_class"] == "STANDING_ROOM_ONLY"
    assert by_id["sim-known"]["occupancy_ratio"] == 0.72
    assert by_id["sim-unknown"]["occupancy_class"] == "UNKNOWN"
    assert by_id["sim-unknown"]["occupancy_ratio"] is None
    assert by_id["sim-unknown"]["occupancy_class"] != "EMPTY"


def test_data_health_reports_freshness_coverage_and_provenance(api):
    client, _ = api
    response = client.get("/v1/admin/data-health")

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "generated_at": NOW.isoformat().replace("+00:00", "Z"),
        "city_id": "delhi",
        "database": True,
        "redis": True,
        "feed_version_id": 6,
        "vehicles_tracked": 2,
        "vehicles_stale": 1,
        "vehicles_with_occupancy": 1,
        "occupancy_coverage": 0.5,
        "oldest_position_age_s": 300,
        "source_types": {"SIMULATED": 2},
        "forecast_model": MODEL_VERSION,
    }


@pytest.mark.parametrize(
    ("path", "params"),
    [
        ("/v1/admin/hotspots", {"horizon_min": 9}),
        ("/v1/admin/routes/route-fast/forecast", {"hours": 25}),
        ("/v1/admin/vehicles", {"limit": 5001}),
    ],
)
def test_admin_query_bounds_use_the_error_contract(api, path, params):
    client, _ = api
    response = client.get(path, params=params)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_COORDINATES"


@pytest.mark.parametrize(
    "path",
    [
        "/v1/trips/trip-known/forecast",
        "/v1/admin/hotspots",
        "/v1/admin/routes/route-fast/forecast",
    ],
)
def test_forecast_endpoints_fail_explicitly_without_a_model(api, monkeypatch, path):
    client, resources = api
    monkeypatch.setattr(resources, "forecaster", None)
    response = client.get(path)

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "FEED_UNAVAILABLE"


@pytest.mark.parametrize(
    "path",
    [
        "/v1/trips/trip-known/forecast",
        "/v1/plan?from_lat=28.6&from_lon=77.1&to_lat=28.7&to_lon=77.2",
        "/v1/admin/hotspots",
    ],
)
def test_schedule_endpoints_fail_explicitly_without_database(api, monkeypatch, path):
    client, resources = api
    monkeypatch.setattr(resources, "db_pool", None)
    response = client.get(path)

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "FEED_UNAVAILABLE"
