"""Slice A.1 acceptance gate (SOLUTION.md section 31).

Gate: "A live poll produces valid VehiclePositionEvents; zero records lack
provenance; speed_mps is left None (section 28.4)."

The live half is in tests/integration/test_mbta_live.py. Here the decoder is
driven with synthetic protobuf, so every branch of the mapping -- including the
ones a live feed rarely exercises -- is provable offline and deterministically.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from google.transit import gtfs_realtime_pb2 as rt

from pravaah.adapters.gtfs_rt import GTFSRealtimeAdapter, occupancy_from_name
from pravaah.adapters.mbta import MBTAAdapter, build
from pravaah.config import load_city
from pravaah.contracts.events import OccupancyClass, VehicleStopStatus
from pravaah.contracts.provenance import SourceType

INGEST = datetime(2026, 8, 28, 14, 4, 0, tzinfo=UTC)
OBSERVED = 1787925808  # epoch seconds inside the recording window


@pytest.fixture
def adapter() -> MBTAAdapter:
    return build(load_city("mbta"))


def feed(
    *,
    vehicle_id: str = "y2075",
    trip_id: str | None = "76789790",
    route_id: str = "64",
    lat: float = 42.364510,
    lon: float = -71.113419,
    occupancy: str | None = "MANY_SEATS_AVAILABLE",
    occupancy_pct: int | None = None,
    bearing: float | None = 270.0,
    speed: float | None = 11.5,
    stop_id: str | None = "1064",
    timestamp: int | None = OBSERVED,
    header_ts: int = 1787925822,
    with_position: bool = True,
) -> bytes:
    """Build a one-entity VehiclePositions payload."""
    message = rt.FeedMessage()
    message.header.gtfs_realtime_version = "2.0"
    message.header.timestamp = header_ts

    entity = message.entity.add()
    entity.id = "e1"
    vehicle = entity.vehicle
    vehicle.vehicle.id = vehicle_id
    if trip_id is not None:
        vehicle.trip.trip_id = trip_id
    vehicle.trip.route_id = route_id
    vehicle.trip.direction_id = 0
    if with_position:
        vehicle.position.latitude = lat
        vehicle.position.longitude = lon
        if bearing is not None:
            vehicle.position.bearing = bearing
        if speed is not None:
            vehicle.position.speed = speed
    if stop_id is not None:
        vehicle.stop_id = stop_id
    vehicle.current_stop_sequence = 12
    vehicle.current_status = rt.VehiclePosition.IN_TRANSIT_TO
    if occupancy is not None:
        vehicle.occupancy_status = rt.VehiclePosition.OccupancyStatus.Value(occupancy)
    if occupancy_pct is not None:
        vehicle.occupancy_percentage = occupancy_pct
    if timestamp is not None:
        vehicle.timestamp = timestamp
    return message.SerializeToString()


# --------------------------------------------------------------------------
# The gate.
# --------------------------------------------------------------------------


def test_decodes_a_valid_position(adapter):
    snapshot = adapter.decode_vehicle_positions(feed(), ingest_ts=INGEST)

    assert len(snapshot.positions) == 1
    event = snapshot.positions[0]
    assert event.vehicle_id == "y2075"
    assert event.trip_id == "76789790"
    assert event.route_id == "64"
    assert event.city_id == "mbta"
    assert event.agency_id == "MBTA"
    assert event.lat == pytest.approx(42.364510, abs=1e-5)
    assert event.current_status is VehicleStopStatus.IN_TRANSIT_TO
    assert event.ts == datetime.fromtimestamp(OBSERVED, tz=UTC)
    assert not snapshot.skipped


def test_every_event_carries_provenance(adapter):
    """The gate: zero records lack provenance."""
    snapshot = adapter.decode_vehicle_positions(feed(), ingest_ts=INGEST)

    for event in [*snapshot.positions, *snapshot.occupancies]:
        assert event.provenance is not None
        assert event.provenance.source_name == "mbta_cdn"
        assert event.provenance.ingest_timestamp == INGEST
        assert 0.0 <= event.provenance.quality_score <= 1.0
        assert event.provenance.raw_payload_ref == snapshot.payload_sha256


def test_speed_is_never_taken_from_the_feed(adapter):
    """Section 28.4: the raw speed field is populated on ~9.8% of MBTA rows, so
    speed is derived from consecutive positions instead. A pass-through here
    would produce a feature present for one row in ten."""
    snapshot = adapter.decode_vehicle_positions(feed(speed=11.5), ingest_ts=INGEST)
    assert snapshot.positions[0].speed_mps is None


def test_payload_hash_is_recorded_for_audit(adapter):
    raw = feed()
    snapshot = adapter.decode_vehicle_positions(raw, ingest_ts=INGEST)
    assert snapshot.payload_sha256 == adapter.sha256(raw)
    assert len(snapshot.payload_sha256) == 64


# --------------------------------------------------------------------------
# Occupancy: unknown is never empty.
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("EMPTY", OccupancyClass.EMPTY),
        ("MANY_SEATS_AVAILABLE", OccupancyClass.MANY_SEATS_AVAILABLE),
        ("FEW_SEATS_AVAILABLE", OccupancyClass.FEW_SEATS_AVAILABLE),
        ("STANDING_ROOM_ONLY", OccupancyClass.STANDING_ROOM_ONLY),
        ("CRUSHED_STANDING_ROOM_ONLY", OccupancyClass.CRUSHED_STANDING_ROOM_ONLY),
        ("FULL", OccupancyClass.FULL),
        ("NOT_ACCEPTING_PASSENGERS", OccupancyClass.NOT_ACCEPTING_PASSENGERS),
        ("NO_DATA_AVAILABLE", OccupancyClass.UNKNOWN),
        ("NOT_BOARDABLE", OccupancyClass.UNKNOWN),
        (None, OccupancyClass.UNKNOWN),
        ("SOMETHING_NEW", OccupancyClass.UNKNOWN),
    ],
)
def test_occupancy_mapping(name, expected):
    assert occupancy_from_name(name) is expected


def test_no_data_available_is_not_empty():
    """The distinction the whole product rests on (section 12.4 rule 3)."""
    assert occupancy_from_name("NO_DATA_AVAILABLE") is not OccupancyClass.EMPTY
    assert occupancy_from_name(None) is not OccupancyClass.EMPTY


def test_vehicle_reporting_nothing_yields_no_occupancy_row(adapter):
    """A vehicle that reported no crowding contributes no evidence.

    Emitting an UNKNOWN observation would pad the record with rows asserting
    nothing -- which OccupancyObservation rejects by design (section 26.2).
    """
    snapshot = adapter.decode_vehicle_positions(
        feed(occupancy=None), ingest_ts=INGEST
    )
    assert len(snapshot.positions) == 1
    assert snapshot.occupancies == []
    assert snapshot.occupancy_coverage == 0.0


def test_reported_empty_vehicle_does_yield_a_row(adapter):
    """EMPTY is real information and must survive, unlike an absent reading."""
    snapshot = adapter.decode_vehicle_positions(feed(occupancy="EMPTY"), ingest_ts=INGEST)
    assert len(snapshot.occupancies) == 1
    assert snapshot.occupancies[0].occupancy_class is OccupancyClass.EMPTY
    assert snapshot.occupancy_coverage == 1.0


def test_occupancy_is_tagged_as_operator_reported(adapter):
    """MBTA occupancy is the operator's own report, not our inference (section 6.5)."""
    snapshot = adapter.decode_vehicle_positions(feed(), ingest_ts=INGEST)
    provenance = snapshot.occupancies[0].provenance
    assert provenance.source_type is SourceType.REAL_OPERATOR
    assert provenance.usable_for_production_training


def test_position_is_tagged_as_public_feed(adapter):
    snapshot = adapter.decode_vehicle_positions(feed(), ingest_ts=INGEST)
    assert snapshot.positions[0].provenance.source_type is SourceType.PUBLIC_FEED


def test_occupancy_percentage_becomes_a_ratio(adapter):
    snapshot = adapter.decode_vehicle_positions(
        feed(occupancy="FEW_SEATS_AVAILABLE", occupancy_pct=74), ingest_ts=INGEST
    )
    assert snapshot.occupancies[0].occupancy_ratio == pytest.approx(0.74)


def test_occupancy_percentage_above_100_is_clamped(adapter):
    """A crush-loaded vehicle can report over 100%; the contract caps ratios at 1."""
    snapshot = adapter.decode_vehicle_positions(
        feed(occupancy="FULL", occupancy_pct=127), ingest_ts=INGEST
    )
    assert snapshot.occupancies[0].occupancy_ratio == 1.0


# --------------------------------------------------------------------------
# Malformed and partial entities.
# --------------------------------------------------------------------------


def test_entity_without_position_is_skipped_with_a_reason(adapter):
    snapshot = adapter.decode_vehicle_positions(
        feed(with_position=False), ingest_ts=INGEST
    )
    assert snapshot.positions == []
    assert len(snapshot.skipped) == 1
    assert "no position" in snapshot.skipped[0]


def test_missing_vehicle_timestamp_falls_back_to_the_feed_header(adapter):
    snapshot = adapter.decode_vehicle_positions(
        feed(timestamp=None, header_ts=1787925822), ingest_ts=INGEST
    )
    event = snapshot.positions[0]
    assert event.ts == datetime.fromtimestamp(1787925822, tz=UTC)
    # The substitution must be visible, not silent.
    assert event.provenance.quality_score < 1.0


def test_missing_trip_id_lowers_the_quality_score(adapter):
    with_trip = adapter.decode_vehicle_positions(feed(), ingest_ts=INGEST)
    without = adapter.decode_vehicle_positions(feed(trip_id=None), ingest_ts=INGEST)

    assert without.positions[0].trip_id is None
    assert (
        without.positions[0].provenance.quality_score
        < with_trip.positions[0].provenance.quality_score
    )


def test_stale_observation_lowers_the_quality_score(adapter):
    """Freshness is a first-class signal (section 16.1), so age must be visible."""
    fresh = adapter.decode_vehicle_positions(feed(), ingest_ts=INGEST)
    stale = adapter.decode_vehicle_positions(
        feed(), ingest_ts=datetime(2026, 8, 28, 15, 0, 0, tzinfo=UTC)
    )
    assert (
        stale.positions[0].provenance.quality_score
        < fresh.positions[0].provenance.quality_score
    )


def test_bearing_is_normalised(adapter):
    snapshot = adapter.decode_vehicle_positions(feed(bearing=360.0), ingest_ts=INGEST)
    assert snapshot.positions[0].bearing == pytest.approx(0.0)


def test_empty_feed_decodes_to_an_empty_snapshot(adapter):
    message = rt.FeedMessage()
    message.header.gtfs_realtime_version = "2.0"
    message.header.timestamp = 1787925822

    snapshot = adapter.decode_vehicle_positions(message.SerializeToString(), ingest_ts=INGEST)
    assert snapshot.positions == []
    assert snapshot.occupancy_coverage == 0.0


# --------------------------------------------------------------------------
# City isolation (section 25 layout rules).
# --------------------------------------------------------------------------


def test_adapter_is_driven_by_the_city_profile(adapter):
    assert adapter.city.city_id == "mbta"
    assert adapter.city.feeds.vehicle_positions.endswith("VehiclePositions.pb")
    assert adapter.city.feeds.requires_api_key is False


def test_generic_adapter_works_for_any_city():
    """A city with a standard feed needs no subclass -- only a profile."""
    generic = GTFSRealtimeAdapter(load_city("delhi"))
    assert generic.source_name == "delhi_gtfsrt"

    snapshot = generic.decode_vehicle_positions(
        feed(lat=28.61, lon=77.23), ingest_ts=INGEST
    )
    assert snapshot.positions[0].city_id == "delhi"
    assert snapshot.positions[0].agency_id == "DTC"


def test_capacity_fallback_distinguishes_rail_from_bus(adapter):
    assert adapter.capacity_for("Red") == adapter.city.capacity.default_rail_capacity
    assert adapter.capacity_for("CR-Worcester") == adapter.city.capacity.default_rail_capacity
    assert adapter.capacity_for("64") == adapter.city.capacity.default_bus_capacity
    assert adapter.capacity_for(None) == adapter.city.capacity.default_bus_capacity
