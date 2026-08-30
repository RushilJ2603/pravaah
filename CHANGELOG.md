# CHANGELOG.md
# ── Full Project History — Newest Entry First ──────────────────
#
# Format for every entry:
#
#   ## [YYYY-MM-DD HH:MM IST] — <one-line summary> | By: [Name]
#
#   ### Done This Session
#   - <specific thing completed>
#
#   ### Errors Hit
#   - <error and how it was resolved, or "None">
#
#   ### Next Session Must
#   - <specific action the next session must take>
#
# ──────────────────────────────────────────────────────────────

## [2026-08-30 15:10 IST] — Conductor mode, staff auth and a trained model land (Codex); full build verified | By: AI

### Done This Session
- **Codex completed the two outstanding features.** `api/auth.py` (pbkdf2 password hashing,
  HMAC-signed bearer tokens, `require_conductor` / `require_operator` dependencies),
  `api/conductor.py` (shift start / position / end, occupancy report), `models/registry.py`
  (serving-model selection with fallback), `migrations/005_auth.sql` (`app_user`,
  `conductor_shift`, and the partial unique index that makes the vehicle claim concurrency-safe),
  `migrations/006_schedule_indexes.sql`, and six new test files.
- **The model is genuinely trained and wired.** `config/models/baseline_v1.json`: 48,766 train /
  12,192 test rows on a **chronological** split, band coverage 0.87, MAE 0.153, pinball losses
  recorded. Served through the registry; the live API reports
  `model_version: "seasonal_median_v1+simulated"`. The artifact stamps itself
  `real_world_accuracy: false` and `SIMULATOR_PERFORMANCE_ONLY_NOT_REAL_WORLD_ACCURACY`, so §6.5
  is enforced by the file rather than by a docstring.
- **Verified the whole build rather than trusting the file list**: 124 unit + 75 integration
  tests pass, ruff clean, all four routers registered, migrations applied, and every endpoint
  group smoke-tested against a running server.
- **Measured model coverage**: 100% at the (hour, position) level with zero fallback; 71% of
  route-hour combinations have learned history. Training history is 60,958 rows spanning 2 days
  with all 24 hours covered evenly.
- **Produced the demo plan** — a six-beat script built around the crowd band at the boarding stop,
  with a rehearsed disclosure that turns the synthetic-data question into the conductor
  cold-start story.

### Errors Hit
- **The context docs I wrote earlier in this session became actively wrong.** They stated "NO
  TRAINED MODEL" and "conductor mode is NOT built"; both were false once Codex's work landed.
  Rewritten against a live verification pass instead of from memory. A stale doc is tolerable; a
  confidently false one is not.
- **I misread `is_fallback: true`** as "the model has no data for this cell". It actually means
  "answered from a coarser key than route-specific". Measured properly: zero fallback at the
  (hour, position) level.
- **Found the demo blocker**: `app_user` is empty and `provision_user()` has no CLI, so login
  always fails and every `/v1/admin/*` route 401s. Operator and conductor are built, tested, and
  unreachable. Not yet fixed.
- **Auth failures serialize as `{"code":"INTERNAL"}`** — `ErrorCode` has no `UNAUTHORIZED` or
  `FORBIDDEN`. Not yet fixed.

### Next Session Must
- **Clock control** — `deps.now()` and the simulator use real time, so only the current hour is
  demonstrable. This blocks the "normal day" demo entirely and is the highest-value item.
- **Seed staff accounts** over the existing `provision_user()`.
- Add `UNAUTHORIZED` / `FORBIDDEN` to `ErrorCode`.
- One-command demo runner; refresh `docs/FRONTEND_HANDOFF.md` from rev 4 (5 of 14 endpoints).

---

## [2026-08-30 13:35 IST] — Delhi pivot: synthetic simulator, occupancy fix, forecast, planner and operator API | By: AI

### Done This Session
- **Fixed the occupancy pipeline.** Occupancy was decoded from the feed and then silently dropped
  — `worker.py` only handled `snapshot.positions` — so every API response returned
  `occupancy_class: UNKNOWN` despite real coverage. Added `LatestOccupancyState`, wired the worker
  to write occupancy to Redis and Postgres, joined it in the API. **Verified live**: a vehicle
  returned `STANDING_ROOM_ONLY` with ratio 0.61. The rejected-position test is mutation-verified.
- **Pivoted the demo city to Delhi, fully synthetic.** New `sim/` package: `network.py` (51 routes
  over 490 stops, 61 real Delhi places at real coordinates on real arterial corridors),
  `demand.py` (behavioural board/alight with conservation and crush clipping), `generate.py`
  (emits canonical events tagged `SIMULATED`), `persist.py` (writes the network as
  **feed_version 6** — 8,568 trips, 113,568 stop_times), `calibrate.py` (fits shape from a real
  corpus).
- **Removed Boston from every shipped artifact.** `mbta_v1.json` deleted, replaced by
  `delhi_v1.json` carrying only the fitted load curve and Delhi assumptions.
- **Built the forecast**: `models/crowd.py` Monte Carlos the demand model into p10/p50/p90 by
  hour and position. 09:00 peak = crushed/crushed/full (72/91/100 onboard); 22:00 = few-seats/
  standing (28/40/55).
- **Six new endpoints**: `/v1/trips/{id}/forecast`, `/v1/plan` (4 preference profiles, reason
  codes, deterministic candidates), `/v1/admin/hotspots` (severity + lead time),
  `/v1/admin/routes/{id}/forecast`, `/v1/admin/vehicles`, `/v1/admin/data-health`.
- **Made departures work** — needed the network in Postgres plus a pool-timeout fix.
- **Amended `docs/SOLUTION.md`** (Appendix C): §28.9 simulator module spec, §31 Slice H, §19.1
  two-city demo, and the earlier Flutter/conductor/auth batch.
- 111 unit tests pass, ruff clean.

### Errors Hit
- **My first calibration silently presented defaults as measurements.** Every unmeasured hour came
  back `1.0`, indistinguishable from a measured average. Rewrote to return `null` for unmeasured
  hours, swapped mean-ordinal for crowding incidence, and added `fit_warnings` recording that the
  corpus spans only 1.6 days with 7/24 weekday hours fittable.
- **Every schedule endpoint had been returning 503 for the process lifetime** — the connection
  pool gave up after 5 s, shorter than the WSL→Docker hop. Raised to 30 s.
- **`/v1/admin/hotspots` did not return within five minutes.** A CTE using
  `trip_id IN (SELECT DISTINCT trip_id FROM win)` produced a pathological plan. Replaced with two
  simple queries and a dict join in Python, plus two indexes.
- **agy delegation failed twice** with `timeout waiting for response`; the repo is on a Windows
  mount over the WSL 9p bridge. Wrote the tests by hand instead.
- Delhi GTFS host `traffickarma.iiitd.edu.in:9010` refused connections, so the network is
  synthetic rather than imported.

### Next Session Must
- Build **conductor mode** (Slice G): migration 005, `POST /v1/auth/login`, shift lifecycle.
- **Actually train a model** — accumulate `occupancy_observation` history and fit
  `models/baseline.py`. The current forecast is simulation, not learning.
- Add tests for forecast, plan and admin — all hand-verified only.

---

## [2026-08-30 09:45 IST] — Slice A.1–A.3 built; pushed to a private GitHub repo | By: AI

### Done This Session
- **Slice A.1 — adapters.** `adapters/base.py` separates fetch from decode so the mapping is
  testable offline and a recorded `.pb` frame replays through the same path as a live poll.
  `gtfs_rt.py` enforces two document rules at the boundary: `speed_mps` is left None (§28.4) and
  absent occupancy becomes `UNKNOWN`, never `EMPTY` (§12.4 rule 3). Live poll measured: **291
  vehicles, 60.8% occupancy coverage, 0 skipped entities, mean quality 0.979.**
- **Slice A.2 — validation and state.** `ingest/validate.py` gives three distinct outcomes:
  accepted with derived speed, rejected with a machine-readable reason, or accepted-but-flagged
  stale. Rejects out-of-bounds, impossible speed, null island `(0,0)` and re-served timestamps.
  `state/redis_state.py` holds only reconstructible state, with a geo set for viewport queries.
  **Latest-state read p95 measured at 0.85 ms** against the 5 ms budget.
- **Slice A.3 — API and worker.** `GET /v1/vehicles` (bbox required), `/v1/vehicles/{id}`,
  `/v1/stops/{id}/departures`, `/v1/health`, plus the poll-validate-store worker. `age_s` and
  `is_stale` are always present so a client renders the freshness badge without computing clock
  skew; `occupancy_class` is always present and `UNKNOWN` with a null ratio when nothing was
  reported.
- **Five approved document amendments** (Appendix C), each made before the corresponding code:
  §31 restructured into vertical slices, §33 frontend specification added, §14.4 single-VM
  deployment added, `GET /v1/vehicles` added to §12.1/§29.2, and earlier the stop-count gate
  and malformed-row policy.
- **Imported the MBTA network** into the running database as feed_version_id 5.
- **Pushed to https://github.com/RushilJ2603/pravaah** — private, 10 commits, repo created today.
  Rewrote history first to strip the AI co-author trailer from every commit, then dropped the
  filter-branch backup refs and verified 0 trailers remain across all refs.
- **106 unit tests pass** plus integration suites; ruff clean.

### Errors Hit
- **A `location_type=3` discovery cascade.** Slice A revealed nothing new here, but earlier in the
  session the P0.3 gate failure led to the stop-count amendment — see the 09:05 entry.
- **Two API tests still skip.** `/v1/stops/{id}/departures` is not verified end to end even with
  feed_version_id 5 imported. **Unresolved — first task next session.**
- **Filter-branch verification nearly gave a false negative.** `git log --all` includes
  `refs/original/`, so the first trailer check reported 10 remaining when the branch was already
  clean. Verified against the branch, then expired the backups and rechecked across all refs.

### Next Session Must
- Fix the two skipped departures tests; A.3 is not honestly complete until they pass.
- Build **Slice A.4**: React + Vite + MapLibre live map per §33, with a self-hosted Protomaps
  `.pmtiles` Boston basemap (no API key, offline-capable, so §31 F.4 survives).
- Then **A.5**: deploy to a single VM per §14.4.

---

## [2026-08-30 09:05 IST] — P0.4 complete; three concurrent recorders found and stopped | By: AI

### Done This Session
- **Built P0.4**, `src/pravaah/ingest/convert.py`: streams recorder CSVs into date-partitioned
  Parquet, deduplicating TripUpdates on the key §28.2 fixes. **Gate passes on the real corpus** —
  TripUpdates 10,854,177 rows → 3,917,785 (**63.9% duplicates dropped**), 0.91 GB → 0.02 GB;
  VehiclePositions 2,889,716 rows, 0.43 GB → 0.03 GB. Peak RSS inside the 1 GB budget.
- **Found and stopped a data-integrity problem.** Three `record_feed.py` processes were appending
  to the same two CSVs concurrently — multiply-recording every observation and interleaving
  mid-row into torn lines. With the owner's approval, stopped PIDs 52120 and 66296 and kept
  PID 39404 running so recording never paused.
- **Amended §28.2 (approved, Appendix C)** with the malformed-row policy — skip and count, fail
  above 0.1% — plus an explicit single-writer requirement and the rationale for never
  deduplicating positions. Document first, then code, both times.
- **56 tests pass (53 unit + 6 integration), ruff clean.**

### Errors Hit
- **Torn rows do not always have the wrong column count.** An interleaved fragment landed with
  exactly 18 commas but an `ingest_ts` of `:46.962563`, which produced a partition directory
  named `date=:46.962563` — not even a legal Windows path. Column-count validation alone is
  insufficient; added `_drop_unusable_timestamps` to require an ISO-8601 prefix, counted as
  malformed under the same policy.
- **Row accounting was off by exactly 8.** pyarrow's schema-sniffing pass reads the first block
  and invoked the counting handler, inflating `rows_read` before the real pass ran. The sniffing
  pass now uses a non-counting handler. Caught only because the corpus test asserts the three
  outcomes partition the input exactly.
- Three separate runs reported **exit code 0 while tests failed** (the pipe to `tail` masks
  pytest's status). Results were read from the summary line, never the exit code.

### Next Session Must
- Begin **P1.1**: `adapters/base.py`, `gtfs_rt.py`, `mbta.py`. Gate: a live poll produces valid
  `VehiclePositionEvent`s and zero records lack provenance.

---

## [2026-08-30 08:20 IST] — P0.2 and P0.3 gates verified against a live database | By: AI

### Done This Session
- Brought up the compose stack. **P0.2 gate passes**: migrations 001–004 applied cleanly from an
  empty volume — `postgis` + `timescaledb` extensions, all 12 tables, all 4 hypertables.
- **P0.3 gate passes**: imported the real MBTA feed — 399 routes, 9,630 routable stops, 89,080
  trips, **2,221,062 stop-times** in ~100 s; re-import returned the same `feed_version_id` and
  wrote nothing; overnight times past 86400 s survived the round trip.
- **First exercise of the doc-first rule.** The initial run failed: the §31 gate expected 10,297
  stops, the importer inserted 9,630. Investigation showed the 667 difference is entirely
  `location_type=3` generic pathway nodes (platform/lobby nodes inside stations) which have no
  coordinates and which **no trip references** in `stop_times.txt`. Since §27 declares
  `stop.geom NOT NULL`, the gate figure and the schema could not both hold.
  **Amended `docs/SOLUTION.md` first (§6.2.1, §28.1, §31, Appendix C) with the owner's approval,
  then changed the code.** Schema unchanged; the importer still refuses to invent coordinates.
- Added a unit test asserting the *justification*, not just the number: all 667 are location_type 3
  and disjoint from the set of stops any trip serves. If a future feed drops coordinates on a
  genuinely served stop, that test fails loudly instead of silently losing the stop.
- **41 tests pass (38 unit + 3 integration), ruff clean.**

### Errors Hit
- **Port 5432 was already owned by an unrelated container** (`postgres-db`, `postgres:16`).
  Docker **silently declines to publish a taken port** — `docker compose up -d` reported success,
  the container was healthy, and `docker compose exec psql` worked (unix socket), while every
  host client silently reached the *other* postgres and failed authentication. Diagnosed by
  correlating a failed connection against our container's logs: it logged nothing, proving the
  traffic never arrived. Resolved by publishing on **15432**.
  Two false leads recorded so I do not repeat them: `NetworkSettings.Ports` showed `[]` which
  looked like a Docker bug, and `psql -h 127.0.0.1` *inside* the container succeeded — but that
  matches a `trust` line in `pg_hba.conf`, so it proved nothing about the password.
- An earlier run reported "3 skipped" with **exit code 0** — the fixture skipped on connection
  failure. A skipped gate is not a passing gate; verified by reading the output, not the exit code.

### Next Session Must
- Build **P0.4**, `src/pravaah/ingest/convert.py` per §28.2 — streaming CSV → date-partitioned
  Parquet with TripUpdates deduplication. Install `pandas` and `pyarrow` first.
- Decide with the owner whether SOLUTION.md §30.2's documented DSN should move to port 15432, or
  whether compose reverts to 5432 once the conflicting container is gone.

---

## [2026-08-30 07:45 IST] — Repo initialized, solution document made binding, P0 started | By: AI

### Done This Session
- **Git repository created** at the project root. Wrote `.gitignore` *before* `git init` so the
  ~1.3 GB recorded corpus was never staged; verified only 1.2 MB entered the baseline commit.
- Moved the context bundle (`CLAUDE.md`, `PROJECT_STATE.md`, `CHANGELOG.md`, `SESSION_LOG.md`,
  `session_prompts.md`, `.context/`) from `templatesv2/` to the project root and removed the
  now-empty directory, so the Session Protocol's root-relative paths resolve.
- **Created `docs/SOLUTION.md` as the binding specification.** Part I is the full architecture
  extracted from the `.docx` and updated; Part II (§25–§32) is new: repository layout, code-level
  contracts, database DDL, module specifications, API request/response schemas, city-profile
  config and a per-phase build order with executable acceptance gates. Appendix C is the
  document change log — the mechanism for the doc-first rule. The `.docx` is unmodified.
- Recorded **ADR-08** (MBTA = development substrate, Delhi = deployment target), **ADR-09**
  (Markdown spec is binding), **ADR-10** (CSV capture, Parquet downstream).
- Grounded the spec in measured data rather than assumptions: verified 399 routes / 10,297 stops
  / 89,080 trips / 2,221,062 stop-times, and field coverage of 68.8% `occupancy_status`,
  92.3% `stop_id`, 80.5% `bearing` and **only 9.8% `speed`** — which led to prohibiting the raw
  feed speed field and mandating derived speed (§9.2, §28.4).
- **Built P0.1:** `contracts/provenance.py`, `contracts/events.py`, `contracts/api.py`,
  `config.py`, `config/settings.toml`, `config/cities/{mbta,delhi}.toml`. Provenance is
  structurally mandatory; `UNKNOWN` occupancy cannot collapse to `EMPTY`; quantiles cannot
  cross; a ranked option cannot have zero reasons.
- **Built P0.2 artifacts:** `migrations/001–004`, `docker-compose.yml` (TimescaleDB + PostGIS,
  Redis). **Written but not executed** — see Errors Hit.
- **Built P0.3:** `ingest/gtfs_import.py` — streaming, validating, atomic, idempotent by ZIP
  sha256. GTFS times parse to seconds past service midnight and are never wrapped at 24:00.
- **Tests: 37 pass, 1 skips, ruff clean.** Includes the P0.1 gate and the database-free half of
  the P0.3 gate (exact entity counts against the real feed, bounds rejection against the wrong
  city profile, overnight-time handling, seven validator rejection cases).
- Wrote `requirements.txt`, `requirements-dev.txt`, `pyproject.toml`.
- Left the recorder running throughout, as intended: 3,516 polls, ~1.33M vehicle rows.

### Errors Hit
- **`docker compose up -d` reported exit code 0 while doing nothing.** The Docker CLI is
  installed but Docker Desktop's daemon is not running
  (`npipe:////./pipe/dockerDesktopLinuxEngine` not found). The misleading exit code nearly
  produced a false "P0.2 verified" claim. **Unresolved — this is the standing blocker.**
- **Bash heredocs are unreliable in this environment.** A multi-file `cat > f <<'EOF'` block
  failed to parse twice and silently wrote nothing. Switched to the editor tool for file writes.
- **A PowerShell here-string (`@'...'@`) used inside the Bash tool corrupted the first commit
  message**, prefixing the subject with `@`. Fixed by amending with repeated `-m` flags.
- Pydantic warned that `model_version` collides with its protected `model_` namespace. The field
  name is fixed by §17.2/§26.3, so `protected_namespaces=()` was set rather than renaming it.

### Next Session Must
- Start Docker Desktop, then `docker compose up -d && python -m pytest tests/integration -q` to
  execute the P0.2 gate and close the second half of P0.3 (import, then re-import and assert an
  identical `feed_version_id`).
- Then build **P0.4**, `src/pravaah/ingest/convert.py` per §28.2 — the CSV → partitioned Parquet
  converter that deduplicates the 864 MB of near-identical TripUpdates rows.

---

## [2026-08-30 07:05 IST] — Project context initialized | By: AI
- Copied context templates and filled them based on codebase exploration.
- No code changes made.

<!-- Prepend new entries ABOVE this line, newest first. -->
