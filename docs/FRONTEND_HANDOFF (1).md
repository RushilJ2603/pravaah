# FRONTEND HANDOFF — PRAVAAH

**For:** the frontend team
**From:** backend
**Date:** 2026-08-30 (rev 3)
**Status of this document:** authoritative for the client/server boundary. Where it disagrees
with `docs/SOLUTION.md`, SOLUTION.md wins and this file is the bug.

---

## 1. Who builds what

| Piece | Owner | Tech |
|---|---|---|
| Passenger + conductor app | Frontend team | Flutter (Android), MapLibre Native |
| Operator dashboard | Frontend team | React 18 + TypeScript + Vite, MapLibre GL JS |
| HTTP API, live state, ingestion, forecasting, routing | Backend (me) | FastAPI, Redis, TimescaleDB/PostGIS |
| Basemap tiles + APK hosting | Backend (me) | Caddy on the deploy VM |

**Two clients, one API.** The operator dashboard is a web app because a control room runs on a
desktop browser and a large screen. Passenger and conductor are one Flutter app with a role
switch in the profile tab — one thing to install for the demo, not three.

**The clients hold no business logic.** They render what the API returns. They never compute a
crowd level, a forecast, a ranking or an ETA locally. If you find yourself deriving one of those
on the device, that is a backend gap — tell me, don't patch around it.

---

## 2. What the API actually gives you today

Base path is `/v1`. Everything below is live and tested. Interactive docs at `/docs`,
machine-readable schema at `/openapi.json`.

### `GET /v1/vehicles?bbox=minLat,minLon,maxLat,maxLon&limit=500`

`bbox` is **required** — there is no "fetch the whole fleet" call, by design. `limit` defaults to
500 and is capped server-side.

```json
{
  "generated_at": "2026-08-30T11:47:30Z",
  "city_id": "mbta",
  "count": 2,
  "vehicles": [{
    "vehicle_id": "y2075",
    "trip_id": "76789790", "route_id": "64", "direction_id": 0,
    "lat": 42.3601, "lon": -71.0589,
    "bearing": 135.0, "speed_mps": null,
    "stop_id": "1234", "current_status": "IN_TRANSIT_TO",
    "occupancy_class": "UNKNOWN", "occupancy_ratio": null,
    "ts": "2026-08-30T11:47:12Z", "age_s": 18, "is_stale": false,
    "source_type": "PUBLIC_FEED", "quality_score": 0.96
  }]
}
```

### `GET /v1/vehicles/{vehicle_id}`
Same `vehicle` object, wrapped as `{generated_at, city_id, vehicle}`. `404` if there is no live
state for that id.

### `GET /v1/stops/{stop_id}/departures`
```json
{
  "generated_at": "...", "city_id": "mbta", "stop_id": "1234",
  "stop_name": "Nubian Station", "feed_version_id": 5,
  "departures": [{
    "trip_id": "76789790", "route_id": "64", "direction_id": 0,
    "scheduled_departure": "2026-08-30T11:52:00Z", "headsign": "Oak Square",
    "crowd_class": "UNKNOWN", "crowd_p50": null, "is_forecast": false
  }]
}
```

### `GET /v1/health`
`{status, city_id, generated_at, database, redis, vehicles_tracked, feed_version_id}`.
Use it for a dev-mode connectivity banner. Do not ship it in a passenger UI.

### Error shape — the only one, everywhere
```json
{"error": {"code": "FEED_UNAVAILABLE", "message": "...", "request_id": "..."}}
```
Codes today: `NO_ROUTE_FOUND`, `INVALID_COORDINATES`, `OUT_OF_SERVICE_AREA`, `FEED_UNAVAILABLE`,
`RATE_LIMITED`, `INTERNAL`. `SHIFT_NOT_ACTIVE` and `VEHICLE_ALREADY_CLAIMED` arrive with the
conductor endpoints. Handle unknown codes generically — the list grows.

### Enum values — hardcode nothing else

- `occupancy_class` / `crowd_class`: `EMPTY`, `MANY_SEATS_AVAILABLE`, `FEW_SEATS_AVAILABLE`,
  `STANDING_ROOM_ONLY`, `CRUSHED_STANDING_ROOM_ONLY`, `FULL`, `NOT_ACCEPTING_PASSENGERS`,
  `UNKNOWN`
- `current_status`: `INCOMING_AT`, `STOPPED_AT`, `IN_TRANSIT_TO`
- `source_type`: `REAL_OPERATOR`, `PUBLIC_FEED`, `APC`, `AFC`, `CROWDSOURCED`, `DERIVED`,
  `SIMULATED`

---

## 3. Three things about today's data that will confuse you if I don't say them

**1. `occupancy_class` is now populated — but a large minority is permanently `UNKNOWN`.**
Measured: 60.8% coverage on a single live poll, 77.8% across the 1.6-day recorded corpus.
This was a backend gap (occupancy was decoded from the feed and then dropped before reaching live
This was a backend gap (occupancy was decoded from the feed and then dropped before reaching live
state); it is now wired through ingestion → Redis → API. **Expect roughly a fifth to two fifths of
vehicles to come back `UNKNOWN` with a null ratio** at any moment, because the operator simply does
not report occupancy for them. That is not a bug, not a loading state, and not something that improves later. Design the
unknown state as a first-class visual, not as an edge case — it is over a third of your map.

Occupancy also **ages out independently of position**. A vehicle can have a fresh position and a
crowd reading that has expired; it then reads `UNKNOWN` rather than showing a stale number. So
`occupancy_class` can flip to `UNKNOWN` on a vehicle that is still moving normally. Do not treat
that as an error.

**2. `speed_mps` is deliberately `null`.** The raw feed's speed field had under 10% coverage, so
it is prohibited. A derived speed replaces it later. Do not display a speed until it is non-null.

**3. `crowd_p50` is `null` and `is_forecast` is `false` on every departure.** There is no
forecasting model yet. When it lands you will get a p10/p50/p90 band, not a single number.

---

## 4. What is coming, and what to stub

Build against the shapes; do not wait for the implementations.

| Endpoint | Gives you | Status |
|---|---|---|
| `GET /v1/trips/{id}/forecast` | Crowd + ETA per upcoming stop, as p10/p50/p90 | after forecasting lands |
| `GET /v1/plan` | Ranked itineraries with reason codes | after routing lands |
| `POST /v1/occupancy/report` | Passenger crowd report | spec'd, not built |
| `GET/WS /v1/journeys/{id}/stream` | Live re-scoring of an active journey | spec'd, not built |
| `POST /v1/auth/login`, `/v1/shifts/*` | Conductor login + shift lifecycle | spec'd, not built |
| `GET /v1/admin/hotspots`, `/admin/routes/{id}/forecast`, `/admin/data-health` | Operator dashboard data | spec'd, not built |

Exact request/response JSON for all of these is in `docs/SOLUTION.md` §29. **Those shapes are
contractual** — if you build to them, integration is a base-URL change.

**Do not hand-write models.** Generate them from `/openapi.json` (`openapi-generator` for Dart,
`openapi-typescript` for the dashboard) and regenerate when I tell you the schema moved. This is
how we stop the client and server drifting.

---

## 5. The six data-state rules — binding, not styling

These come from `docs/SOLUTION.md` §33.3. Each one has an acceptance gate. Violating one is a
correctness defect, not a design opinion. They apply to **both** clients.

1. **Unknown is never empty.** A missing occupancy renders as "Unknown" in a neutral style. Never
   as 0%, never as an empty vehicle, never in the same colour as a genuinely empty one. About 31%
   of real rows have no occupancy — if unknown looks empty, the app confidently tells people to
   board a bus it knows nothing about. This is the single most damaging bug this product can ship.
2. **Uncertainty is always visible.** Any forecast shown as a number carries its p10–p90 band. A
   bare point estimate is a defect.
3. **Every ranked option shows its reason.** Reason codes come from the API. The client never
   invents an explanation.
4. **Stale data is labelled.** Use `is_stale` and `age_s` — both are always present so you never
   compute clock skew yourself. When stale, show a "live tracking delayed" badge rather than
   silently drawing an old position.
5. **Fallbacks are disclosed.** `is_fallback: true` renders as "estimated from history".
6. **Simulated data is marked.** Anything with `source_type: "SIMULATED"` is visibly tagged and
   never presented as operator data.

Plus, from §33.5: **crowding is never conveyed by colour alone.** Every crowd level carries a text
label. Red/green is the exact pairing most affected by colour blindness, and this is a public
transit app.

---

## 6. Navigation

**Passenger — four tabs**

| Tab | Contents |
|---|---|
| Home | "Where to?" search, nearby vehicles, saved stops, recent destinations |
| Journey | Planning mode (origin/destination, four preference profiles, ranked options with reasons). Becomes the live journey tracker once a trip starts. |
| Alerts & Saved | Saved routes available offline, disruptions, commute alerts |
| Profile | Accessibility settings, theme, role switch |

**Conductor — one screen.** Shift start (pick route + service), four large high-contrast crowd
buttons, shift end. Usable one-handed, in sunlight, by someone who is also doing their actual job.
No operator role in the mobile app.

**Operator — web, four views** in a persistent side nav (desktop layout, not tabs): Fleet Command,
Predicted Hotspots, Route Diagnostics, System Health. Design for 1440px and wider; it does not
need to be phone-responsive. The operator's entire value is **lead time** — a hotspot without a
lead time is just a report of something already going wrong, which is the status quo we exist to
beat.

---

## 7. Auth

| Role | Access |
|---|---|
| Passenger | Anonymous. No login, no account, no credentials in the build. |
| Conductor | Signs in. May write position + occupancy **for their own active shift only**. |
| Operator | Signs in. Read-only across the fleet, plus scenario endpoints. |

Short-lived bearer tokens, sent as `Authorization: Bearer <token>`. Credentials are issued out of
band — **there is no public sign-up screen, do not build one.**

A conductor position report is only accepted while a shift is active. The shift is what binds a
phone to a vehicle and a trip; without it a GPS point cannot be joined to the network and is
useless. Starting a shift on a vehicle that already has one fails with `VEHICLE_ALREADY_CLAIMED`
— surface that clearly, it is the "two crew members opened the app" case.

Background location is requested **only** for an active shift, disclosed in-app, and stops when
the shift ends.

---

## 8. Map and basemap

- **No proprietary tile key, ever.** The basemap is a self-hosted Protomaps `.pmtiles` extract
  served from our VM, and it must work with networking disabled — the demo has to run offline.
  I will give you the URL and the file.
- Both clients use MapLibre (Native on Flutter, GL JS on web) against that same tile source.
- **Always request by viewport bbox.** Never try to fetch the whole fleet; the endpoint will
  refuse.
- Animate markers between updates rather than letting them jump. Polling is roughly every 15–20 s,
  so without interpolation the buses teleport.
- Streaming runs only while a live screen is foregrounded, and stops when the app is backgrounded.
  Continuous polling from a mobile client is a defect — it holds the radio awake and eats battery.

---

## 9. Which city, and what the data is

**Decided: the demo is Delhi. Boston is the evidence, not the stage.**

Two cities doing two different jobs, and the difference must be visible in the UI:

| | Delhi | Boston (MBTA) |
|---|---|---|
| Role | The demo city — what the audience sees | The evidence city — where accuracy claims come from |
| Network, stops, route names | Real Delhi GTFS (543 routes, 3,464 stops, 16,562 trips) | Real MBTA GTFS |
| Vehicle movement | **Simulated** | Real recorded feed |
| Crowding | **Simulated**, from a demand model calibrated on Boston's real data | **Real** operator occupancy labels |

Why: no Indian transit agency publishes machine-readable occupancy — verified, and it is the exact
gap this project exists to fill. So Delhi crowd numbers are generated by a behavioural simulator
whose parameters are *measured from* Boston's real corpus, not invented.

**What this means for you, concretely:**

- **Every Delhi vehicle will carry `source_type: "SIMULATED"`.** Rule 6 in §5 stops being a
  checkbox and becomes the most visible thing on the screen. It needs a real, always-present
  treatment — a banner, a badge on each vehicle, something that cannot be missed — not a tooltip.
  If a viewer can screenshot your map and present it as live Delhi data, the treatment is wrong.
- Boston vehicles will carry `PUBLIC_FEED` / `REAL_OPERATOR` and must look visibly different.
- `city_id` will be `"delhi"` for the demo and `"mbta"` for the real-data views. **Still read the
  city and bounds from the API** — you may need to show both in one session.

**One caveat you should know about**, because it will show up in the data: Boston's corpus contains
**zero** `STANDING_ROOM_ONLY` and `CRUSHED_STANDING_ROOM_ONLY` observations. Its measured
distribution is 87% many-seats, 11.8% few-seats, 1.2% full. Delhi routinely operates in the
crush range Boston never reports, so those upper classes come from Delhi capacity norms rather
than from transferred Boston behaviour. **Design and test all eight occupancy classes anyway** —
including the two Boston never produces — because Delhi will produce them.

What is real, so you label it honestly:
- Vehicle positions and occupancy: **real**, from the MBTA public feed (`PUBLIC_FEED` /
  `REAL_OPERATOR`), recorded continuously since 2026-08-28.
- Routes, stops, timetables: **real** MBTA static GTFS — 399 routes, 9,630 stops, 2.2M stop-times.
- Forecasts: will be **real model output** trained on the recorded corpus, tagged `DERIVED`.
- Conductor reports during a demo, with no real crew on board: **simulated**, tagged `SIMULATED`,
  and rule 6 says you must show that.

---

## 10. Environments

| | Base URL |
|---|---|
| Local | `http://localhost:8000` (`uvicorn pravaah.api.main:app --reload`) |
| Deployed | HTTPS on the demo VM — URL to follow |

TLS is mandatory in deployment because Android blocks cleartext HTTP by default. CORS is currently
allowed only for `http://localhost:5173` (the Vite dev server) — tell me if the dashboard dev
server runs anywhere else. Flutter is a native client and is unaffected by CORS.

---

## 11. How to change the contract

`docs/SOLUTION.md` is binding: code is written to match it, and a change that diverges from it is
a defect even if it works. So if you need a field that isn't there, a different shape, or a new
endpoint — **ask, don't work around it.** I amend the document first, then implement. Turnaround
is fast; silent client-side workarounds are what we're avoiding, because they hide missing
backend capability until demo day.

---

## 12. What I need back from you

1. **Flutter and Android SDK are not installed here.** Confirm your team has a working toolchain
   and a physical device or emulator for the demo — this is the first thing that can silently
   block A.4.
2. **Confirm the four passenger tabs and the four operator views**, or send changes now, while
   changing them is free.
3. **Which screens do you want stubbed first?** I can prioritise returning realistic shaped data
   for a screen you are actively building.
4. **Your dashboard dev-server origin**, so I can widen CORS.
5. **Anything in §5 you think you cannot honour.** Those six rules are gates — if one is going to
   be a problem, I need to know before it fails at review, not after.

Ping me on anything ambiguous here. An assumption written into the client is much more expensive
to unwind than a question.
