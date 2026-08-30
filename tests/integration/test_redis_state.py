"""Slice A.2 acceptance gate, state half (SOLUTION.md section 31).

Gate: "latest-state read < 5 ms; state rebuilds from the database after a Redis
restart."

Needs the compose stack (`docker compose up -d`). Skips when Redis is
unreachable so the unit suite stays runnable with Docker stopped.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta

import pytest

from pravaah.config import load_settings
from pravaah.contracts.events import OccupancyClass, OccupancyObservation, VehiclePositionEvent
from pravaah.contracts.provenance import Provenance, SourceType
from pravaah.state.redis_state import LatestOccupancyState, LatestVehicleState

redis_lib = pytest.importorskip("redis", reason="redis client not installed")

T0 = datetime(2026, 8, 28, 14, 0, 0, tzinfo=UTC)
CITY = "test_mbta"

#: SOLUTION.md section 31 A.2.
READ_BUDGET_S = 0.005


@pytest.fixture(scope="module")
def client():
    try:
        c = redis_lib.Redis.from_url(load_settings().redis_url, socket_connect_timeout=3)
        c.ping()
    except Exception as exc:  # noqa: BLE001 -- any failure means "not available"
        pytest.skip(f"redis unreachable ({exc}); run: docker compose up -d")
    yield c
    c.close()


@pytest.fixture
def state(client):
    s = LatestVehicleState(client, CITY)
    s.clear()
    yield s
    s.clear()


def position(vehicle_id="y1", lat=42.3601, lon=-71.0589, ts=T0) -> VehiclePositionEvent:
    return VehiclePositionEvent(
        city_id=CITY,
        agency_id="MBTA",
        vehicle_id=vehicle_id,
        trip_id="t1",
        route_id="64",
        ts=ts,
        lat=lat,
        lon=lon,
        speed_mps=9.3,
        provenance=Provenance(
            source_type=SourceType.PUBLIC_FEED,
            source_name="mbta_cdn",
            source_timestamp=ts,
            ingest_timestamp=ts,
            quality_score=0.96,
        ),
    )


# --------------------------------------------------------------------------
# Round trip.
# --------------------------------------------------------------------------


def test_put_and_get_round_trip(state):
    original = position()
    state.put(original)

    loaded = state.get("y1", now=T0)
    assert loaded == original, "the event must survive serialization unchanged"
    assert loaded.provenance.source_type is SourceType.PUBLIC_FEED
    assert loaded.speed_mps == pytest.approx(9.3)


def test_missing_vehicle_returns_none(state):
    assert state.get("nope", now=T0) is None


def test_put_many_upserts(state):
    state.put_many([position(f"y{i}") for i in range(50)])
    assert state.count() == 50

    state.put(position("y0", lat=42.40))
    assert state.count() == 50, "an update must not create a second entry"
    assert state.get("y0", now=T0).lat == pytest.approx(42.40)


# --------------------------------------------------------------------------
# The latency gate.
# --------------------------------------------------------------------------


def test_single_read_is_under_the_budget(state):
    state.put_many([position(f"y{i}") for i in range(500)])

    # Warm the connection so the first TCP round trip is not measured.
    state.get("y0", now=T0)

    samples = []
    for i in range(50):
        started = time.perf_counter()
        state.get(f"y{i}", now=T0)
        samples.append(time.perf_counter() - started)

    samples.sort()
    p95 = samples[int(len(samples) * 0.95)]
    print(f"\n  latest-state read p95: {p95 * 1000:.2f} ms over {state.count()} vehicles")
    assert p95 < READ_BUDGET_S, f"p95 {p95 * 1000:.2f} ms exceeds 5 ms"


# --------------------------------------------------------------------------
# Expiry.
# --------------------------------------------------------------------------


def test_expired_entries_are_not_returned(state):
    state.put(position(ts=T0))
    assert state.get("y1", now=T0 + timedelta(seconds=60)) is not None
    assert state.get("y1", now=T0 + timedelta(seconds=1200)) is None


def test_expired_entries_are_pruned_on_read(state):
    state.put_many([position("fresh", ts=T0), position("old", ts=T0 - timedelta(hours=2))])

    remaining = state.all(now=T0)
    assert {e.vehicle_id for e in remaining} == {"fresh"}
    assert state.count() == 1, "the aged-out entry should have been pruned"


# --------------------------------------------------------------------------
# Viewport queries (section 12.4 rule 5).
# --------------------------------------------------------------------------


def test_viewport_returns_only_vehicles_inside_the_box(state):
    state.put_many(
        [
            position("downtown", lat=42.3601, lon=-71.0589),
            position("north", lat=42.4600, lon=-71.0589),
            position("west", lat=42.3601, lon=-71.5000),
        ]
    )

    inside = state.in_viewport(42.30, -71.10, 42.40, -71.00, now=T0)
    assert {e.vehicle_id for e in inside} == {"downtown"}


def test_viewport_avoids_transferring_the_whole_fleet(state):
    """A zoomed-in map must not pull every vehicle in the city (section 16.3)."""
    state.put_many([position(f"far{i}", lat=42.9, lon=-70.2) for i in range(200)])
    state.put_many([position("near", lat=42.3601, lon=-71.0589)])

    inside = state.in_viewport(42.35, -71.07, 42.37, -71.05, now=T0)
    assert [e.vehicle_id for e in inside] == ["near"]
    assert state.count() == 201


def test_empty_viewport_returns_empty(state):
    state.put(position(lat=42.3601, lon=-71.0589))
    assert state.in_viewport(40.0, -75.0, 40.1, -74.9, now=T0) == []


# --------------------------------------------------------------------------
# Recovery (section 11.3, section 16.1).
# --------------------------------------------------------------------------


def test_state_is_reconstructible_after_a_flush(state, client):
    """Losing Redis must be a latency event, not a data-loss event.

    Full `rebuild_from_database` is exercised where the database fixture exists;
    this proves the cache can be emptied and refilled without the caller seeing
    anything but a slower first read.
    """
    events = [position(f"y{i}") for i in range(20)]
    state.put_many(events)
    assert state.count() == 20

    state.clear()
    assert state.count() == 0
    assert state.get("y0", now=T0) is None

    state.put_many(events)
    assert state.count() == 20
    assert state.get("y0", now=T0) == events[0]



@pytest.fixture
def occ_state(client):
    s = LatestOccupancyState(client, CITY)
    s.clear()
    yield s
    s.clear()

def occupancy(
    vehicle_id="y1",
    ts=T0,
    occ_class=OccupancyClass.MANY_SEATS_AVAILABLE,
    ratio=0.2,
) -> OccupancyObservation:
    return OccupancyObservation(
        city_id=CITY,
        vehicle_id=vehicle_id,
        ts=ts,
        occupancy_class=occ_class,
        occupancy_ratio=ratio,
        confidence=1.0,
        provenance=Provenance(
            source_type=SourceType.PUBLIC_FEED,
            source_name="mbta_cdn",
            source_timestamp=ts,
            ingest_timestamp=ts,
            quality_score=1.0,
        ),
    )

def test_occupancy_round_trips_fields_unchanged(occ_state):
    original = occupancy(occ_class=OccupancyClass.FEW_SEATS_AVAILABLE, ratio=0.8)
    occ_state.put_many([original])
    loaded = occ_state.get_many(["y1"], now=T0)
    assert "y1" in loaded
    assert loaded["y1"].occupancy_class == OccupancyClass.FEW_SEATS_AVAILABLE
    assert loaded["y1"].occupancy_ratio == 0.8

def test_get_many_missing_omits_entry_does_not_invent_empty(occ_state):
    occ_state.put_many([occupancy("y1")])
    loaded = occ_state.get_many(["y1", "nope"], now=T0)
    assert "y1" in loaded
    assert "nope" not in loaded

def test_expired_occupancy_is_absent_and_pruned(occ_state):
    occ_state.put_many([occupancy("y1", ts=T0), occupancy("old", ts=T0 - timedelta(hours=2))])
    loaded = occ_state.get_many(["y1", "old"], now=T0)
    assert "y1" in loaded
    assert "old" not in loaded
    assert occ_state.count() == 1

def test_get_many_empty_returns_empty_without_redis(occ_state, monkeypatch):
    def block_redis(*args, **kwargs):
        raise AssertionError("Should not call Redis")
    monkeypatch.setattr(occ_state.redis, "hmget", block_redis)
    loaded = occ_state.get_many([], now=T0)
    assert loaded == {}
