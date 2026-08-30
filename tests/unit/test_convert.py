"""P0.4 acceptance gate, small-input portion (SOLUTION.md section 31).

Gate: "Full CSV corpus converts to Parquet; TripUpdates row count drops
materially after dedup; peak RSS stays under 1 GB."

The full-corpus half needs the 1.3 GB of recorded CSV and runs for minutes, so
it lives in tests/integration/test_convert_corpus.py. What is proven here is the
behaviour that must hold regardless of input size: the dedup key is exactly the
one the document fixes, partitioning follows ingest date, id columns survive as
text, and an absent occupancy stays absent.
"""

from __future__ import annotations

import pandas as pd
import pyarrow.parquet as pq
import pytest

from pravaah.ingest.convert import (
    MALFORMED_ROW_LIMIT,
    TU_DEDUP_KEY,
    CorruptCaptureError,
    csv_to_parquet,
)

VP_HEADER = (
    "ingest_ts,feed_ts,agency,vehicle_id,trip_id,route_id,direction_id,lat,lon,"
    "bearing,speed,stop_id,current_stop_sequence,current_status,occupancy_status,"
    "occupancy_pct,vehicle_ts,source_type\n"
)
TU_HEADER = (
    "ingest_ts,agency,trip_id,route_id,stop_id,stop_sequence,arrival_time,"
    "arrival_delay,departure_time,departure_delay,schedule_relationship\n"
)


def vp_row(ts: str, vehicle: str, occupancy: str = "MANY_SEATS_AVAILABLE") -> str:
    return (
        f"{ts},1787925822,mbta,{vehicle},76789790,64,0,42.364510,-71.113419,"
        f"270.0,,1064,12,IN_TRANSIT_TO,{occupancy},0,1787925808,PUBLIC_FEED\n"
    )


def tu_row(ts: str, trip: str, stop: str, seq: int, arrival: int) -> str:
    return (
        f"{ts},mbta,{trip},64,{stop},{seq},{arrival},0,{arrival},0,SCHEDULED\n"
    )


def read_all(paths) -> pd.DataFrame:
    return pd.concat([pq.read_table(p).to_pandas() for p in paths], ignore_index=True)


# --------------------------------------------------------------------------
# Vehicle positions: no dedup, partitioned by ingest date.
# --------------------------------------------------------------------------


def test_vp_converts_and_partitions_by_ingest_date(tmp_path):
    csv = tmp_path / "vp.csv"
    csv.write_text(
        VP_HEADER
        + vp_row("2026-08-28T14:03:43.164287+00:00", "y1")
        + vp_row("2026-08-28T23:59:59.000000+00:00", "y2")
        + vp_row("2026-08-29T00:00:01.000000+00:00", "y3"),
        encoding="utf-8",
    )
    stats = csv_to_parquet(csv, tmp_path / "out", "vp")

    assert stats.rows_read == 3
    assert stats.rows_written == 3
    assert stats.duplicates_dropped == 0
    assert {p.parent.name for p in stats.partitions} == {
        "date=2026-08-28",
        "date=2026-08-29",
    }


def test_vp_keeps_identical_rows(tmp_path):
    """Position rows are never deduplicated: a stationary vehicle legitimately
    reports the same position repeatedly, and dropping those would destroy dwell
    time, which is a feature (SOLUTION.md section 9.2)."""
    csv = tmp_path / "vp.csv"
    row = vp_row("2026-08-28T14:03:43.164287+00:00", "y1")
    csv.write_text(VP_HEADER + row + row + row, encoding="utf-8")

    stats = csv_to_parquet(csv, tmp_path / "out", "vp")
    assert stats.rows_written == 3
    assert stats.duplicates_dropped == 0


def test_id_columns_stay_text(tmp_path):
    """stop_id "1064" typed as an integer would silently fail to join against
    the GTFS stop_id text column and return zero rows rather than an error."""
    csv = tmp_path / "vp.csv"
    csv.write_text(
        VP_HEADER + vp_row("2026-08-28T14:03:43.164287+00:00", "y1"), encoding="utf-8"
    )
    df = read_all(csv_to_parquet(csv, tmp_path / "out", "vp").partitions)

    for column in ("stop_id", "trip_id", "route_id", "vehicle_id", "agency"):
        assert df[column].dtype == object, f"{column} lost its text type"
    assert df["stop_id"].iloc[0] == "1064"


def test_absent_occupancy_stays_absent(tmp_path):
    """An empty occupancy_status becomes null, never "EMPTY" and never 0.

    The archive preserves what was recorded; mapping null to
    OccupancyClass.UNKNOWN is the adapter's job (SOLUTION.md section 26.2).
    What must never happen is a missing reading turning into an empty bus.
    """
    csv = tmp_path / "vp.csv"
    csv.write_text(
        VP_HEADER
        + vp_row("2026-08-28T14:03:43.164287+00:00", "y1", occupancy="")
        + vp_row("2026-08-28T14:03:43.164287+00:00", "y2", occupancy="FULL"),
        encoding="utf-8",
    )
    df = read_all(csv_to_parquet(csv, tmp_path / "out", "vp").partitions)

    absent = df[df["vehicle_id"] == "y1"]["occupancy_status"].iloc[0]
    assert absent is None or pd.isna(absent)
    assert absent != "EMPTY"
    assert absent != 0
    assert df[df["vehicle_id"] == "y2"]["occupancy_status"].iloc[0] == "FULL"


# --------------------------------------------------------------------------
# Trip updates: deduplication on the documented key.
# --------------------------------------------------------------------------


def test_dedup_key_is_the_documented_one():
    assert TU_DEDUP_KEY == (
        "trip_id",
        "stop_id",
        "stop_sequence",
        "arrival_time",
        "departure_time",
    )


def test_tu_drops_rows_repeated_across_polls(tmp_path):
    """Consecutive TripUpdates polls re-emit the same future stop-time table.

    This is the whole 864 MB problem (SOLUTION.md section 22): three polls of an
    unchanged two-stop trip must collapse to two rows.
    """
    csv = tmp_path / "tu.csv"
    poll = tu_row("{ts}", "T1", "S1", 1, 1787926126) + tu_row("{ts}", "T1", "S2", 2, 1787926211)
    csv.write_text(
        TU_HEADER
        + poll.format(ts="2026-08-28T14:08:24.723100+00:00")
        + poll.format(ts="2026-08-28T14:13:24.723100+00:00")
        + poll.format(ts="2026-08-28T14:18:24.723100+00:00"),
        encoding="utf-8",
    )
    stats = csv_to_parquet(csv, tmp_path / "out", "tu")

    assert stats.rows_read == 6
    assert stats.rows_written == 2
    assert stats.duplicates_dropped == 4
    assert stats.dedup_ratio == pytest.approx(2 / 3)


def test_tu_keeps_a_row_whose_prediction_changed(tmp_path):
    """A revised arrival time is new information, not a duplicate.

    arrival_time is part of the key precisely so that a delay update survives.
    """
    csv = tmp_path / "tu.csv"
    csv.write_text(
        TU_HEADER
        + tu_row("2026-08-28T14:08:24.723100+00:00", "T1", "S1", 1, 1787926126)
        + tu_row("2026-08-28T14:13:24.723100+00:00", "T1", "S1", 1, 1787926126)
        + tu_row("2026-08-28T14:18:24.723100+00:00", "T1", "S1", 1, 1787926500),
        encoding="utf-8",
    )
    stats = csv_to_parquet(csv, tmp_path / "out", "tu")

    assert stats.rows_written == 2, "the revised arrival time must be kept"
    assert stats.duplicates_dropped == 1

    arrivals = sorted(read_all(stats.partitions)["arrival_time"].tolist())
    assert arrivals == [1787926126, 1787926500]


def test_tu_dedups_across_chunk_boundaries(tmp_path):
    """Duplicates must be caught even when the repeats land in different blocks.

    A tiny block_size forces multiple chunks, which is what a 864 MB file does
    naturally. Per-chunk dedup would silently pass the small tests and fail here.
    """
    csv = tmp_path / "tu.csv"
    rows = "".join(
        tu_row(f"2026-08-28T14:{m:02d}:00.000000+00:00", "T1", "S1", 1, 1787926126)
        for m in range(40)
    )
    csv.write_text(TU_HEADER + rows, encoding="utf-8")

    stats = csv_to_parquet(csv, tmp_path / "out", "tu", block_size=1 << 10)
    assert stats.rows_read == 40
    assert stats.rows_written == 1
    assert stats.duplicates_dropped == 39


def test_rerun_with_clean_does_not_double_count(tmp_path):
    csv = tmp_path / "tu.csv"
    csv.write_text(
        TU_HEADER + tu_row("2026-08-28T14:08:24.723100+00:00", "T1", "S1", 1, 1787926126),
        encoding="utf-8",
    )
    out = tmp_path / "out"

    first = csv_to_parquet(csv, out, "tu")
    second = csv_to_parquet(csv, out, "tu", clean=True)

    assert len(first.partitions) == len(second.partitions) == 1
    assert len(read_all(second.partitions)) == 1


def test_conversion_is_deterministic(tmp_path):
    """Byte-identical output across runs -- the offline replay demo depends on it."""
    csv = tmp_path / "tu.csv"
    csv.write_text(
        TU_HEADER
        + tu_row("2026-08-28T14:08:24.723100+00:00", "T1", "S1", 1, 1787926126)
        + tu_row("2026-08-28T14:13:24.723100+00:00", "T1", "S2", 2, 1787926211)
        + tu_row("2026-08-28T14:18:24.723100+00:00", "T1", "S1", 1, 1787926126),
        encoding="utf-8",
    )
    a = csv_to_parquet(csv, tmp_path / "a", "tu")
    b = csv_to_parquet(csv, tmp_path / "b", "tu")

    assert a.rows_written == b.rows_written == 2
    assert a.partitions[0].read_bytes() == b.partitions[0].read_bytes()


def test_missing_csv_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        csv_to_parquet(tmp_path / "nope.csv", tmp_path / "out", "vp")


# --------------------------------------------------------------------------
# Malformed rows (SOLUTION.md section 28.2).
# --------------------------------------------------------------------------


def test_torn_final_line_is_skipped_not_fatal(tmp_path):
    """The recorder appends continuously, so the last line is usually mid-write.

    That single torn row must not fail the conversion -- otherwise the converter
    could never run while recording is live, which is always.
    """
    csv = tmp_path / "vp.csv"
    good = "".join(
        vp_row("2026-08-28T14:03:43.164287+00:00", f"y{i}") for i in range(2000)
    )
    csv.write_text(VP_HEADER + good + "2026-08-28T14:03:44.000000+00:00,17879", encoding="utf-8")

    stats = csv_to_parquet(csv, tmp_path / "out", "vp")

    assert stats.rows_written == 2000
    assert stats.rows_malformed == 1
    assert stats.malformed_ratio < MALFORMED_ROW_LIMIT


def test_widespread_tearing_fails_the_conversion(tmp_path):
    """Many torn rows mean the capture is broken -- most often two recorders
    appending to one file -- and must not be reported as a faithful archive."""
    csv = tmp_path / "vp.csv"
    rows = "".join(
        vp_row("2026-08-28T14:03:43.164287+00:00", f"y{i}") for i in range(100)
    )
    torn = "".join(
        f"4618,3,STOPPED_AT,MANY_SEATS_AVAILABLE,20,178792973{i % 10},PUBLIC_FEED\n"
        for i in range(20)
    )
    csv.write_text(VP_HEADER + rows + torn, encoding="utf-8")

    with pytest.raises(CorruptCaptureError, match="exceed the"):
        csv_to_parquet(csv, tmp_path / "out", "vp")


def test_torn_row_with_the_right_column_count_is_rejected(tmp_path):
    """The nastiest corruption: a fragment that happens to have 18 commas.

    Its ingest_ts is a piece of a timestamp like ":46.962563", which the CSV
    parser accepts and which would otherwise become a partition directory of
    that name. It must be counted as malformed, not written.
    """
    csv = tmp_path / "vp.csv"
    good = "".join(
        vp_row("2026-08-28T14:03:43.164287+00:00", f"y{i}") for i in range(2000)
    )
    torn = vp_row(":46.962563", "y-torn")
    csv.write_text(VP_HEADER + good + torn, encoding="utf-8")

    stats = csv_to_parquet(csv, tmp_path / "out", "vp")

    assert stats.rows_written == 2000
    assert stats.rows_malformed == 1
    assert {p.parent.name for p in stats.partitions} == {"date=2026-08-28"}
    assert stats.rows_written + stats.rows_malformed == stats.rows_read


def test_malformed_limit_matches_the_document(tmp_path):
    assert MALFORMED_ROW_LIMIT == 0.001
