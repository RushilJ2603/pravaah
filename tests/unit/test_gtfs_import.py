"""P0.3 acceptance gate, database-free portion (SOLUTION.md section 31).

Gate: "Importing data/mbta_gtfs.zip yields exactly 399 routes, 10,297 stops,
89,080 trips, 2,221,062 stop-times. Re-import returns the same feed_version_id."

The exact-count half runs here against the real ZIP with no database, because
the counts are a property of the feed and should be checkable without
infrastructure. The idempotence half needs a live database and lives in
tests/integration/test_gtfs_import_db.py.
"""

from __future__ import annotations

import zipfile

import pytest

from pravaah.config import PROJECT_ROOT, load_city
from pravaah.ingest.gtfs_import import (
    GTFSValidationError,
    count_entities,
    parse_gtfs_time,
    read_feed_info,
    sha256_of,
    validate,
)

MBTA_ZIP = PROJECT_ROOT / "data" / "mbta_gtfs.zip"

#: The numbers quoted in SOLUTION.md sections 6.2.1 and 31. If the feed is ever
#: replaced these must be re-derived and the document updated -- that is the
#: point of asserting them.
#:
#: Note the distinction the document draws: `stops` here is the RAW ROW COUNT of
#: stops.txt. Only 9,630 of those rows are importable; the other 667 are
#: coordinate-less location_type=3 pathway nodes (section 6.2.1). The database
#: gate in tests/integration asserts 9,630.
EXPECTED = {
    "routes": 399,
    "stops": 10_297,
    "trips": 89_080,
    "stop_times": 2_221_062,
}

#: Rows in stops.txt that carry no coordinates, all location_type=3.
EXPECTED_COORDINATELESS_STOPS = 667
EXPECTED_ROUTABLE_STOPS = EXPECTED["stops"] - EXPECTED_COORDINATELESS_STOPS

requires_feed = pytest.mark.skipif(
    not MBTA_ZIP.exists(), reason="data/mbta_gtfs.zip absent (it is git-ignored)"
)


# --------------------------------------------------------------------------
# GTFS time parsing: the >24:00 rule.
# --------------------------------------------------------------------------


def test_parse_ordinary_time():
    assert parse_gtfs_time("07:42:00") == 27720


def test_parse_time_past_midnight_is_not_wrapped():
    """GTFS allows hours >= 24 for trips continuing past midnight.

    Wrapping 25:10:00 to 01:10 would silently move a trip back 24 hours, which
    is why section 27 forbids storing these as TIME.
    """
    assert parse_gtfs_time("25:10:00") == 90_600
    assert parse_gtfs_time("28:00:00") == 100_800


def test_parse_empty_time_is_none():
    assert parse_gtfs_time("") is None
    assert parse_gtfs_time("   ") is None


@pytest.mark.parametrize("bad", ["7:42", "07:42:00:00", "aa:bb:cc", "07:99:00"])
def test_malformed_times_are_rejected(bad):
    with pytest.raises(GTFSValidationError):
        parse_gtfs_time(bad)


# --------------------------------------------------------------------------
# The exact-count gate.
# --------------------------------------------------------------------------


@requires_feed
def test_mbta_feed_has_the_documented_entity_counts():
    counts = count_entities(MBTA_ZIP)
    assert counts.routes == EXPECTED["routes"]
    assert counts.stops == EXPECTED["stops"]
    assert counts.trips == EXPECTED["trips"]
    assert counts.stop_times == EXPECTED["stop_times"]


@requires_feed
def test_coordinateless_stops_are_pathway_nodes_never_served_by_a_trip():
    """Why 667 stop rows are excluded at import (SOLUTION.md section 6.2.1).

    This asserts the *justification*, not just the number. If a future feed ever
    omits coordinates on a stop that trips actually serve, this fails loudly --
    which is the moment to revisit the exclusion rather than lose a real stop.
    """
    import csv
    import io as _io
    import zipfile as _zipfile

    with _zipfile.ZipFile(MBTA_ZIP) as zf:
        with zf.open("stops.txt") as fh:
            rows = list(csv.DictReader(_io.TextIOWrapper(fh, "utf-8-sig", newline="")))
        coordinateless = {
            r["stop_id"] for r in rows if not r.get("stop_lat") or not r.get("stop_lon")
        }
        assert len(coordinateless) == EXPECTED_COORDINATELESS_STOPS

        # Every one of them is a generic node (location_type 3).
        assert {
            r.get("location_type") for r in rows if r["stop_id"] in coordinateless
        } == {"3"}

        # And no trip serves any of them, so excluding them loses no service.
        with zf.open("stop_times.txt") as fh:
            served = {
                r["stop_id"]
                for r in csv.DictReader(_io.TextIOWrapper(fh, "utf-8-sig", newline=""))
            }
    assert coordinateless.isdisjoint(served)


@requires_feed
def test_mbta_feed_passes_validation_against_its_own_city_profile():
    validate(MBTA_ZIP, load_city("mbta"))


@requires_feed
def test_mbta_feed_fails_validation_against_the_wrong_city():
    """Bounds checking is what catches an operator pointing at the wrong feed."""
    with pytest.raises(GTFSValidationError, match="outside the delhi bounding box"):
        validate(MBTA_ZIP, load_city("delhi"))


@requires_feed
def test_feed_info_matches_the_recording_window():
    """The static snapshot must cover the period the corpus was recorded in.

    SOLUTION.md section 6.2.1 pins this feed as Summer 2026, valid
    2026-08-12 to 2026-09-05; the corpus recording began 2026-08-28.
    """
    info = read_feed_info(MBTA_ZIP)
    assert info.publisher == "MBTA"
    assert info.valid_from is not None and info.valid_to is not None
    assert info.valid_from.isoformat() == "2026-08-12"
    assert info.valid_to.isoformat() == "2026-09-05"


@requires_feed
def test_feed_hash_is_stable():
    """Idempotence rests on this hash, so it must not depend on read order."""
    assert sha256_of(MBTA_ZIP) == sha256_of(MBTA_ZIP)
    assert len(sha256_of(MBTA_ZIP)) == 64


# --------------------------------------------------------------------------
# Validation rejects broken feeds.
# --------------------------------------------------------------------------


def _make_feed(tmp_path, stops: str, routes: str, trips: str, stop_times: str):
    path = tmp_path / "feed.zip"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("stops.txt", stops)
        zf.writestr("routes.txt", routes)
        zf.writestr("trips.txt", trips)
        zf.writestr("stop_times.txt", stop_times)
    return path


GOOD_STOPS = "stop_id,stop_name,stop_lat,stop_lon\nS1,First,42.36,-71.11\nS2,Second,42.37,-71.12\n"
GOOD_ROUTES = "route_id,route_short_name,route_type\nR1,1,3\n"
GOOD_TRIPS = "trip_id,route_id,service_id,direction_id\nT1,R1,WEEK,0\n"
GOOD_TIMES = (
    "trip_id,stop_sequence,stop_id,arrival_time,departure_time\n"
    "T1,1,S1,07:00:00,07:00:30\n"
    "T1,2,S2,07:10:00,07:10:30\n"
)


def test_minimal_valid_feed_passes(tmp_path):
    feed = _make_feed(tmp_path, GOOD_STOPS, GOOD_ROUTES, GOOD_TRIPS, GOOD_TIMES)
    validate(feed, load_city("mbta"))
    counts = count_entities(feed)
    assert (counts.stops, counts.routes, counts.trips, counts.stop_times) == (2, 1, 1, 2)


def test_missing_required_file_is_rejected(tmp_path):
    path = tmp_path / "feed.zip"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("stops.txt", GOOD_STOPS)
    with pytest.raises(GTFSValidationError, match="missing required GTFS files"):
        validate(path, load_city("mbta"))


def test_stop_time_referencing_unknown_stop_is_rejected(tmp_path):
    bad = GOOD_TIMES + "T1,3,S99,07:20:00,07:20:30\n"
    feed = _make_feed(tmp_path, GOOD_STOPS, GOOD_ROUTES, GOOD_TRIPS, bad)
    with pytest.raises(GTFSValidationError, match="unknown stop"):
        validate(feed, load_city("mbta"))


def test_trip_referencing_unknown_route_is_rejected(tmp_path):
    bad_trips = GOOD_TRIPS + "T2,R99,WEEK,0\n"
    feed = _make_feed(tmp_path, GOOD_STOPS, GOOD_ROUTES, bad_trips, GOOD_TIMES)
    with pytest.raises(GTFSValidationError, match="unknown route"):
        validate(feed, load_city("mbta"))


def test_non_increasing_stop_sequence_is_rejected(tmp_path):
    bad = (
        "trip_id,stop_sequence,stop_id,arrival_time,departure_time\n"
        "T1,2,S1,07:00:00,07:00:30\n"
        "T1,1,S2,07:10:00,07:10:30\n"
    )
    feed = _make_feed(tmp_path, GOOD_STOPS, GOOD_ROUTES, GOOD_TRIPS, bad)
    with pytest.raises(GTFSValidationError, match="stop_sequence not increasing"):
        validate(feed, load_city("mbta"))


def test_duplicate_stop_id_is_rejected(tmp_path):
    dup = GOOD_STOPS + "S1,Duplicate,42.38,-71.13\n"
    feed = _make_feed(tmp_path, dup, GOOD_ROUTES, GOOD_TRIPS, GOOD_TIMES)
    with pytest.raises(GTFSValidationError, match="duplicate stop_id"):
        validate(feed, load_city("mbta"))


def test_overnight_stop_times_are_accepted(tmp_path):
    """A trip crossing midnight must validate, not trip the time parser."""
    overnight = (
        "trip_id,stop_sequence,stop_id,arrival_time,departure_time\n"
        "T1,1,S1,23:50:00,23:50:30\n"
        "T1,2,S2,24:15:00,24:15:30\n"
    )
    feed = _make_feed(tmp_path, GOOD_STOPS, GOOD_ROUTES, GOOD_TRIPS, overnight)
    validate(feed, load_city("mbta"))
