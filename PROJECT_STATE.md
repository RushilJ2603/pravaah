# PROJECT_STATE.md
# ── Living State Document — Update Every Session ────────────────
# Last Updated: 2026-08-30 07:05 IST | By: AI (Claude Opus 5, context bootstrap)

## Current Phase
**Phase P0 — Data foundation**, and only the *collection* half of it. Per the roadmap in §20 of
`Transit_Crowding_Route_Prediction_Solution_Architecture (1).docx`, P0's exit criteria are
"real network visible; feed versioning works" — neither is met. There is no application code,
no database, no schema, and no repository. P1–P7 have not been started.

## Current Status
A single Python script, `data/record_feed.py`, has been polling the MBTA GTFS-Realtime feeds
every 20 s since **2026-08-28 19:33 IST** and is **still running as of 06:54 IST today**
(3,372 polls, zero failed polls in the log). It has accumulated ~1.27M vehicle-position rows
(411 MB) and ~4.78M stop-time updates (864 MB) alongside an 18.5 MB static GTFS snapshot —
~1.2 GB total. Sampling confirms the data is genuinely usable: 68.8% of vehicle rows carry a
real operator-reported `occupancy_status`, 92.3% carry a `stop_id`, 100% carry a `trip_id`.

Everything else exists only as design. No `src/`, no `tests/`, no `requirements.txt`, no
FastAPI service, no PostGIS/Redis instance, no models, no frontend. The project is not under
version control. The design itself is thorough and settled: a 25-section architecture document
and a 10-slide deck define requirements FR-01…FR-16, the event contracts, the P0–P7 roadmap
and the technology choices.

## Blocking Issues
- **Not a git repository.** `git rev-parse` fails at the project root. The Session Protocol's
  step 6 (`git add -A && git commit`) cannot run, so no session can be closed correctly.
- **`git add -A` would commit ~1.2 GB of CSV** the moment a repo exists. A `.gitignore`
  excluding `data/*.csv`, `data/*.zip` and `data/recorder.log` must land *before* the first
  `git add`, or the history is permanently poisoned.
- **The context bundle is in `templatesv2/`, not at the project root.** Every path in the
  Session Protocol and in `session_prompts.md` is root-relative, and Claude Code auto-loads
  `CLAUDE.md` only from the root. Until the bundle is moved up one level, the whole ritual
  silently targets files that do not exist.

## Next Session Must Start With
> Make the repo safe and the ritual functional, in this exact order — do not create source
> code first: (1) write `.gitignore` at the project root ignoring `data/*.csv`, `data/*.zip`,
> `data/recorder.log`, `data/raw/`, `__pycache__/`, `.env`; (2) move `templatesv2/CLAUDE.md`,
> `PROJECT_STATE.md`, `CHANGELOG.md`, `SESSION_LOG.md`, `session_prompts.md` and
> `templatesv2/.context/` up to the project root and delete the empty `templatesv2/`;
> (3) `git init` and commit that baseline, verifying with `git status` that **no file over
> 10 MB is staged**; (4) then write `requirements.txt` pinning `gtfs-realtime-bindings==2.2.0`
> and `protobuf==7.36.0`. Only after that begin P0 proper — the GTFS importer.

## Environment Notes
- OS: Windows 11 Home Single Language 10.0.26200
- Python: 3.12.10 (`C:\Users\jishu\AppData\Local\Programs\Python\Python312`). Installed packages relevant to this project: `gtfs-realtime-bindings` 2.2.0, `protobuf` 7.36.0. **No pandas, numpy, fastapi, lightgbm, scikit-learn or redis client is installed.**
- Node: v24.15.0 (nothing uses it yet — no `package.json` anywhere)
- Docker: 29.5.3 installed and available (the planned Compose stack is feasible locally)
- DB: **none.** No PostgreSQL/PostGIS, no Redis; `psql` is not on PATH. All state is CSV in `data/`.
- Git: 2.51.0.windows.2 installed, but the project root is **not** a repo.
- Shell: PowerShell 5.1 is primary; Git Bash also available. Note that large `bash` heredocs get mangled here — write files with the editor/Write tool rather than piping heredocs through the shell.
- Disk: `data/` is ~1.2 GB and grows roughly 35 MB/hour while the recorder runs. Check free space before leaving it running for multiple days.
- Timezone: IST (UTC+05:30). The recorder writes `ingest_ts` in **UTC**; `recorder.log` timestamps are **local IST**. Do not confuse the two when joining.

## Recent Decisions (this phase)
| Decision | Rationale | Date |
|---|---|---|
| Record **MBTA (Boston)** rather than the Delhi network named in the architecture doc | MBTA publishes GTFS-Realtime with **no API key** *and* real operator-reported `occupancy_status` on ~69% of vehicles. Delhi OTD requires an access request and publishes no occupancy — i.e. no crowd labels to train on. Rationale is stated in the `record_feed.py` docstring. | 2026-08-28 |
| Run the recorder continuously and leave it running overnight | Live occupancy labels cannot be back-filled; every hour not recorded is training data lost forever. | 2026-08-28 |
| Poll TripUpdates only every 15th cycle (`--trip-every 15`) | Each TripUpdates poll emits ~22–26k rows; polling it every cycle would multiply storage ~15× for near-duplicate content. | 2026-08-28 |
| Keep routing deterministic (RAPTOR/CSA); ML predicts conditions only | Explainability is an acceptance criterion — a ranked itinerary must be traceable to reason codes, which a learned router cannot provide. | 2026-08-27 |
| Strong baseline (historical/GBDT) before any deep model | Debuggability and honest evaluation; §22 lists model over-complexity as a named risk. | 2026-08-27 |
| Emit forecasts as quantiles (p10/p50/p90), never point estimates | Calibration is a stated KPI and uncertainty is a pitch differentiator ("uncertainty is shown, not hidden"). | 2026-08-27 |

## Known Issues / Tech Debt
- **Docs disagree with the data.** The architecture doc §2.4 fixes the reference geography as **Delhi** and its references R1–R3 are Delhi OTD, but every byte collected is **MBTA Boston**, and the deck's slide 7 quotes MBTA numbers (399 routes / 10,297 stops / 2.2M stop-times — all three verified correct against `mbta_gtfs.zip`). The doc needs updating or the divergence needs to be deliberate and stated.
- **`mbta_trip_updates.csv` is ~864 MB of heavy redundancy.** Each TripUpdates poll re-dumps the full future stop-time table (~22k rows), so consecutive polls are near-identical. It needs dedup + Parquet conversion before it is usable for training; treat the raw CSV as an archive, not a feature source.
- **`speed` is effectively unavailable**: only 9.8% of sampled vehicle rows have it. `bearing` is 80.5%. Do not plan features on `speed`. Derive speed from consecutive positions instead.
- **`record_feed.py` uses the deprecated `datetime.datetime.utcnow()`** (in `poll_vehicles`, the `--keep-raw` branch). Harmless today but deprecated in 3.12; fix when the recorder is next stopped.
- **No `requirements.txt` / `pyproject.toml`.** Dependencies are implicit and undocumented.
- **No tests, no linter, no CI.** Nothing is configured.
- **The recorder has no rotation or size cap.** It appends to one CSV forever; a multi-day run will produce files too large for pandas to load in one pass on a laptop.
- **`SIH_NITK_241EC148_D4CULT.pdf` was not machine-read** during this bootstrap (text extraction failed). Its contents are assumed to overlap the deck; open it manually if it matters.

## Reference Links
- MBTA VehiclePositions feed (no key): https://cdn.mbta.com/realtime/VehiclePositions.pb
- MBTA TripUpdates feed (no key): https://cdn.mbta.com/realtime/TripUpdates.pb
- GTFS Schedule reference: https://gtfs.org/documentation/schedule/reference/
- GTFS-Realtime VehiclePositions (occupancy semantics): https://gtfs.org/documentation/realtime/feed-entities/vehicle-positions/
- Open-Meteo historical weather API (planned weather features): https://open-meteo.com/en/docs/historical-weather-api
- TfL open data / BUSTO boardings-and-loadings (external crowd benchmark): https://tfl.gov.uk/info-for/open-data-users/our-open-data
- Delhi Open Transit Data (original reference geography in the doc): https://otd.delhi.gov.in/data/static/ · https://otd.delhi.gov.in/data/realtime/
