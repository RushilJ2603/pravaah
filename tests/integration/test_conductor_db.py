"""Slice G acceptance gate against the real Postgres and Redis services."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from pravaah.api.auth import hash_password
from pravaah.api.main import app
from pravaah.contracts.provenance import SourceType

SECRET = "integration-only-auth-secret-at-least-32-bytes"


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("PRAVAAH_AUTH_SECRET", SECRET)
    with TestClient(app) as test_client:
        resources = test_client.app.state.resources
        if resources.db_pool is None or not resources.redis_ok():
            pytest.skip("Postgres and Redis are required; run docker compose up -d")
        yield test_client


def test_conductor_lifecycle_and_operator_rbac(client):
    resources = client.app.state.resources
    suffix = uuid4().hex[:10]
    conductor_name = f"it_conductor_{suffix}"
    operator_name = f"it_operator_{suffix}"
    password = f"test-password-{suffix}"
    vehicle_id = f"IT-BUS-{suffix}"
    user_ids: list[int] = []

    try:
        with resources.db_pool.connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT t.trip_id, t.route_id FROM trip t
                JOIN feed_version f ON f.feed_version_id = t.feed_version_id
                WHERE f.city_id = %s ORDER BY f.imported_at DESC, t.trip_id LIMIT 1
                """,
                (resources.city.city_id,),
            )
            trip_id, route_id = cur.fetchone()
            for username, role in (
                (conductor_name, "CONDUCTOR"),
                (operator_name, "OPERATOR"),
            ):
                cur.execute(
                    """
                    INSERT INTO app_user
                        (username, password_hash, role, city_id, agency_id)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING user_id
                    """,
                    (
                        username,
                        hash_password(password),
                        role,
                        resources.city.city_id,
                        resources.city.agency_id,
                    ),
                )
                user_ids.append(cur.fetchone()[0])
            conn.commit()

        conductor_login = client.post(
            "/v1/auth/login", json={"username": conductor_name, "password": password}
        )
        operator_login = client.post(
            "/v1/auth/login", json={"username": operator_name, "password": password}
        )
        assert conductor_login.status_code == operator_login.status_code == 200
        conductor_headers = {
            "Authorization": f"Bearer {conductor_login.json()['access_token']}"
        }
        operator_headers = {
            "Authorization": f"Bearer {operator_login.json()['access_token']}"
        }

        start = client.post(
            "/v1/shifts/start",
            headers=conductor_headers,
            json={
                "vehicle_id": vehicle_id,
                "trip_id": trip_id,
                "route_id": route_id,
                "device_id": f"device-{suffix}",
            },
        )
        assert start.status_code == 200
        shift_id = start.json()["shift_id"]

        duplicate = client.post(
            "/v1/shifts/start",
            headers=conductor_headers,
            json={
                "vehicle_id": vehicle_id,
                "trip_id": trip_id,
                "route_id": route_id,
                "device_id": f"second-device-{suffix}",
            },
        )
        assert duplicate.status_code == 409
        assert duplicate.json()["error"]["code"] == "VEHICLE_ALREADY_CLAIMED"

        reported_at = datetime.now(UTC).isoformat()
        position = client.post(
            f"/v1/shifts/{shift_id}/position",
            headers=conductor_headers,
            json={
                "lat": 28.6139,
                "lon": 77.2090,
                "accuracy_m": 8.0,
                "speed_mps": 9.0,
                "timestamp": reported_at,
            },
        )
        assert position.status_code == 204

        crowd = client.post(
            "/v1/occupancy/report",
            headers=conductor_headers,
            json={
                "trip_id": trip_id,
                "vehicle_id": vehicle_id,
                "occupancy_class": "STANDING_ROOM_ONLY",
                "reported_at": datetime.now(UTC).isoformat(),
            },
        )
        assert crowd.status_code == 202
        assert resources.state.get(vehicle_id).provenance.source_type is SourceType.REAL_OPERATOR
        assert (
            resources.occupancy.get(vehicle_id).provenance.source_name
            == "conductor_app"
        )

        assert client.get("/v1/admin/data-health").status_code == 401
        assert (
            client.get(
                "/v1/admin/data-health", headers=conductor_headers
            ).status_code
            == 403
        )
        assert (
            client.get("/v1/admin/data-health", headers=operator_headers).status_code
            == 200
        )

        assert (
            client.post(
                f"/v1/shifts/{shift_id}/end", headers=conductor_headers
            ).status_code
            == 204
        )
        ended = client.post(
            f"/v1/shifts/{shift_id}/position",
            headers=conductor_headers,
            json={
                "lat": 28.6139,
                "lon": 77.2090,
                "accuracy_m": 8.0,
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )
        assert ended.status_code == 409
        assert ended.json()["error"]["code"] == "SHIFT_NOT_ACTIVE"
    finally:
        resources.redis.hdel(f"pravaah:{resources.city.city_id}:vehicles", vehicle_id)
        resources.redis.zrem(f"pravaah:{resources.city.city_id}:geo", vehicle_id)
        resources.redis.hdel(f"pravaah:{resources.city.city_id}:occupancy", vehicle_id)
        with resources.db_pool.connection() as conn, conn.cursor() as cur:
            cur.execute(
                "DELETE FROM occupancy_observation WHERE city_id = %s AND vehicle_id = %s",
                (resources.city.city_id, vehicle_id),
            )
            cur.execute(
                "DELETE FROM vehicle_position WHERE city_id = %s AND vehicle_id = %s",
                (resources.city.city_id, vehicle_id),
            )
            if user_ids:
                cur.execute("DELETE FROM conductor_shift WHERE user_id = ANY(%s)", (user_ids,))
                cur.execute("DELETE FROM app_user WHERE user_id = ANY(%s)", (user_ids,))
            conn.commit()
