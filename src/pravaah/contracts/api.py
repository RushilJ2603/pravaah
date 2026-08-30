"""API-facing contracts.

Implements SOLUTION.md section 26.3 and section 29.

Response invariants these types enforce structurally (SOLUTION.md section 12.4):
  - uncertainty is always exposed as quantiles, never a bare point estimate;
  - a missing crowd forecast serializes as class UNKNOWN with a null quantile
    block, never as zeros;
  - every ranked option carries reason codes -- an empty `reasons` list is
    rejected, because reason coverage is an acceptance criterion (section 21).
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .events import OccupancyClass


class PreferenceProfile(str, Enum):
    """The four passenger preference profiles (SOLUTION.md section 10.2)."""

    FASTEST = "fastest"
    LEAST_CROWDED = "least_crowded"
    MOST_RELIABLE = "most_reliable"
    BALANCED = "balanced"


class Quantiles(BaseModel):
    """A predictive distribution summarised at three points.

    Quantiles must be non-crossing: p10 <= p50 <= p90. A model that emits
    crossing quantiles is misconfigured, and silently sorting them would hide
    that, so it is an error.
    """

    model_config = ConfigDict(frozen=True)

    p10: float
    p50: float
    p90: float

    @model_validator(mode="after")
    def _assert_non_crossing(self) -> Quantiles:
        if not (self.p10 <= self.p50 <= self.p90):
            raise ValueError(
                f"crossing quantiles: p10={self.p10} p50={self.p50} p90={self.p90}"
            )
        return self

    @property
    def spread(self) -> float:
        """p90 - p10. The uncertainty penalty in ranking is built on this."""
        return self.p90 - self.p10


class CrowdForecast(BaseModel):
    """Predicted occupancy for one trip at one future stop.

    `occupancy` is None exactly when `occupancy_class` is UNKNOWN -- the two
    together are how "we do not know" is transmitted without ever looking like
    "empty".
    """

    # `model_version` is fixed by SOLUTION.md 17.2/26.3; the protected
    # namespace yields to the spec rather than the field being renamed.
    model_config = ConfigDict(frozen=True, protected_namespaces=())

    trip_id: str
    target_stop_id: str
    target_time: datetime

    occupancy: Quantiles | None = None
    occupancy_class: OccupancyClass = OccupancyClass.UNKNOWN

    model_version: str = Field(min_length=1)
    feature_ts: datetime
    is_fallback: bool = False

    @model_validator(mode="after")
    def _assert_unknown_is_consistent(self) -> CrowdForecast:
        if self.occupancy is None and self.occupancy_class.is_known:
            raise ValueError(
                "a known occupancy_class requires quantiles; "
                "use UNKNOWN when there is no forecast"
            )
        if self.occupancy is not None and not self.occupancy_class.is_known:
            raise ValueError("quantiles present but occupancy_class is UNKNOWN")
        return self

    @classmethod
    def unknown(
        cls,
        trip_id: str,
        target_stop_id: str,
        target_time: datetime,
        model_version: str,
        feature_ts: datetime,
    ) -> CrowdForecast:
        """The explicit 'no forecast available' response.

        Exists so that callers have something correct to return, rather than
        being tempted to fill in zeros.
        """
        return cls(
            trip_id=trip_id,
            target_stop_id=target_stop_id,
            target_time=target_time,
            occupancy=None,
            occupancy_class=OccupancyClass.UNKNOWN,
            model_version=model_version,
            feature_ts=feature_ts,
            is_fallback=True,
        )


class EtaForecast(BaseModel):
    """Predicted arrival time distribution at a stop."""

    model_config = ConfigDict(frozen=True, protected_namespaces=())

    trip_id: str
    target_stop_id: str
    arrival: Quantiles  # epoch seconds, so the quantile ordering is meaningful
    model_version: str = Field(min_length=1)
    feature_ts: datetime
    is_fallback: bool = False


class ScoreTerms(BaseModel):
    """Every weighted contribution to a candidate's generalized cost.

    Stored on the recommendation row as JSONB (SOLUTION.md section 27) so a
    ranking can always be explained after the fact.
    """

    model_config = ConfigDict(frozen=True)

    travel: float
    wait: float
    transfer: float
    crowd: float
    delay: float
    uncertainty: float
    walk: float

    @property
    def total(self) -> float:
        return (
            self.travel
            + self.wait
            + self.transfer
            + self.crowd
            + self.delay
            + self.uncertainty
            + self.walk
        )

    def dominant(self, n: int = 3) -> list[tuple[str, float]]:
        """The n largest terms, for generating reason codes."""
        items = self.model_dump().items()
        return sorted(items, key=lambda kv: kv[1], reverse=True)[:n]


class Leg(BaseModel):
    """One vehicle or walking leg of an itinerary."""

    model_config = ConfigDict(frozen=True)

    mode: str
    route_id: str | None = None
    trip_id: str | None = None
    board_stop_id: str | None = None
    alight_stop_id: str | None = None
    board_time: datetime | None = None
    alight_time: datetime | None = None
    walk_distance_m: int | None = Field(default=None, ge=0)


class RankedOption(BaseModel):
    """One ranked itinerary as returned by GET /v1/plan."""

    model_config = ConfigDict(frozen=True)

    candidate_id: str
    rank: int = Field(ge=1)
    legs: list[Leg] = Field(min_length=1)
    travel_time_s: int = Field(gt=0)

    crowd_at_boarding: CrowdForecast
    eta: EtaForecast | None = None
    delay_risk_p_gt_10min: float | None = Field(default=None, ge=0.0, le=1.0)

    score: float
    score_terms: ScoreTerms
    reasons: list[str] = Field(min_length=1)

    data_freshness_s: int = Field(ge=0)
    is_fallback: bool = False


class DepartureAdvice(BaseModel):
    """"Leave N minutes later" advice (SOLUTION.md section 10.4)."""

    model_config = ConfigDict(frozen=True)

    recommended_shift_min: int = Field(ge=0)
    reason: str = Field(min_length=1)
    score_improvement: float


class PlanResponse(BaseModel):
    """Full GET /v1/plan response (SOLUTION.md section 29.1)."""

    model_config = ConfigDict(frozen=True)

    request_id: UUID
    generated_at: datetime
    city_id: str
    feed_version_id: int
    preference: PreferenceProfile
    options: list[RankedOption]
    departure_advice: DepartureAdvice | None = None


class ErrorCode(str, Enum):
    NO_ROUTE_FOUND = "NO_ROUTE_FOUND"
    INVALID_COORDINATES = "INVALID_COORDINATES"
    OUT_OF_SERVICE_AREA = "OUT_OF_SERVICE_AREA"
    FEED_UNAVAILABLE = "FEED_UNAVAILABLE"
    RATE_LIMITED = "RATE_LIMITED"
    INTERNAL = "INTERNAL"


class ErrorBody(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: ErrorCode
    message: str
    request_id: UUID | None = None


class ErrorResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    error: ErrorBody
