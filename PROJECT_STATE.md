# PROJECT_STATE.md
# ── Living State Document — Update Every Session ────────────────
# Last Updated: 2026-08-30 09:45 IST | By: AI (Claude Opus 5)

## Current Phase
**Slice A — "It is alive".** A.1 (adapters), A.2 (validation + Redis state) and A.3 (read-only
API + ingestion worker) are built and gated. **A.4 (frontend live map) and A.5 (deploy) remain.**
Slice 0 / phase P0 is complete. Build order is now the vertical slices in SOLUTION.md §31.

## Current Status
**106 unit tests pass, plus integration suites; ruff clean.** Pushed to
**https://github.com/RushilJ2603/pravaah** (private, 10 commits, created 2026-08-30).

Running infrastructure: Compose stack up — TimescaleDB + PostGIS on **host port 15432** and
Redis on 6379, both healthy. MBTA GTFS imported as **feed_version_id 5** (399 routes, 9,630
routable stops, 89,080 trips, 2,221,062 stop-times).

Built this session beyond Slice 0: the GTFS-Realtime adapter chain producing canonical events
(291 vehicles, 60.8% occupancy coverage, 0 skipped, mean quality 0.979 on a live poll); the
position validator with derived speed and machine-readable rejection reasons; Redis latest-state
with viewport queries (read p95 **0.85 ms**); the read-only passenger API; and the
poll-validate-store worker that keeps live state moving.

The document was amended five times this session, each approved before any code changed and each
logged in Appendix C: the stop-count gate, the malformed-row policy, the vertical-slice
restructure of §31, the §33 frontend specification, §14.4 deployment, and the `GET /v1/vehicles`
viewport endpoint.

Not started: frontend (§33), deployment (§14.4), forecasting, routing, operator dashboard.

## Blocking Issues
- NONE blocking the build.
- **Watch item:** two tests in `tests/integration/test_api.py` still **skip** —
  `/v1/stops/{id}/departures` is not verified end to end even though feed_version_id 5 is
  imported. Diagnose before trusting that endpoint. It is the only part of A.3 not proven.

## Next Session Must Start With
> First, resolve the two skipped tests in `tests/integration/test_api.py` — run with
> `PRAVAAH_DATABASE_DSN="postgresql://pravaah:pravaah@localhost:15432/pravaah"` and find why the
> departures endpoint returns 503/404 when feed_version_id 5 exists. It is a small bug, and A.3
> is not honestly complete until it passes.
>
> Then build **Slice A.4**: the React + Vite + MapLibre live map per SOLUTION.md §33, with a
> **self-hosted Protomaps `.pmtiles` basemap for Boston** (approved — no API key, works offline,
> so §31 F.4 survives). Put the extract in `deploy/basemap/` and git-ignore it.
> Gate: vehicles move on the correct routes; a stale feed shows the freshness badge; an unknown
> occupancy never renders as empty (§33.3). Then **A.5**: deploy per §14.4.

## Environment Notes
- OS: Windows 11 Home Single Language 10.0.26200
- Python: 3.12.10. Installed for this project: `pydantic` 2.9.2, `pytest` 8.3.3, `ruff` 0.6.9,
  `psycopg[binary]` 3.2.3, `gtfs-realtime-bindings` 2.2.0, `protobuf` 7.36.0. **Not yet installed**
  (pinned in `requirements.txt`): pandas, pyarrow, redis, fastapi, lightgbm, scikit-learn, numpy.
- Node: v24.15.0 (unused until P4).
- Docker: 29.5.3, daemon running. `docker compose up -d` brings up `sih-db-1`
  (timescale/timescaledb-ha:pg16, PostgreSQL 16.14) and `sih-redis-1`, both healthy.
- Git remote: `origin` -> https://github.com/RushilJ2603/pravaah (**private**). Authenticated as
  **RushilJ2603**, which is a teammate's account, not this session's email. Commit messages carry
  **no AI co-author trailer** by the owner's instruction — do not re-add one.
- Python packages added this session: `psycopg[binary]`, `psycopg-pool`, `redis`, `fastapi`,
  `uvicorn`, `httpx`, `pandas`, `pyarrow`, `numpy`, `ruff`, `pytest`.
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
- **Recorder: exactly ONE process must run.** Three were found running concurrently this
  session (PIDs 39404, 52120, 66296); two were stopped. Before any long capture, check with
  `Get-CimInstance Win32_Process -Filter "Name='python.exe'"` and confirm a single
  `record_feed.py`. Concurrent writers interleave mid-row and corrupt the CSV.
- **The recorded corpus is multiply-written for 2026-08-28 → 08-30.** Three recorders ran
  concurrently, so vehicle-position rows repeat with the same `vehicle_ts` under different
  `ingest_ts` (~2.89M rows recorded where one process logged ~1.27M). The converter deliberately
  does not deduplicate positions (§28.2), so **the feature layer must decide** whether to
  deduplicate on `(vehicle_id, vehicle_ts)` before training on this window. Data recorded after
  09:00 on 2026-08-30 is single-sourced and clean.
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
