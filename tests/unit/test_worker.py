"""Ingestion worker behaviour (SOLUTION.md section 7.2).

The worker is the process that makes the map move, so the property that matters
most is that it *keeps running*. Section 16.1 requires graceful degradation, and
a worker that exits on the first bad poll takes the live map down with it.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from pravaah.adapters.base import FeedSnapshot, RealtimeAdapter
from pravaah.config import load_city
from pravaah.contracts.events import VehiclePositionEvent
from pravaah.contracts.provenance import Provenance, SourceType
from pravaah.ingest.worker import IngestWorker

T0 = datetime(2026, 8, 28, 14, 0, 0, tzinfo=UTC)


def position(vehicle_id="y1", lat=42.3601, lon=-71.0589, ts=None) -> VehiclePositionEvent:
    ts = ts or datetime.now(UTC)
    return VehiclePositionEvent(
        city_id="mbta",
        agency_id="MBTA",
        vehicle_id=vehicle_id,
        trip_id="t1",
        route_id="64",
        ts=ts,
        lat=lat,
        lon=lon,
        provenance=Provenance(
            source_type=SourceType.PUBLIC_FEED,
            source_name="mbta_cdn",
            source_timestamp=ts,
            ingest_timestamp=ts,
            quality_score=1.0,
        ),
    )


class FakeAdapter(RealtimeAdapter):
    """Serves scripted snapshots, and can be told to fail."""

    def __init__(self, city, snapshots, fail_on=()):
        super().__init__(city)
        self.snapshots = snapshots
        self.fail_on = set(fail_on)
        self.calls = 0

    @property
    def source_name(self) -> str:
        return "fake"

    def fetch_vehicle_positions(self, timeout: float = 30.0) -> bytes:
        return b""

    def decode_vehicle_positions(self, raw, ingest_ts=None) -> FeedSnapshot:
        raise NotImplementedError

    def poll(self, timeout: float = 30.0) -> FeedSnapshot:
        index = self.calls
        self.calls += 1
        if index in self.fail_on:
            raise ConnectionError("feed unreachable")
        return self.snapshots[min(index, len(self.snapshots) - 1)]


class FakeState:
    def __init__(self, fail=False):
        self.written = []
        self.fail = fail

    def put_many(self, events):
        if self.fail:
            raise ConnectionError("redis down")
        self.written.extend(events)
        return len(events)


@pytest.fixture
def city():
    return load_city("mbta")


def snapshot(positions) -> FeedSnapshot:
    return FeedSnapshot(feed_timestamp=T0, positions=positions)


def test_cycle_validates_and_stores(city):
    state = FakeState()
    worker = IngestWorker(FakeAdapter(city, [snapshot([position()])]), city, state=state)

    assert worker.cycle() == 1
    assert len(state.written) == 1
    assert worker.accepted_total == 1


def test_invalid_positions_never_reach_storage(city):
    """A Delhi coordinate in an MBTA feed is corruption, not data."""
    state = FakeState()
    worker = IngestWorker(
        FakeAdapter(
            city,
            [snapshot([position("good"), position("bad", lat=28.61, lon=77.23)])],
        ),
        city,
        state=state,
    )

    worker.cycle()
    assert [e.vehicle_id for e in state.written] == ["good"]
    assert worker.rejected_total == 1


def test_speed_is_derived_across_cycles(city):
    """The whole reason speed is not taken from the feed (section 28.4)."""
    now = datetime.now(UTC)
    state = FakeState()
    worker = IngestWorker(
        FakeAdapter(
            city,
            [
                snapshot([position(lat=42.3601, lon=-71.0589, ts=now)]),
                snapshot(
                    [position(lat=42.3701, lon=-71.0589, ts=now + timedelta(seconds=120))]
                ),
            ],
        ),
        city,
        state=state,
    )

    worker.cycle()
    assert state.written[0].speed_mps is None, "nothing to measure against yet"

    worker.cycle()
    assert state.written[1].speed_mps == pytest.approx(9.3, abs=0.5)


def test_a_failed_poll_does_not_end_the_loop(city):
    """The property that keeps the map alive."""
    worker = IngestWorker(
        FakeAdapter(city, [snapshot([position()])], fail_on={0, 2}), city, state=FakeState()
    )
    worker.run(interval_s=1, max_cycles=4)

    assert worker.cycles == 4
    assert worker.accepted_total > 0, "recovered cycles should still have stored data"


def test_a_redis_failure_does_not_end_the_loop(city):
    """Section 16.1: Redis down means higher latency, not data loss or a crash."""
    worker = IngestWorker(
        FakeAdapter(city, [snapshot([position()])]), city, state=FakeState(fail=True)
    )

    assert worker.cycle() == 1  # validation still succeeded
    assert worker.accepted_total == 1


def test_stop_ends_the_loop(city):
    worker = IngestWorker(FakeAdapter(city, [snapshot([position()])]), city, state=FakeState())
    worker.stop()
    worker.run(interval_s=1, max_cycles=10)
    assert worker.cycles == 0
