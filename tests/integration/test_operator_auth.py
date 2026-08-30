"""Operator endpoints are staff-only; the dashboard is not a public API."""

from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from pravaah.api import main
from pravaah.api.auth import StaffIdentity, optional_staff


class Resources:
    city = SimpleNamespace(
        city_id="delhi", validation=SimpleNamespace(stale_after_s=120)
    )
    db_pool = None
    forecaster = None

    def redis_ok(self) -> bool:
        return False

    def database_ok(self) -> bool:
        return False

    def close(self) -> None:
        return None


def _request_with_identity(identity: StaffIdentity | None):
    resources = Resources()
    main.app.dependency_overrides[optional_staff] = lambda: identity
    try:
        with (
            patch.object(main, "build_resources", return_value=resources),
            TestClient(main.app) as client,
        ):
            return client.get("/v1/admin/data-health")
    finally:
        main.app.dependency_overrides.pop(optional_staff, None)


def test_operator_endpoint_rejects_anonymous_and_conductor_roles():
    anonymous = _request_with_identity(None)
    conductor = _request_with_identity(StaffIdentity(7, "CONDUCTOR", "delhi"))

    assert anonymous.status_code == 401
    assert conductor.status_code == 403


def test_operator_endpoint_accepts_operator_role():
    response = _request_with_identity(StaffIdentity(8, "OPERATOR", "delhi"))

    assert response.status_code == 200
    assert response.json()["city_id"] == "delhi"
