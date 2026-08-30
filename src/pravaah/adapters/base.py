"""Adapter interfaces.

Implements SOLUTION.md section 8 (Realtime Adapter, Occupancy Adapter) and the
layout rule in section 25: **`adapters/` and `config/cities/` are the only places
city knowledge may live.** Everything downstream consumes the canonical contracts
in `pravaah.contracts`, never a city-specific payload.

Fetching and decoding are deliberately separate methods. Decoding is a pure
function of bytes, so the whole mapping can be tested against fixtures without a
network, and a recorded `.pb` frame replays through exactly the same code path as
a live poll -- which is what section 19's offline demo depends on.
"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime

from ..config import CityProfile
from ..contracts.events import OccupancyObservation, VehiclePositionEvent


@dataclass(frozen=True)
class FeedSnapshot:
    """One decoded poll of a realtime feed.

    Attributes:
        feed_timestamp: The feed's own header timestamp -- when the *publisher*
            says this snapshot was true. Distinct from each event's `ts`.
        positions: Canonical vehicle positions.
        occupancies: Occupancy observations extracted from the same payload.
            Empty when the city publishes no occupancy (Delhi, section 6.2.2).
        payload_sha256: Hash of the raw bytes, recorded as `raw_payload_ref` on
            every event's provenance so any observation is traceable to the exact
            upstream payload (section 6.8).
        skipped: Entities that could not form a valid event, with the reason.
    """

    feed_timestamp: datetime
    positions: list[VehiclePositionEvent] = field(default_factory=list)
    occupancies: list[OccupancyObservation] = field(default_factory=list)
    payload_sha256: str = ""
    skipped: list[str] = field(default_factory=list)

    @property
    def occupancy_coverage(self) -> float:
        """Share of positions that came with a known occupancy.

        Measured rather than assumed: section 6.2.1 records ~68.8% for MBTA, and a
        sharp drop is a data-quality signal worth alerting on (section 16.2).
        """
        if not self.positions:
            return 0.0
        return len(self.occupancies) / len(self.positions)


class RealtimeAdapter(ABC):
    """Converts one city's realtime feed into canonical events."""

    def __init__(self, city: CityProfile) -> None:
        self.city = city

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Concrete source identifier recorded in provenance, e.g. "mbta_cdn"."""

    @abstractmethod
    def fetch_vehicle_positions(self, timeout: float = 30.0) -> bytes:
        """Retrieve the raw upstream payload. The only method that does I/O."""

    @abstractmethod
    def decode_vehicle_positions(
        self, raw: bytes, ingest_ts: datetime | None = None
    ) -> FeedSnapshot:
        """Decode raw bytes into canonical events. Pure: no I/O, no clock reads
        beyond the supplied `ingest_ts`."""

    def poll(self, timeout: float = 30.0) -> FeedSnapshot:
        """Fetch and decode in one step. The normal entry point for a worker."""
        raw = self.fetch_vehicle_positions(timeout=timeout)
        return self.decode_vehicle_positions(raw, ingest_ts=datetime.now(UTC))

    @staticmethod
    def sha256(raw: bytes) -> str:
        return hashlib.sha256(raw).hexdigest()
