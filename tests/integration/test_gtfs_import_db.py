"""P0.3 acceptance gate, database half (SOLUTION.md section 31).

Gate: "Re-import returns the same feed_version_id."

Requires the compose stack:

    docker compose up -d

These tests skip -- they do not fail -- when the database is unreachable, so
the unit suite stays runnable on a laptop with Docker stopped. They must be run
before P0 is called complete.
"""

from __future__ import annotations

import pytest

from pravaah.config import PROJECT_ROOT, load_city, load_settings
from pravaah.ingest.gtfs_import import import_gtfs

MBTA_ZIP = PROJECT_ROOT / "data" / "mbta_gtfs.zip"

psycopg = pytest.importorskip("psycopg", reason="psycopg not installed")


@pytest.fixture(scope="module")
def conn():
    """A connection to the compose database, or a skip."""
    try:
        c = psycopg.connect(load_settings().database_dsn, connect_timeout=3)
    except Exception as exc:  # noqa: BLE001 -- any failure means "not available"
        pytest.skip(f"database unreachable ({exc}); run: docker compose up -d")
    yield c
    c.close()


@pytest.fixture
def clean_feed_versions(conn):
    """Remove test feed versions before and after. Cascades to all child tables."""

    def _purge():
        with conn.cursor() as cur:
            cur.execute("DELETE FROM feed_version WHERE city_id = 'mbta'")
        conn.commit()

    _purge()
    yield
    _purge()


def test_migrations_created_the_expected_schema(conn):
    """P0.2 gate: migrations apply cleanly from empty."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT extname FROM pg_extension WHERE extname IN ('postgis','timescaledb')"
        )
        assert {r[0] for r in cur.fetchall()} == {"postgis", "timescaledb"}

        cur.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
        )
        tables = {r[0] for r in cur.fetchall()}
        assert {
            "feed_version",
            "stop",
            "route",
            "trip",
            "stop_time",
            "vehicle_position",
            "occupancy_observation",
            "stop_passage",
            "segment_travel_time",
            "forecast",
            "recommendation",
            "feedback",
        } <= tables

        cur.execute("SELECT hypertable_name FROM timescaledb_information.hypertables")
        assert {
            "vehicle_position",
            "occupancy_observation",
            "stop_passage",
            "segment_travel_time",
        } <= {r[0] for r in cur.fetchall()}


@pytest.mark.skipif(not MBTA_ZIP.exists(), reason="data/mbta_gtfs.zip absent")
def test_import_is_idempotent_by_feed_hash(conn, clean_feed_versions):
    """The gate: re-importing the same ZIP returns the same feed_version_id."""
    city = load_city("mbta")

    first = import_gtfs(MBTA_ZIP, city, conn)
    assert not first.already_imported
    assert first.feed_version_id is not None
    assert first.routes == 399
    assert first.stops == 10_297
    assert first.trips == 89_080
    assert first.stop_times == 2_221_062

    second = import_gtfs(MBTA_ZIP, city, conn)
    assert second.already_imported
    assert second.feed_version_id == first.feed_version_id

    # And the no-op wrote nothing.
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM feed_version WHERE city_id = 'mbta'")
        assert cur.fetchone()[0] == 1
        cur.execute(
            "SELECT count(*) FROM stop_time WHERE feed_version_id = %s",
            (first.feed_version_id,),
        )
        assert cur.fetchone()[0] == 2_221_062


@pytest.mark.skipif(not MBTA_ZIP.exists(), reason="data/mbta_gtfs.zip absent")
def test_overnight_times_survive_the_round_trip(conn, clean_feed_versions):
    """Seconds past service midnight may exceed 86400 (section 27)."""
    fv = import_gtfs(MBTA_ZIP, load_city("mbta"), conn).feed_version_id
    with conn.cursor() as cur:
        cur.execute(
            "SELECT max(departure_seconds) FROM stop_time WHERE feed_version_id = %s",
            (fv,),
        )
        assert cur.fetchone()[0] > 86_400, "overnight trips were wrapped or dropped"
