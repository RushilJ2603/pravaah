"""P0.4 acceptance gate, full-corpus portion (SOLUTION.md section 31).

Gate: "Full CSV corpus converts to Parquet; TripUpdates row count drops
materially after dedup; peak RSS stays under 1 GB."

This runs against the real ~1.3 GB recording and takes minutes. It skips when
the corpus is absent (it is git-ignored). Run it with:

    python -m pytest tests/integration/test_convert_corpus.py -q -s

Note: the recorder may still be appending to these files. That is safe -- the
reader stops at whatever EOF it sees on open -- but it means row counts are a
floor, not a fixed number, so the assertions below are all inequalities.
"""

from __future__ import annotations

import ctypes
import sys
from pathlib import Path

import pyarrow.parquet as pq
import pytest

from pravaah.config import PROJECT_ROOT
from pravaah.ingest.convert import csv_to_parquet

VP_CSV = PROJECT_ROOT / "data" / "mbta_vehicle_positions.csv"
TU_CSV = PROJECT_ROOT / "data" / "mbta_trip_updates.csv"

#: SOLUTION.md section 31 P0.4: "peak RSS stays under 1 GB".
MEMORY_BUDGET_BYTES = 1 << 30


def peak_rss_bytes() -> int | None:
    """Peak working set of this process, or None if it cannot be measured."""
    if sys.platform == "win32":

        class _Counters(ctypes.Structure):
            _fields_ = [
                ("cb", ctypes.c_ulong),
                ("PageFaultCount", ctypes.c_ulong),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        counters = _Counters()
        counters.cb = ctypes.sizeof(_Counters)
        handle = ctypes.windll.kernel32.GetCurrentProcess()  # type: ignore[attr-defined]
        ok = ctypes.windll.psapi.GetProcessMemoryInfo(  # type: ignore[attr-defined]
            handle, ctypes.byref(counters), counters.cb
        )
        return int(counters.PeakWorkingSetSize) if ok else None

    try:
        import resource

        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # Linux reports kilobytes, macOS reports bytes.
        return peak if sys.platform == "darwin" else peak * 1024
    except Exception:
        return None


def gb(value: int) -> str:
    return f"{value / (1 << 30):.2f} GB"


requires_tu = pytest.mark.skipif(not TU_CSV.exists(), reason="trip updates corpus absent")
requires_vp = pytest.mark.skipif(not VP_CSV.exists(), reason="vehicle positions corpus absent")


@requires_tu
def test_trip_updates_corpus_converts_and_shrinks(tmp_path: Path):
    """The headline of P0.4: the 864 MB of near-duplicate rows collapses."""
    before = peak_rss_bytes()
    stats = csv_to_parquet(TU_CSV, tmp_path, "tu", clean=True)
    after = peak_rss_bytes()

    print(f"\n  {stats}")
    print(f"  csv on disk:     {gb(TU_CSV.stat().st_size)}")
    parquet_bytes = sum(p.stat().st_size for p in stats.partitions)
    print(f"  parquet on disk: {gb(parquet_bytes)}")
    if after is not None:
        print(f"  peak rss:        {gb(after)}")

    assert stats.rows_read > 4_000_000, "corpus smaller than expected"
    assert stats.partitions, "no partitions written"

    # "Drops materially after dedup". Each poll re-emits the whole future
    # stop-time table, so the great majority of rows are repeats.
    assert stats.dedup_ratio > 0.5, (
        f"only {stats.dedup_ratio:.1%} of rows were duplicates; "
        "expected the majority, since polls re-emit the same table"
    )
    assert (
        stats.rows_written + stats.duplicates_dropped + stats.rows_malformed
        == stats.rows_read
    )

    # The point of the exercise: the result is far smaller than the CSV.
    assert parquet_bytes < TU_CSV.stat().st_size / 4

    if before is not None and after is not None:
        assert after < MEMORY_BUDGET_BYTES, (
            f"peak RSS {gb(after)} breaches the {gb(MEMORY_BUDGET_BYTES)} budget"
        )


@requires_tu
def test_trip_updates_parquet_is_readable_and_deduplicated(tmp_path: Path):
    """Verify the written data, not just the counters that produced it."""
    stats = csv_to_parquet(TU_CSV, tmp_path, "tu", clean=True)

    # Read one partition back and confirm the dedup key is unique within it.
    table = pq.read_table(stats.partitions[0])
    frame = table.to_pandas()
    key = ["trip_id", "stop_id", "stop_sequence", "arrival_time", "departure_time"]
    assert not frame[key].duplicated().any(), "duplicate keys survived into Parquet"
    assert frame["stop_id"].dtype == object, "stop_id lost its text type"

    total = sum(pq.read_metadata(p).num_rows for p in stats.partitions)
    assert total == stats.rows_written


@requires_vp
def test_vehicle_positions_corpus_converts_within_budget(tmp_path: Path):
    """Positions are never deduplicated, so this is purely a streaming test."""
    stats = csv_to_parquet(VP_CSV, tmp_path, "vp", clean=True)
    peak = peak_rss_bytes()

    print(f"\n  {stats}")
    parquet_bytes = sum(p.stat().st_size for p in stats.partitions)
    print(f"  csv on disk:     {gb(VP_CSV.stat().st_size)}")
    print(f"  parquet on disk: {gb(parquet_bytes)}")
    if peak is not None:
        print(f"  peak rss:        {gb(peak)}")

    assert stats.rows_read > 1_000_000
    assert stats.duplicates_dropped == 0, "position rows must never be deduplicated"
    assert stats.rows_written + stats.rows_malformed == stats.rows_read
    assert parquet_bytes < VP_CSV.stat().st_size

    if peak is not None:
        assert peak < MEMORY_BUDGET_BYTES, (
            f"peak RSS {gb(peak)} breaches the {gb(MEMORY_BUDGET_BYTES)} budget"
        )
