"""Shared application resources.

Connections are opened once at startup and reused, rather than per request. A
new Postgres connection costs more than the whole query budget for the endpoints
in Slice A, and section 4.2 sets p95 < 2.5 s for far heavier work than this.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from ..config import CityProfile, Settings, active_city, load_settings
from ..models.registry import ServingForecaster, load_serving_forecaster
from ..state.redis_state import LatestOccupancyState, LatestVehicleState

log = logging.getLogger(__name__)


@dataclass
class AppResources:
    """Everything the request handlers need, resolved once."""

    settings: Settings
    city: CityProfile
    redis: object | None = None
    db_pool: object | None = None
    forecaster: ServingForecaster | None = None

    @property
    def state(self) -> LatestVehicleState:
        if self.redis is None:
            raise RuntimeError("redis is not connected")
        return LatestVehicleState(self.redis, self.city.city_id)

    @property
    def occupancy(self) -> LatestOccupancyState:
        if self.redis is None:
            raise RuntimeError("redis is not connected")
        return LatestOccupancyState(self.redis, self.city.city_id)

    def database_ok(self) -> bool:
        if self.db_pool is None:
            return False
        try:
            with self.db_pool.connection() as conn, conn.cursor() as cur:
                cur.execute("SELECT 1")
                return cur.fetchone()[0] == 1
        except Exception:  # noqa: BLE001 -- health checks report, never raise
            return False

    def redis_ok(self) -> bool:
        if self.redis is None:
            return False
        try:
            return bool(self.redis.ping())
        except Exception:  # noqa: BLE001
            return False

    def close(self) -> None:
        if self.redis is not None:
            try:
                self.redis.close()
            except Exception:  # noqa: BLE001
                pass
        if self.db_pool is not None:
            try:
                self.db_pool.close()
            except Exception:  # noqa: BLE001
                pass


def build_resources() -> AppResources:
    """Connect to Redis and Postgres, tolerating either being unavailable.

    A missing dependency degrades the affected endpoints and is reported by
    `/v1/health`; it does not prevent the process from starting. Section 16.1
    requires graceful degradation, and a server that refuses to boot cannot tell
    anyone what is wrong.
    """
    settings = load_settings()
    resources = AppResources(settings=settings, city=active_city())

    # The forecast table is small and immutable; load it once. If it is missing
    # the forecast endpoints report UNKNOWN rather than failing the whole app.
    models_dir = Path("config/models")
    if not models_dir.exists():
        models_dir = Path(__file__).resolve().parents[3] / "config/models"
    try:
        resources.forecaster = load_serving_forecaster(
            models_dir, resources.city.capacity.default_bus_capacity
        )
        log.info("loaded crowd forecast %s", resources.forecaster.model_version)
    except Exception as exc:  # noqa: BLE001
        log.warning("crowd forecast unavailable: %s", exc)

    try:
        import redis as redis_lib

        client = redis_lib.Redis.from_url(settings.redis_url, socket_connect_timeout=3)
        client.ping()
        resources.redis = client
    except Exception as exc:  # noqa: BLE001
        log.warning("redis unavailable at startup: %s", exc)

    try:
        from psycopg_pool import ConnectionPool

        # 30s, not 5s: the first connection can be slow when the database runs
        # in a VM behind a port forward, and a pool that gives up at startup
        # leaves every schedule endpoint returning 503 for the process lifetime.
        pool = ConnectionPool(
            settings.database_dsn, min_size=1, max_size=4, timeout=30, open=True
        )
        pool.wait(timeout=30)
        resources.db_pool = pool
    except Exception as exc:  # noqa: BLE001
        log.warning("database unavailable at startup: %s", exc)

    return resources


def now() -> datetime:
    """Single source of the current time, so tests can reason about freshness."""
    return datetime.now(UTC)
