"""Slice A.2 acceptance gate, validation half (SOLUTION.md section 31).

Gate: "Out-of-bounds and impossible-speed positions are rejected with a reason."

Also pins section 28.4's derived speed, since the raw feed field is unusable.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from pravaah.config import load_city
from pravaah.contracts.events import VehiclePositionEvent
from pravaah.contracts.provenance import Provenance, SourceType
from pravaah.ingest.validate import (
    PositionValidator,
    RejectionReason,
    derive_speed,
    haversine_m,
)

T0 = datetime(2026, 8, 28, 14, 0, 0, tzinfo=UTC)

# Boston, and two points ~1113 m apart in latitude (0.01 degrees).
BOSTON = (42.3601, -71.0589)
BOSTON_NORTH = (42.3701, -71.0589)


def position(
    lat: float = BOSTON[0],
    lon: float = BOSTON[1],
    ts: datetime = T0,
    vehicle_id: str = "y1",
) -> VehiclePositionEvent:
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


@pytest.fixture
def validator() -> PositionValidator:
    return PositionValidator(load_city("mbta"))


# --------------------------------------------------------------------------
# Derived speed (section 28.4).
# --------------------------------------------------------------------------


def test_haversine_matches_a_known_distance():
    metres = haversine_m(*BOSTON, *BOSTON_NORTH)
    assert metres == pytest.approx(1112, abs=15)  # 0.01 deg latitude


def test_derive_speed_over_a_minute():
    a = position(*BOSTON, ts=T0)
    b = position(*BOSTON_NORTH, ts=T0 + timedelta(seconds=60))
    assert derive_speed(a, b) == pytest.approx(18.5, abs=0.5)


def test_derive_speed_needs_elapsed_time():
    a = position(ts=T0)
    assert derive_speed(a, position(ts=T0)) is None
    assert derive_speed(a, position(ts=T0 - timedelta(seconds=5))) is None


def test_derive_speed_refuses_a_long_gap():
    """Over a long gap the path is unknowable, so a straight-line speed lies."""
    a = position(*BOSTON, ts=T0)
    b = position(*BOSTON_NORTH, ts=T0 + timedelta(seconds=600))
    assert derive_speed(a, b) is None


# --------------------------------------------------------------------------
# The gate: rejection with a reason.
# --------------------------------------------------------------------------


def test_out_of_bounds_position_is_rejected_with_a_reason(validator):
    result = validator.validate([position(lat=28.61, lon=77.23)])  # Delhi

    assert result.accepted == []
    assert len(result.rejected) == 1
    assert result.rejected[0].reason is RejectionReason.OUT_OF_BOUNDS
    assert "outside mbta" in result.rejected[0].detail
    assert result.reasons() == {"OUT_OF_BOUNDS": 1}


def test_null_island_is_rejected_distinctly(validator):
    """(0, 0) means 'no GPS fix', not a position in the Gulf of Guinea."""
    result = validator.validate([position(lat=0.0, lon=0.0)])
    assert result.rejected[0].reason is RejectionReason.NULL_ISLAND


def test_impossible_speed_is_rejected_with_a_reason(validator):
    """A teleport between consecutive polls is a spoof or an outlier (15.2)."""
    validator.validate([position(*BOSTON, ts=T0)])
    # ~78 km north in 10 seconds.
    result = validator.validate(
        [position(lat=43.0, lon=-71.0589, ts=T0 + timedelta(seconds=10))]
    )

    assert result.accepted == []
    assert result.rejected[0].reason is RejectionReason.IMPOSSIBLE_SPEED
    assert "exceeds 35.0 m/s" in result.rejected[0].detail


def test_plausible_movement_is_accepted_with_derived_speed(validator):
    validator.validate([position(*BOSTON, ts=T0)])
    result = validator.validate([position(*BOSTON_NORTH, ts=T0 + timedelta(seconds=120))])

    assert len(result.accepted) == 1
    assert result.accepted[0].speed_mps == pytest.approx(9.3, abs=0.5)
    assert not result.rejected


def test_first_sighting_has_no_speed(validator):
    """Nothing to measure against yet -- None, not zero."""
    result = validator.validate([position()])
    assert result.accepted[0].speed_mps is None


def test_repeated_timestamp_is_rejected_as_duplicate(validator):
    """Feeds re-serve an unchanged reading; accepting it would fabricate a
    zero-speed sample and inflate dwell time."""
    validator.validate([position(ts=T0)])
    result = validator.validate([position(ts=T0)])

    assert result.accepted == []
    assert result.rejected[0].reason is RejectionReason.DUPLICATE


def test_out_of_order_position_is_rejected(validator):
    validator.validate([position(ts=T0)])
    result = validator.validate([position(ts=T0 - timedelta(seconds=30))])
    assert result.rejected[0].reason is RejectionReason.DUPLICATE


# --------------------------------------------------------------------------
# Staleness is a label, not a rejection (section 16.1).
# --------------------------------------------------------------------------


def test_stale_position_is_accepted_but_flagged(validator):
    result = validator.validate(
        [position(ts=T0)], now=T0 + timedelta(seconds=300)
    )
    assert len(result.accepted) == 1, "stale data must stay visible, not vanish"
    assert result.stale == ["y1"]


def test_fresh_position_is_not_flagged(validator):
    result = validator.validate([position(ts=T0)], now=T0 + timedelta(seconds=10))
    assert result.stale == []


# --------------------------------------------------------------------------
# Batch behaviour.
# --------------------------------------------------------------------------


def test_one_bad_vehicle_does_not_reject_the_batch(validator):
    result = validator.validate(
        [
            position(vehicle_id="good1"),
            position(lat=28.61, lon=77.23, vehicle_id="bad"),
            position(vehicle_id="good2"),
        ]
    )
    assert {e.vehicle_id for e in result.accepted} == {"good1", "good2"}
    assert result.rejection_rate == pytest.approx(1 / 3)


def test_vehicles_are_tracked_independently(validator):
    validator.validate([position(*BOSTON, ts=T0, vehicle_id="a")])
    result = validator.validate(
        [position(*BOSTON_NORTH, ts=T0 + timedelta(seconds=1), vehicle_id="b")]
    )
    # b is a first sighting, so a's history must not be used for its speed.
    assert result.accepted[0].speed_mps is None
    assert validator.tracked_vehicles == 2


def test_reset_clears_history(validator):
    validator.validate([position()])
    validator.reset()
    assert validator.tracked_vehicles == 0
