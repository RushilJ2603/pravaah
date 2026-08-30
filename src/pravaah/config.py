"""Settings and city-profile loading.

Implements SOLUTION.md section 30.

City knowledge lives in `config/cities/*.toml` and in `src/pravaah/adapters/`.
Nowhere else. This module is the only thing that reads those files, so the rest
of the codebase gets a `CityProfile` object and never a city name.
"""

from __future__ import annotations

import os
import tomllib
from datetime import datetime
from functools import cache, lru_cache
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .contracts.provenance import SourceType

#: Repository root, resolved from this file's location: src/pravaah/config.py
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "config"
CITIES_DIR = CONFIG_DIR / "cities"


class Bounds(BaseModel):
    """Geographic box. Positions outside it are rejected at validation."""

    model_config = ConfigDict(frozen=True)

    min_lat: float = Field(ge=-90.0, le=90.0)
    max_lat: float = Field(ge=-90.0, le=90.0)
    min_lon: float = Field(ge=-180.0, le=180.0)
    max_lon: float = Field(ge=-180.0, le=180.0)

    @model_validator(mode="after")
    def _assert_ordered(self) -> Bounds:
        if self.min_lat >= self.max_lat or self.min_lon >= self.max_lon:
            raise ValueError("bounds min must be strictly less than max")
        return self

    def contains(self, lat: float, lon: float) -> bool:
        return self.min_lat <= lat <= self.max_lat and self.min_lon <= lon <= self.max_lon


class FeedConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    gtfs_static: str
    vehicle_positions: str
    trip_updates: str = ""
    requires_api_key: bool = False
    poll_interval_s: int = Field(default=20, gt=0)
    trip_update_every: int = Field(default=15, ge=0)


class OccupancyConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_type: SourceType
    available: bool
    coverage_estimate: float = Field(ge=0.0, le=1.0)


class CapacityConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    default_bus_capacity: int = Field(gt=0)
    default_rail_capacity: int = Field(gt=0)


class ValidationConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    max_plausible_speed_mps: float = Field(gt=0.0)
    stale_after_s: int = Field(gt=0)


class CityProfile(BaseModel):
    """Everything city-specific, in one object."""

    model_config = ConfigDict(frozen=True)

    city_id: str = Field(min_length=1)
    agency_id: str = Field(min_length=1)
    timezone: str = Field(min_length=1)
    display_name: str = Field(min_length=1)

    bounds: Bounds
    feeds: FeedConfig
    occupancy: OccupancyConfig
    capacity: CapacityConfig
    validation: ValidationConfig

    @property
    def has_operator_occupancy(self) -> bool:
        """True when the city publishes real crowd labels.

        When False, crowd metrics must be reported as simulator or crowdsourced
        performance, never as real-world accuracy (SOLUTION.md section 2.4).
        """
        return self.occupancy.available and self.occupancy.source_type in (
            SourceType.REAL_OPERATOR,
            SourceType.APC,
            SourceType.AFC,
        )

    def is_stale(self, source_timestamp: datetime, now: datetime) -> bool:
        return (now - source_timestamp).total_seconds() > self.validation.stale_after_s


class PreferenceWeights(BaseModel):
    """Generalized cost weights (SOLUTION.md section 10.2)."""

    model_config = ConfigDict(frozen=True)

    wT: float = Field(ge=0.0)
    wW: float = Field(ge=0.0)
    wX: float = Field(ge=0.0)
    wC: float = Field(ge=0.0)
    wD: float = Field(ge=0.0)
    wU: float = Field(ge=0.0)
    wP: float = Field(ge=0.0)


class DepartureConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    horizons_min: list[int]
    improvement_threshold: float = Field(ge=0.0)
    waiting_disutility_per_min: float = Field(ge=0.0)


class RerouteConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    material_threshold: float = Field(ge=0.0)
    cooldown_s: int = Field(ge=0)


class Settings(BaseModel):
    """Application settings, loaded from config/settings.toml.

    The database DSN and Redis URL may be overridden by the PRAVAAH_DATABASE_DSN
    and PRAVAAH_REDIS_URL environment variables, so secrets never enter the repo.
    """

    model_config = ConfigDict(frozen=True)

    active_city: str
    preferences: dict[str, PreferenceWeights]
    departure: DepartureConfig
    reroute: RerouteConfig
    database_dsn: str
    redis_url: str
    data_dir: Path
    parquet_dir: Path


def _load_toml(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"config file not found: {path}")
    with path.open("rb") as fh:
        return tomllib.load(fh)


@cache
def load_city(city_id: str) -> CityProfile:
    """Load one city profile by id. Cached; profiles are immutable."""
    return CityProfile(**_load_toml(CITIES_DIR / f"{city_id}.toml"))


def available_cities() -> list[str]:
    return sorted(p.stem for p in CITIES_DIR.glob("*.toml"))


@lru_cache(maxsize=1)
def load_settings() -> Settings:
    """Load config/settings.toml, with environment overrides for connections."""
    raw = _load_toml(CONFIG_DIR / "settings.toml")
    return Settings(
        active_city=raw["active_city"],
        preferences={
            name: PreferenceWeights(**w) for name, w in raw["preferences"].items()
        },
        departure=DepartureConfig(**raw["departure"]),
        reroute=RerouteConfig(**raw["reroute"]),
        database_dsn=os.environ.get("PRAVAAH_DATABASE_DSN", raw["database"]["dsn"]),
        redis_url=os.environ.get("PRAVAAH_REDIS_URL", raw["redis"]["url"]),
        data_dir=PROJECT_ROOT / raw["paths"]["data_dir"],
        parquet_dir=PROJECT_ROOT / raw["paths"]["parquet_dir"],
    )


def active_city() -> CityProfile:
    """The city profile named by settings.active_city."""
    return load_city(load_settings().active_city)
