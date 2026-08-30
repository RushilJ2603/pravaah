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
