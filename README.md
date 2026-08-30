# PRAVAAH

Predicting how crowded a bus will be **when it reaches your stop** — not how crowded it is now,
somewhere else on the route.

An SIH 2026 entry (NIT Karnataka, Surathkal) for *"Intelligent Public Transport Crowding &
Route Prediction"*. The same forecasts drive three surfaces: a passenger app, an operator
control room, and a conductor console.

## What it actually does

A passenger searches Red Fort → Chandni Chowk and picks a preference. The planner returns
several journeys, each carrying a **predicted crowd band** for the bus they would board, and a
plain-language reason for its rank. Choosing a different preference returns a different bus:

| Preference | Optimises | Typical pick |
|---|---|---|
| Fastest | arrival time | quickest bus, even if it may be near crush |
| Least crowded | predicted load | a slower bus with a lower band |
| Most reliable | forecast confidence | the bus with the **narrowest** p10–p90 band |
| Balanced | all three | the compromise |

Routing stays deterministic and explainable. **Machine learning predicts the conditions routes
will face; it does not pick routes.**

## Honesty rules the code actually enforces

These are correctness requirements here, not presentation preferences:

- **Predictions are distributions.** Crowd is emitted as p10/p50/p90 and never collapsed to a
  single number in any response or screen.
- **Missing occupancy is `UNKNOWN`** — never `0`, never "empty bus". Roughly a third of real
  vehicle rows carry no occupancy, and drawing a blank as empty is a bug.
- **Provenance is mandatory.** Every record keeps `source_type`
  (`PUBLIC_FEED` / `APC` / `CROWDSOURCED` / `SIMULATED`) and its timestamp.
- **Fallbacks are disclosed.** A forecast served from a coarser table is labelled
  *"estimated from history"* in the UI rather than presented as a route-specific prediction.
- **Every ranked option carries a reason code.** Explainability is an acceptance criterion.

## The data is synthetic — and says so

The city is **Delhi** and the network, vehicle movement and crowding are **generated**
(`src/pravaah/sim/`), tagged `SIMULATED` on every record. The load curve is fitted from a real
recorded MBTA corpus (~1.2 GB of GTFS-Realtime with genuine operator occupancy labels), which
is used as a *statistical base only* — no Boston place, route or trip appears anywhere in the
product. Hours the corpus could not measure are stored as `null`, not filled in.

No real Delhi feed is ingested today. Nothing in the demo requires the internet except map
tiles and road geometry.

## Running it

```bash
./scripts/demo.sh            # Postgres + Redis + simulator + API on :8000
./scripts/demo.sh --tunnel   # ...and a public HTTPS URL

cd pravaah_frontend/build/web && python3 -m http.server 8090
```

Then open <http://localhost:8090>.

The app resolves its backend **at runtime**: served from localhost it calls `localhost:8000`,
served from anywhere else it calls the public API. One build serves both, so a dropped tunnel
never breaks the local demo.

Staff sign-in is under **Profile → Staff**:

| Role | Username | Password |
|---|---|---|
| Operator | `operator` | `pravaah-demo` |
| Conductor | `conductor` | `pravaah-demo` |


## Machine Learning
RLHF was used for training data over crowded places in which the buses are often filled. LightBGM was used for the mvp.
## API

Passenger endpoints need no credentials. Everything under `/v1/admin/*` requires an operator
token; shift and occupancy writes require a conductor token. The role is read from the signed
token, never from the request.

```
GET  /v1/health
GET  /v1/vehicles?bbox=minLat,minLon,maxLat,maxLon
GET  /v1/vehicles/{vehicleId}
GET  /v1/stops/{stopId}/departures
GET  /v1/trips/{tripId}                 origin, destination, ordered stop path
GET  /v1/trips/{tripId}/forecast        predicted crowd at each upcoming stop
GET  /v1/plan?from_lat=&from_lon=&to_lat=&to_lon=&profile=
POST /v1/auth/login
POST /v1/shifts/start · /v1/shifts/{id}/position · /v1/shifts/{id}/end
POST /v1/occupancy/report
GET  /v1/admin/hotspots · /v1/admin/vehicles · /v1/admin/data-health
GET  /v1/admin/routes/{routeId}/forecast
```

Note `bbox` order is `minLat,minLon,maxLat,maxLon`.

## Layout

```
src/pravaah/
  contracts/  wire + provenance types; imports nothing else in the package
  adapters/   city-specific decoding -- the ONLY place a city name may appear
  ingest/     feed -> canonical events -> live state
  state/      Redis live vehicle + occupancy state
  models/     seasonal baseline, Monte Carlo forecaster, serving registry
  sim/        synthetic Delhi network, demand and vehicle movement
  api/        FastAPI: passenger, admin, conductor, auth
pravaah_frontend/   Flutter client (web, Android, iOS)
docs/SOLUTION.md    the binding specification
```

`docs/SOLUTION.md` is the contract: the repo layout, schemas, DDL and API shapes are fixed by
it. Deviating requires editing that document and logging the change in its Appendix C
**before** writing code.

## Tests

```bash
python -m pytest -q                      # 199 tests
python -m ruff check src/ tests/
cd pravaah_frontend && flutter analyze && flutter test
```

## Known limits

- Journey legs carry no `trip_id`, so the journey map routes through stop coordinates via OSRM
  rather than the exact operated shape. The dashboard map draws true geometry because it has
  the trip's stops.
- Landmark lookup knows ~61 Delhi places; a leg boarding elsewhere is skipped on the map.
- Some origin/destination pairs legitimately return no options — a network-coverage limit of
  the generated network, not a UI failure.
- Map tiles and road geometry are fetched over the network; a fully offline demo still needs
  bundled tiles.
