"""Fit simulator parameters from a real recorded corpus (SOLUTION.md section 28.9).

The point of this module is that the simulator's numbers are **measured, not
chosen**. Section 18.1 requires behavioural rules rather than random occupancy
percentages, and a rule whose multipliers were invented is only a slower way of
making the data up. So the peak shape, the load profile along a trip and the
crowding distribution all come from the MBTA corpus -- the only data in this
project with real operator occupancy labels.

What is fitted here is *shape*, not *scale*. Boston is an uncrowded system by
Indian standards; transplanting its crowding levels to Delhi would be wrong.
The target city supplies capacity, peak windows and a demand multiplier through
its city profile, and `sim/demand.py` applies them. See section 28.9.

**Deduplication is mandatory and is the reason this module reads the CSV rather
than the Parquet corpus.** Between 2026-08-28 and 08-30 three recorders ran
concurrently (section 28.2), so the same observation appears several times under
different `ingest_ts`. Fitting on the raw file triple-counts the busiest window
and biases every parameter. The unique observation is `(vehicle_id, vehicle_ts)`
-- the vehicle's own clock, not ours.

Usage:

    python -m pravaah.sim.calibrate --corpus data/mbta_vehicle_positions.csv \\
        --out config/calibration/mbta_v1.json
"""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from ..contracts.events import OccupancyClass

log = logging.getLogger(__name__)

#: Columns actually needed. Reading all 18 costs several hundred MB for nothing.
USECOLS = [
    "vehicle_id",
    "vehicle_ts",
    "route_id",
    "trip_id",
    "current_stop_sequence",
    "occupancy_status",
]

#: Rows per chunk. Tuned to stay well inside the 1 GB budget in section 28.2.
CHUNK_ROWS = 500_000

#: Trips shorter than this tell us nothing about a load profile.
MIN_TRIP_OBSERVATIONS = 5

#: Buckets along a trip, from origin (0) to terminus (1).
PROFILE_BUCKETS = 10

#: Below this, an hour is reported as null rather than fitted. A default that
#: looks like a measurement is worse than an admitted gap -- the corpus covers
#: only a few days, so most (day_type, hour) cells are genuinely empty.
MIN_HOUR_OBSERVATIONS = 500

#: Ordinal at or above which a vehicle counts as "crowded". FEW_SEATS_AVAILABLE
#: is the first class a passenger would notice. Mean ordinal is a poor demand
#: proxy here because 87% of MBTA observations sit in a single class; the share
#: crossing this threshold moves far more across the day.
CROWDED_ORDINAL = 2

CALIBRATION_VERSION = 1


@dataclass(frozen=True)
class CalibrationProfile:
    """Measured shape parameters. Scale lives in the city profile, not here."""

    version: int
    source_corpus: str
    source_city: str
    timezone: str
    fitted_at: str

    rows_read: int
    rows_after_dedup: int
    duplicate_share: float
    observations_with_occupancy: int
    occupancy_coverage: float

    #: Share of each occupancy class among *known* observations.
    class_distribution: dict[str, float]

    #: Demand index by (day_type, hour), normalized so the overall mean is 1.0.
    #: `day_type` is "weekday" | "saturday" | "sunday".
    hourly_demand_index: dict[str, list[float]]

    #: Mean normalized load at each tenth of a trip, origin to terminus.
    #: This is the "fills up then empties" curve the behavioural model needs.
    load_profile: list[float]

    #: Peak-to-offpeak demand ratio, or None when the corpus cannot support it.
    peak_ratio: float | None
    am_peak_hour: int | None
    pm_peak_hour: int | None

    #: Corpus coverage, so a consumer can see what this was actually fitted on.
    corpus_start: str
    corpus_end: str
    corpus_days: float
    hours_measured: dict[str, int]
    fit_warnings: list[str]

    def to_json(self) -> str:
        return json.dumps(self.__dict__, indent=2, sort_keys=True)


def _day_type(dow: int) -> str:
    """0=Monday. Saturday and Sunday are separated deliberately.

    In Indian cities Saturday is a working day for a large share of commuters,
    so a simulator that lumps it with Sunday will understate weekend demand on
    the target city. Keeping them apart here means the city profile can weight
    them differently without refitting.
    """
    if dow == 6:
        return "sunday"
    if dow == 5:
        return "saturday"
    return "weekday"


def fit(corpus: Path, city_id: str, timezone: str) -> CalibrationProfile:
    """Stream the corpus and fit shape parameters."""
    import pandas as pd

    tz = ZoneInfo(timezone)

    rows_read = 0
    frames: list[pd.DataFrame] = []

    reader = pd.read_csv(
        corpus,
        usecols=USECOLS,
        chunksize=CHUNK_ROWS,
        dtype={
            "vehicle_id": "string",
            "route_id": "string",
            "trip_id": "string",
            "occupancy_status": "string",
        },
        on_bad_lines="skip",  # torn rows from concurrent recorders (section 28.2)
    )

    for chunk in reader:
        rows_read += len(chunk)
        # vehicle_ts is the vehicle's own clock as POSIX seconds. Rows torn
        # mid-write can carry garbage here; coercion drops them.
        chunk["vehicle_ts"] = pd.to_numeric(chunk["vehicle_ts"], errors="coerce")
        chunk["current_stop_sequence"] = pd.to_numeric(
            chunk["current_stop_sequence"], errors="coerce"
        )
        chunk = chunk.dropna(subset=["vehicle_id", "vehicle_ts"])
        frames.append(chunk)
        log.info("read %d rows", rows_read)

    if not frames:
        raise ValueError(f"no usable rows in {corpus}")

    df = pd.concat(frames, ignore_index=True)
    del frames

    # THE deduplication. Section 28.2: concurrent recorders multiply-wrote this
    # window. Without this every fitted parameter is biased toward whatever was
    # happening while the extra recorders ran.
    before = len(df)
    df = df.drop_duplicates(subset=["vehicle_id", "vehicle_ts"], keep="first")
    after = len(df)
    duplicate_share = (before - after) / before if before else 0.0
    log.info("deduplicated %d -> %d rows (%.1f%% duplicates)", before, after, duplicate_share * 100)

    # Local wall-clock time, because demand follows the city's clock, not UTC.
    ts = pd.to_datetime(df["vehicle_ts"], unit="s", utc=True).dt.tz_convert(tz)
    df["hour"] = ts.dt.hour.astype("int8")
    df["dow"] = ts.dt.dayofweek.astype("int8")

    known = df[df["occupancy_status"].notna() & (df["occupancy_status"] != "")].copy()
    coverage = len(known) / after if after else 0.0

    known["ordinal"] = known["occupancy_status"].map(_ordinal_by_name)
    known = known.dropna(subset=["ordinal"])
    known["ordinal"] = known["ordinal"].astype("float32")

    class_distribution = (
        known["occupancy_status"].value_counts(normalize=True).round(6).to_dict()
    )

    hourly_index, hours_measured, peak_ratio, am_peak, pm_peak = _fit_hourly(known)
    load_profile = _fit_load_profile(known)

    span_start = pd.to_datetime(df["vehicle_ts"].min(), unit="s", utc=True).tz_convert(tz)
    span_end = pd.to_datetime(df["vehicle_ts"].max(), unit="s", utc=True).tz_convert(tz)
    corpus_days = round((span_end - span_start).total_seconds() / 86400.0, 2)

    warnings: list[str] = []
    if corpus_days < 14:
        warnings.append(
            f"corpus spans only {corpus_days} days; the weekly demand pattern is NOT "
            "reliably fittable and unmeasured hours are reported as null"
        )
    for day_type, count in hours_measured.items():
        if count < 12:
            warnings.append(f"{day_type}: only {count}/24 hours had enough observations to fit")
    if not any(cls in class_distribution for cls in ("STANDING_ROOM_ONLY",
                                                     "CRUSHED_STANDING_ROOM_ONLY")):
        warnings.append(
            "corpus contains NO standing-room or crushed observations; the upper crowding "
            "range is unobserved here and cannot be transferred, only assumed by the target city"
        )

    return CalibrationProfile(
        version=CALIBRATION_VERSION,
        source_corpus=corpus.name,
        source_city=city_id,
        timezone=timezone,
        fitted_at=datetime.now(UTC).isoformat(),
        rows_read=rows_read,
        rows_after_dedup=after,
        duplicate_share=round(duplicate_share, 6),
        observations_with_occupancy=len(known),
        occupancy_coverage=round(coverage, 6),
        class_distribution=class_distribution,
        hourly_demand_index=hourly_index,
        load_profile=load_profile,
        peak_ratio=peak_ratio,
        am_peak_hour=am_peak,
        pm_peak_hour=pm_peak,
        corpus_start=span_start.isoformat(),
        corpus_end=span_end.isoformat(),
        corpus_days=corpus_days,
        hours_measured=hours_measured,
        fit_warnings=warnings,
    )


def _ordinal_by_name(name: str) -> float | None:
    """Map a feed occupancy name onto the ordinal ladder, or None if unknown."""
    try:
        cls = OccupancyClass(name)
    except ValueError:
        return None
    ordinal = cls.ordinal
    return float(ordinal) if ordinal is not None else None


def _fit_hourly(
    known,
) -> tuple[
    dict[str, list[float | None]], dict[str, int], float | None, int | None, int | None
]:
    """Crowding incidence by hour, normalized so the overall mean is 1.0.

    The value is the share of observations at or above `CROWDED_ORDINAL`, not the
    mean ordinal: with 87% of MBTA observations in one class the mean barely
    moves across the day, which produced a near-flat curve and a nonsense 05:00
    "peak" on the first fit.

    Hours with fewer than `MIN_HOUR_OBSERVATIONS` return **None**, not a default.
    A 1.0 that means "no data" is indistinguishable from a 1.0 that means
    "average", and downstream that silently becomes an invented demand curve.
    """
    known = known.assign(
        day_type=known["dow"].map(_day_type),
        crowded=(known["ordinal"] >= CROWDED_ORDINAL).astype("float32"),
    )
    overall = float(known["crowded"].mean())
    if overall <= 0:
        raise ValueError("corpus contains no crowded observations; cannot normalize")

    index: dict[str, list[float | None]] = {}
    measured: dict[str, int] = {}
    for day_type in ("weekday", "saturday", "sunday"):
        subset = known[known["day_type"] == day_type]
        hourly: list[float | None] = [None] * 24
        count = 0
        if not subset.empty:
            grouped = subset.groupby("hour")["crowded"]
            means, sizes = grouped.mean(), grouped.size()
            for hour, value in means.items():
                if sizes[hour] >= MIN_HOUR_OBSERVATIONS:
                    hourly[int(hour)] = round(float(value) / overall, 4)
                    count += 1
        index[day_type] = hourly
        measured[day_type] = count

    weekday = index["weekday"]

    def _best(window: range) -> int | None:
        candidates = [h for h in window if weekday[h] is not None]
        return max(candidates, key=lambda h: weekday[h]) if candidates else None

    am_peak, pm_peak = _best(range(5, 12)), _best(range(15, 22))
    offpeak = [weekday[h] for h in (10, 11, 13, 14) if weekday[h] is not None]

    peak_ratio = None
    peaks = [weekday[h] for h in (am_peak, pm_peak) if h is not None]
    if peaks and offpeak:
        offpeak_value = sum(offpeak) / len(offpeak)
        if offpeak_value > 0:
            peak_ratio = round(max(peaks) / offpeak_value, 4)

    return index, measured, peak_ratio, am_peak, pm_peak


def _fit_load_profile(known) -> list[float]:
    """Mean load at each tenth of a trip, origin to terminus.

    This is the curve that makes simulated occupancy behave like a bus rather
    than like noise: load builds toward the middle of a run and sheds near the
    terminus. `sim/demand.py` turns it into boarding and alighting propensity.
    """
    import numpy as np

    usable = known.dropna(subset=["trip_id", "current_stop_sequence"])
    if usable.empty:
        return [1.0] * PROFILE_BUCKETS

    counts = usable.groupby("trip_id")["current_stop_sequence"].transform("count")
    usable = usable[counts >= MIN_TRIP_OBSERVATIONS]
    if usable.empty:
        return [1.0] * PROFILE_BUCKETS

    max_seq = usable.groupby("trip_id")["current_stop_sequence"].transform("max")
    min_seq = usable.groupby("trip_id")["current_stop_sequence"].transform("min")
    span = (max_seq - min_seq).replace(0, np.nan)
    position = (usable["current_stop_sequence"] - min_seq) / span
    usable = usable.assign(position=position).dropna(subset=["position"])
    if usable.empty:
        return [1.0] * PROFILE_BUCKETS

    bucket = (usable["position"] * PROFILE_BUCKETS).clip(0, PROFILE_BUCKETS - 1).astype(int)
    means = usable.assign(bucket=bucket).groupby("bucket")["ordinal"].mean()

    overall = float(usable["ordinal"].mean()) or 1.0
    return [round(float(means.get(b, overall)) / overall, 4) for b in range(PROFILE_BUCKETS)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fit simulator parameters from a real corpus.")
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--city", default="mbta", help="city the corpus was recorded from")
    parser.add_argument("--timezone", default="America/New_York")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

    profile = fit(args.corpus, args.city, args.timezone)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(profile.to_json(), encoding="utf-8")

    log.info("wrote %s", args.out)
    log.info(
        "rows %d -> %d after dedup (%.1f%% duplicates); occupancy coverage %.1f%%",
        profile.rows_read,
        profile.rows_after_dedup,
        profile.duplicate_share * 100,
        profile.occupancy_coverage * 100,
    )
    log.info(
        "corpus spans %.2f days (%s -> %s)",
        profile.corpus_days, profile.corpus_start, profile.corpus_end,
    )
    log.info(
        "AM peak %s, PM peak %s, peak/offpeak ratio %s",
        profile.am_peak_hour, profile.pm_peak_hour, profile.peak_ratio,
    )
    for warning in profile.fit_warnings:
        log.warning("FIT WARNING: %s", warning)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
