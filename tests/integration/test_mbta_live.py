"""Slice A.1 acceptance gate, live half (SOLUTION.md section 31).

Gate: "A live poll produces valid VehiclePositionEvents; zero records lack
provenance; speed_mps is left None."

This performs one real request to the MBTA CDN. It skips -- it does not fail --
when the feed is unreachable, so the suite stays runnable offline. The offline
demo path (section 19) never depends on this.
"""

from __future__ import annotations

import urllib.error

import pytest

from pravaah.adapters.mbta import build
from pravaah.contracts.events import OccupancyClass
from pravaah.contracts.provenance import SourceType


@pytest.fixture(scope="module")
def snapshot():
    adapter = build()
    try:
        return adapter.poll(timeout=20.0)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        pytest.skip(f"MBTA feed unreachable ({exc})")


def test_live_poll_returns_a_populated_fleet(snapshot):
    """MBTA runs several hundred vehicles at any hour of the day."""
    assert len(snapshot.positions) > 50, "suspiciously small fleet"
    assert snapshot.feed_timestamp is not None
    assert len(snapshot.payload_sha256) == 64


def test_zero_live_records_lack_provenance(snapshot):
    """The gate itself, against real data rather than a fixture."""
    for event in [*snapshot.positions, *snapshot.occupancies]:
        assert event.provenance is not None
        assert event.provenance.source_name == "mbta_cdn"
        assert event.provenance.raw_payload_ref == snapshot.payload_sha256
        assert 0.0 <= event.provenance.quality_score <= 1.0


def test_no_live_record_carries_feed_speed(snapshot):
    assert all(p.speed_mps is None for p in snapshot.positions)


def test_positions_are_inside_the_city_bounds(snapshot):
    """Catches a wrong feed URL or a wrong city profile immediately."""
    city = build().city
    outside = [p for p in snapshot.positions if not city.bounds.contains(p.lat, p.lon)]
    assert not outside, f"{len(outside)} vehicle(s) outside the MBTA bounding box"


def test_live_occupancy_coverage_is_broadly_as_documented(snapshot):
    """Section 6.2.1 measured ~68.8% coverage over the recorded corpus.

    A single live poll varies with time of day, so this only asserts the
    property that matters -- that real crowd labels are arriving at a plausible
    rate. A collapse to near zero means the feed changed and the substrate
    rationale in ADR-08 needs revisiting.
    """
    coverage = snapshot.occupancy_coverage
    assert 0.2 < coverage <= 1.0, f"occupancy coverage {coverage:.1%} is implausible"


def test_live_occupancy_is_operator_reported(snapshot):
    if not snapshot.occupancies:
        pytest.skip("no occupancy in this poll")
    assert all(
        o.provenance.source_type is SourceType.REAL_OPERATOR for o in snapshot.occupancies
    )
    assert all(o.occupancy_class is not OccupancyClass.UNKNOWN for o in snapshot.occupancies)


def test_most_live_vehicles_are_on_a_trip(snapshot):
    """Section 6.2.1 measured trip_id at 100%; allow slack for vehicles between trips."""
    with_trip = [p for p in snapshot.positions if p.trip_id]
    assert len(with_trip) / len(snapshot.positions) > 0.8
