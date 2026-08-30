# PROJECT_STATE.md
# ── Living State Document — Update Every Session ────────────────
# Last Updated: 2026-08-30 07:45 IST | By: AI (Claude Opus 5)

## Current Phase
**Phase P0 — Data foundation.** P0.1 (contracts + config) and P0.3 code (GTFS importer) are
done and gated. P0.2 (schema + compose stack) is written but **unverified** — the Docker daemon
is not running on this machine. P0.4 (CSV → Parquet conversion) has not been started.

## Current Status
The repository now exists and has a binding specification. [`docs/SOLUTION.md`](docs/SOLUTION.md)
supersedes the original `.docx` for engineering purposes: Part I carries the full architecture
(updated for the MBTA-as-stand-in decision), Part II is a new implementation contract — repo
layout, code-level contracts, DDL, module specs, API schemas, city profiles and per-phase
acceptance gates. **Code is built exactly to it; deviations go into the document first.**

Working and verified: the canonical contracts (`src/pravaah/contracts/`), city-profile loading
(`src/pravaah/config.py`, MBTA + Delhi), and the GTFS importer (`src/pravaah/ingest/gtfs_import.py`).
**37 tests pass, 1 skips, ruff is clean.** The exact-count gate runs against the real 2.2M-row
MBTA feed and matches the documented figures.

The recorder has never stopped: 3,516 polls, ~1.33M vehicle rows, ~4.97M stop-time updates,
1.3 GB. It is intentionally left running to accumulate training data.

Not started: adapters, map matching, state, features, models, routing, API, frontend.

## Blocking Issues
- **Docker Desktop is not running**, so the P0.2 gate is unverified. `docker compose up -d`
  returned exit code 0 but the daemon was unreachable
  (`npipe:////./pipe/dockerDesktopLinuxEngine`), so *no container was ever created*. The
  migrations, the hypertable definitions and the importer's database path are all
  **written but never executed**. Start Docker Desktop, then run
  `docker compose up -d && python -m pytest tests/integration -q`.

## Next Session Must Start With
> Start Docker Desktop, run `docker compose up -d`, and then
> `python -m pytest tests/integration -q`. This executes the P0.2 gate (extensions, 12 tables,
> 4 hypertables) and the second half of the P0.3 gate (import 2.2M stop-times, then re-import
> and assert the same `feed_version_id`). Expect the first import to take a few minutes.
> If it passes, P0.2 and P0.3 are closed and the next build item is **P0.4**:
> `src/pravaah/ingest/convert.py`, the CSV → partitioned Parquet converter specified in
> SOLUTION.md §28.2 — the fix for the 864 MB of near-duplicate TripUpdates rows.

## Environment Notes
- OS: Windows 11 Home Single Language 10.0.26200
- Python: 3.12.10. Installed for this project: `pydantic` 2.9.2, `pytest` 8.3.3, `ruff` 0.6.9,
  `gtfs-realtime-bindings` 2.2.0, `protobuf` 7.36.0. **Not yet installed** (in `requirements.txt`
  but unneeded so far): pandas, pyarrow, psycopg, redis, fastapi, lightgbm, scikit-learn, numpy.
- Node: v24.15.0 (unused until P4).
- Docker: 29.5.3 CLI present, **daemon not running** — see Blocking Issues.
- DB: PostgreSQL/PostGIS/TimescaleDB defined in `docker-compose.yml`, never yet started.
  DSN default `postgresql://pravaah:pravaah@localhost:5432/pravaah`, overridable with
  `PRAVAAH_DATABASE_DSN`.
- Git: repo initialized at the project root. 3 commits, nothing pushed (no remote).
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
- **P0.2 and half of P0.3 are unexecuted.** Migrations, hypertables and the importer's DB path
  have never run against a real database. Treat them as unproven until the integration suite passes.
- **`mbta_trip_updates.csv` is ~864 MB of near-duplicates.** Each TripUpdates poll re-dumps the
  full ~22k-row future stop-time table. P0.4 (§28.2) is the fix; until then it is not trainable.
- **`record_feed.py` uses deprecated `datetime.datetime.utcnow()`** in the `--keep-raw` branch.
  Fix when the recorder is next stopped — do not edit it while it is running.
- **The recorder has no rotation or size cap.** A multi-day run will produce CSVs too large to
  load in one pass.
- **`stop_times.txt` is loaded via `executemany` in 50k batches.** 2.2M rows will be slow on the
  first import; if it is intolerable, switch to `COPY` — but that is a §28.1 change, so document first.
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
