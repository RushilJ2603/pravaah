"""Position validation and derived speed.

Implements SOLUTION.md section 6.4 and section 28.4.

The feed is not trustworthy on its own. GPS spoofs, outliers and stale entries
are named threats (section 15.2), and a bad position does not announce itself --
it quietly corrupts segment travel times and every ETA built on them. So each
position is checked against the city's bounds, against physics, and against what
we already saw from that vehicle.

Three outcomes, deliberately distinct:

* **accepted** -- usable, with `speed_mps` derived from the previous position.
* **rejected** -- discarded, always with a machine-readable reason. Nothing is
  dropped silently.
* **stale** -- accepted but flagged. Section 16.1 requires degraded data to stay
  visible rather than disappear, so staleness is a label, never a rejection.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ..config import CityProfile
from ..contracts.events import VehiclePositionEvent

log = logging.getLogger(__name__)

EARTH_RADIUS_M = 6_371_008.8

#: Beyond this gap two positions say nothing about speed: the vehicle could have
#: gone anywhere in between, so the derived value would be meaningless.
MAX_SPEED_WINDOW_S = 300.0


class RejectionReason(str, Enum):
    OUT_OF_BOUNDS = "OUT_OF_BOUNDS"
    IMPOSSIBLE_SPEED = "IMPOSSIBLE_SPEED"
    DUPLICATE = "DUPLICATE"
    NULL_ISLAND = "NULL_ISLAND"


@dataclass(frozen=True)
class Rejection:
    vehicle_id: str
    reason: RejectionReason
    detail: str


@dataclass
class ValidationResult:
    accepted: list[VehiclePositionEvent] = field(default_factory=list)
    rejected: list[Rejection] = field(default_factory=list)
    stale: list[str] = field(default_factory=list)

    @property
    def rejection_rate(self) -> float:
        total = len(self.accepted) + len(self.rejected)
        return len(self.rejected) / total if total else 0.0

    def reasons(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for rejection in self.rejected:
            counts[rejection.reason.value] = counts.get(rejection.reason.value, 0) + 1
        return counts


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in metres."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def derive_speed(
    previous: VehiclePositionEvent, current: VehiclePositionEvent
) -> float | None:
    """Great-circle distance over elapsed time, in m/s (SOLUTION.md section 28.4).

    Returns None when the pair cannot support a speed estimate: no elapsed time,
    or a gap so long the vehicle's path between the two points is unknowable.

    This exists because the raw GTFS-RT `speed` field is populated on ~9.8% of
    MBTA rows (section 6.2.1) and is therefore unusable as a feature.
    """
    elapsed = (current.ts - previous.ts).total_seconds()
    if elapsed <= 0 or elapsed > MAX_SPEED_WINDOW_S:
        return None
    distance = haversine_m(previous.lat, previous.lon, current.lat, current.lon)
    return distance / elapsed


class PositionValidator:
    """Stateful validator: remembers the last accepted position per vehicle.

    Held per city because the plausibility limits are city-specific
    (`config/cities/*.toml`), and because two cities' vehicle ids may collide.
    """

    def __init__(self, city: CityProfile) -> None:
        self.city = city
        self._last: dict[str, VehiclePositionEvent] = {}

    def reset(self) -> None:
        self._last.clear()

    @property
    def tracked_vehicles(self) -> int:
        return len(self._last)

    def validate(
        self, events: list[VehiclePositionEvent], now: datetime | None = None
    ) -> ValidationResult:
        """Validate a batch, filling `speed_mps` on everything accepted."""
        result = ValidationResult()

        for event in events:
            rejection = self._check(event)
            if rejection is not None:
                result.rejected.append(rejection)
                continue

            previous = self._last.get(event.vehicle_id)
            speed = derive_speed(previous, event) if previous else None

            if speed is not None and speed > self.city.validation.max_plausible_speed_mps:
                result.rejected.append(
                    Rejection(
                        vehicle_id=event.vehicle_id,
                        reason=RejectionReason.IMPOSSIBLE_SPEED,
                        detail=(
                            f"{speed:.1f} m/s over "
                            f"{(event.ts - previous.ts).total_seconds():.0f}s exceeds "
                            f"{self.city.validation.max_plausible_speed_mps} m/s"
                        ),
                    )
                )
                continue

            accepted = event.model_copy(update={"speed_mps": speed})
            self._last[event.vehicle_id] = accepted
            result.accepted.append(accepted)

            if now is not None and self.city.is_stale(accepted.ts, now):
                result.stale.append(accepted.vehicle_id)

        if result.rejected:
            log.info(
                "validated %d, rejected %d %s",
                len(result.accepted),
                len(result.rejected),
                result.reasons(),
            )
        return result

    def _check(self, event: VehiclePositionEvent) -> Rejection | None:
        # (0, 0) is in the Gulf of Guinea and is what a feed emits when it means
        # "no fix". It would pass a naive bounds check for a city spanning zero.
        if event.lat == 0.0 and event.lon == 0.0:
            return Rejection(
                event.vehicle_id, RejectionReason.NULL_ISLAND, "position is (0, 0)"
            )

        if not self.city.bounds.contains(event.lat, event.lon):
            return Rejection(
                event.vehicle_id,
                RejectionReason.OUT_OF_BOUNDS,
                f"({event.lat:.5f}, {event.lon:.5f}) outside {self.city.city_id}",
            )

        previous = self._last.get(event.vehicle_id)
        if previous is not None and event.ts <= previous.ts:
            # Feeds re-serve the same reading between updates. Re-accepting it
            # would fabricate a zero-speed sample and inflate dwell time.
            return Rejection(
                event.vehicle_id,
                RejectionReason.DUPLICATE,
                f"ts {event.ts.isoformat()} not newer than {previous.ts.isoformat()}",
            )

        return None
