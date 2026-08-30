# SESSION_LOG.md
# ── Personal Developer Journal — For the User, Not the AI ─────────
#
# Purpose: A detailed, narrative record of every session for the human.
# The AI-facing handoff files (PROJECT_STATE, session.json, CHANGELOG,
# dead_ends) are terse and optimized for fast onboarding. This file is
# the opposite: verbose, story-shaped, honest about mistakes, written
# so you can re-read it months later and remember what actually happened.
#
# RULES FOR THE AI WRITING ENTRIES:
#   1. Append a new entry at the TOP of the log every session.
#   2. ALWAYS include the date AND time (start + end, with timezone).
#   3. ALWAYS list the EXACT file paths touched, not vague summaries.
#      Example: `src/api/users.ts` (lines 42–87, added pagination)
#   4. Be honest about what went wrong, what got redone, and what you
#      were uncertain about. The user wants the truth, not a clean diff.
#   5. Use the section template below. Skip sections that don't apply,
#      but don't invent content to fill them.
#
# ─────────────────────────────────────────────────────────────────

## Session 2b — 2026-08-30 (Codex finishes the features; I check its homework)

**AI:** Claude Opus 5 via Claude Code, with conductor mode / auth / model training from Codex
**Start → End:** 2026-08-30 13:40 IST → 2026-08-30 15:10 IST (~1h 30m)

### What happened

You brought Codex in to finish the two things I'd flagged as outstanding — conductor mode and an
actually-trained model — and asked me to explore what it changed. So this stretch was mostly
verification rather than construction, which is the right split: I had just written most of the
surrounding code, so I was the one positioned to notice if something didn't fit.

**Codex's work is good.** It built `api/auth.py` (pbkdf2 hashing, HMAC-signed tokens, role
dependencies), `api/conductor.py`, `models/registry.py`, `migrations/005_auth.sql` and
`006_schedule_indexes.sql` — the latter turning the two indexes I'd created by hand against the
database into a proper forward-only migration, which was on my tech-debt list. Six new test files.
199 tests pass, ruff clean, all four routers registered.

The detail I liked most: `baseline_v1.json` contains
`"metrics_label": "SIMULATOR_PERFORMANCE_ONLY_NOT_REAL_WORLD_ACCURACY"` and
`"real_world_accuracy": false` as fields **inside the artifact**. The rule that synthetic-label
metrics may never be quoted as real-world accuracy now travels with the model file rather than
living in a docstring someone can ignore.

### What I got wrong

**I told you `is_fallback: true` meant the model had no learned data for that cell.** That was
wrong and I should have measured before saying it. It actually means "answered from a coarser key
than the fully route-and-position-specific one". Measured properly: **100% coverage with zero
fallback** at the (hour, position) level, 71% at route-hour. The sparse level is only the most
granular one. I'd downplayed the model's quality on a misreading.

**My own context docs had gone from stale to false.** The `PROJECT_STATE.md` and `session.json` I
wrote about ninety minutes earlier said "NO TRAINED MODEL" and "conductor mode is NOT built" in
bold. Both were untrue by the time you read them. Stale docs are survivable; confidently wrong
ones actively mislead the next session. Rewrote both against a live verification pass.

### The blocker I found

`app_user` has **zero rows**, and `provision_user()` exists in `api/auth.py` but nothing calls it —
there is no CLI. So `POST /v1/auth/login` returns "invalid username or password" for every input,
and every `/v1/admin/*` route returns 401. **The operator dashboard and conductor mode are fully
built, fully tested, and completely unreachable at runtime.** Codex wired the security correctly
and then there was no way to create a user to get past it. Easy fix, but nothing demos without it.

Also: authentication failures come back as `{"code":"INTERNAL"}` because `ErrorCode` never gained
an `UNAUTHORIZED` member. The app can't distinguish "log in again" from "the server broke".

### The thing that actually blocks your demo

You described wanting "a normal day using the app". You currently cannot show one. Both
`api/deps.now()` and the simulator read real wall-clock time, so if the demo runs at 3pm you can
only ever show 3pm — never the 09:00 crush (72/91/100 onboard) or the 22:00 lull (28/40/55), which
are the most visually convincing outputs the model produces. Everything else for that demo exists;
this one thing gates it.

### Files touched by me this stretch

Verification only, no source changes: `PROJECT_STATE.md`, `CHANGELOG.md`, `SESSION_LOG.md`,
`.context/session.json` (archived to `.context/sessions/2026-08-30T13-35-00+05-30.json`).

### Where it stands

Backend feature-complete. 14 endpoints, 199 tests, trained model serving live. Five items left,
all demo enablement rather than features: clock control, seed accounts, auth error codes, a
one-command runner, and refreshing the frontend handoff which is still at rev 4 documenting 5 of
14 endpoints. Nothing committed yet.

---

## Session 2 — 2026-08-30 (Delhi pivot: a working MVP, and two bugs that were quietly lying)

**AI:** Claude Opus 5 via Claude Code (VS Code extension), Windows 11 + WSL2
**Start → End:** 2026-08-30 10:05 IST → 2026-08-30 13:40 IST (~3h 35m)

### What this session was actually about

It started as "review Mayank's proposal document", turned into a Flutter/conductor architecture
amendment, then mid-session you changed direction twice — first to an Indian city, then to
"mostly synthetic, MVP today". The scope moved a lot, and the code followed it. What came out the
other end is a working ten-endpoint backend on a synthetic Delhi.

### The two bugs that mattered

**1. Occupancy was never reaching the API.** This is the one worth remembering. The GTFS adapter
had been decoding `occupancy_status` correctly since Slice A.1 — and then `IngestWorker.cycle()`
only ever looked at `snapshot.positions` and threw `snapshot.occupancies` on the floor every
single poll. Redis stored positions only. So `GET /v1/vehicles` returned
`occupancy_class: "UNKNOWN"` for **every vehicle, always**, while the logs cheerfully printed
"occupancy 60.8%" from the snapshot. The headline feature of a crowd-prediction product was
silently absent and nothing failed. I found it while writing the frontend handoff, not from a
test.

- `src/pravaah/state/redis_state.py` — added `LatestOccupancyState` (~100 new lines), its own
  hash `pravaah:{city}:occupancy`, expiry-on-read, `get_many` for one round trip.
- `src/pravaah/ingest/worker.py:70-99` — filters `snapshot.occupancies` to vehicles whose position
  *passed* validation, writes to Redis and to `occupancy_observation`.
- `src/pravaah/api/passenger.py:48-71` — `_view()` joins position to crowd, handling absence in
  exactly one place.
- `src/pravaah/api/deps.py` — `occupancy` accessor.

**2. Every schedule endpoint had been returning 503 for the process lifetime.** The connection
pool in `api/deps.py` gave up after 5 seconds. The WSL→Docker hop is slower than that. So the
pool never initialised, `db_pool` stayed `None`, and `/departures` answered
`FEED_UNAVAILABLE` forever — which reads exactly like "the database is down" rather than "the
pool timed out at startup". Raised to 30 s and it worked immediately. Those two skipped tests
from last session were probably always this.

### What I got wrong and had to redo

**My first calibration was dishonest, and I shipped it before catching it.** `sim/calibrate.py`
filled unmeasured hours with `1.0`. In the output JSON that is indistinguishable from "measured,
and it was average". The weekday curve was mostly `1.0`, the peak came out at 05:00, and the
peak/off-peak ratio was 1.08 — a flat line dressed as a finding. Two causes: the default fill,
and using *mean ordinal* as a demand proxy when 87% of observations sit in one class. Rewrote it
to return `null` for unmeasured hours, switched to crowding incidence, and added a `fit_warnings`
field. Honest output: the corpus spans **1.6 days**, only 7 of 24 weekday hours are fittable, and
it contains **zero** standing-room or crushed observations. That last fact is the important one —
the crowding range Delhi lives in was simply not present in the source data, so it could never
have been transferred, only assumed.

**The simulator's first run was Boston-shaped.** 85% "many seats available", 2 standing out of
200 buses. Correct behaviour, wrong city. Raised `base_boardings` 6.0 → 16.0 and it moved to
47% few-seats / 22% standing / crush at peak, which is much closer to Delhi's reported ~88% load
factor. That single constant is the difference between "a transit sim" and "a Delhi transit sim".

**`/v1/admin/hotspots` hung for over five minutes.** A CTE with
`trip_id IN (SELECT DISTINCT trip_id FROM win)` over 113k stop_times. The window CTE alone runs in
0.02 s, so it was entirely the correlation. Rewrote as two flat queries plus a dict join in
Python. Also added two indexes — **directly to the database, not via a migration**, which is tech
debt I logged.

**agy/Antigravity failed twice.** `timeout waiting for response`, identical at 10 min and 25 min,
so not a size problem. The repo is on `/mnt/c/...` over the WSL 9p bridge at 20s+ per file read.
The one delegation that did complete (the SOLUTION.md amendments) came back with a **false
Appendix C row claiming the table of contents had been updated when it hadn't** — in a document
whose entire premise is that its change log is trustworthy. Also a duplicated table row and three
Markdown tables missing header separators. All fixed by hand. I stopped delegating after that.

### Files touched

New: `src/pravaah/sim/{__init__,calibrate,network,demand,generate,persist}.py`,
`src/pravaah/models/{__init__,baseline,crowd}.py`, `src/pravaah/api/admin.py`,
`config/calibration/delhi_v1.json`, `config/models/crowd_v1.json`, `docs/FRONTEND_HANDOFF.md`.

Modified: `docs/SOLUTION.md` (§25, §28.9, §31 Slice H, §19.1, Appendix C — plus the earlier
Flutter/conductor/auth batch), `src/pravaah/api/{deps,passenger,schemas,main}.py`,
`src/pravaah/state/redis_state.py`, `src/pravaah/ingest/worker.py`,
`config/settings.toml` (active_city → delhi, DSN → 15432), `config/cities/delhi.toml`,
`tests/unit/test_worker.py`, `tests/integration/{test_api,test_redis_state}.py`.

Deleted: `config/calibration/mbta_v1.json` (per your "no connection to Boston whatsoever").

### What I'm uncertain about

- **Every Delhi number is an assumption.** Capacity 35/70/100, the hourly curve, the weekly
  pattern, arterial speeds. The research came back with citations whose URLs looked fabricated
  (article IDs like `101691234567890`), so I refused to treat them as sourced and marked them all
  ASSUMPTION in the config. They are plausible. They are not verified.
- **There is no trained model, and I want to be blunt about it.** `/v1/trips/{id}/forecast` and
  everything downstream is a Monte Carlo over the demand model — a simulation querying itself.
  It produces real quantiles and it is reproducible, but it is not machine learning.
  `models/baseline.py` is a genuine fitted model with a chronological split and held-out metrics,
  and it has **never been run**. If someone asks "is the model trained?", the answer today is no.
- **Forecast, plan and all four admin endpoints have zero test coverage.** I verified every one by
  hand against a live server and pasted the real responses into the handoff, but there is no
  regression protection on any of them.
- `/v1/plan` finds direct services only. `transfers` is always 0, so the `fewest_transfers`
  profile cannot actually differentiate anything yet.

### Where it stands

Ten endpoints live. 111 unit tests pass, ruff clean. Synthetic Delhi persisted as feed_version 6:
490 stops, 51 routes, 8,568 trips, 113,568 stop_times. Conductor mode is the one requested feature
not built. Nothing committed yet.

---

## Session 1 — 2026-08-30 (from blank templates to a deployed-ready Slice A, on GitHub)

**AI:** Claude Opus 5 via Claude Code (VS Code extension), Windows 11
**Start → End:** 2026-08-30 06:52 IST → 2026-08-30 09:45 IST (~2h 55m)
**Goal at start:** Fill in the blank context templates by exploring the codebase. That scope grew
four times during the session: make a git repo, make the solution document binding and more
detailed, build the thing, and finally push to GitHub.

### What we set out to do

The session began as pure documentation: read the project, fill `CLAUDE.md` and
`PROJECT_STATE.md`, create `CHANGELOG.md`. What the exploration found was a project with an
unusually good design document and almost no code — one recorder script and 1.3 GB of captured
feed data. Once the context files were filled, you set a standing rule that reshaped everything
after: **the solution document is binding, and code deviations require an approved doc edit
first.** The rest of the session was building Phase P0 and Slice A under that rule.

### Files touched

Context and specification:
- `CLAUDE.md` — filled from exploration; later rewrote the directory map for the root layout and
  added the doc-first rule as the top coding rule. Behavioral Guidelines and Session Protocol
  left byte-identical, as instructed.
- `PROJECT_STATE.md`, `CHANGELOG.md`, `SESSION_LOG.md`, `session_prompts.md`, `.context/*` —
  moved from `templatesv2/` to the project root; `templatesv2/` removed.
- `docs/SOLUTION.md` — **created (1,973 lines)**. Part I extracted from the `.docx` and updated;
  Part II (§25–§33) written from scratch: repo layout, code-level contracts, DDL, module specs,
  API schemas, city profiles, build order with gates, conventions, frontend spec.
- `.gitignore` — written *before* `git init`, deliberately.
- `.context/dead_ends.md` — two entries: the port-5432 conflict, and trusting exit codes.

Code (all new):
- `src/pravaah/contracts/{provenance,events,api}.py` — the canonical contracts.
- `src/pravaah/config.py` — settings and city profiles.
- `src/pravaah/adapters/{base,gtfs_rt,mbta}.py` — GTFS-Realtime decoding.
- `src/pravaah/ingest/{gtfs_import,convert,validate,worker}.py`
- `src/pravaah/state/redis_state.py`
- `src/pravaah/api/{main,passenger,schemas,deps}.py`
- `migrations/001–004.sql`, `docker-compose.yml`, `config/*.toml`, `requirements*.txt`,
  `pyproject.toml`
- `tests/unit/*` (6 files), `tests/integration/*` (5 files)

### Chronological narrative

1. Explored the project. Read the 25-section architecture `.docx` in full, the 10-slide deck, and
   `data/record_feed.py`. Verified the deck's claims against the actual GTFS rather than copying
   them — 399 routes / 10,297 stops / 2,221,062 stop-times all checked out.
2. Sampled the recorded CSVs and found the numbers that shaped the whole design: 68.8%
   occupancy coverage, 92.3% `stop_id`, and **only 9.8% `speed`**. That last one killed a planned
   feature before a line of code was written.
3. Filled the context templates. Flagged that they sat in `templatesv2/` rather than the root.
4. You confirmed MBTA is a stand-in, the recorder should keep running, and set the doc-first rule.
5. Created the git repo — `.gitignore` first, so the 1.3 GB corpus never entered history.
6. Converted the `.docx` to `docs/SOLUTION.md` and wrote Part II, the implementation contract.
7. Built P0.1 (contracts), P0.2 (schema), P0.3 (importer). Docker wasn't running, so P0.2/P0.3
   went unverified — I said so rather than claiming they passed.
8. You started Docker. Fought a port conflict for several exchanges (see below). Gates passed.
9. **First real exercise of the doc-first rule:** the importer inserted 9,630 stops where the gate
   demanded 10,297. Investigated, found 667 coordinate-less pathway nodes, asked, amended the
   document, *then* changed the test.
10. Built P0.4, the CSV→Parquet converter. Found three recorders running concurrently.
11. You asked how much was left and reminded me about frontend and deployment. Discovered §31 had
    17 phase rows and exactly one mention of a UI, and zero mention of deployment.
12. Restructured §31 into vertical slices, wrote §33 (frontend) and §14.4 (deployment).
13. Built Slice A.1, A.2, A.3.
14. You said stop. Then: push to GitHub, no AI co-author trailer, repo created today.

### What went right

- **Verifying rather than trusting.** Every headline number in this project's docs was checked
  against the data. Three separate times that caught something: the `speed` field, the label
  imbalance, and the stop count.
- **The doc-first rule worked exactly as intended.** Six amendments, each with a reason recorded
  in Appendix C. The stop-count one in particular would have been a silent test edit under any
  other process.
- **Tests that assert the *reason*, not just the number.** The pathway-node test checks that all
  667 are `location_type=3` and unserved by any trip. If a future feed drops coordinates on a real
  stop, it fails loudly instead of quietly losing a stop.
- Contracts made the invariants structural. `UNKNOWN` cannot become `EMPTY`, quantiles cannot
  cross, a ranked option cannot have zero reasons — enforced by validators, not by discipline.

### What went wrong / what got redone

- **I stated a wrong root cause under pressure.** When database auth failed I said the
  TimescaleDB image ignores `POSTGRES_PASSWORD`. It doesn't. The password was always fine; an
  unrelated `postgres:16` container owned port 5432, and Docker silently declines to publish a
  taken port. I corrected it, but I asserted it before proving it, which is the mistake.
- **Two false leads on that same problem.** `NetworkSettings.Ports` showing `[]` looked like a
  Docker bug, and `psql -h 127.0.0.1` *inside* the container succeeded — but that matches a
  `trust` line in `pg_hba.conf` and proved nothing. The decisive test was that our container
  logged nothing for the failed attempt.
- **Exit codes lied three times.** `docker compose up -d` returned 0 with no daemon running.
  pytest returned 0 while reporting `3 skipped`, and again while 3 tests failed — piping to `tail`
  masks the status. Nearly produced a false "verified" claim. Now in `dead_ends.md`.
- **My own row accounting was off by 8** in the converter, because pyarrow's schema-sniffing pass
  invoked the counting handler. Caught only because the corpus test asserts the three outcomes
  partition the input exactly. A looser assertion would have hidden it.
- **Tooling friction, twice.** A PowerShell here-string used in the Bash tool corrupted the first
  commit message. Large bash heredocs silently failed to parse and wrote nothing — twice — before
  I switched to writing files with the editor tool.
- **Filter-branch verification nearly gave a false negative:** `git log --all` includes
  `refs/original/`, so the check reported 10 trailers when the branch was already clean.

### Decisions made (with rationale)

| Decision | Why | Reversible? |
|---|---|---|
| `docs/SOLUTION.md` binding, `.docx` frozen | A binary file cannot be diffed or reviewed | Yes |
| MBTA substrate, Delhi target (ADR-08) | Delhi publishes no occupancy; crowd labels are the product | Yes — adapter + config |
| §31 restructured into vertical slices | You want a working frontend and a deployment; bottom-up hides both until the end | Yes |
| Single VM deployment (§14.4) | Keeps §27 unchanged; TimescaleDB is absent from most free tiers | Yes |
| Self-hosted Protomaps basemap | Credible map, no key, and survives networking-disabled demo | Yes |
| Stop gate 10,297 → 9,630 | 667 pathway nodes have no coordinates and no trip serves them | Yes |
| Malformed rows: skip, count, fail above 0.1% | A live CSV always ends mid-write | Yes |
| Private repo, no AI co-author trailer | Your instruction; keeps the deck and architecture doc unpublished before judging | Public: yes. Trailer: history already rewritten |

### Surprises / things learned

- **Three recorders were running.** The trip-updates file held ~10.8M rows while the log reported
  ~4.97M. Concurrent appends also interleaved mid-row, producing torn lines — and one torn
  fragment landed with *exactly* the right column count but an `ingest_ts` of `:46.962563`, which
  tried to create a directory of that name. Column-count validation alone is not enough.
- The dedup result was larger than expected: **63.9% of TripUpdates rows were duplicates**, and
  1.34 GB of CSV became 0.05 GB of Parquet.
- MBTA's occupancy labels are severely imbalanced — 61% "many seats", 0.5% "full". Global
  accuracy would be a meaningless headline metric, which is now written into §9.6 and §22.

### Loose ends / deferred

- **Two skipped API tests.** `/v1/stops/{id}/departures` unverified end to end. First task next
  session — A.3 is not honestly complete without it.
- **The 28–30 Aug corpus is multiply-written.** Positions repeat with the same `vehicle_ts` under
  different `ingest_ts`. §28.2 says positions are never deduplicated, so the *feature layer* must
  decide about `(vehicle_id, vehicle_ts)` before training on that window.
- **Compose publishes 15432 while §30.2 documents 5432.** A fresh clone on a clean machine will
  not connect without the env override. Needs either a doc amendment or reverting compose once
  your other container is gone.
- `record_feed.py` still uses deprecated `datetime.datetime.utcnow()`; don't edit it while it runs.
- `SIH_NITK_241EC148_D4CULT.pdf` never machine-read — text extraction failed. Contents assumed to
  overlap the deck; open it manually if it matters.
- `.context/sessions/` was **not** created. The protocol says to archive the previous
  `session.json` before regenerating, but the previous one was an unfilled template with literal
  `YYYY-MM-DD` placeholders — archiving it would have produced a junk file preserving nothing.
  The next session end will create the directory with the first real archive.

### Time-rough breakdown

- exploring and verifying the existing project: ~15%
- writing and amending `docs/SOLUTION.md`: ~30%
- building P0 (contracts, schema, importer, converter): ~25%
- building Slice A (adapters, validation, state, API, worker): ~20%
- infrastructure fights (Docker port, recorders, tooling): ~10%

---

## Session N — YYYY-MM-DD (one-line headline)

**AI:** <which AI / IDE / model>
**Start → End:** YYYY-MM-DD HH:MM TZ → YYYY-MM-DD HH:MM TZ (~Xh)
**Goal at start:** <what the user asked for at the top of the session>

### What we set out to do
<2–4 sentence narrative of the intent>

### Files touched
- `path/to/file.ext` — what changed, with line numbers if useful
- `path/to/other.ext` — created / modified / deleted

### Chronological narrative
1. ...
2. ...
3. ...

### What went right
- ...

### What went wrong / what got redone
- ...

### Decisions made (with rationale)
| Decision | Why | Reversible? |
|---|---|---|
| ... | ... | Yes / No |

### Surprises / things learned
- ...

### Loose ends / deferred
- ...

### Time-rough breakdown
- area A: ~X%
- area B: ~Y%

---
<!-- Append new sessions ABOVE this line, newest first. -->
