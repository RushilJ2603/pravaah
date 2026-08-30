"""Behavioural board/alight model (SOLUTION.md sections 18.1 and 28.9).

Section 18.1 is explicit that the simulator generates **board and alight events
from behavioural rules**, not random occupancy percentages. That distinction is
the whole point: occupancy here is the running sum of people who got on minus
people who got off, so it moves like a bus load and not like noise, and it is
conserved by construction.

Two sources feed it, and they do different jobs:

* **Shape comes from a fitted calibration profile** -- the load curve along a
  run, measured from a real recorded corpus rather than chosen. That is the only
  thing carried over from the corpus; no place, route or identifier is.
* **Scale comes from the city profile** -- vehicle capacity, peak windows, the
  weekly pattern and a demand multiplier. Delhi routinely runs in a crush range
  the source corpus never recorded, so the upper end of the ladder is set by
  Delhi capacity norms, not transferred.

Every value produced here is synthetic and is emitted with
`source_type=SIMULATED`. Nothing in this module may produce a record without it.
"""

from __future__ import annotations

import logging
import math
import random
from dataclasses import dataclass

from ..contracts.events import OccupancyClass

log = logging.getLogger(__name__)

#: Fallback load curve if no calibration profile is supplied: flat. Used only so
#: the simulator still runs; a flat curve is visibly wrong rather than subtly so.
FLAT_PROFILE = [1.0] * 10


@dataclass(frozen=True)
class VehicleCapacity:
    """Delhi bus capacity.

    ASSUMPTION -- these follow the Urban Bus Specification figures reported for
    a 12m Indian city bus, but the primary MoHUA document was not confirmed when
    this was written. They are marked as assumptions in the city profile and
    must be replaced with sourced values before any claim rests on them.
    """

    seated: int = 35
    #: Comfortable peak load: seated plus normal standing.
    peak: int = 70
    #: Structural "dense crush load" -- the physical maximum, not a comfort level.
    crush: int = 100

    def occupancy_class(self, onboard: int) -> OccupancyClass:
        """Map a headcount onto the GTFS ladder.

        The thresholds are deliberately Delhi's, not the source city's: standing
        is normal here, so `STANDING_ROOM_ONLY` begins as soon as seats run out
        rather than at some fraction of a nominal capacity.
        """
        if onboard <= 0:
            return OccupancyClass.EMPTY
        if onboard <= self.seated * 0.5:
            return OccupancyClass.MANY_SEATS_AVAILABLE
        if onboard < self.seated:
            return OccupancyClass.FEW_SEATS_AVAILABLE
        if onboard < self.peak:
            return OccupancyClass.STANDING_ROOM_ONLY
        if onboard < self.crush:
            return OccupancyClass.CRUSHED_STANDING_ROOM_ONLY
        return OccupancyClass.FULL

    def ratio(self, onboard: int) -> float:
        return round(min(onboard / self.crush, 1.0), 4)


@dataclass(frozen=True)
class DemandProfile:
    """Scale parameters for one city. All Delhi values are ASSUMPTIONS today."""

    #: Multiplier by hour of day, 0-23. Delhi's curve is flatter than a US
    #: commute: heavy all-day ridership with two broad peaks rather than two
    #: sharp ones.
    hourly: list[float]
    capacity: VehicleCapacity
    #: Multiplier by weekday index, 0=Monday. Saturday is a working day for a
    #: large share of Indian commuters, so it is much closer to a weekday than
    #: to Sunday.
    weekly: list[float]
    #: Passengers wanting to board per stop at multiplier 1.0.
    #:
    #: Set so a midday bus runs standing-room and a peak bus reaches crush,
    #: which is the reported Delhi reality (~88% load factor). The source
    #: corpus is a far emptier system -- 87% of its observations were
    #: "many seats available" and it recorded no crush at all -- so this is
    #: the parameter that must NOT be inherited from it. ASSUMPTION.
    base_boardings: float = 16.0

    @staticmethod
    def delhi() -> DemandProfile:
        """Delhi defaults. Every number here is an assumption, not a measurement."""
        # Broad morning (08-10) and evening (17-20) peaks over a high daytime
        # plateau, rather than the sharp bimodal shape of a US commuter system.
        hourly = [
            0.15, 0.08, 0.05, 0.05, 0.10, 0.30, 0.60, 0.85,  # 00-07
            1.35, 1.40, 1.10, 1.00, 1.00, 1.00, 1.00, 1.05,  # 08-15
            1.15, 1.40, 1.45, 1.35, 1.10, 0.80, 0.50, 0.28,  # 16-23
        ]
        weekly = [1.0, 1.0, 1.0, 1.0, 1.0, 0.85, 0.55]
        return DemandProfile(hourly=hourly, capacity=VehicleCapacity(), weekly=weekly)


@dataclass
class TripLoad:
    """The outcome of simulating one vehicle over one run."""

    onboard: list[int]
    boardings: list[int]
    alightings: list[int]

    @property
    def conserved(self) -> bool:
        """Everyone who boarded must have alighted by the terminus."""
        return sum(self.boardings) == sum(self.alightings) and self.onboard[-1] == 0


def simulate_trip(
    stop_count: int,
    hour: int,
    weekday: int,
    profile: DemandProfile,
    load_profile: list[float] | None,
    rng: random.Random,
    route_demand: float = 1.0,
) -> TripLoad:
    """Simulate boardings and alightings across one run.

    Returns the onboard count *after* each stop. Passengers are conserved: the
    terminus forces every remaining passenger off, and the totals must match.
    """
    curve = load_profile or FLAT_PROFILE
    intensity = (
        profile.hourly[hour % 24]
        * profile.weekly[weekday % 7]
        * route_demand
        * profile.base_boardings
    )

    onboard = 0
    onboards: list[int] = []
    boardings: list[int] = []
    alightings: list[int] = []

    for index in range(stop_count):
        position = index / max(stop_count - 1, 1)
        shape = curve[min(int(position * len(curve)), len(curve) - 1)]

        if index == stop_count - 1:
            # Terminus: everyone off. This is what makes conservation exact
            # rather than approximate.
            alight = onboard
            board = 0
        else:
            # Alighting propensity rises along the run -- few people get off near
            # the origin, most get off toward the end.
            alight_share = 0.05 + 0.55 * (position**1.7)
            alight = _binomial(onboard, alight_share, rng)
            # Boarding demand falls as the run progresses past its midpoint,
            # scaled by the fitted load curve.
            want = intensity * shape * (1.25 - 0.85 * position)
            board = max(0, _poisson(max(want, 0.0), rng))

        onboard -= alight
        # Capacity clipping: a full bus leaves people at the stop (section 18.1).
        room = max(0, profile.capacity.crush - onboard)
        board = min(board, room)
        onboard += board

        boardings.append(board)
        alightings.append(alight)
        onboards.append(onboard)

    return TripLoad(onboard=onboards, boardings=boardings, alightings=alightings)


def _poisson(lam: float, rng: random.Random) -> int:
    """Knuth's algorithm. Small lambdas only, which is all we generate."""
    if lam <= 0:
        return 0
    if lam > 60:  # normal approximation, keeps the loop bounded
        return max(0, int(rng.gauss(lam, math.sqrt(lam))))
    target = math.exp(-lam)
    k, p = 0, 1.0
    while True:
        p *= rng.random()
        if p <= target:
            return k
        k += 1


def _binomial(n: int, p: float, rng: random.Random) -> int:
    if n <= 0 or p <= 0:
        return 0
    p = min(p, 1.0)
    return sum(1 for _ in range(n) if rng.random() < p)
