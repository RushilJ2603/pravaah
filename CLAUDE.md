# CLAUDE.md
# ── Project Rules & AI Onboarding ──────────────────────────────

## What This Project Does
**PRAVAAH** — an SIH 2026 entry (NIT Karnataka, Surathkal) for the problem statement
*"Intelligent Public Transport Crowding & Route Prediction"*. It forecasts how crowded and
how delayed a transit vehicle will be **when it reaches the passenger's stop** (not now, at
the vehicle's current position), then ranks candidate journeys — or advises departing later —
using those forecasts. The same predictions drive an operator dashboard that flags predicted
crowding hotspots with lead time. Users: passengers, transit control-room operators, planners.

> **Read this before trusting anything below.** Only the **data-collection layer** exists as
> code today (`data/record_feed.py`). The Tech Stack and Directory Map sections describe the
> *designed* system from the architecture document — they are the target, not the state.
> `PROJECT_STATE.md` is authoritative for what actually runs.

## Tech Stack
- **Language:** Python 3.12.10 — the only language with running code. Node v24.15.0 is installed for the planned frontend.
- **Framework:** *Planned, not built* — FastAPI backend with async feed workers; React + MapLibre frontend; Docker Compose for single-command startup.
- **Database:** *Planned, not provisioned* — PostgreSQL + PostGIS (network graph), Redis (live vehicle state + pub/sub), Parquet (history archive). `psql` is not on PATH. **Today every byte of data is flat CSV in `data/`.**
- **Key Libraries:** *Installed today (the complete list):* `gtfs-realtime-bindings` 2.2.0, `protobuf` 7.36.0. *Planned:* pandas, LightGBM (quantile regression), scikit-learn, a RAPTOR/CSA GTFS routing library, MLflow.

## Directory Map
```
SIH/                                       ← project root (git repo)
├── CLAUDE.md                              ← You are here (rules + pointers)
├── PROJECT_STATE.md                       ← Current build status (read this!)
├── CHANGELOG.md                           ← Full history (read last 3 entries)
├── SESSION_LOG.md                         ← Personal detailed journal for the USER (write to it, don't read on onboarding)
├── session_prompts.md                     ← Copy-paste prompts for the session start/end rituals
├── .gitignore                             ← excludes the ~1.2 GB recorded corpus
├── .context/
│   ├── session.json                       ← Machine-readable LATEST-session state (well-known path)
│   ├── sessions/                          ← Archive: every prior session.json (created at first session end)
│   └── dead_ends.md                       ← Approaches already ruled out
├── docs/
│   └── SOLUTION.md                        ← ★ THE BINDING SPEC — code is built exactly to this
├── config/                                ← settings.toml + cities/{mbta,delhi}.toml   [P0, planned]
├── migrations/                            ← forward-only SQL                            [P0, planned]
├── src/pravaah/                            ← application code — layout fixed by SOLUTION.md §25
│   ├── contracts/ adapters/ ingest/ state/ features/ models/ routing/ ops/ api/
├── tests/                                 ← unit/ integration/ parity/                  [planned]
├── frontend/                              ← React + MapLibre                            [P4, planned]
├── data/                                  ← recorder + corpus (git-ignored except scripts)
│   ├── record_feed.py                     ← GTFS-Realtime recorder → CSV (canonical VP_COLS/TU_COLS)
│   ├── START_RECORDING.bat                ← Windows launcher; leave the window open
│   ├── mbta_gtfs.zip                      ← static GTFS (399 routes, 10,297 stops, 2,221,062 stop-times)
│   ├── mbta_vehicle_positions.csv         ← ~411 MB, real occupancy labels
│   ├── mbta_trip_updates.csv              ← ~864 MB, arrival/departure delays
│   └── recorder.log                       ← per-poll counters, one line per 20 s
├── Transit_Crowding_Route_Prediction_Solution_Architecture (1).docx  ← frozen original, superseded by docs/SOLUTION.md
├── PRAVAAH_SIH_Internal_Deck.pptx         ← 10-slide pitch
└── SIH_NITK_241EC148_D4CULT.pdf           ← SIH submission artifact
```

## Coding Rules

- **★ THE DOCUMENT IS BINDING.** `docs/SOLUTION.md` is the specification; the codebase is built
  exactly to it. If you need to deviate — different schema, module boundary, library, endpoint
  shape — **edit `docs/SOLUTION.md` first, get the owner's approval (log it in Appendix C), then
  write the code.** A commit that diverges from the document without a prior approved doc edit
  is a defect even if it works. If the document does not answer your question, it is incomplete:
  propose an edit, do not improvise.
- **The layout in §25 is fixed**, as are the contracts in §26, the DDL in §27 and the API shapes
  in §29. `contracts/` imports nothing else in the package. No city name may appear outside
  `adapters/` and `config/cities/`.
- **The recorder is append-only and may be live right now.** `data/record_feed.py` opens CSVs with mode `"a"`. Never truncate, rewrite in place, or re-sort those files, and never edit `record_feed.py` while a recording is running — restart cost is permanent data loss for that window.
- **Never hand-edit anything in `data/`.** Those CSVs are the training set and cannot be re-recorded for past time. Derive new files; do not mutate sources.
- **Provenance is mandatory.** Every record keeps `source_type` (`PUBLIC_FEED` / `APC` / `CROWDSOURCED` / `SIMULATED`) and its timestamp. The architecture treats real vs. inferred vs. simulated as a first-class tag — never drop or default it.
- **Missing occupancy is `unknown`, never `0` and never "empty bus."** ~31% of vehicle rows carry no `occupancy_status`. Rendering a blank as an empty vehicle is a correctness bug, not a display choice.
- **Predictions are distributions, not points.** Crowd and ETA are emitted as p10/p50/p90 (see Appendix A of the architecture doc). Do not collapse to a single number in any API response or UI.
- **Routing stays deterministic and explainable** (RAPTOR/CSA behind a `TripPlanner` interface). ML predicts the *conditions* routes will face; it does not pick routes.
- **Baseline before sophistication.** Seasonal/historical-median baseline, then GBDT, and only then anything deep — and only with a measured improvement to justify it.
- **Every ranked option needs a human-readable reason code.** Explainability is an acceptance criterion, not a nice-to-have.
- **New Python dependency ⇒ create/update `requirements.txt`.** It does not exist yet; whoever adds the first dependency creates it.
- **Nothing may make the demo require internet.** The hardening phase requires the full flow to run from recorded replay, offline.

## Files You Must Never Touch Without Asking
- `data/mbta_vehicle_positions.csv`, `data/mbta_trip_updates.csv` — ~1.2 GB of irreplaceable recorded ground truth with real operator occupancy labels. Cannot be regenerated for elapsed time.
- `data/mbta_gtfs.zip` — the static snapshot matching the recording window (MBTA "Summer 2026", valid 2026-08-12 → 2026-09-05). Replacing it silently invalidates every trip_id join.
- `data/record_feed.py` — while a recording is in progress. Confirm the recorder is stopped first.
- `data/recorder.log` — the only record of feed gaps and failed polls.
- `PRAVAAH_SIH_Internal_Deck.pptx`, `SIH_NITK_241EC148_D4CULT.pdf`, `Transit_Crowding_Route_Prediction_Solution_Architecture (1).docx` — submission artifacts.
- `.env` / `.env.production` — secrets (none exist yet).

## How to Run
```bash
# Install the recorder's dependency (that is the whole dependency set today)
pip install gtfs-realtime-bindings

# Record the live MBTA feed — currently the only runnable thing in the project
cd data && python record_feed.py --interval 20
#   ...or double-click data/START_RECORDING.bat on Windows (keeps the console open)
#   --no-trips        skip TripUpdates entirely
#   --trip-every N    poll TripUpdates only every Nth cycle (default 15; ~22k rows per poll)
#   --keep-raw        also archive raw .pb frames for exact replay
# Ctrl+C stops it and prints totals.

# Watch progress
tail -f data/recorder.log

# Dev server  — none yet (no FastAPI app exists)
# Tests       — none yet (no test runner configured)
# Lint        — none configured
```

## Key Reference Files
- **★ BINDING SPEC:** [`docs/SOLUTION.md`](docs/SOLUTION.md) — Part I is the architecture (§4 requirements FR-01…FR-16, §6 data strategy, §9 ML, §10 routing/ranking, §12 API + event contracts, §20 roadmap P0–P7, §21 KPIs, §23 stack); **Part II is the implementation contract** (§25 repo layout, §26 code-level contracts, §27 DDL, §28 module specs, §29 API schemas, §30 config, §31 build order with acceptance gates, §32 conventions). Appendix C is the doc change log — every deviation is recorded there.
- **Frozen original:** `Transit_Crowding_Route_Prediction_Solution_Architecture (1).docx` — the 27 Aug submission artifact. Superseded by `docs/SOLUTION.md` for all engineering purposes; retained unmodified for provenance.
- **Scope and claims:** `PRAVAAH_SIH_Internal_Deck.pptx` — slide 5 (competitor comparison), slide 7 (data strategy and measured feed counts), slide 9 (stack + promised deliverables).
- **Canonical row schemas:** `data/record_feed.py` — `VP_COLS` and `TU_COLS` define the column contract every downstream reader must follow.
- **Static network:** `data/mbta_gtfs.zip` — `routes.txt`, `stops.txt`, `trips.txt`, `stop_times.txt`, `shapes.txt`, `calendar*.txt`.
- **Feed endpoints:** the `FEEDS` dict in `data/record_feed.py` (MBTA VehiclePositions + TripUpdates, no API key required).
---
## Behavioral Guidelines

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

### 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it — don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

---
## Session Protocol

### On Session START → Read in this order:
1. This file (CLAUDE.md)
2. `PROJECT_STATE.md` → current status
3. `.context/session.json` → machine-readable last-session state
4. `.context/dead_ends.md` → approaches already ruled out
5. Last **3 entries** of `CHANGELOG.md` (most recent first)

Then respond with:
- 3-bullet summary of your understanding of the current state
- The single next action you recommend
- Any ambiguities or conflicts you noticed

**Do NOT start any work until the user confirms your understanding is correct.**

### On Session END → Do this before closing:
1. Update `PROJECT_STATE.md` (status, last-updated timestamp, next step)
2. Prepend entry to `CHANGELOG.md` using the format in that file
3. Append any new dead ends to `.context/dead_ends.md`
4. **Archive then regenerate `.context/session.json`:**
   - Copy existing `.context/session.json` to `.context/sessions/<generated_at-ISO>.json` (use the `generated_at` timestamp already inside the file; replace `:` with `-` for filesystem safety, e.g. `2026-05-28T22-23-00+0530.json`). Create `.context/sessions/` if it doesn't exist.
   - Then regenerate `.context/session.json` with this session's data. The canonical path always holds the LATEST; history lives in the archive folder.
5. **Prepend a detailed entry to `SESSION_LOG.md`** — this is the user's personal journal, NOT an AI handoff file. It must be verbose and honest. **Required in every entry:**
   - Exact **date AND time** for both start and end of session (with timezone)
   - **Exact file paths** of every file you touched (not vague summaries — full paths with line numbers where useful)
   - What went right, what went wrong, what got redone, and what you were uncertain about
   - Follow the template/format already in `SESSION_LOG.md`
6. Commit all files: `git add -A && git commit -m "session: <one-line summary>"` — **do NOT push; only push when the user explicitly asks**
