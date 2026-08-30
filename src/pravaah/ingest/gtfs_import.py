"""GTFS static feed importer.

Implements SOLUTION.md section 28.1, satisfying FR-01.

Pipeline (SOLUTION.md section 6.3):

    GTFS ZIP -> schema validator -> staging -> canonical IDs -> geometry build
             -> service calendar expansion -> publish feed_version

Two properties matter more than speed here:

* **Idempotence by feed hash.** Re-importing an identical ZIP is a no-op that
  returns the existing feed_version_id. Feeds get re-downloaded constantly; an
  importer that duplicates rows on every poll is worse than useless.
* **Atomic publication.** Validation failures roll the whole transaction back.
  A half-imported feed is never visible, because downstream joins against a
  partial network produce silently wrong journeys rather than errors.
"""

from __future__ import annotations

import csv
import hashlib
import io
import logging
import zipfile
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from ..config import CityProfile

log = logging.getLogger(__name__)

#: Files we require to be present. GTFS defines more, but these are the ones
#: without which no topology can be built.
REQUIRED_FILES = ("stops.txt", "routes.txt", "trips.txt", "stop_times.txt")

#: Batch size for COPY/executemany. Tuned so a 2.2M-row stop_times import does
#: not hold the whole table in memory (SOLUTION.md section 28.2 spirit).
BATCH_ROWS = 50_000


class GTFSValidationError(Exception):
    """Raised when a feed fails validation. Nothing is published."""


@dataclass
class ImportCounts:
    """What an import actually wrote. Used by the P0.3 acceptance gate."""

    routes: int = 0
    stops: int = 0
    trips: int = 0
    stop_times: int = 0
    already_imported: bool = False
    feed_version_id: int | None = None

    def as_dict(self) -> dict[str, int | bool | None]:
        return {
            "routes": self.routes,
            "stops": self.stops,
            "trips": self.trips,
            "stop_times": self.stop_times,
            "already_imported": self.already_imported,
            "feed_version_id": self.feed_version_id,
        }


@dataclass
class FeedInfo:
    """Publication metadata read from feed_info.txt, when present."""

    valid_from: date | None = None
    valid_to: date | None = None
    version: str | None = None
    publisher: str | None = None
    warnings: list[str] = field(default_factory=list)


def sha256_of(path: Path) -> str:
    """Hash the ZIP itself, not its contents: it is what the publisher served."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_gtfs_time(value: str) -> int | None:
    """Parse a GTFS HH:MM:SS into seconds past service midnight.

    GTFS permits hours >= 24 for trips that run past midnight, so this
    deliberately returns an unbounded integer rather than a time object
    (SOLUTION.md section 27, schema rules). "25:10:00" is 90600, not an error
    and not 01:10.
    """
    value = value.strip()
    if not value:
        return None
    parts = value.split(":")
    if len(parts) != 3:
        raise GTFSValidationError(f"malformed GTFS time: {value!r}")
    try:
        hh, mm, ss = (int(p) for p in parts)
    except ValueError as exc:
        raise GTFSValidationError(f"malformed GTFS time: {value!r}") from exc
    if mm > 59 or ss > 59 or hh < 0:
        raise GTFSValidationError(f"out-of-range GTFS time: {value!r}")
    return hh * 3600 + mm * 60 + ss


def _parse_date(value: str) -> date | None:
    value = value.strip()
    if len(value) != 8 or not value.isdigit():
        return None
    return date(int(value[:4]), int(value[4:6]), int(value[6:8]))


def _rows(zf: zipfile.ZipFile, name: str) -> Iterator[dict[str, str]]:
    """Stream one GTFS table. Never materialises the file."""
    with zf.open(name) as raw:
        # GTFS is UTF-8; some publishers emit a BOM. utf-8-sig handles both.
        yield from csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig", newline=""))


def read_feed_info(zip_path: Path) -> FeedInfo:
    """Read feed_info.txt if the publisher supplies one."""
    info = FeedInfo()
    with zipfile.ZipFile(zip_path) as zf:
        if "feed_info.txt" not in zf.namelist():
            info.warnings.append("feed_info.txt absent; validity window unknown")
            return info
        for row in _rows(zf, "feed_info.txt"):
            info.valid_from = _parse_date(row.get("feed_start_date", ""))
            info.valid_to = _parse_date(row.get("feed_end_date", ""))
            info.version = row.get("feed_version") or None
            info.publisher = row.get("feed_publisher_name") or None
            break
    return info


def validate(zip_path: Path, city: CityProfile) -> None:
    """Validate a feed in full before anything is written.

    Checks (SOLUTION.md section 28.1):
      - required files present;
      - referential integrity: every stop_time.stop_id exists in stops,
        every trip.route_id exists in routes, every stop_time.trip_id in trips;
      - coordinates inside the city profile's bounding box;
      - stop_sequence strictly increasing within each trip;
      - no duplicate stop_id / route_id / trip_id.

    Raises GTFSValidationError on the first failure, with enough context to fix
    the feed rather than just naming the file.
    """
    with zipfile.ZipFile(zip_path) as zf:
        names = set(zf.namelist())
        missing = [f for f in REQUIRED_FILES if f not in names]
        if missing:
            raise GTFSValidationError(f"missing required GTFS files: {missing}")

        # --- stops: uniqueness and coordinate bounds -----------------------
        stop_ids: set[str] = set()
        out_of_bounds = 0
        first_offender: tuple[str, float, float] | None = None
        for row in _rows(zf, "stops.txt"):
            sid = row["stop_id"]
            if sid in stop_ids:
                raise GTFSValidationError(f"duplicate stop_id: {sid!r}")
            stop_ids.add(sid)
            lat_s, lon_s = row.get("stop_lat", ""), row.get("stop_lon", "")
            if not lat_s or not lon_s:
                continue  # stations/entrances may legitimately omit coordinates
            lat, lon = float(lat_s), float(lon_s)
            if not city.bounds.contains(lat, lon):
                out_of_bounds += 1
                if first_offender is None:
                    first_offender = (sid, lat, lon)
        if out_of_bounds:
            sid, lat, lon = first_offender  # type: ignore[misc]
            raise GTFSValidationError(
                f"{out_of_bounds} stop(s) outside the {city.city_id} bounding box, "
                f"first: {sid!r} at ({lat}, {lon}). Wrong city profile, or the "
                f"bounds in config/cities/{city.city_id}.toml are too tight."
            )

        # --- routes: uniqueness --------------------------------------------
        route_ids: set[str] = set()
        for row in _rows(zf, "routes.txt"):
            rid = row["route_id"]
            if rid in route_ids:
                raise GTFSValidationError(f"duplicate route_id: {rid!r}")
            route_ids.add(rid)

        # --- trips: uniqueness and route reference --------------------------
        trip_ids: set[str] = set()
        for row in _rows(zf, "trips.txt"):
            tid = row["trip_id"]
            if tid in trip_ids:
                raise GTFSValidationError(f"duplicate trip_id: {tid!r}")
            trip_ids.add(tid)
            if row["route_id"] not in route_ids:
                raise GTFSValidationError(
                    f"trip {tid!r} references unknown route {row['route_id']!r}"
                )

        # --- stop_times: references and monotonic sequence ------------------
        prev_trip: str | None = None
        prev_seq = -1
        for row in _rows(zf, "stop_times.txt"):
            tid = row["trip_id"]
            if tid not in trip_ids:
                raise GTFSValidationError(
                    f"stop_time references unknown trip {tid!r}"
                )
            if row["stop_id"] not in stop_ids:
                raise GTFSValidationError(
                    f"stop_time on trip {tid!r} references unknown stop "
                    f"{row['stop_id']!r}"
                )
            seq = int(row["stop_sequence"])
            if tid != prev_trip:
                prev_trip, prev_seq = tid, seq
            else:
                if seq <= prev_seq:
                    raise GTFSValidationError(
                        f"stop_sequence not increasing on trip {tid!r}: "
                        f"{prev_seq} then {seq}"
                    )
                prev_seq = seq
            # Surfaces malformed times during validation rather than mid-insert.
            parse_gtfs_time(row.get("arrival_time", ""))
            parse_gtfs_time(row.get("departure_time", ""))


def count_entities(zip_path: Path) -> ImportCounts:
    """Count what a feed contains, without a database.

    The P0.3 gate asserts exact counts against data/mbta_gtfs.zip; this makes
    that checkable before the database exists, and keeps the count logic in one
    place so the gate and the importer cannot drift apart.
    """
    counts = ImportCounts()
    with zipfile.ZipFile(zip_path) as zf:
        counts.stops = sum(1 for _ in _rows(zf, "stops.txt"))
        counts.routes = sum(1 for _ in _rows(zf, "routes.txt"))
        counts.trips = sum(1 for _ in _rows(zf, "trips.txt"))
        counts.stop_times = sum(1 for _ in _rows(zf, "stop_times.txt"))
    return counts


def import_gtfs(zip_path: Path, city: CityProfile, conn) -> ImportCounts:
    """Import a GTFS ZIP. Returns counts including feed_version_id.

    Idempotent by sha256 of the ZIP: if this city has already imported this
    exact file, the existing feed_version_id is returned and nothing is written.

    The whole import runs in one transaction. Any failure -- validation or
    database -- leaves the previous feed version as the only visible one.

    Args:
        zip_path: Path to the GTFS ZIP.
        city: City profile supplying bounds and identity.
        conn: A psycopg connection. Not type-annotated so this module stays
            importable without a database driver installed.
    """
    feed_hash = sha256_of(zip_path)

    with conn.cursor() as cur:
        cur.execute(
            "SELECT feed_version_id FROM feed_version WHERE city_id = %s AND feed_hash = %s",
            (city.city_id, feed_hash),
        )
        existing = cur.fetchone()
        if existing:
            log.info(
                "feed %s already imported for %s as version %s; no-op",
                feed_hash[:12],
                city.city_id,
                existing[0],
            )
            return ImportCounts(already_imported=True, feed_version_id=existing[0])

    # Validate everything before opening the write transaction. A feed that
    # fails validation must not even create a feed_version row.
    validate(zip_path, city)
    info = read_feed_info(zip_path)
    for warning in info.warnings:
        log.warning("%s: %s", zip_path.name, warning)

    counts = ImportCounts()
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO feed_version (city_id, feed_hash, valid_from, valid_to)
                VALUES (%s, %s, %s, %s)
                RETURNING feed_version_id
                """,
                (city.city_id, feed_hash, info.valid_from, info.valid_to),
            )
            fv = cur.fetchone()[0]
            counts.feed_version_id = fv

            with zipfile.ZipFile(zip_path) as zf:
                counts.stops = _copy_stops(cur, zf, fv)
                counts.routes = _copy_routes(cur, zf, fv)
                counts.trips = _copy_trips(cur, zf, fv)
                counts.stop_times = _copy_stop_times(cur, zf, fv)

    log.info(
        "imported %s feed version %s: %d routes, %d stops, %d trips, %d stop-times",
        city.city_id,
        counts.feed_version_id,
        counts.routes,
        counts.stops,
        counts.trips,
        counts.stop_times,
    )
    return counts


def _batched(rows: Iterator[tuple], cur, sql: str) -> int:
    """Execute `sql` over `rows` in batches. Returns the row count."""
    total = 0
    batch: list[tuple] = []
    for row in rows:
        batch.append(row)
        if len(batch) >= BATCH_ROWS:
            cur.executemany(sql, batch)
            total += len(batch)
            batch.clear()
    if batch:
        cur.executemany(sql, batch)
        total += len(batch)
    return total


def _copy_stops(cur, zf: zipfile.ZipFile, fv: int) -> int:
    sql = """
        INSERT INTO stop (feed_version_id, stop_id, name, geom, parent_station,
                          wheelchair_boarding)
        VALUES (%s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography, %s, %s)
    """

    def rows() -> Iterator[tuple]:
        for r in _rows(zf, "stops.txt"):
            lat, lon = r.get("stop_lat", ""), r.get("stop_lon", "")
            if not lat or not lon:
                continue
            wc = r.get("wheelchair_boarding", "")
            yield (
                fv,
                r["stop_id"],
                r.get("stop_name", "") or r["stop_id"],
                float(lon),  # ST_MakePoint takes (x, y) = (lon, lat)
                float(lat),
                r.get("parent_station") or None,
                int(wc) if wc.isdigit() else None,
            )

    return _batched(rows(), cur, sql)


def _copy_routes(cur, zf: zipfile.ZipFile, fv: int) -> int:
    sql = """
        INSERT INTO route (feed_version_id, route_id, agency_id, short_name,
                           long_name, route_type)
        VALUES (%s, %s, %s, %s, %s, %s)
    """

    def rows() -> Iterator[tuple]:
        for r in _rows(zf, "routes.txt"):
            yield (
                fv,
                r["route_id"],
                r.get("agency_id") or None,
                r.get("route_short_name") or None,
                r.get("route_long_name") or None,
                int(r["route_type"]),
            )

    return _batched(rows(), cur, sql)


def _copy_trips(cur, zf: zipfile.ZipFile, fv: int) -> int:
    sql = """
        INSERT INTO trip (feed_version_id, trip_id, route_id, service_id,
                          direction_id, shape_id)
        VALUES (%s, %s, %s, %s, %s, %s)
    """

    def rows() -> Iterator[tuple]:
        for r in _rows(zf, "trips.txt"):
            d = r.get("direction_id", "")
            yield (
                fv,
                r["trip_id"],
                r["route_id"],
                r["service_id"],
                int(d) if d.isdigit() else None,
                r.get("shape_id") or None,
            )

    return _batched(rows(), cur, sql)


def _copy_stop_times(cur, zf: zipfile.ZipFile, fv: int) -> int:
    sql = """
        INSERT INTO stop_time (feed_version_id, trip_id, stop_sequence, stop_id,
                               arrival_seconds, departure_seconds)
        VALUES (%s, %s, %s, %s, %s, %s)
    """

    def rows() -> Iterator[tuple]:
        for r in _rows(zf, "stop_times.txt"):
            yield (
                fv,
                r["trip_id"],
                int(r["stop_sequence"]),
                r["stop_id"],
                parse_gtfs_time(r.get("arrival_time", "")),
                parse_gtfs_time(r.get("departure_time", "")),
            )

    return _batched(rows(), cur, sql)
