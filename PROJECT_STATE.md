# PROJECT_STATE.md
# ── Living State Document — Update Every Session ────────────────
# Last Updated: 2026-08-30 15:10 IST | By: AI (Claude Opus 5)

## Current Phase
**Backend feature-complete — Delhi, synthetic.** The network, vehicle movement and crowding are
all **synthetic and tagged `SIMULATED`**. Slice A complete; B (predict), C (decide) and E
(operators) delivered; H (simulator) built; **G (conductor mode + staff auth) built by Codex and
verified**. Remaining work is **demo enablement, not features**.

## Current Status
**14 endpoints live, verified against a running server. 199 tests pass** (124 unit + 75
integration), ruff clean.

| Endpoint | Status |
|---|---|
| `GET /v1/health` | ✅ |
| `GET /v1/vehicles` (bbox required) | ✅ crowd + provenance |
| `GET /v1/vehicles/{id}` | ✅ |
| `GET /v1/stops/{id}/departures` | ✅ real schedule from feed_version 6 |
| `GET /v1/trips/{id}/forecast` | ✅ p10/p50/p90 per upcoming stop |
| `GET /v1/plan` | ✅ ranked options with reason codes, 4 profiles |
| `GET /v1/admin/hotspots` | ✅ severity + lead time |
| `GET /v1/admin/routes/{id}/forecast` | ✅ hour-by-hour |
| `GET /v1/admin/vehicles` | ✅ full fleet, no bbox |
| `GET /v1/admin/data-health` | ✅ freshness + occupancy coverage |
| `POST /v1/auth/login` | ⚠️ works, but **no accounts exist** |
| `POST /v1/shifts/start` · `/{id}/position` · `/{id}/end` | ⚠️ built + tested, unreachable without a login |
| `POST /v1/occupancy/report` | ⚠️ built + tested |

All `/v1/admin/*` routes are gated behind `require_operator`; conductor writes behind
`require_conductor` (§15.3).

Running infrastructure: Compose stack up — TimescaleDB + PostGIS on **host port 15432**, Redis
6379. Synthetic Delhi network persisted as **feed_version_id 6**: 490 stops (61 real named Delhi
places + 429 generated intermediates), 51 routes, 8,568 trips, 113,568 stop_times.

**Occupancy pipeline fixed this session.** It had been decoded from the feed and then silently
dropped before reaching live state, so every response returned `UNKNOWN`. Now flows
ingestion → Redis → API and is verified live.

**The model is trained and serving.** `config/models/baseline_v1.json` was fit on 48,766 train /
12,192 test rows with a **chronological** split: band coverage 0.87, MAE 0.153, pinball losses
recorded. It is served through `models/registry.py` and the live API reports
`model_version: "seasonal_median_v1+simulated"` — the trained baseline, falling back to the Monte
Carlo table only for cells with no learned history. Coverage is **100% at the (hour, position)
level with zero fallback**; 71% of route-hour combinations have learned history. The artifact
stamps itself `real_world_accuracy: false` and
`SIMULATOR_PERFORMANCE_ONLY_NOT_REAL_WORLD_ACCURACY`.

Training history in the database: **60,958 rows spanning 2 days with all 24 hours covered evenly**
(~2,500 rows/hour), written by `sim/generate.py --persist-history`.

## Blocking Issues
- **NO STAFF ACCOUNTS EXIST.** `app_user` has zero rows and `provision_user()` (in
  `api/auth.py`) has no CLI entry point. `POST /v1/auth/login` therefore always fails and every
  `/v1/admin/*` route returns 401. **The operator dashboard and conductor mode are fully built,
  fully tested, and completely unreachable at runtime.** This is the single blocker for demoing
  those two roles.
- **No clock control.** `api/deps.now()` and the simulator both use real time, so only the
  current hour can ever be demonstrated. Showing a normal day — morning crush, midday, evening
  peak, late-night lull — is impossible without a time override or accelerated clock. This is the
  highest-value remaining item for the demo.
- **Auth failures return the wrong error code.** `ErrorCode` has no `UNAUTHORIZED`/`FORBIDDEN`,
  so a 401 serializes as `{"code": "INTERNAL"}` and a client cannot tell "log in again" from
  "server broke".

## Next Session Must Start With
> **Demo enablement, in this order:**
> 1. **Clock control** — a time override plus optional acceleration. Without it "a normal day
>    using the app" cannot be shown at all.
> 2. **Seed staff accounts** — a small CLI over the existing `provision_user()`. Unblocks
>    operator and conductor.
> 3. **Add `UNAUTHORIZED` / `FORBIDDEN`** to `ErrorCode`.
> 4. **One-command demo runner** — compose up, persist network, seed users, start simulator,
>    start API, wait for health. Five manual steps today, each with a gotcha.
> 5. **Refresh `docs/FRONTEND_HANDOFF.md`** — still rev 4, documents 5 of 14 endpoints. The app
>    team is building against a doc missing two thirds of the API.

## Environment Notes
- OS: Windows 11. Python 3.12.10 at
  `/mnt/c/Users/jishu/AppData/Local/Programs/Python/Python312/python.exe`.
  **The WSL `python3` does NOT have the project dependencies — always use the Windows interpreter.**
- Modules must run from `src/` (`cd src && python -m pravaah...`); `pyproject.toml` sets
  `pythonpath=["src"]` for pytest only, not for `-m`.
- **DB DSN now points at 15432 in `config/settings.toml`** — the long-standing mismatch is fixed.
- **Connection pool timeout raised to 30 s** in `api/deps.py`; 5 s was shorter than the
  WSL→Docker hop and left every schedule endpoint returning 503 for the process lifetime.
- Docker Desktop must be started manually; `docker` is not on the WSL PATH, use `docker.exe`.
- **Do not use `pkill -f uvicorn`** — it matches and kills the agent's own shell (exit 144).
- Node/Flutter: **not installed**. The frontend is another team's.

## Recent Decisions (this phase)
| Decision | Rationale | Date |
|---|---|---|
| **Delhi is the demo city; everything is synthetic and tagged `SIMULATED`** | Owner wants an Indian city. Verified no Indian agency publishes machine-readable occupancy, and the Delhi GTFS host was unreachable. Owner chose synthetic over waiting. | 2026-08-30 |
| **Boston removed from every shipped artifact** | Owner: "no connection to Boston whatsoever otherwise". Only the fitted load curve survives, carrying no Boston identifiers. `mbta_v1.json` deleted. | 2026-08-30 |
| Simulator demand scale raised so midday runs standing-room and peak reaches crush | The first run inherited the source corpus's uncrowded shape (85% many-seats), wrong for Delhi's reported ~88% load factor. Marked ASSUMPTION. | 2026-08-30 |
| Routing stays deterministic; the model only predicts conditions | Explainability is an acceptance criterion. `/v1/plan` candidates come from the timetable; ranking is an explicit weighted cost. | 2026-08-30 |
| agy/Antigravity delegation abandoned for this repo | Two delegations failed with `timeout waiting for response`; the 9p bridge costs 20s+ per file read and inverts the break-even. | 2026-08-30 |

## Known Issues / Tech Debt
- **Every Delhi number is an ASSUMPTION**, marked as such in `config/cities/delhi.toml` and
  `sim/demand.py`: capacity 35 seated / 70 peak / 100 crush, the hourly demand curve, the weekly
  pattern, and arterial speeds. The research that produced them returned **citations whose URLs
  appeared fabricated**, so none were treated as sourced. Replace from the primary MoHUA Urban Bus
  Specification before any claim rests on them.
- ~~Indexes created outside a migration~~ — **fixed**, now `migrations/006_schedule_indexes.sql`.
- ~~No tests for forecast, plan or admin~~ — **fixed**: `tests/integration/test_forecast_admin_api.py`,
  `test_operator_auth.py`, `test_conductor_db.py`, `tests/unit/test_baseline.py`,
  `test_conductor_api.py`, `test_model_registry.py`.
- **The route-and-position-specific model level is sparse** — ~126 cells against ~12,240 possible,
  so route-specific lookups usually answer from a coarser key and return `is_fallback: true`.
  That is honest behaviour and the UI must render it as "estimated from history" (§33.3 rule 5),
  but "trained per route" would overstate it.
- `/v1/plan` finds **direct services only** — no transfers. Honest for an MVP, but the
  `transfers` field is always 0 and `fewest_transfers` therefore cannot differentiate.
- The recorded MBTA corpus (~1.3 GB) is still on disk and still git-ignored. It is no longer used
  by anything except `sim/calibrate.py`.
- `data/record_feed.py` shows as modified — whole file converted to CRLF, zero logic change.
  Revert once no recorder is running.
- Delhi GTFS static is downloadable from `otd.delhi.gov.in` behind a purpose form (543 routes,
  3,464 stops, 16,562 trips), but its file host `traffickarma.iiitd.edu.in:9010` refused
  connections. Real network import remains available later.

## Reference Links
- Binding spec: [`docs/SOLUTION.md`](docs/SOLUTION.md) — §28.9 simulator, §31 Slice H, §12.5 conductor.
- Frontend contract: [`docs/FRONTEND_HANDOFF.md`](docs/FRONTEND_HANDOFF.md) — rev 4, Delhi only.
- Delhi OTD: https://otd.delhi.gov.in/data/static/
