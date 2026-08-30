"""Recorder CSV to date-partitioned Parquet.

Implements SOLUTION.md section 28.2 (ADR-10).

The recorder appends to one flat CSV forever, because flat append is the most
crash-tolerant capture available and must never block on a database. That makes
it a good archive and a poor feature source:

* `mbta_trip_updates.csv` is ~864 MB, and most of it is redundant. Every
  TripUpdates poll re-dumps the whole future stop-time table (~22k rows), so
  consecutive polls are near-identical (SOLUTION.md section 22).
* A single CSV of that size cannot be loaded in one pass on a laptop.

This module fixes both without touching the archive: it streams the CSV in
bounded chunks, deduplicates TripUpdates on the key the document specifies, and
writes date-partitioned Parquet that downstream feature code can scan by day.

    out_dir/kind=<vp|tu>/date=YYYY-MM-DD/part-NNN.parquet

**Fidelity rule.** This is an archive conversion, not a semantic one. Values are
preserved as recorded; an empty `occupancy_status` becomes a Parquet null and is
*not* rewritten to "UNKNOWN" here. Mapping null to `OccupancyClass.UNKNOWN` is
the adapter's job (SOLUTION.md section 26.2). What matters is that a null is
never read as "empty bus" -- see section 12.4 rule 3.
"""

from __future__ import annotations

import argparse
import logging
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import pandas as pd
import pyarrow as pa
import pyarrow.csv as pacsv
import pyarrow.parquet as pq

log = logging.getLogger(__name__)

Kind = Literal["vp", "tu"]

#: Columns that must stay text even though they look numeric. `stop_id` "1064"
#: parsed as an integer would silently fail to join against the GTFS `stop_id`
#: text column, and the join would return zero rows rather than an error.
_ID_COLUMNS = (
    "agency",
    "vehicle_id",
    "trip_id",
    "route_id",
    "stop_id",
    "current_status",
    "occupancy_status",
    "source_type",
    "schedule_relationship",
    "ingest_ts",
)

#: Explicit types. Left to inference, pyarrow would type a column differently
#: between two chunks of the same file and fail the write.
_COLUMN_TYPES: dict[str, pa.DataType] = {
    **{c: pa.string() for c in _ID_COLUMNS},
    "feed_ts": pa.int64(),
    "vehicle_ts": pa.int64(),
    "direction_id": pa.int8(),
    "lat": pa.float64(),
    "lon": pa.float64(),
    "bearing": pa.float32(),
    "speed": pa.float32(),
    "current_stop_sequence": pa.int32(),
    "occupancy_pct": pa.int16(),
    "stop_sequence": pa.int32(),
    "arrival_time": pa.int64(),
    "arrival_delay": pa.int32(),
    "departure_time": pa.int64(),
    "departure_delay": pa.int32(),
}

#: The TripUpdates dedup key, fixed by SOLUTION.md section 28.2.
TU_DEDUP_KEY = ("trip_id", "stop_id", "stop_sequence", "arrival_time", "departure_time")


#: Above this fraction of malformed rows the capture is considered broken and
#: the conversion fails (SOLUTION.md section 28.2).
MALFORMED_ROW_LIMIT = 0.001


class CorruptCaptureError(Exception):
    """Raised when malformed rows exceed MALFORMED_ROW_LIMIT."""


@dataclass
class ConversionStats:
    """What a conversion did. The P0.4 gate reads these."""

    kind: str = ""
    rows_read: int = 0
    rows_written: int = 0
    duplicates_dropped: int = 0
    rows_malformed: int = 0
    partitions: list[Path] = field(default_factory=list)

    @property
    def dedup_ratio(self) -> float:
        """Fraction of input rows discarded as duplicates."""
        return self.duplicates_dropped / self.rows_read if self.rows_read else 0.0

    @property
    def malformed_ratio(self) -> float:
        """Malformed share of all input rows.

        `rows_read` counts every data row encountered, including those the CSV
        parser skipped, so the three outcomes partition the input:
        rows_written + duplicates_dropped + rows_malformed == rows_read.
        """
        return self.rows_malformed / self.rows_read if self.rows_read else 0.0

    def __str__(self) -> str:
        return (
            f"{self.kind}: read {self.rows_read:,}, wrote {self.rows_written:,}, "
            f"dropped {self.duplicates_dropped:,} duplicates "
            f"({self.dedup_ratio:.1%}), skipped {self.rows_malformed:,} malformed "
            f"({self.malformed_ratio:.4%}) across {len(self.partitions)} partition(s)"
        )


def _convert_options(columns: list[str]) -> pacsv.ConvertOptions:
    return pacsv.ConvertOptions(
        column_types={c: t for c, t in _COLUMN_TYPES.items() if c in columns},
        strings_can_be_null=True,
        null_values=[""],
    )


def _next_part_index(partition_dir: Path) -> int:
    """Smallest unused part index, so re-running adds parts instead of clobbering."""
    existing = sorted(partition_dir.glob("part-*.parquet"))
    if not existing:
        return 0
    return max(int(p.stem.split("-")[1]) for p in existing) + 1


class _PartitionWriters:
    """One open ParquetWriter per date, closed together at the end.

    Holding writers open across chunks is what keeps memory flat: each chunk is
    appended as its own row group and released, rather than accumulating a whole
    day in memory before writing.
    """

    def __init__(self, out_dir: Path, kind: str, schema: pa.Schema) -> None:
        self._root = out_dir / f"kind={kind}"
        self._schema = schema
        self._writers: dict[str, pq.ParquetWriter] = {}
        self._paths: list[Path] = []

    def write(self, date: str, table: pa.Table) -> None:
        writer = self._writers.get(date)
        if writer is None:
            partition_dir = self._root / f"date={date}"
            partition_dir.mkdir(parents=True, exist_ok=True)
            path = partition_dir / f"part-{_next_part_index(partition_dir):03d}.parquet"
            writer = pq.ParquetWriter(path, self._schema, compression="zstd")
            self._writers[date] = writer
            self._paths.append(path)
            log.info("opened partition %s", path)
        writer.write_table(table)

    def close(self) -> list[Path]:
        for writer in self._writers.values():
            writer.close()
        return sorted(self._paths)


def csv_to_parquet(
    csv_path: Path,
    out_dir: Path,
    kind: Kind,
    *,
    block_size: int = 64 << 20,
    clean: bool = False,
) -> ConversionStats:
    """Convert an append-only recorder CSV into date-partitioned Parquet.

    Streams the CSV in blocks and never materialises it. For `kind="tu"`,
    deduplicates on TU_DEDUP_KEY across the whole file.

    Args:
        csv_path: The recorder CSV.
        out_dir: Parquet root. Partitions land at
            `out_dir/kind=<kind>/date=YYYY-MM-DD/part-NNN.parquet`.
        kind: "vp" for vehicle positions, "tu" for trip updates.
        block_size: CSV read block in bytes. Trades memory for fewer chunks.
        clean: Remove any existing `kind=<kind>` tree first. Without this a
            re-run adds new part files alongside the old ones, which double-counts.

    Returns:
        ConversionStats with row counts and the partition paths written.

    Note on deduplication: keys are tracked as 64-bit hashes rather than tuples,
    which keeps the seen-set to a few hundred MB on a five-million-row file. At
    that scale the collision probability is around 7e-7 -- a collision would drop
    one extra row, never corrupt one. Exact tuple tracking would cost several GB
    and breach the memory budget in SOLUTION.md section 31.
    """
    if not csv_path.exists():
        raise FileNotFoundError(csv_path)

    root = out_dir / f"kind={kind}"
    if clean and root.exists():
        shutil.rmtree(root)

    stats = ConversionStats(kind=kind)
    seen: set[int] = set()
    writers: _PartitionWriters | None = None

    def skip_malformed(row: pacsv.InvalidRow) -> str:
        """Count and skip a row with the wrong column count.

        A live recorder's CSV routinely ends mid-write, so the final line is
        commonly truncated. Widespread tearing means something worse -- most
        likely more than one process appending to the same file -- and is caught
        by the MALFORMED_ROW_LIMIT check after the read completes.
        """
        stats.rows_read += 1
        stats.rows_malformed += 1
        if stats.rows_malformed <= 5:
            log.warning(
                "skipping malformed row near line %s: %.80s",
                row.number if row.number is not None else "?",
                row.text,
            )
        return "skip"

    parse_options = pacsv.ParseOptions(invalid_row_handler=skip_malformed)

    # Schema sniffing reads the first block, which may itself contain malformed
    # rows. Give that pass a handler that skips without counting, so those rows
    # are not tallied twice once the real pass reaches them.
    reader = pacsv.open_csv(
        csv_path,
        read_options=pacsv.ReadOptions(block_size=block_size),
        parse_options=pacsv.ParseOptions(invalid_row_handler=lambda _row: "skip"),
    )
    columns = reader.schema.names
    reader.close()

    reader = pacsv.open_csv(
        csv_path,
        read_options=pacsv.ReadOptions(block_size=block_size),
        parse_options=parse_options,
        convert_options=_convert_options(columns),
    )
    try:
        for batch in reader:
            if batch.num_rows == 0:
                continue
            stats.rows_read += batch.num_rows
            frame = batch.to_pandas(types_mapper=None)

            frame = _drop_unusable_timestamps(frame, stats)
            if frame.empty:
                continue

            if kind == "tu":
                frame = _drop_duplicates(frame, seen, stats)
                if frame.empty:
                    continue

            # ingest_ts is ISO-8601 UTC, so the date is its first ten characters.
            # Slicing beats parsing five million timestamps just to bucket them.
            dates = frame["ingest_ts"].str.slice(0, 10)

            for date, group in frame.groupby(dates, sort=True):
                table = pa.Table.from_pandas(
                    group, preserve_index=False
                ).cast(_schema_for(columns))
                if writers is None:
                    writers = _PartitionWriters(out_dir, kind, table.schema)
                writers.write(str(date), table)
                stats.rows_written += table.num_rows
    finally:
        reader.close()

    stats.partitions = writers.close() if writers else []

    if stats.malformed_ratio > MALFORMED_ROW_LIMIT:
        raise CorruptCaptureError(
            f"{stats.rows_malformed:,} malformed rows "
            f"({stats.malformed_ratio:.2%}) exceed the "
            f"{MALFORMED_ROW_LIMIT:.1%} limit in {csv_path.name}. A live capture "
            "ends mid-write, so a torn final line is expected; this many means "
            "the capture is broken. Check that only one recorder process is "
            "appending to this file (SOLUTION.md section 28.2)."
        )

    log.info("%s", stats)
    return stats


def _schema_for(columns: list[str]) -> pa.Schema:
    return pa.schema(
        [(c, _COLUMN_TYPES.get(c, pa.string())) for c in columns]
    )


def _drop_unusable_timestamps(
    frame: pd.DataFrame, stats: ConversionStats
) -> pd.DataFrame:
    """Drop rows whose `ingest_ts` is not an ISO-8601 timestamp.

    A torn row does not always have the wrong column count. When two processes
    interleave a write, the surviving fragment can land with exactly the right
    number of commas while its first field holds a piece of a timestamp such as
    ":46.962563". The CSV parser accepts that row, and it then produces a
    partition named `date=:46.962563` -- which on Windows is not even a legal
    directory name.

    These are malformed rows by the definition in SOLUTION.md section 28.2 and are
    counted as such, so widespread tearing still trips MALFORMED_ROW_LIMIT.
    """
    usable = frame["ingest_ts"].str.match(r"^\d{4}-\d{2}-\d{2}T", na=False)
    if usable.all():
        return frame

    rejected = int((~usable).sum())
    stats.rows_malformed += rejected
    if stats.rows_malformed <= 5:
        sample = frame.loc[~usable, "ingest_ts"].head(3).tolist()
        log.warning("dropping %d row(s) with unusable ingest_ts, e.g. %s", rejected, sample)
    return frame[usable.to_numpy()]


def _drop_duplicates(
    frame: pd.DataFrame, seen: set[int], stats: ConversionStats
) -> pd.DataFrame:
    """Drop rows whose dedup key has already been written.

    Hashes the key columns vectorised. `hash_pandas_object` is deterministic
    across runs and processes, so a re-run produces byte-identical output --
    which the offline demo replay in section 19 depends on.
    """
    key = pd.util.hash_pandas_object(frame[list(TU_DEDUP_KEY)], index=False)
    fresh = ~key.isin(seen)
    # Within-chunk repeats survive the isin check, so drop those too.
    fresh &= ~key.duplicated()
    seen.update(key[fresh].tolist())
    dropped = int((~fresh).sum())
    stats.duplicates_dropped += dropped
    return frame[fresh.to_numpy()]


def main(argv: list[str] | None = None) -> int:
    from ..config import load_settings

    settings = load_settings()
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--kind", choices=("vp", "tu"), required=True)
    parser.add_argument("--csv", type=Path, help="defaults to the recorder file for --kind")
    parser.add_argument("--out", type=Path, default=settings.parquet_dir)
    parser.add_argument("--clean", action="store_true", help="remove existing partitions first")
    parser.add_argument("--block-mb", type=int, default=64)
    args = parser.parse_args(argv)

    csv_path = args.csv or settings.data_dir / (
        "mbta_vehicle_positions.csv" if args.kind == "vp" else "mbta_trip_updates.csv"
    )
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    stats = csv_to_parquet(
        csv_path, args.out, args.kind, block_size=args.block_mb << 20, clean=args.clean
    )
    print(stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
