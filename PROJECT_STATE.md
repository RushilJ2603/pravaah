# PROJECT_STATE.md
# ── Living State Document — Update Every Session ────────────────
# Last Updated: 2026-08-30 08:20 IST | By: AI (Claude Opus 5)

## Current Phase
**Phase P0 — Data foundation.** P0.1 (contracts + config), P0.2 (schema + compose stack) and
P0.3 (GTFS importer) are **complete and verified against a live database**. P0.4 (CSV → Parquet
conversion) is the next build item and has not been started.

## Current Status
The repository has a binding specification, [`docs/SOLUTION.md`](docs/SOLUTION.md), and the P0
foundation is built to it and proven. **41 tests pass (38 unit + 3 integration), ruff clean.**

The compose stack runs: TimescaleDB-HA + PostGIS and Redis, both healthy. Migrations 001–004
applied cleanly from an empty volume — both extensions, all 12 tables, all 4 hypertables. The
GTFS importer has round-tripped the real feed twice: 399 routes, 9,630 routable stops, 89,080
trips and **2,221,062 stop-times** in ~100 s, idempotent on re-import (same `feed_version_id`,
nothing rewritten), with overnight times past 86400 s preserved.

The first integration run **failed usefully** and produced the first exercise of the doc-first
rule: the §31 gate demanded 10,297 stops while §27 declared `geom NOT NULL`. Investigation showed
667 of those rows are coordinate-less `location_type=3` pathway nodes that no trip serves. The
document was amended with the owner's approval (Appendix C), *then* the code followed.

The recorder has still never stopped, as intended.

Not started: adapters, map matching, state, features, models, routing, API, frontend.

## Blocking Issues
- NONE blocking the build.
- **Watch item — port 5432 is taken on this machine.** An unrelated container (`postgres-db`,
  image `postgres:16`) already publishes `0.0.0.0:5432`. Docker **silently declines** to publish
  a taken port, so our stack looked healthy while clients reached the *other* server and failed
  authentication. `docker-compose.yml` therefore publishes **15432**. Consequence: the compose
  host port (15432) and the DSN documented in SOLUTION.md §30.2 (`localhost:5432`) now disagree —
  see Known Issues.

## Next Session Must Start With
> Build **P0.4**: `src/pravaah/ingest/convert.py`, the CSV → date-partitioned Parquet converter
> specified in SOLUTION.md §28.2. It must stream in chunks (peak RSS under 1 GB, never load the
> whole CSV), write `parquet/kind=<vp|tu>/date=YYYY-MM-DD/part-NNN.parquet`, and deduplicate
> TripUpdates on `(trip_id, stop_id, stop_sequence, arrival_time, departure_time)` — consecutive
> polls re-emit near-identical rows, which is the whole 864 MB problem. Gate: the corpus
> converts, the TripUpdates row count drops materially after dedup, and peak RSS stays under 1 GB.
> `pandas` and `pyarrow` are pinned in `requirements.txt` but **not yet installed** — install them
> first.

## Environment Notes
- OS: Windows 11 Home Single Language 10.0.26200
- Python: 3.12.10. Installed for this project: `pydantic` 2.9.2, `pytest` 8.3.3, `ruff` 0.6.9,
  `psycopg[binary]` 3.2.3, `gtfs-realtime-bindings` 2.2.0, `protobuf` 7.36.0. **Not yet installed**
  (pinned in `requirements.txt`): pandas, pyarrow, redis, fastapi, lightgbm, scikit-learn, numpy.
- Node: v24.15.0 (unused until P4).
- Docker: 29.5.3, daemon running. `docker compose up -d` brings up `sih-db-1`
  (timescale/timescaledb-ha:pg16, PostgreSQL 16.14) and `sih-redis-1`, both healthy.
- **DB: reachable on host port 15432, NOT 5432.** Run tests with:
  `PRAVAAH_DATABASE_DSN="postgresql://pravaah:pravaah@localhost:15432/pravaah" python -m pytest tests -q`
  Migrations apply automatically on first boot of an empty volume; `docker compose down -v` to reset.
- Git: repo initialized at the project root. Nothing pushed (no remote configured).
- Shell: **large bash heredocs get mangled in this environment** — a multi-file
  `cat > f <<'EOF'` block failed to parse twice and wrote nothing. Write files with the editor
  tool, not shell heredocs. PowerShell here-strings (`@'...'@`) do not work in the Bash tool
  either; they silently corrupted a git commit message.
- Disk: `data/` is 1.3 GB, growing ~35 MB/hour while the recorder runs.
- Timezone: IST (UTC+05:30). Recorder writes `ingest_ts` in **UTC**; `recorder.log` is local IST.

## Recent Decisions (this phase)
| Decision | Rationale | Date |
|---|---|---|
| `docs/SOLUTION.md` is the binding spec; code follows it, deviations are doc-edits first | Owner's explicit instruction. A `.docx` cannot be diffed or reviewed, so the contract moved to version-controlled Markdown (ADR-09). The `.docx` is frozen, unmodified. | 2026-08-30 |
| MBTA is the **development substrate**, Delhi the **deployment target** (ADR-08) | Delhi OTD publishes no occupancy at all, and crowd labels are the product. MBTA publishes real operator occupancy with no API key. City knowledge is confined to `adapters/` + `config/cities/` so the swap is configuration. | 2026-08-30 |
| Raw capture stays append-only CSV; Parquet is a separate downstream step (ADR-10) | The recorder must never block on a database. Flat append is the most crash-tolerant capture. | 2026-08-30 |
| Raw GTFS-RT `speed` is prohibited; speed is derived from consecutive positions | Measured 9.8% coverage on MBTA — unusable as a feature. | 2026-08-30 |
| `UNKNOWN` occupancy is a first-class enum member, enforced by validators and a DB `NOT NULL` | 31% of rows have no occupancy; rendering that as "empty bus" is the single most damaging bug this system could ship. | 2026-08-30 |
| Global accuracy is never a headline crowd metric | Label distribution is 61% `MANY_SEATS_AVAILABLE`, 0.5% `FULL`. Threshold-region metrics only. | 2026-08-30 |
| Recorder keeps running continuously | Owner confirmed it is meant to accumulate data; live occupancy labels cannot be back-filled. | 2026-08-30 |
| Routing deterministic (RAPTOR/CSA); ML predicts conditions only | Explainability is an acceptance criterion. | 2026-08-27 |
| Baseline (seasonal median → GBDT) before any deep model | Debuggability; §22 names model over-complexity as a risk. | 2026-08-27 |
| Forecasts are quantiles (p10/p50/p90), never point estimates | Calibration is a KPI; uncertainty is a pitch differentiator. | 2026-08-27 |

## Known Issues / Tech Debt
- **Compose host port and the documented DSN disagree.** `docker-compose.yml` publishes 15432
  (because another project's container owns 5432 here), while SOLUTION.md §30.2 and
  `config/settings.toml` still document `localhost:5432`. A fresh clone on a clean machine will
  therefore not connect out of the box without the env override. **Decide with the owner:** either
  align the documented default to 15432 (a §30.2 doc edit), or revert compose to 5432 once the
  conflicting container is gone. Until then `PRAVAAH_DATABASE_DSN` is mandatory locally.
- **Importing 2.2M stop-times takes ~100 s** via `executemany` in 50k batches. Tolerable for now.
  Switching to `COPY` would be a §28.1 change, so it needs a doc edit first.
- **`mbta_trip_updates.csv` is ~864 MB of near-duplicates.** Each TripUpdates poll re-dumps the
  full ~22k-row future stop-time table. P0.4 (§28.2) is the fix; until then it is not trainable.
- **`record_feed.py` uses deprecated `datetime.datetime.utcnow()`** in the `--keep-raw` branch.
  Fix when the recorder is next stopped — do not edit it while it is running.
- **The recorder has no rotation or size cap.** A multi-day run will produce CSVs too large to
  load in one pass.
- **Delhi profile is untested.** `config/cities/delhi.toml` has plausible bounds and endpoints but
  the real-time URL is a guess and the portal requires an authorization request.
- No frontend, no CI, no observability yet.
- `SIH_NITK_241EC148_D4CULT.pdf` still unread (text extraction failed); assumed to overlap the deck.

## Reference Links
- Binding spec: [`docs/SOLUTION.md`](docs/SOLUTION.md) — §31 is the build order with gates.
- MBTA VehiclePositions (no key): https://cdn.mbta.com/realtime/VehiclePositions.pb
- MBTA TripUpdates (no key): https://cdn.mbta.com/realtime/TripUpdates.pb
- MBTA GTFS static: https://cdn.mbta.com/MBTA_GTFS.zip
- GTFS Schedule reference: https://gtfs.org/documentation/schedule/reference/
- GTFS-RT VehiclePositions (occupancy semantics): https://gtfs.org/documentation/realtime/feed-entities/vehicle-positions/
- Open-Meteo historical weather: https://open-meteo.com/en/docs/historical-weather-api
- Delhi OTD: https://otd.delhi.gov.in/data/static/ · https://otd.delhi.gov.in/data/realtime/
