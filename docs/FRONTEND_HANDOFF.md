# FRONTEND HANDOFF — PRAVAAH

**For:** the frontend team · **From:** backend · **2026-08-30 (rev 4 — MVP)**

The city is **Delhi**. `city_id` is `"delhi"` everywhere. There is no other city in the API.

Every response below was **captured from the running server**, not written by hand.

---

## 1. Run it

```bash
docker compose up -d                            # Postgres + Redis
cd src
python -m pravaah.sim.generate --interval 5     # Delhi vehicles into live state
python -m uvicorn pravaah.api.main:app --port 8000
```

- Base URL: `http://localhost:8000`
- Interactive docs: `/docs` · OpenAPI schema: `/openapi.json`
- **Generate your client from `/openapi.json`.** Don't hand-write models.
  `openapi-generator` for Dart, `openapi-typescript` for the dashboard.

Map default viewport — Delhi bounds, but read them from the API rather than hardcoding:
`min_lat 28.35, max_lat 28.90, min_lon 76.80, max_lon 77.45` (centre ≈ 28.63, 77.21).

---

## 2. Working endpoints

### `GET /v1/vehicles?bbox=minLat,minLon,maxLat,maxLon&limit=500`

`bbox` is **required** — there is no fetch-everything call. `limit` caps at 2000.

```json
{
  "generated_at": "2026-08-30T07:31:13.972547Z",
  "city_id": "delhi",
  "count": 2,
  "vehicles": [
    {
      "vehicle_id": "DL0181",
      "trip_id": "DL429-1788073784",
      "route_id": "DL429",
      "direction_id": 1,
      "lat": 28.633284,
      "lon": 77.123581,
      "bearing": 102.8,
      "speed_mps": null,
      "stop_id": "DLS0290204",
      "current_status": "IN_TRANSIT_TO",
      "occupancy_class": "STANDING_ROOM_ONLY",
      "occupancy_ratio": 0.61,
      "ts": "2026-08-30T07:29:24.013941Z",
      "age_s": 109,
      "is_stale": false,
      "source_type": "SIMULATED",
      "quality_score": 1.0
    }
  ]
}
```

### `GET /v1/vehicles/{vehicle_id}`

```json
{
  "generated_at": "2026-08-30T07:31:14.041414Z",
  "city_id": "delhi",
  "vehicle": { "...same shape as the objects above..." }
}
```

`404` with the error shape when there is no live state for that id.

### `GET /v1/health`

```json
{"status":"degraded","city_id":"delhi","generated_at":"2026-08-30T07:30:59.217153Z",
 "database":false,"redis":true,"vehicles_tracked":300,"feed_version_id":null}
```

Dev banner only — never ship this in a passenger UI. `status` is `"degraded"` when a
dependency is down; the map still works on Redis alone.

### Error shape — the only one, everywhere

```json
{"error": {"code": "FEED_UNAVAILABLE", "message": "...", "request_id": "..."}}
```

Codes: `NO_ROUTE_FOUND`, `INVALID_COORDINATES`, `OUT_OF_SERVICE_AREA`, `FEED_UNAVAILABLE`,
`RATE_LIMITED`, `INTERNAL`. Handle unknown codes generically — the list grows.

---

## 3. Enums — the complete set, hardcode nothing else

| Field | Values |
|---|---|
| `occupancy_class` | `EMPTY`, `MANY_SEATS_AVAILABLE`, `FEW_SEATS_AVAILABLE`, `STANDING_ROOM_ONLY`, `CRUSHED_STANDING_ROOM_ONLY`, `FULL`, `NOT_ACCEPTING_PASSENGERS`, `UNKNOWN` |
| `current_status` | `INCOMING_AT`, `STOPPED_AT`, `IN_TRANSIT_TO` |
| `source_type` | `SIMULATED` (everything today), plus `REAL_OPERATOR`, `PUBLIC_FEED`, `APC`, `AFC`, `CROWDSOURCED`, `DERIVED` |

**Design all eight occupancy classes.** Delhi runs standing-room and crush routinely — a
300-bus fleet at midday sits around 47% few-seats, 30% many-seats, 22% standing, with crush
appearing at peak hours. This is not a system where "empty" is the common case.

`occupancy_ratio` is a 0–1 load fraction against crush capacity (100 passengers). It is an
ordinal position rendered as a fraction so you can draw a bar — not a measured load factor.

---

## 4. What the data is — and what you must say on screen

**Every vehicle carries `source_type: "SIMULATED"`. All of it is synthetic.**

- **The network is synthetic**, built over **real Delhi places at real coordinates** —
  Kashmere Gate ISBT, Connaught Place, Nehru Place, Dwarka, Anand Vihar, Azadpur and ~55
  more. Distances between named stops are real distances. Stop ids beginning `DLN` are real
  named places; `DLS` are generated intermediate stops along the corridor.
- **Crowding comes from a behavioural model** — passengers board and alight stop by stop,
  occupancy is the running sum, and it is clipped at Delhi crush capacity. It is not a random
  percentage, and it is conserved: everyone who boards alights by the terminus.
- **One borrowed quantity**: the load-along-the-run curve, fitted from a real recorded transit
  corpus. No place, route, identifier or crowding level from that corpus appears anywhere in
  this project. Delhi capacity, peak windows and demand scale are Delhi assumptions.

**This makes rule 6 below the most important thing on your screen.** A persistent, unmissable
"simulated data" treatment — a banner plus per-vehicle marking. If someone can screenshot your
map and pass it off as live Delhi data, the treatment is wrong.

---

## 5. The six data-state rules — binding, not styling

Each has an acceptance gate. Breaking one is a correctness defect, not a design opinion.

1. **Unknown is never empty.** Missing occupancy renders as "Unknown" in a neutral style —
   never 0%, never an empty bus, never the same colour as a genuinely empty one. Confidently
   telling someone to board a bus you know nothing about is the worst bug this product ships.
2. **Uncertainty is always visible.** Any forecast shown as a number carries its p10–p90 band.
3. **Every ranked option shows its reason.** Reason codes come from the API; never invent one.
4. **Stale data is labelled.** Use `is_stale` and `age_s` — both always present, so you never
   compute clock skew. Show a "live tracking delayed" badge rather than drawing an old position.
5. **Fallbacks are disclosed.** `is_fallback: true` renders as "estimated from history".
6. **Simulated data is marked.** See §4. Today this is everything.

Plus: **crowding is never conveyed by colour alone.** Every level carries a text label —
red/green is the pairing most affected by colour blindness, and this is a public transit app.

---

## 6. Navigation

**Passenger app (Flutter) — four tabs:** Home (search, nearby buses, saved stops) · Journey
(planner, becoming the live trip tracker once started) · Alerts & Saved · Profile.

**Operator dashboard (React web) — four views** in a persistent side nav, designed for 1440px
and wider: Fleet Command · Predicted Hotspots · Route Diagnostics · System Health.

---

## 7. Not in the MVP — future work

These are the honest answer to "where does real data come from?" — future improvements for
pulling real and reliable data:

| | Why it is deferred |
|---|---|
| `GET /v1/stops/{id}/departures` | Needs the network persisted to Postgres; the MVP network lives in the simulator only |
| `GET /v1/trips/{id}/forecast` | Baseline crowd model is written but not yet wired to an endpoint |
| `GET /v1/plan` — journey ranking | Routing engine not built |
| Conductor app, login, shift tracking | The path to real Delhi occupancy data; specified, not built |
| Operator `/v1/admin/*` endpoints | Specified, not built |
| Real Delhi GTFS + live vehicle feed | Official file host was unreachable today; download is form-gated |

Contracts for all of these are in `docs/SOLUTION.md` §29 and are stable — build against them
and integration becomes a base-URL change.

---

## 8. Rules of engagement

- **Don't work around a missing field.** If you need something that isn't there, ask — I amend
  the spec and implement it. Silent client-side workarounds hide missing backend capability
  until demo day.
- **The client holds no business logic.** It renders what the API returns and never computes a
  crowd level, forecast, ranking or ETA locally.
- CORS currently allows `http://localhost:5173` only — tell me your dev-server origin.
  Flutter is native and unaffected by CORS.
