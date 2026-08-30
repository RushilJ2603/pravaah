"""P0.1 acceptance gate (SOLUTION.md section 31).

Gate: "a model missing `provenance` raises ValidationError".

The tests below also lock in the invariants that the rest of the system relies
on being structurally impossible to violate -- above all the rule that a missing
occupancy is UNKNOWN and never EMPTY (SOLUTION.md section 12.4 rule 3).
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from pravaah.config import available_cities, load_city
from pravaah.contracts.api import (
    CrowdForecast,
    Leg,
    Quantiles,
    RankedOption,
    ScoreTerms,
)
from pravaah.contracts.events import (
    OccupancyClass,
    OccupancyObservation,
    StopPassageEvent,
    VehiclePositionEvent,
)
from pravaah.contracts.provenance import Provenance, SourceType

NOW = datetime(2026, 8, 28, 14, 3, 43, tzinfo=UTC)


def prov(source_type: SourceType = SourceType.PUBLIC_FEED) -> Provenance:
    return Provenance(
        source_type=source_type,
        source_name="mbta_cdn",
        source_timestamp=NOW,
        ingest_timestamp=NOW,
        quality_score=0.96,
    )


# --------------------------------------------------------------------------
# The gate itself: provenance is mandatory everywhere.
# --------------------------------------------------------------------------


def test_vehicle_position_requires_provenance():
    with pytest.raises(ValidationError):
        VehiclePositionEvent(
            city_id="mbta",
            agency_id="MBTA",
            vehicle_id="y2075",
            ts=NOW,
            lat=42.364510,
            lon=-71.113419,
        )


def test_occupancy_observation_requires_provenance():
    with pytest.raises(ValidationError):
        OccupancyObservation(
            city_id="mbta",
            vehicle_id="y2075",
            ts=NOW,
            occupancy_class=OccupancyClass.FULL,
            confidence=0.9,
        )


def test_stop_passage_requires_provenance():
    with pytest.raises(ValidationError):
        StopPassageEvent(
            city_id="mbta",
            vehicle_id="y2075",
            trip_id="76789790",
            stop_id="1064",
            stop_sequence=12,
            arrival_ts=NOW,
        )


def test_valid_vehicle_position_round_trips():
    ev = VehiclePositionEvent(
        city_id="mbta",
        agency_id="MBTA",
        vehicle_id="y2075",
        trip_id="76789790",
        route_id="64",
        direction_id=0,
        ts=NOW,
        lat=42.364510,
        lon=-71.113419,
        bearing=270.0,
        stop_id="1064",
        current_stop_sequence=12,
        provenance=prov(),
    )
    assert ev.speed_mps is None, "adapters must not populate raw feed speed"
    assert VehiclePositionEvent.model_validate_json(ev.model_dump_json()) == ev


# --------------------------------------------------------------------------
# Unknown occupancy is never empty occupancy.
# --------------------------------------------------------------------------


def test_unknown_is_distinct_from_empty():
    assert OccupancyClass.UNKNOWN is not OccupancyClass.EMPTY
    assert not OccupancyClass.UNKNOWN.is_known
    assert OccupancyClass.EMPTY.is_known
    assert OccupancyClass.UNKNOWN.ordinal is None
    assert OccupancyClass.EMPTY.ordinal == 0


def test_occupancy_ladder_is_monotonic():
    ladder = [
        OccupancyClass.EMPTY,
        OccupancyClass.MANY_SEATS_AVAILABLE,
        OccupancyClass.FEW_SEATS_AVAILABLE,
        OccupancyClass.STANDING_ROOM_ONLY,
        OccupancyClass.CRUSHED_STANDING_ROOM_ONLY,
        OccupancyClass.FULL,
    ]
    ordinals = [c.ordinal for c in ladder]
    assert ordinals == sorted(ordinals)


def test_empty_occupancy_observation_is_rejected():
    """An observation asserting nothing must not be storable as an implicit 'empty'."""
    with pytest.raises(ValidationError):
        OccupancyObservation(
            city_id="mbta",
            vehicle_id="y2075",
            ts=NOW,
            confidence=0.5,
            provenance=prov(),
        )


def test_onboard_may_not_exceed_capacity():
    with pytest.raises(ValidationError):
        OccupancyObservation(
            city_id="mbta",
            vehicle_id="y2075",
            ts=NOW,
            onboard=80,
            capacity=60,
            confidence=0.9,
            provenance=prov(SourceType.APC),
        )


def test_crowd_forecast_unknown_carries_no_zeros():
    fc = CrowdForecast.unknown(
        trip_id="76789790",
        target_stop_id="1190",
        target_time=NOW,
        model_version="crowd_gbdt_mbta_2026_08_v1",
        feature_ts=NOW,
    )
    assert fc.occupancy is None
    assert fc.occupancy_class is OccupancyClass.UNKNOWN
    assert fc.is_fallback
    assert '"occupancy":null' in fc.model_dump_json().replace(" ", "")


def test_known_class_without_quantiles_is_rejected():
    with pytest.raises(ValidationError):
        CrowdForecast(
            trip_id="t",
            target_stop_id="s",
            target_time=NOW,
            occupancy=None,
            occupancy_class=OccupancyClass.FULL,
            model_version="v1",
            feature_ts=NOW,
        )


# --------------------------------------------------------------------------
# Uncertainty and explainability are structural, not optional.
# --------------------------------------------------------------------------


def test_crossing_quantiles_are_rejected():
    with pytest.raises(ValidationError):
        Quantiles(p10=0.9, p50=0.5, p90=0.95)


def test_quantile_spread_drives_uncertainty_penalty():
    assert Quantiles(p10=0.68, p50=0.84, p90=0.95).spread == pytest.approx(0.27)


def test_ranked_option_requires_reasons():
    """Reason coverage is an acceptance criterion (SOLUTION.md section 21)."""
    with pytest.raises(ValidationError):
        RankedOption(
            candidate_id="c1",
            rank=1,
            legs=[Leg(mode="BUS", route_id="22")],
            travel_time_s=2340,
            crowd_at_boarding=CrowdForecast.unknown("t", "s", NOW, "v1", NOW),
            score=0.41,
            score_terms=ScoreTerms(
                travel=0.18,
                wait=0.06,
                transfer=0.0,
                crowd=0.09,
                delay=0.05,
                uncertainty=0.03,
                walk=0.0,
            ),
            reasons=[],
            data_freshness_s=18,
        )


def test_score_terms_dominant_explains_the_ranking():
    terms = ScoreTerms(
        travel=0.18,
        wait=0.06,
        transfer=0.0,
        crowd=0.09,
        delay=0.05,
        uncertainty=0.03,
        walk=0.0,
    )
    assert terms.total == pytest.approx(0.41)
    assert [name for name, _ in terms.dominant(2)] == ["travel", "crowd"]


# --------------------------------------------------------------------------
# Provenance semantics.
# --------------------------------------------------------------------------


def test_simulated_data_is_excluded_from_production_training():
    assert not prov(SourceType.SIMULATED).usable_for_production_training
    assert prov(SourceType.SIMULATED).is_simulated
    assert prov(SourceType.REAL_OPERATOR).usable_for_production_training
    assert prov(SourceType.CROWDSOURCED).usable_for_production_training is False


# --------------------------------------------------------------------------
# City profiles.
# --------------------------------------------------------------------------


def test_both_city_profiles_load():
    assert set(available_cities()) == {"mbta", "delhi"}


def test_mbta_has_operator_occupancy_and_delhi_does_not():
    """The reason MBTA is the development substrate (SOLUTION.md ADR-08)."""
    mbta = load_city("mbta")
    delhi = load_city("delhi")
    assert mbta.has_operator_occupancy
    assert not delhi.has_operator_occupancy
    assert mbta.occupancy.coverage_estimate == pytest.approx(0.688)


def test_city_bounds_reject_foreign_positions():
    mbta = load_city("mbta")
    delhi = load_city("delhi")
    assert mbta.bounds.contains(42.364510, -71.113419)
    assert not mbta.bounds.contains(28.61, 77.23)
    assert delhi.bounds.contains(28.61, 77.23)
    assert not delhi.bounds.contains(42.364510, -71.113419)
