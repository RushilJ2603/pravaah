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
