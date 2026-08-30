"""Provenance contract.

Implements SOLUTION.md section 6.8 and section 26.1.

Every observation entering the platform carries provenance. This is what keeps
real, derived and simulated data separable, and it is what stops synthetic
labels from silently contaminating a "real data" evaluation.

A record without provenance is invalid and is rejected at ingress -- never
defaulted. That rule is enforced here by giving `Provenance` no default on any
event model in `events.py`.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class SourceType(str, Enum):
    """Where an observation came from.

    Ordered loosely by trust for occupancy fusion (see SOLUTION.md section 6.5):
    APC and REAL_OPERATOR outrank CROWDSOURCED, and SIMULATED never enters
    production training unless explicitly allowed.
    """

    REAL_OPERATOR = "REAL_OPERATOR"  # operator-published load (MBTA occupancy_status)
    PUBLIC_FEED = "PUBLIC_FEED"  # public GTFS-RT position feed
    APC = "APC"  # automatic passenger counter
    AFC = "AFC"  # automatic fare collection / e-ticketing
    CROWDSOURCED = "CROWDSOURCED"  # passenger reports
    DERIVED = "DERIVED"  # computed by us (map-matched, interpolated)
    SIMULATED = "SIMULATED"  # synthetic


#: Sources that may be used to train a model that will serve production traffic.
#: SOLUTION.md section 15.2 names model poisoning through synthetic data as a threat;
#: this set is the mitigation.
PRODUCTION_TRAINING_SOURCES: frozenset[SourceType] = frozenset(
    {
        SourceType.REAL_OPERATOR,
        SourceType.PUBLIC_FEED,
        SourceType.APC,
        SourceType.AFC,
        SourceType.DERIVED,
    }
)


class Provenance(BaseModel):
    """Origin and quality metadata attached to every observation.

    Attributes:
        source_type: Which class of source produced this.
        source_name: Concrete source identifier, e.g. "mbta_cdn", "simulator_v1".
        source_timestamp: When the source says the observation was true.
        ingest_timestamp: When we received it. Never earlier than source_timestamp
            by more than a small clock-skew allowance.
        quality_score: Confidence in the observation itself, in [0, 1].
        raw_payload_ref: Pointer to the archived raw payload, for audit.
        schema_version: Version of the event schema this was produced against.
    """

    model_config = ConfigDict(frozen=True)

    source_type: SourceType
    source_name: str = Field(min_length=1)
    source_timestamp: datetime
    ingest_timestamp: datetime
    quality_score: float = Field(ge=0.0, le=1.0)
    raw_payload_ref: str | None = None
    schema_version: int = 1

    @property
    def is_simulated(self) -> bool:
        return self.source_type is SourceType.SIMULATED

    @property
    def usable_for_production_training(self) -> bool:
        return self.source_type in PRODUCTION_TRAINING_SOURCES

    def age_seconds(self, now: datetime) -> float:
        """Age of the observation at `now`, per its own source timestamp."""
        return (now - self.source_timestamp).total_seconds()
