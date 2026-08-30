# PRAVAAH — Solution Architecture & Implementation Contract

**Intelligent Public Transport Crowding & Route Prediction**
Smart India Hackathon 2026 · NIT Karnataka, Surathkal

| Document item | Value |
|---|---|
| Problem statement | Intelligent Public Transport Crowding & Route Prediction |
| Primary users | Passengers, transit control-room operators, planners |
| Deployment target geography | Delhi bus network (adaptable to any GTFS-based system) |
| Development substrate | **MBTA (Boston)** — stand-in feed, see §6.2 |
| Architecture style | Event-driven spatiotemporal data platform + ML inference + multi-objective routing |
| Prototype profile | Single-node/container deployment on real GTFS + live vehicle data with a pluggable occupancy feed |
| Production profile | Horizontally scalable services with streaming ingestion, model serving, observability and resilient storage |
| Original document date | 27 August 2026 |
| This revision | 30 August 2026 |

---

## ⚠ Status of this document

**This document is binding.** The codebase is built exactly to this specification.

If an implementation needs to deviate — a different schema, a different module boundary, a
different library, a different endpoint shape — the change is **proposed here first, approved
by the project owner, and only then written into code**. A commit that diverges from this
document without a corresponding prior edit here is a defect, regardless of whether it works.

Practical consequence for anyone (human or AI) working on this repo:

1. Read the relevant section before writing code.
2. If the section does not answer your question, the section is incomplete — **propose an edit**, do not improvise.
3. If your approach conflicts with a section, **propose an edit and wait for approval**.
4. Deviations discovered after the fact are reconciled by changing the code, not by retro-fitting the document.

`Transit_Crowding_Route_Prediction_Solution_Architecture (1).docx` is the frozen original
submission artifact and is **superseded by this file** for all engineering purposes. It is
retained unmodified for provenance. This Markdown version exists because a binary `.docx`
cannot be diffed, reviewed or version-controlled, which the rule above requires.

---

## Contents

**Part I — Product and architecture**
1. [Executive summary](#1-executive-summary)
2. [Problem definition and scope](#2-problem-definition-and-scope)
3. [Stakeholders and use cases](#3-stakeholders-and-use-cases)
4. [Requirements](#4-requirements)
5. [Architecture principles and key decisions](#5-architecture-principles-and-key-decisions)
6. [Data architecture and real-data strategy](#6-data-architecture-and-real-data-strategy)
7. [End-to-end logical architecture](#7-end-to-end-logical-architecture)
8. [Component design](#8-component-design)
9. [Machine-learning architecture](#9-machine-learning-architecture)
10. [Routing and recommendation engine](#10-routing-and-recommendation-engine)
11. [Storage and data model](#11-storage-and-data-model)
12. [API and event contracts](#12-api-and-event-contracts)
13. [Runtime flows and sequence behaviour](#13-runtime-flows-and-sequence-behaviour)
14. [Deployment architecture](#14-deployment-architecture)
15. [Security, privacy and governance](#15-security-privacy-and-governance)
16. [Reliability, scalability and observability](#16-reliability-scalability-and-observability)
17. [MLOps and model lifecycle](#17-mlops-and-model-lifecycle)
18. [Testing and validation strategy](#18-testing-and-validation-strategy)
19. [SIH demo architecture and script](#19-sih-demo-architecture-and-script)
20. [Implementation roadmap](#20-implementation-roadmap)
21. [KPIs and acceptance criteria](#21-kpis-and-acceptance-criteria)
22. [Risks and mitigations](#22-risks-and-mitigations)
23. [Technology stack](#23-technology-stack)
24. [References](#24-references)

**Part II — Implementation contract** *(new in this revision — the buildable specification)*
25. [Repository layout](#25-repository-layout)
26. [Canonical contracts (code-level)](#26-canonical-contracts-code-level)
27. [Database schema (DDL)](#27-database-schema-ddl)
28. [Module specifications](#28-module-specifications)
29. [API request/response schemas](#29-api-requestresponse-schemas)
30. [Configuration and city profiles](#30-configuration-and-city-profiles)
31. [Build order with acceptance gates](#31-build-order-with-acceptance-gates)
32. [Conventions](#32-conventions)
33. [Frontend specification](#33-frontend-specification)

**Appendices**
- [Appendix A — Example payloads](#appendix-a--example-payloads)
- [Appendix B — Judge-facing technical answers](#appendix-b--judge-facing-technical-answers)
- [Appendix C — Change log for this document](#appendix-c--change-log-for-this-document)

---
---

# Part I — Product and architecture

## 1. Executive summary

PRAVAAH is a predictive public-transport intelligence platform. It does not merely show the
current location of a bus or the current crowd level. It forecasts future crowding, arrival
delay and journey reliability for each feasible itinerary, then ranks the alternatives
according to the passenger's preference: fastest, least crowded, most reliable or balanced.

The core differentiator is the **prediction-to-decision loop**. Live vehicle movement and
occupancy signals are combined with static transit topology, historical passenger flow,
headway behaviour, weather, events and time-of-day patterns. The ML layer predicts occupancy
and ETA distributions at future stops. A transit routing engine produces candidate journeys,
and a multi-objective ranker scores them using those forecasts. When new vehicle or crowd
events materially change the prediction, the system re-scores the active journey and can
recommend a different route or departure time.

The same intelligence is exposed to a transport-authority dashboard. Instead of only reacting
to existing overcrowding, operators receive predicted hotspots, route-level demand buildup,
delay clusters and suggested capacity interventions such as short-turning, adding a bus,
adjusting headway or shifting reserve vehicles.

The architecture keeps *ground truth*, *derived* and *simulated* data explicitly tagged.
Synthetic occupancy may be used for a controlled demo, but the production interfaces are
designed for real APC, AFC/e-ticketing, crowdsourcing or operator-supplied occupancy feeds
without changing downstream services.

### 1.1 Core outcomes

- Predict vehicle/route occupancy 5, 10, 15 and 30 minutes ahead and at the passenger's boarding stop.
- Predict ETA, segment travel time, delay probability and confidence intervals.
- Generate feasible public-transport itineraries and rank them using **predicted** rather than only current conditions.
- Recommend alternative departure times when waiting produces a materially better crowd/reliability outcome.
- Continuously adapt the recommendation when new real-time data arrives.
- Give operators a network-level view of predicted crowding, delay and service instability.
- Create an auditable historical dataset from live feeds for future model improvement.

### 1.2 What the user sees

| Option | Travel time | Predicted crowd at boarding | Delay risk | Result |
|---|---|---|---|---|
| Bus 14 | 34 min | 91% · very crowded | High | Avoid |
| Bus 22 | 39 min | 42% · seats likely | Low | **Recommended** |
| Bus 31 | 31 min | 72% · standing possible | Medium | Fastest |

The recommended option is not hard-coded. It is the result of a generalized cost function over
predicted journey time, waiting, transfers, walking, crowd discomfort, delay uncertainty and
the user's selected preference profile (§10.2).

---

## 2. Problem definition and scope

### 2.1 Problem statement

Public-transport users normally make route decisions with incomplete information. A route
planner may know the scheduled trip, current vehicle location or estimated arrival time, but
the user often does not know whether the arriving vehicle will be overcrowded, whether
crowding will worsen before their stop, or whether a slightly later departure would produce a
substantially better journey. Operators face the inverse problem: crowding and delay signals
become obvious only after the service is already degraded.

The platform treats public transport as a **spatiotemporal prediction problem**. It estimates
the future state of the network and turns that state into passenger and operator decisions.

### 2.2 In scope

- GTFS schedule ingestion and transit-network graph construction.
- GTFS-Realtime/AVL vehicle-position ingestion and map matching.
- Occupancy ingestion from APC, AFC, crowdsourcing, operator feeds or a simulator.
- Historical data collection and feature engineering.
- Crowding, passenger-flow, ETA and delay forecasting.
- Multi-modal candidate journey generation (bus/metro/walk where data is available).
- Multi-objective route and departure-time recommendation.
- Passenger-facing map, route comparison and live journey updates.
- Authority dashboard for predicted hotspots and fleet-action recommendations.
- Observability, model monitoring, data-quality controls and auditability.

### 2.3 Explicitly out of scope for the first release

- Autonomous control of transit vehicles or signals.
- Guaranteeing seat availability; predictions are probabilistic.
- Replacing the operator's dispatch system. The platform provides recommendations and integration APIs.
- Continuous storage of identifiable passenger movement.
- Fare payment, ticket issuance or financial settlement (AFC data may be consumed as an aggregate input).
- Computer-vision surveillance of passengers as a mandatory dependency.

### 2.4 Reference geography and the development substrate

**Deployment target: Delhi.** The Delhi Open Transit Data portal publishes bus GTFS static
data and offers an authorized real-time VehiclePositions feed, and its access form explicitly
lists "Student Projects" as a purpose. [R1–R3]

**Development substrate: MBTA (Boston), as a stand-in.** Delhi OTD publishes **no occupancy
data at all**, which means it cannot supply crowd labels — and crowd prediction is the entire
product. MBTA is used during development because it is the closest available proxy that
supplies the missing signal:

| Property | Delhi OTD | MBTA |
|---|---|---|
| GTFS Schedule | Yes | Yes |
| GTFS-Realtime VehiclePositions | Yes (authorization required) | Yes, **no API key** |
| **Operator-reported occupancy** | **No** | **Yes — `occupancy_status` on ~69% of vehicles** |
| TripUpdates with arrival delay | Yes | Yes |

The architecture is **location-agnostic by construction** (§30). All city-specific knowledge
is confined to an adapter and a city profile; every downstream service consumes the canonical
schema in §26. Switching from MBTA to Delhi is a configuration change plus one adapter class,
not a rewrite.

**Rules that follow from this, and that the code must honour:**

- No `mbta` string may appear outside `src/pravaah/adapters/` and `config/cities/`.
- Model artefacts are named and versioned per city; an MBTA-trained model is never silently served for Delhi.
- Any metric reported for Delhi must state whether the model was trained on Delhi data or transferred from MBTA.
- The demo may present MBTA data as MBTA data. It must never be presented as Delhi data.

---

## 3. Stakeholders and use cases

| Stakeholder | Primary goals | Key system capabilities |
|---|---|---|
| Passenger | Reach destination with a preferred trade-off between time, comfort and reliability | Route search, crowd forecast, ETA, departure recommendation, live reroute, alerts |
| Transit control room | Detect future overload and delay before service collapses | Hotspot map, route forecast, fleet-state view, intervention suggestions |
| Planning/analytics team | Understand recurring demand patterns | Historical dashboards, route/stop heatmaps, model exports, KPI trends |
| Data/ML team | Maintain predictive quality | Feature pipelines, model registry, drift/error monitoring, retraining |
| System administrator | Operate safely and reliably | RBAC, data-source health, audit logs, configuration, rate limits |
| Transport authority / API partner | Integrate operational systems | Data contracts, API keys, APC/AFC/AVL adapters, governance controls |

### 3.1 Passenger use cases

1. Plan a journey and compare alternatives by predicted crowding and delay.
2. Choose Fastest, Least Crowded, Most Reliable or Balanced.
3. See forecast occupancy **at the future boarding stop**, not only current vehicle occupancy.
4. Receive "leave 15 minutes later" advice when future crowding materially improves.
5. Receive a live notification if the selected trip becomes significantly more crowded or delayed.
6. Report observed crowd status using simple ordinal categories when operator occupancy is unavailable.
7. View accessible alternatives subject to mobility constraints.

### 3.2 Operator use cases

1. View predicted crowding by route, trip, vehicle, stop and time horizon.
2. Identify where passenger accumulation is likely to exceed capacity.
3. Identify bunching, headway instability and recurrent delay segments.
4. Compare "do nothing" with capacity actions such as adding a vehicle or changing headway.
5. Review forecast confidence to distinguish strong signals from uncertain ones.
6. Export route-level operational summaries for planning.

---

## 4. Requirements

### 4.1 Functional requirements

| ID | Requirement | Built in phase |
|---|---|---|
| FR-01 | Import GTFS schedule data and construct stop/route/trip relationships. | P0 |
| FR-02 | Consume vehicle positions at a configurable interval and retain raw observations. | P1 |
| FR-03 | Map-match each vehicle to a trip/route/segment and detect stale or impossible positions. | P1 |
| FR-04 | Ingest occupancy observations with source, timestamp, capacity and confidence metadata. | P2 |
| FR-05 | Join weather/event/context data by location and time. | P3 |
| FR-06 | Compute current service state: location, speed, headway, schedule deviation, next stop, occupancy state. | P1–P2 |
| FR-07 | Forecast crowding/occupancy at future stops and time horizons. | P3 |
| FR-08 | Forecast segment travel time, ETA, delay and uncertainty. | P3 |
| FR-09 | Generate candidate itineraries satisfying service schedules and transfer rules. | P4 |
| FR-10 | Rank itineraries under selectable user preferences. | P4 |
| FR-11 | Recommend alternative departure windows when beneficial. | P4 |
| FR-12 | Re-score active recommendations when material new data arrives. | P5 |
| FR-13 | Expose passenger and operator APIs plus a real-time update channel. | P4–P5 |
| FR-14 | Show route/vehicle/hotspot maps and forecast explanations. | P4, P6 |
| FR-15 | Store feedback/outcome data for model evaluation and retraining. | P3 |
| FR-16 | Record whether every data point is real, inferred, crowdsourced or simulated. | P0 |

### 4.2 Non-functional requirements

| Attribute | Target / design intent |
|---|---|
| Latency | Journey recommendation p95 < 2.5 s; live re-score < 1.5 s once updated features are available. |
| Freshness | Vehicle state < 15–30 s old where the upstream feed supports it; stale data must be visibly flagged. |
| Availability | Production target 99.9% for passenger read APIs; graceful degradation when an external feed fails. |
| Scale | Partition by city/agency/route; scale ingestion and inference independently. |
| Security | TLS, scoped credentials, RBAC for operator functions, encryption at rest, secrets manager. |
| Privacy | Minimize storage of personal location; separate analytics identifiers from account identity; configurable retention. |
| Explainability | Every recommendation exposes its dominant reasons: time, crowd, delay risk, transfer count, uncertainty. |

---

## 5. Architecture principles and key decisions

- **AP-01 — Predict the future state, not merely display current state.** Product value comes from forecasting occupancy and delay at the time and place relevant to a future boarding decision.
- **AP-02 — GTFS as the canonical transit topology.** Routes, trips, stops and stop-times are normalized so city integrations do not leak into business logic.
- **AP-03 — Event-driven live state.** Vehicle positions, occupancy updates, context changes and feedback are immutable timestamped events. Derived current state is materialized separately.
- **AP-04 — Separate raw, derived and simulated data.** Every observation carries provenance and quality metadata. Simulated data can exercise the pipeline without being mistaken for operational truth.
- **AP-05 — Prediction uncertainty is first-class.** APIs return quantiles and confidence, never only a point estimate. Ranking can penalize uncertainty for reliability-sensitive users.
- **AP-06 — Candidate generation and ranking are separate.** A deterministic transit planner generates feasible journeys; ML forecasts enrich them; a preference-aware ranker selects among them.
- **AP-07 — Graceful degradation.** Missing live occupancy falls back to historical passenger-flow forecasts; missing GPS falls back to schedule/headway estimates. The app indicates degraded confidence.
- **AP-08 — Prototype and production share contracts.** The demo may collapse logical services into fewer processes, but data schemas and APIs remain production-shaped.

### 5.1 Major architecture decisions (ADRs)

| ADR | Decision | Reason |
|---|---|---|
| ADR-01 | Event stream for live observations | Decouples ingestion rate from model/ranking workloads and preserves replayability. |
| ADR-02 | PostgreSQL + PostGIS as canonical operational store | Strong relational model plus spatial queries for stops, routes and geofences. |
| ADR-03 | Time-series optimized storage for dense telemetry | Efficient vehicle-position and forecast-history queries (TimescaleDB extension or dedicated store). |
| ADR-04 | Object storage + Parquet for training history | Low-cost immutable history and efficient batch ML scans. |
| ADR-05 | GBDT production baseline before deep sequence models | Strong tabular performance, fast inference, easier explanation; advanced models only if they beat baselines. |
| ADR-06 | RAPTOR/CSA-style transit planner | Timetable-aware routing handles transfers better than generic shortest path. |
| ADR-07 | Quantile forecasts (p10/p50/p90) | Enables reliability-aware decisions and honest uncertainty display. |
| **ADR-08** | **MBTA as development substrate, Delhi as deployment target** | Delhi publishes no occupancy; MBTA publishes real operator occupancy with no API key. City knowledge is adapter-confined so the swap is configuration. *(Added 30 Aug 2026)* |
| **ADR-09** | **Markdown solution document under version control is the binding spec** | The doc-first rule requires reviewable diffs, which a `.docx` cannot provide. *(Added 30 Aug 2026)* |
| **ADR-10** | **Raw feed capture is append-only CSV, converted to Parquet downstream** | The recorder must never block on a database. Flat append is the most crash-tolerant capture; Parquet conversion is a separate, restartable step. *(Added 30 Aug 2026)* |

---

## 6. Data architecture and real-data strategy

The system joins independent feeds into a time-aligned canonical model. No single public
dataset contains all required domains.

### 6.1 Data-source matrix

| Domain | Preferred source | Canonical fields | Update pattern | Fallback |
|---|---|---|---|---|
| Transit topology | GTFS Schedule | agency, route, trip, stop, stop sequence, calendar, shape | Daily / on publisher update | Last known valid feed |
| Vehicle movement | GTFS-Realtime VehiclePositions / AVL | vehicle_id, trip_id, lat, lon, timestamp, stop sequence | 5–30 s | Schedule + historical segment times |
| Occupancy | APC / AFC / operator load feed | vehicle/trip, board, alight, onboard, capacity, confidence | Per stop / seconds–minutes | Historical prediction or simulator |
| Crowdsourcing | Passenger reports | vehicle/trip, ordinal crowd class, timestamp, reporter confidence | Event-driven | Ignore if insufficient consensus |
| Weather | Forecast + historical weather API | rain, precipitation probability, temperature, humidity, weather code | Hourly | Recent value / climatology |
| Events | Authority/event calendar | location, start/end, expected attendance, event class | Daily / event-driven | No-event assumption |
| Traffic/context | Road speed or inferred bus segment speed | segment speed, congestion index | Minutes | Historical segment profile |
| Capacity | Fleet master data | vehicle_type, seated/total capacity | Rare | Route-level default |

### 6.2 City integrations

#### 6.2.1 MBTA (development substrate — active)

- **Static GTFS:** `https://cdn.mbta.com/MBTA_GTFS.zip`. The snapshot in use is `data/mbta_gtfs.zip`, feed version *"Summer 2026, 2026-08-19, version D"*, valid 2026-08-12 → 2026-09-05. Verified contents: **399 routes, 10,297 stop rows, 89,080 trips, 2,221,062 stop-times.**
- **Of those 10,297 stop rows, only 9,630 are routable and importable.** The remaining **667 are `location_type=3` generic nodes** — pathway nodes inside stations (platform and lobby nodes). GTFS makes `stop_lat`/`stop_lon` optional for them, and all 667 lack coordinates. **None is referenced by `stop_times.txt`**: no trip ever serves one. They are therefore excluded at import rather than given invented coordinates, and `stop.geom` stays `NOT NULL` (§27).
  Full composition by `location_type`: 7,768 stops/platforms (0), 276 stations (1), 332 entrances (2), 1,921 generic nodes (3), of which the 667 without coordinates are skipped.
  *If in-station pathway routing is ever built, these nodes need their own table with nullable geometry; they must not be forced into `stop`.*
- **VehiclePositions:** `https://cdn.mbta.com/realtime/VehiclePositions.pb` — no API key.
- **TripUpdates:** `https://cdn.mbta.com/realtime/TripUpdates.pb` — no API key.
- **Occupancy:** carried inline on VehiclePositions as `occupancy_status` and `occupancy_percentage`.

Measured field coverage from the recorded corpus (sampled, 200–300k rows):

| Field | Non-empty | Consequence for modelling |
|---|---|---|
| `trip_id` | 100% | Safe join key. |
| `stop_id` | 92.3% | Usable; handle the 7.7% gap explicitly. |
| `occupancy_status` | 68.8% | **The crowd label.** The 31.2% gap is `unknown`, never "empty". |
| `bearing` | 80.5% | Usable as a map-matching aid, not as a required feature. |
| `speed` | **9.8%** | **Unusable.** Derive speed from consecutive positions instead (§28.4). |

Observed `occupancy_status` distribution: `MANY_SEATS_AVAILABLE` 60.6%, `FEW_SEATS_AVAILABLE`
7.8%, `FULL` 0.5%, absent 31.1%. **The label set is severely imbalanced toward "not crowded".**
Section 9.6 mandates threshold-region metrics for exactly this reason; global accuracy on this
distribution is meaningless.

#### 6.2.2 Delhi OTD (deployment target — not yet integrated)

The portal publishes `agency.txt`, `calendar.txt`, `stops.txt`, `routes.txt`, `trips.txt` and
`stop_times.txt`, and lists 3,464 active stops/terminals, 543 routes, 16,562 trips and 378,324
stop-time records as of a June 2024 update. It warns that arrival/departure times in
`stop_times.txt` are rough estimates generated using an assumed constant speed. **Therefore
Delhi's static times are used for topology and service definition only; operational travel
times are learned from live observations.** [R1–R3]

Delhi supplies no occupancy. When Delhi is enabled, crowd labels must come from one of: an
operator APC/AFC integration, crowdsourced reports at sufficient density, or the simulator
with `source_type=SIMULATED` (§6.5) — and the resulting metrics must be labelled accordingly.

### 6.3 GTFS normalization

```
GTFS ZIP → schema validator → staging tables → canonical IDs → geometry build
         → service calendar expansion → publish feed_version
```

The importer validates referential integrity, service dates, coordinates and stop sequences
before publishing a new feed version. Import is **idempotent by feed hash**: re-importing an
identical ZIP is a no-op that returns the existing `feed_version_id`. [R4]

### 6.4 Real-time vehicle state

GTFS-Realtime VehiclePositions supplies location, trip linkage, timestamps, current passage
and optional occupancy. Even without occupancy, the position feed is the backbone for ETA and
delay estimation. [R5] Processing rules:

- Reject positions outside geographic bounds or implying impossible speed jumps.
- Map-match each point to the expected route shape or stop-to-stop segment.
- Mark feed entries stale when age exceeds a configurable threshold.
- Deduplicate repeated timestamps; retain raw upstream payload hashes for audit.
- Infer segment travel time from successive positions and stop-passage events.
- Materialize "latest vehicle state" in Redis while retaining historical events in the time-series store and object storage.

### 6.5 Occupancy strategy

Occupancy is the most operator-specific source. The platform supports a hierarchy, each mapped
into the same observation contract (§26.2):

| Priority | Source | `source_type` | Notes |
|---|---|---|---|
| 1 | APC (door sensors/counters) | `APC` | Boardings, alightings, onboard count. Strongest ground truth. |
| 2 | Operator load feed | `REAL_OPERATOR` | Direct load category. **This is what MBTA provides.** |
| 3 | AFC / e-ticketing | `AFC` | Boarding demand; alighting may need inference. |
| 4 | Crowdsourcing | `CROWDSOURCED` | Fused by recency and consensus (§8.3). |
| 5 | Simulation | `SIMULATED` | Always tagged. Never mixed into production training without an explicit flag. |

Higher priority overrides lower when fresh and trusted. For a demo, synthetic occupancy is an
acceptable instrumentation substitute, but **metrics computed on synthetic labels are reported
as simulator performance, never as real-world accuracy.**

### 6.6 External passenger-flow data for experimentation

Transport for London publishes BUSTO, an annual dataset estimating bus boardings, alightings
and loadings for typical weekdays, Saturdays and Sundays. It can validate feature pipelines or
benchmark passenger-flow methods while the deployment city retains its own topology and live
movement. [R6]

### 6.7 Weather and context

Open-Meteo provides hourly historical and forecast variables — temperature, humidity,
precipitation, weather codes — joined to the transport timeline by location and timestamp. [R7]

### 6.8 Data provenance contract

Every observation, without exception, carries:

```
observation_id | city_id | agency_id | entity_id
source_type ∈ {REAL_OPERATOR, PUBLIC_FEED, APC, AFC, CROWDSOURCED, DERIVED, SIMULATED}
source_name | source_timestamp | ingest_timestamp
quality_score ∈ [0,1] | raw_payload_ref | schema_version
```

This prevents synthetic or inferred values from contaminating real-data evaluations and allows
models to learn source-specific reliability. **A record without provenance is invalid and is
rejected at ingress**, not defaulted.

---

## 7. End-to-end logical architecture

Five planes. Services communicate through stable schemas, never city-specific payloads.

```
┌─────────────┐  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  SOURCES    │→ │ INGESTION   │→ │DATA PLATFORM │→ │ INTELLIGENCE │→ │ APPLICATIONS │
├─────────────┤  ├─────────────┤  ├──────────────┤  ├──────────────┤  ├──────────────┤
│GTFS schedule│  │validate     │  │PostgreSQL    │  │crowd forecast│  │passenger app │
│GTFS-RT / AVL│  │dedup        │  │  + PostGIS   │  │delay / ETA   │  │journey stream│
│occupancy    │  │map matching │  │time-series   │  │trip planner  │  │operator dash │
│weather      │  │stop passage │  │Redis latest  │  │multi-obj     │  │partner APIs  │
│events       │  │source tags  │  │Parquet arch. │  │  ranker      │  │              │
└─────────────┘  └─────────────┘  └──────────────┘  └──────────────┘  └──────────────┘
```

**Every reading is kept; nothing is overwritten.** Each reading is stored once with its time
and its source. Because the record stays complete, any past hour can be replayed exactly.

### 7.1 Request path

1. Passenger submits origin, destination, departure/arrival time and preference profile.
2. Trip Planner generates feasible itineraries using the current GTFS service graph.
3. Feature Service snapshots the latest relevant vehicle, headway, occupancy, weather and historical features for each candidate.
4. Crowd and Delay services produce forecasts for the candidate segments/trips, with uncertainty.
5. Route Ranker computes generalized cost and returns several **labelled** alternatives, not one opaque recommendation.
6. Backend streams material changes during the journey over WebSocket/SSE.

### 7.2 Streaming path

1. Source adapters fetch or receive GPS, occupancy and context events.
2. Schema validation, deduplication, timestamp normalization and source-quality tagging at ingress.
3. Events published to the stream bus and persisted to raw history.
4. Stream processors update latest vehicle/route state, headway, stop passage and derived segment travel times.
5. Affected features and forecasts are recomputed **selectively**, not city-wide.
6. Active user itineraries and operator hotspots subscribed to those entities are re-scored.

---

## 8. Component design

| Component | Responsibility | Important behaviour |
|---|---|---|
| GTFS Importer | Validates ZIP, versions source, normalizes agency/route/trip/stop/calendar/shape tables, builds spatial indexes and the trip-stop graph. | Scheduled batch; **idempotent by feed hash**. |
| Realtime Adapter | Fetches/subscribes to VehiclePositions/AVL; converts protobuf/vendor JSON into canonical `vehicle_position` events. | Stateless; scalable per agency/feed. |
| Occupancy Adapter | Accepts APC/AFC/operator/crowd/simulator input; standardizes onboard count or ordinal class. | Adds capacity and confidence; resolves vehicle/trip association. |
| Stream Processor | Deduplicates, map-matches, detects stop passage, computes speed/headway/schedule deviation, updates current state. | Partitions by city/route/vehicle. |
| Feature Service | Builds low-latency feature vectors from historical aggregates plus latest live state. | **Online/offline parity required.** |
| Crowd Forecast Service | Predicts boardings, alightings or occupancy ratio/bucket for future stops/horizons. | Returns quantiles + model metadata. |
| Delay Forecast Service | Predicts segment travel time, stop ETA, journey time and delay risk. | Uses live speed/headway plus historical segment patterns. |
| Transit Trip Planner | Generates schedule-feasible candidate journeys and transfers. | RAPTOR/CSA; optional walking links. |
| Route Ranker | Scores candidates by preference profile, hard constraints and uncertainty. | Deterministic formula; explainable. |
| Recommendation Orchestrator | Coordinates planner, forecasts, ranker and active-trip subscriptions. | Main passenger request service. |
| Operations Alert Engine | Aggregates future capacity/delay risk into hotspot windows and interventions. | Threshold + model-based rules. |
| Passenger BFF/API | Auth, geocoding, trip endpoints, WebSocket/SSE. | Caches popular OD/time queries. |
| Admin BFF/API | Role-controlled route/vehicle/hotspot queries and operational actions. | No passenger PII for the core dashboard. |
| Notification Service | Push/SMS/email for trip disruption or operator alerts. | Deduplicates noisy alerts; enforces cooldown. |
| Model Registry / MLOps | Versions models, metrics, feature schema, promotion status, rollback. | **Every prediction records `model_version`.** |

### 8.1 Map matching and stop-passage detection

Raw GPS must become transit semantics. The processor picks the most likely route segment from
trip assignment, route shape, bearing, distance and sequence constraints. A **stop passage**
event is emitted when the vehicle enters/leaves a stop geofence or when position interpolation
crosses the stop sequence.

```
vehicle_position → candidate route segments → score(distance, heading, expected_sequence)
                 → matched_segment → stop_passage / segment_travel_time
```

Stop-passage events are critical: they are the stable labels for segment travel-time learning.

### 8.2 Headway and bunching

For high-frequency networks, schedule deviation alone misleads. Track **headway** — the time
gap between consecutive vehicles on the same route/direction. Features: current headway,
planned headway, headway ratio, previous-bus gap, following-bus gap. Persistent low headway
between two vehicles indicates **bunching** and is a strong delay/crowding signal.

### 8.3 Crowd-report fusion

Crowdsourced occupancy is noisy evidence, not ground truth. Reports are weighted by recency,
agreement with other reports, reporter reliability (where available without intrusive identity
tracking) and compatibility with vehicle capacity. The result is a posterior crowd-state
estimate with a confidence score. **Operator APC data overrides crowd reports when fresh.**

---

## 9. Machine-learning architecture

### 9.1 Prediction tasks

| Task | Target | Example output | Primary use |
|---|---|---|---|
| Crowd regression | Occupancy ratio 0–1 at future stop/horizon | 0.84 (p10=.72, p90=.94) | Route ranking, capacity alert |
| Crowd classification | Ordinal class | Standing room only | Passenger UI when counts unavailable |
| Passenger-flow forecast | Boardings and alightings per stop | +18 board, −6 alight | Propagate occupancy downstream |
| Segment travel time | Seconds for next segment | 310 s | ETA construction |
| Stop ETA | Arrival timestamp distribution | 17:42 p50; 17:39–17:48 | Passenger display |
| Delay risk | Probability threshold exceeded | P(delay>10 min)=0.71 | Reliability score |
| Hotspot forecast | Capacity exceedance window | Route R12, stops S8–S12, 17:20–17:50 | Operator dashboard |

### 9.2 Feature catalog

| Group | Examples |
|---|---|
| Identity/topology | route_id, direction, trip_id, stop_id, stop sequence, segment_id, vehicle type/capacity |
| Time | hour, minute bucket, day of week, weekend, holiday, peak flags, cyclical sin/cos |
| Live movement | lat/lon, matched segment, **derived** speed, acceleration, distance to stop, dwell time, ETA residual |
| Headway | actual headway, scheduled headway, deviation, previous/following gap, bunching flag |
| Occupancy state | current onboard, ratio/class, last trusted observation age, source confidence |
| Passenger-flow lags | board/alight/occupancy at prior stops; same trip previous stops; same route previous vehicles |
| Historical aggregates | median/quantiles by route-stop-time-day; rolling 7/28-day; special-day profiles |
| Weather | rain, precipitation probability, temperature, humidity, weather code |
| Events | distance to event, start/end window, attendance bucket, category |
| Traffic proxy | current segment time / historical median, upstream vehicle speed |
| Data quality | GPS age, occupancy age, missingness flags, `source_type`, source quality score |

> **Note on `speed`:** MBTA populates the GTFS-RT `speed` field on only ~9.8% of rows (§6.2.1).
> The "Live movement" group therefore uses **derived** speed computed from consecutive
> positions. Feature definitions must not read the raw feed `speed` column.

### 9.3 Model progression

| Stage | Crowd model | Delay model | Why |
|---|---|---|---|
| Baseline 0 | Route-stop-time seasonal median | Historical segment median | Honest lower bound; zero ML complexity. |
| Baseline 1 | GBDT on engineered lags | GBDT on segment/live features | Strong on heterogeneous tabular data; fast, explainable. |
| Sequence | TFT/LSTM/Transformer over stop sequence | Sequence model over segment trajectory | Temporal dependencies, long horizons. |
| Network-aware | Graph temporal model across nearby routes/stops | Graph/spatial congestion propagation | Spillover across shared corridors and hubs. |
| Production ensemble | Weighted/stacked baseline + sequence | GBDT + sequence quantile ensemble | Robust across data regimes; graceful fallback. |

### 9.4 Recommended first production model

**Gradient-boosted decision trees.** They handle route/stop categorical encodings, non-linear
relationships, missing values and mixed live/historical features at low inference latency.
Deep sequence or graph models are promoted **only** on material gains over time-based holdout
sets and peak-hour slices.

### 9.5 Time-based validation

Random train/test splits leak future patterns into the past and are **prohibited**. Split
chronologically: train on earlier weeks, validate on a later window, test on the most recent
untouched window. Additionally evaluate unseen-event days, rainy days, peak periods and sparse
routes.

### 9.6 Metrics

| Layer | Metrics |
|---|---|
| Occupancy regression | MAE, RMSE, **weighted MAE near the capacity threshold**, quantile pinball loss |
| Occupancy class | Macro F1, weighted F1, ordinal error, **confusion around the standing/full boundary** |
| Board/alight | MAE per stop, cumulative occupancy conservation error |
| ETA/delay | MAE in minutes, p90 absolute error, on-time-within-5-min rate, calibration |
| Ranking | Top-1 regret vs observed outcome, route-switch benefit, recommendation acceptance |
| Operations | Hotspot precision/recall, lead time before capacity exceedance |
| System | Feature freshness, prediction latency, coverage, fallback rate |

> Because the observed label distribution is ~61% `MANY_SEATS_AVAILABLE` and 0.5% `FULL`
> (§6.2.1), **global accuracy must never be reported as a headline metric.** The threshold
> region is the product; report it separately and always alongside the baseline.

### 9.7 Forecast uncertainty

Crowding and ETA are returned as quantiles: e.g. occupancy p10=0.62, p50=0.76, p90=0.91. A
"Most Reliable" user can prefer a slightly slower median with narrower uncertainty. Operator
alerts require the **lower** confidence bound to exceed a threshold before escalating.

### 9.8 Passenger-flow conservation

When boardings and alightings are predicted separately, onboard count propagates by a
constrained recurrence:

```
onboard[s] = clip(onboard[s-1] + boardings[s] - alightings[s], 0, vehicle_capacity)
```

Outputs implying negative counts or sustained load above physical capacity are flagged.
Constraint-aware post-processing improves realism and reviewer confidence.

---

## 10. Routing and recommendation engine

### 10.1 Candidate journey generation

The Trip Planner is **deterministic and separate from ML**. It uses the transit schedule graph
to create feasible journeys respecting service calendars, stop order, transfer time, maximum
transfers and optional walking links. RAPTOR or Connection Scan Algorithm is appropriate
because both are designed for timetable transit routing. A prototype may use an existing GTFS
routing library **behind the same `TripPlanner` interface** (§28.7).

### 10.2 Multi-objective generalized cost

```
score(route) = wT · normalized_travel_time
             + wW · normalized_wait_time
             + wX · transfer_penalty
             + wC · predicted_crowding_cost
             + wD · delay_risk
             + wU · uncertainty_penalty
             + wP · walking_penalty
```

Lower is better. Weights change by preference profile. Hard constraints — wheelchair
accessibility, maximum walking distance, "avoid standing" — are applied **before** ranking.

| Preference | Travel | Crowd | Delay risk | Transfers | Interpretation |
|---|---|---|---|---|---|
| Fastest | Very high | Low | Medium | Medium | Optimize arrival while avoiding obviously unstable options. |
| Least crowded | Medium | Very high | Medium | Medium | Prefer comfort even if travel time rises moderately. |
| Most reliable | Medium | Medium | Very high + uncertainty | Medium | Prefer narrow ETA distribution and stable headways. |
| Balanced | High | High | High | Medium | Pareto-style compromise. |

Concrete weight vectors are specified in §30.2 and live in configuration, not in code.

### 10.3 Crowd discomfort function

Crowding is **not** linear. 20%→40% matters less than 80%→100%. Use a piecewise penalty that
rises sharply near standing/full:

```python
if   occ < 0.50: crowd_cost = 0.2 * occ
elif occ < 0.80: crowd_cost = 0.10 + 0.8 * (occ - 0.50)
else:            crowd_cost = 0.34 + 2.5 * (occ - 0.80)
```

### 10.4 Departure-time optimization

For a requested departure window, evaluate the best itinerary at several nearby departure times
(now, +5, +10, +15, +20 min). Recommend waiting **only** when the improvement crosses a
threshold, avoiding annoying suggestions for trivial gains:

```
recommend WAIT if  best_score(t+Δ) + waiting_disutility(Δ) < best_score(t) - improvement_threshold
```

### 10.5 Live rerouting policy

Do **not** reroute on every small fluctuation. Use hysteresis and cooldown.

- Trigger only when expected journey cost worsens beyond a material threshold, or a route becomes infeasible.
- Prefer changes **before** boarding; after boarding, only recommend transfer changes with significant benefit.
- Always explain: *"Bus 14 is now predicted 92% full at your stop; Bus 22 is 44% and 6 minutes slower."*
- Retain the previous recommendation and forecast snapshot for audit and A/B evaluation.

---

## 11. Storage and data model

### 11.1 Storage responsibilities

| Store | Data | Access pattern |
|---|---|---|
| PostgreSQL + PostGIS | GTFS canonical model, stops, shapes, routes, fleet metadata, users/roles, configuration | Transactional + spatial joins |
| Time-series (TimescaleDB) | Vehicle positions, stop passages, occupancy observations, feature snapshots, forecast outcomes | Time-window scans by route/vehicle |
| Redis | Latest vehicle state, active trip sessions, hot feature values, route-plan cache | Sub-millisecond KV, TTL |
| Object storage (Parquet) | Raw immutable feed archives, training datasets, model artefacts, batch exports | Large sequential batch reads |
| Model registry | Model binaries, feature schema, metrics, promotion stage | Versioned lifecycle metadata |

### 11.2 Core entities

| Entity | Important fields |
|---|---|
| `agency` | agency_id, name, timezone |
| `route` | route_id, agency_id, names, type |
| `stop` | stop_id, name, geom, parent_station |
| `trip` | trip_id, route_id, service_id, direction_id, shape_id |
| `stop_time` | trip_id, stop_sequence, stop_id, scheduled_arrival/departure |
| `vehicle` | vehicle_id, type, capacity |
| `vehicle_position` | vehicle_id, trip_id, ts, geom, speed, matched_segment, source_quality |
| `stop_passage` | vehicle_id, trip_id, stop_id, arrival_ts, departure_ts |
| `occupancy_observation` | vehicle/trip, ts, onboard, boardings, alightings, class, source_type, confidence |
| `segment_travel_time` | segment_id, vehicle_id, start_ts, end_ts, seconds |
| `weather_observation` | grid/location, ts, rain, temp, humidity, code |
| `event_context` | event_id, geom, start/end, attendance_bucket, category |
| `forecast` | entity_id, target_time/stop, type, p10, p50, p90, model_version, feature_ts |
| `recommendation` | request_id, candidate_id, score, rank, reasons, prediction_refs |
| `feedback` | request_id, accepted_route, reported_crowd, observed_outcome |

Executable DDL is in §27.

### 11.3 Partitioning and retention

- Partition dense telemetry by city and time (daily/weekly chunks); index by vehicle_id, trip_id, timestamp.
- Keep raw feed payloads long enough to reproduce training snapshots; archive older partitions to object storage.
- Redis latest-state keys use TTL and are reconstructed from the stream/database after restart.
- Passenger live-session state has short TTL; historical analytics use anonymized/aggregate IDs.
- Features backing a recommendation are reproducible through **snapshot identifiers**, not by storing every raw personal query indefinitely.

---

## 12. API and event contracts

### 12.1 Passenger APIs

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/v1/plan` | Ranked itineraries for origin/destination/time/preference. |
| GET | `/v1/trips/{tripId}/forecast` | Crowd + ETA forecast by upcoming stop. |
| GET | `/v1/vehicles/{vehicleId}` | Current vehicle state and freshness. |
| GET | `/v1/stops/{stopId}/departures` | Predicted upcoming departures with crowd status. |
| POST | `/v1/occupancy/report` | Submit a passenger crowd observation. |
| POST | `/v1/journeys/{id}/subscribe` | Create a live update subscription. |
| GET/WS | `/v1/journeys/{id}/stream` | Receive material forecast/routing changes. |

### 12.2 Operator APIs

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/v1/admin/hotspots` | Predicted crowd/delay hotspots by time horizon. |
| GET | `/v1/admin/routes/{id}/forecast` | Route-level load, headway and delay profile. |
| GET | `/v1/admin/vehicles` | Fleet live state with data freshness. |
| POST | `/v1/admin/scenarios` | Evaluate an intervention scenario. |
| GET | `/v1/admin/data-health` | Feed freshness, missing coverage, validation failures. |
| GET | `/v1/admin/models` | Deployed model versions and monitoring metrics. |

### 12.3 Event topics

| Topic | Producer | Consumers |
|---|---|---|
| `vehicle.position.raw` | Realtime adapter | Validator, archive |
| `vehicle.position.canonical` | Validator / map matcher | State store, ETA features, archive |
| `vehicle.stop_passage` | Stream processor | Travel-time learner, occupancy propagation, analytics |
| `occupancy.observation` | Occupancy adapter | State store, feature service, archive |
| `context.weather` | Weather adapter | Feature service |
| `forecast.updated` | ML services | Recommendation orchestrator, admin alerts |
| `recommendation.changed` | Recommendation service | Passenger notification/stream |
| `data.quality.alert` | Validators / monitoring | Admin dashboard, ops alerting |

### 12.4 API response design principles

1. Always include `generated_at`, source freshness and forecast/model version.
2. Expose uncertainty and reason codes; never return an unexplained single score.
3. **Distinguish "unknown" from "low crowd".** Missing occupancy must not silently become zero.
4. Return stable IDs for route, trip, vehicle and stop so clients can subscribe to updates.
5. Use pagination / viewport bounding boxes for operator map endpoints to prevent payload explosion.

---

## 13. Runtime flows and sequence behaviour

### 13.1 Initial journey plan flow

1. Resolve coordinates and nearby transit stops; filter inaccessible/invalid stops.
2. Generate candidate itineraries for the requested departure time and service calendar.
3. **Batch** candidate trip/segment IDs into one feature request to avoid N+1 model calls.
4. Predict crowding and delay for each candidate at the relevant future stop/time.
5. Calculate expected journey metrics and confidence ranges.
6. Rank candidates, label alternatives, return explanation strings derived from the scoring terms.
7. Cache by origin/destination grid cells, departure bucket, preference and feed/model versions.

### 13.2 Live update flow

A new GPS position or occupancy observation updates **only** the affected vehicle/trip/route
features. If the forecast change exceeds a material threshold, the recommendation service
checks active journey subscriptions touching those entities. Re-ranking is selective. The user
is notified **only** if the preferred route changes or a meaningful warning threshold is crossed.

### 13.3 Operator hotspot flow

1. Each forecast cycle aggregates predicted occupancy and delay by route-stop-time bucket.
2. Capacity exceedance probability and duration are computed.
3. Adjacent stop buckets merge into corridor hotspots.
4. Rules estimate interventions: added capacity, headway adjustment, short-turning, or information only.
5. Operator sees risk level, lead time, affected stops and supporting evidence.

---

## 14. Deployment architecture

### 14.1 Demo profile

- Frontend: React + MapLibre.
- Backend: one FastAPI application containing trip planning, recommendation and admin APIs.
- ML: crowd and delay models loaded in-process, or one separate inference service.
- PostgreSQL + PostGIS (optionally TimescaleDB) for GTFS, telemetry and forecasts.
- Redis for latest-state cache and live update pub/sub.
- Background workers for GTFS import, vehicle polling and occupancy events.
- **Docker Compose** on a laptop or cloud VM. No Kubernetes.

### 14.2 Production profile

- Containerized services behind a regional load balancer / API gateway.
- Kafka (or equivalent) partitioned by city/agency/route for telemetry fan-out.
- PostgreSQL/PostGIS HA with read replicas for map/analytics traffic.
- Redis cluster for latest-state and route-plan cache.
- Object storage for raw and feature history.
- Independent autoscaling of ingestion, inference, recommendation and dashboard workloads.
- Blue/green or canary model deployment with rollback.
- Cross-zone replication and managed backups.

### 14.3 Multi-city scaling

`city_id` and `agency_id` are first-class partition keys. Each city receives an adapter
configuration describing timezone, GTFS feed, real-time source, capacity mapping and data-policy
parameters (§30). Core forecasting and ranking remain shared, or are regionally isolated for
data residency.

---

### 14.4 Public demo deployment (single VM)

The demo is served from **one cloud VM running the existing Compose stack** behind a
TLS-terminating reverse proxy. This keeps §27 exactly as written -- PostGIS and TimescaleDB both
work, because we control the database image -- and gives judges a single URL.

```
                    internet
                       |
                  Caddy :443            automatic TLS, HTTP/2
                   /        \
        static frontend    /api -> FastAPI :8000
                                      |
                          +-----------+-----------+
                          |                       |
                 timescaledb + postgis        redis
                     (named volume)        (latest state)
```

| Concern | Decision |
|---|---|
| Host | One VM, **minimum 4 GB RAM / 2 vCPU / 40 GB disk**. The static GTFS import alone is 2.2M stop-times. |
| TLS | Caddy, automatic certificates. No manual certificate handling. |
| Compose | A `deploy` profile adds Caddy and the built frontend to the existing stack. The dev stack stays unchanged. |
| Secrets | `.env` on the host only, never in the repo (§32). The database password is not the development default. |
| Exposure | **Only 80/443 are published.** Postgres and Redis stay on the internal Compose network -- never published to the host in the deploy profile. |
| Data | The recorded corpus is not shipped in the image. The VM imports GTFS and replays a Parquet subset. |
| Backups | `pg_dump` on a schedule to object storage; the corpus is the irreplaceable part, not the derived tables. |
| Cost | Sized for a free or student tier. |

**The hosted deployment does not replace the offline requirement.** §19 and the hardening slice
still require the full demo to run from recorded replay with networking disabled -- judges may
have no connectivity, and the live feed may be down at the wrong moment. Both paths must work.

## 15. Security, privacy and governance

| Area | Controls |
|---|---|
| Transport feed credentials | Secrets manager; never embed keys in the frontend; rotate and scope; outbound proxy if required. |
| Passenger authentication | Optional for anonymous planning; OAuth/OIDC for accounts; short-lived tokens. |
| Operator access | RBAC roles (viewer, dispatcher, admin); MFA for privileged accounts. |
| Transport security | TLS everywhere; certificate validation; secure WebSocket. |
| Data at rest | Encrypted managed disks/object storage; encrypted backups. |
| Personal location | Process origin/destination for routing; minimize historical retention; aggregate analytics to grid/stop level. |
| Crowd reports | Rate limit, abuse detection, coarse identity/reputation; never expose reporter identity. |
| Audit | Record operator actions, model deployments, feed configuration changes, privileged exports. |
| Input safety | Schema validation, max payload sizes, geospatial bounds, SQL parameterization, rate limits. |
| Supply chain | Pinned dependencies, container scanning, SBOM in the production pipeline. |

### 15.1 Privacy by design

- Route planning can be anonymous; an account is not required for the core value proposition.
- Active journey subscriptions use opaque session IDs and expire automatically.
- Raw device trajectories are not persisted for analytics without explicit opt-in and a legitimate purpose.
- Prefer aggregated OD demand counts with minimum group sizes over individual histories.
- Personalized preferences, if stored, are kept separate from raw location history.
- Crowd model training relies on vehicle/stop aggregates, never personal passenger identities.

### 15.2 Threat model

| Threat | Impact | Mitigation |
|---|---|---|
| Fake crowd reports | Manipulated recommendations | Consensus, rate limits, source weighting, anomaly detection, trusted APC precedence. |
| Stolen transit API key | Feed abuse or quota exhaustion | Server-side secrets, rotation, IP restrictions. |
| GPS spoof / outlier | Corrupted ETA and crowd features | Map matching, impossible-speed checks, multi-point consistency. |
| Model poisoning via synthetic data | Biased production model | Provenance filtering; production training excludes `SIMULATED` unless explicitly allowed. |
| Trip-history exposure | Privacy harm | Minimal retention, access controls, aggregation, encryption. |

---

## 16. Reliability, scalability and observability

### 16.1 Graceful degradation matrix

| Failure | System behaviour | User/operator indication |
|---|---|---|
| Live vehicle feed stale | Last position + historical segment model; increase uncertainty | "Live tracking delayed" badge |
| Occupancy missing | Historical/passenger-flow prediction without a current-load anchor | Crowd forecast marked lower confidence |
| Weather feed unavailable | Last forecast, or omit weather features with a missing flag | No hard failure |
| ML service unavailable | Fall back to seasonal crowd and historical ETA baseline | "Estimated from history" |
| Redis unavailable | Read latest state from DB; disable some live-subscription speedups | Higher latency, no data loss |
| One city feed broken | Isolate by city/agency partition | Other cities unaffected |

### 16.2 Observability

- **Metrics:** ingest lag, feed freshness, positions/minute, map-match failure rate, missing occupancy coverage, model latency, API p50/p95/p99, cache hit rate.
- **Model metrics:** online error when labels arrive, calibration, feature drift, prediction drift, fallback rate.
- **Business metrics:** journeys planned, live reroutes, least-crowded preference usage, hotspot lead time.
- **Logs:** structured JSON with `request_id`, `city_id`, route/trip/vehicle IDs, `model_version`. Never log secrets.
- **Traces:** distributed trace from `/plan` → planner → feature service → model → ranker.
- **Dashboards:** source health, application SLO, model health and city operations, separated by audience.

### 16.3 Capacity model

Telemetry dominates write volume. With *N* vehicles reporting every *R* seconds, the event rate
is ≈ *N/R* position events per second before duplication and derived events. *(Measured on the
MBTA substrate: ~365 vehicles at 20 s ≈ 18 events/s, ~1.27 M rows and ~411 MB per 35 h.)*
Partition the bus and time-series tables by city/route, batch database inserts, keep only
latest state in Redis. Passenger searches are read-heavy and highly cacheable by OD grid and
departure-time bucket.

---

## 17. MLOps and model lifecycle

1. Archive raw immutable events with source provenance.
2. Run data-quality checks; construct labels only after enough future data exists.
3. Build an offline feature dataset using the **same transformation definitions** as online features.
4. Train baseline and candidate models with chronological splits.
5. Evaluate global metrics **and critical slices**: peak hours, rain, events, high occupancy, sparse routes.
6. Register the candidate with dataset version, code commit, feature schema and metrics.
7. Deploy shadow/canary; compare predictions without changing user output.
8. Promote only if quality, latency and calibration gates pass.
9. Monitor error/drift; retrain on schedule or on drift threshold breach.
10. Roll back by model version without changing API clients.

### 17.1 Online/offline feature parity

The largest ML-system risk here is training–serving skew. Definitions such as "previous 3 stop
occupancies", "route-stop median for this 15-minute bucket" and "headway ratio" are
**implemented once** (§28.5) and reused by batch training and live inference, with parity tests
enforcing equality.

### 17.2 Model governance metadata

```
model_version · training_window · dataset_version · feature_schema_hash · target_definition
metrics_global · metrics_peak_hour · metrics_high_occupancy · calibration_metrics
approved_by · deployment_stage · created_at · city_id
```

---

## 18. Testing and validation strategy

| Layer | Tests |
|---|---|
| GTFS importer | Schema validity, referential integrity, calendar expansion, coordinate bounds, duplicate IDs, shape continuity. |
| Realtime ingestion | Protocol decoding, stale timestamps, duplicate events, impossible speeds, retries, malformed feed. |
| Map matching | Known trajectories, loops, crossings, out-of-order GPS, sparse points. |
| Occupancy | Capacity limits, board/alight conservation, conflicting reports, stale sensors. |
| Feature pipeline | **Offline/online parity**, lag windows, missing values, timezone/DST handling. |
| ML | Chronological holdout, peak/high-crowd slices, calibration, leakage checks, baseline comparison. |
| Routing | No-route case, transfers, overnight GTFS times >24:00, service exceptions, accessibility. |
| Ranking | Preference weight tests, deterministic ordering, uncertainty penalties, hysteresis. |
| API | Contract tests, auth/RBAC, rate limit, payload validation, idempotency. |
| Performance | City-scale replay, burst searches, cache behaviour, p95 latency. |
| Resilience | Feed outage, Redis restart, model rollback, DB failover, stale-feature fallback. |
| Demo | Scripted scenario replay with fixed seed and offline fallback. |

### 18.1 Synthetic simulation validation

The simulator generates board/alight events from **explicit behavioural rules**, not random
occupancy percentages: AM/PM peak multipliers, stop-specific boarding propensity,
destination-driven alighting, rain/event multipliers, capacity clipping, route-specific demand
profiles. Simulator output is tested for conservation, realistic peak patterns and
repeatability by seed.

---

## 19. SIH demo architecture and script

### 19.1 Demo data composition

| Layer | Demo choice |
|---|---|
| Transit network | Real GTFS routes/stops/trips from the active city profile. |
| Vehicle movement | Recorded GTFS-Realtime replay (§28.3) — deterministic and offline-capable. |
| Occupancy | Real operator `occupancy_status` where available; simulator elsewhere, tagged `SIMULATED`. |
| Weather | Real historical values joined by timestamp. |
| Models | Pre-trained artefacts loaded from the registry; no training during the demo. |

### 19.2 The five-minute script

1. **The problem** — show a vehicle that is empty now and full at the passenger's stop.
2. **Plan a journey** — three options, differentiated by predicted crowd at the boarding stop.
3. **Switch preference** — the ranking visibly re-orders; reason codes change.
4. **Departure advice** — "leave 15 minutes later" with the forecast curve behind it.
5. **Inject an event** — replay a crowding spike; the active journey re-scores live.
6. **Operator view** — the same event appears as a predicted hotspot with lead time.

**The entire script must run offline from recorded replay.** No live internet dependency.

---

## 20. Implementation roadmap

| Phase | Deliverable | Exit criteria |
|---|---|---|
| **P0 — Data foundation** | GTFS importer, PostGIS schema, map with stops/routes, feed provenance | Real network visible; feed versioning works. |
| **P1 — Live fleet** | VehiclePositions adapter/replay, vehicle markers, map matching, latest-state cache | Vehicles move on correct routes with a freshness indicator. |
| **P2 — Occupancy pipeline** | Occupancy contract + operator feed + simulator + optional crowd report | Current occupancy propagates through the system and is source-tagged. |
| **P3 — Forecasting baseline** | Historical aggregates + GBDT crowd/ETA baseline + quantiles | Backtest beats the seasonal baseline on the chosen dataset. |
| **P4 — Trip planning/ranking** | Candidate itineraries + four preference profiles + explanations | Same OD returns clearly differentiated choices. |
| **P5 — Live adaptation** | Event-triggered re-score + WebSocket/SSE notifications | Injected crowd/delay event changes the recommendation live. |
| **P6 — Operator dashboard** | Hotspot map, route forecast, fleet health | Future hotspot displayed with lead time and supporting metrics. |
| **P7 — Hardening** | Offline demo replay, tests, monitoring, pitch metrics | Full 5-minute flow repeatable without external dependencies. |

Per-phase acceptance gates are in §31.

### 20.1 Suggested team split

| Workstream | Responsibilities |
|---|---|
| Data/backend | GTFS, realtime adapters, database, APIs, stream/replay engine |
| ML | Feature generation, crowd model, delay model, uncertainty, evaluation |
| Routing/optimization | Trip planner, preference scoring, departure-time optimization, reroute logic |
| Frontend | Passenger journey UX, map, charts, live update states |
| Dashboard/devops | Operator view, telemetry health, deployment, observability, demo automation |

---

## 21. KPIs and acceptance criteria

| Category | KPI | Prototype target |
|---|---|---|
| Data | Vehicle-feed freshness | Show age; majority of live vehicles within upstream cadence. |
| Data | Map-match success | >95% on a clean replay sample; investigate route-loop edge cases. |
| ML | Crowd MAE / class F1 | Report honestly on the validation set, **separated by source**. |
| ML | ETA MAE | Compare against static schedule and historical median baselines. |
| ML | Calibration | p90 intervals contain roughly the expected share of observed outcomes. |
| Product | Recommendation latency | p95 < 2.5 s for a demo-sized deployment. |
| Product | Reroute reaction | Injected event reflected in the active journey within seconds. |
| Explainability | Reason coverage | **Every** ranked option has human-readable reason codes. |
| Operator | Hotspot lead time | Forecast demonstrated before the capacity threshold occurs. |
| Reliability | Offline demo success | Full scripted flow works in replay mode with no internet. |

---

## 22. Risks and mitigations

| Risk | Why it matters | Mitigation |
|---|---|---|
| No occupancy ground truth in the target city | The main crowd target is missing | Canonical occupancy adapter; MBTA substrate for real labels; simulator for demo; APC/AFC integration path. |
| Static timetable is approximate | Naive schedule-delay labels mislead | Use GTFS for topology/service; derive operational segment times from live vehicle history. |
| Realtime API unavailable during the demo | Live feature fails visibly | Recorded feed replay through the same event contract. |
| Synthetic data perceived as fake | Credibility risk | Explicitly label; never claim real-world accuracy for simulator metrics. |
| Model over-complexity | Hard to debug and explain | Strong baseline first; advanced models only on measured improvement. |
| Sparse or new routes | Poor historical features | Hierarchical features by corridor/time; route-type fallbacks. |
| **Severe label imbalance** | 0.5% `FULL` means a naive classifier scores well while being useless | Threshold-region metrics (§9.6); never headline global accuracy. |
| **Substrate/target mismatch** | An MBTA-trained model may not transfer to Delhi | Adapter isolation; per-city model versioning; transfer must be stated explicitly (§2.4). |
| **Recorded corpus growth** | ~35 MB/h with no rotation fills the disk | Parquet conversion + partitioning (§28.2); monitor free space. |

---

## 23. Technology stack

| Layer | Choice | Notes |
|---|---|---|
| Passenger UI | React + MapLibre (web) | Flutter/React Native if mobile is required. |
| Operator UI | React + map component | Server-side auth/RBAC. |
| Backend APIs | **Python 3.12 + FastAPI** | Async I/O for feeds; good fit with the Python ML stack. |
| Transit planning | RAPTOR/CSA implementation or a GTFS routing engine | Kept behind the `TripPlanner` interface. |
| Operational DB | **PostgreSQL 16 + PostGIS** | TimescaleDB extension for telemetry. |
| Cache/state | **Redis** | Latest vehicle state, plan cache, pub/sub. |
| Streaming | Redis Streams (prototype), Kafka (production) | Same canonical events either way. |
| Object storage | S3-compatible + **Parquet** | Raw archives and ML datasets. |
| ML baseline | **LightGBM** (quantile objective) + scikit-learn | Fast tabular/time-feature inference. |
| Advanced ML | PyTorch TFT/LSTM/Transformer/GNN | Only after a measured baseline comparison. |
| Model registry | MLflow or equivalent | Metrics, artefacts, promotion/rollback. |
| Batch orchestration | Prefect/Airflow | Feature jobs, retraining, backfills. |
| Observability | Prometheus + Grafana + structured logs | OpenTelemetry tracing in production. |
| Packaging | **Docker Compose** (demo), Kubernetes (production) | No orchestration complexity in the demo. |

---

## 24. References

| Ref | Source | URL |
|---|---|---|
| R1 | Delhi Open Transit Data — Static | https://otd.delhi.gov.in/data/static/ |
| R2 | Delhi Open Transit Data — Real Time | https://otd.delhi.gov.in/data/realtime/ |
| R3 | Delhi Open Transit Data — Documentation | https://otd.delhi.gov.in/documentation/ |
| R4 | GTFS Schedule Reference | https://gtfs.org/documentation/schedule/reference/ |
| R5 | GTFS-Realtime — Vehicle Positions | https://gtfs.org/documentation/realtime/feed-entities/vehicle-positions/ |
| R6 | Transport for London — Open Data / BUSTO | https://tfl.gov.uk/info-for/open-data-users/our-open-data |
| R7 | Open-Meteo — Historical Weather API | https://open-meteo.com/en/docs/historical-weather-api |
| R8 | MBTA Developer Portal / GTFS | https://www.mbta.com/developers/gtfs |

Web references were verified on 27 August 2026 (R1–R7). External APIs, terms, feed coverage and
cadence should be rechecked immediately before deployment.

---
---

# Part II — Implementation contract

> Everything below is new in the 30 August 2026 revision. Part I says *what* the system is;
> Part II says *exactly what to build*, so that "built to the document" is a checkable claim.

## 25. Repository layout

```
SIH/
├── docs/
│   └── SOLUTION.md                  ← this file, the binding contract
├── config/
│   ├── settings.toml                ← non-secret defaults
│   └── cities/
│       ├── mbta.toml                ← active development profile
│       └── delhi.toml               ← deployment target profile
├── data/                            ← git-ignored except the scripts
│   ├── record_feed.py               ← raw recorder (P0, already built)
│   ├── START_RECORDING.bat
│   ├── mbta_gtfs.zip
│   ├── mbta_vehicle_positions.csv
│   ├── mbta_trip_updates.csv
│   ├── parquet/                     ← converted, partitioned corpus
│   └── raw/                         ← optional .pb frames
├── src/pravaah/
│   ├── __init__.py
│   ├── config.py                    ← settings + city profile loading
│   ├── contracts/                   ← canonical schemas; the stable interface
│   │   ├── provenance.py
│   │   ├── events.py
│   │   └── api.py
│   ├── adapters/                    ← THE ONLY place city knowledge may live
│   │   ├── base.py
│   │   ├── gtfs_rt.py
│   │   ├── mbta.py
│   │   ├── delhi_otd.py
│   │   └── replay.py
│   ├── ingest/
│   │   ├── gtfs_import.py
│   │   ├── convert.py               ← CSV → partitioned Parquet
│   │   ├── validate.py
│   │   ├── mapmatch.py
│   │   └── stop_passage.py
│   ├── state/
│   │   ├── redis_state.py
│   │   └── headway.py
│   ├── features/
│   │   ├── definitions.py           ← ONE definition per feature
│   │   ├── offline.py
│   │   └── online.py
│   ├── models/
│   │   ├── baseline.py
│   │   ├── crowd.py
│   │   ├── delay.py
│   │   └── registry.py
│   ├── routing/
│   │   ├── planner.py
│   │   ├── ranker.py
│   │   └── departure.py
│   ├── ops/
│   │   ├── hotspots.py
│   │   └── health.py
│   └── api/
│       ├── main.py
│       ├── passenger.py
│       ├── admin.py
│       └── stream.py
├── migrations/                      ← SQL migrations, forward-only
├── tests/
│   ├── unit/
│   ├── integration/
│   └── parity/                      ← online/offline feature parity
├── frontend/                        ← React + Vite + MapLibre (see §33)
│   ├── src/
│   │   ├── api/                     ← generated client for §29 contracts
│   │   ├── components/              ← map, option cards, forecast bands, badges
│   │   ├── routes/                  ← live map · planner · journey · operator
│   │   └── lib/                     ← formatting, live-update socket, state rules
│   └── index.html
├── deploy/
│   ├── Caddyfile                    ← TLS + static + /api reverse proxy
│   ├── compose.deploy.yml           ← the `deploy` profile overlay (§14.4)
│   └── README.md                    ← provisioning runbook
├── docker-compose.yml
├── requirements.txt
├── pyproject.toml
└── CLAUDE.md · PROJECT_STATE.md · CHANGELOG.md · SESSION_LOG.md
```

**Layout rules:**

- `src/pravaah/contracts/` may not import from any other package in `pravaah`. It is the leaf.
- `adapters/` may import `contracts/` only.
- Nothing outside `adapters/` and `config/cities/` may contain a city name.
- `features/definitions.py` is imported by **both** `offline.py` and `online.py`. No feature logic exists anywhere else.
- `models/` may not import `routing/`; `routing/` may not import `models/` directly — it consumes forecasts through the orchestrator.

## 26. Canonical contracts (code-level)

All contracts are Pydantic v2 models in `src/pravaah/contracts/`. They are the stable interface
between planes; changing one is a **document-level change**.

### 26.1 Provenance (`contracts/provenance.py`)

```python
class SourceType(str, Enum):
    REAL_OPERATOR = "REAL_OPERATOR"   # operator-published load (MBTA occupancy_status)
    PUBLIC_FEED   = "PUBLIC_FEED"     # public GTFS-RT position feed
    APC           = "APC"
    AFC           = "AFC"
    CROWDSOURCED  = "CROWDSOURCED"
    DERIVED       = "DERIVED"         # computed by us (map-matched, interpolated)
    SIMULATED     = "SIMULATED"

class Provenance(BaseModel):
    source_type: SourceType
    source_name: str                  # "mbta_cdn", "delhi_otd", "simulator_v1"
    source_timestamp: datetime        # when the source says it was true
    ingest_timestamp: datetime        # when we received it
    quality_score: float = Field(ge=0.0, le=1.0)
    raw_payload_ref: str | None = None
    schema_version: int = 1
```

`Provenance` is a **required** field on every event model. There is no default.

### 26.2 Events (`contracts/events.py`)

```python
class VehiclePositionEvent(BaseModel):
    city_id: str; agency_id: str
    vehicle_id: str
    trip_id: str | None; route_id: str | None; direction_id: int | None
    ts: datetime
    lat: float = Field(ge=-90, le=90); lon: float = Field(ge=-180, le=180)
    bearing: float | None = None
    speed_mps: float | None = None            # DERIVED, never the raw feed field
    stop_id: str | None; current_stop_sequence: int | None
    current_status: VehicleStopStatus | None
    matched_segment_id: str | None = None
    provenance: Provenance

class OccupancyObservation(BaseModel):
    city_id: str; vehicle_id: str; trip_id: str | None
    ts: datetime
    onboard: int | None = None
    capacity: int | None = None
    occupancy_ratio: float | None = Field(default=None, ge=0.0, le=1.0)
    occupancy_class: OccupancyClass | None = None
    boardings: int | None = None; alightings: int | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    provenance: Provenance

class StopPassageEvent(BaseModel):
    city_id: str; vehicle_id: str; trip_id: str; stop_id: str
    stop_sequence: int
    arrival_ts: datetime | None; departure_ts: datetime | None
    dwell_seconds: float | None
    schedule_deviation_seconds: float | None
    provenance: Provenance
```

`OccupancyClass` is the GTFS-RT ordinal ladder, preserved verbatim so the mapping is lossless:
`EMPTY < MANY_SEATS_AVAILABLE < FEW_SEATS_AVAILABLE < STANDING_ROOM_ONLY <
CRUSHED_STANDING_ROOM_ONLY < FULL < NOT_ACCEPTING_PASSENGERS`, plus `UNKNOWN`.

> **`UNKNOWN` is a distinct member, not `None` and not `EMPTY`.** Any code path that coerces a
> missing occupancy into an empty vehicle is a defect (§12.4 rule 3).

### 26.3 Forecast (`contracts/api.py`)

```python
class Quantiles(BaseModel):
    p10: float; p50: float; p90: float

class CrowdForecast(BaseModel):
    trip_id: str; target_stop_id: str; target_time: datetime
    occupancy: Quantiles
    occupancy_class: OccupancyClass
    model_version: str
    feature_ts: datetime
    is_fallback: bool = False        # true when the seasonal baseline served this
```

## 27. Database schema (DDL)

Forward-only migrations in `migrations/`, numbered `NNN_description.sql`. PostGIS and
TimescaleDB extensions are required.

```sql
-- 001_extensions.sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- 002_static_gtfs.sql
CREATE TABLE feed_version (
    feed_version_id  BIGSERIAL PRIMARY KEY,
    city_id          TEXT NOT NULL,
    feed_hash        TEXT NOT NULL,            -- sha256 of the ZIP; import is idempotent on this
    published_at     TIMESTAMPTZ,
    valid_from       DATE, valid_to DATE,
    imported_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (city_id, feed_hash)
);

CREATE TABLE stop (
    feed_version_id  BIGINT NOT NULL REFERENCES feed_version,
    stop_id          TEXT NOT NULL,
    name             TEXT NOT NULL,
    geom             GEOGRAPHY(POINT, 4326) NOT NULL,
    parent_station   TEXT,
    wheelchair_boarding SMALLINT,
    PRIMARY KEY (feed_version_id, stop_id)
);
CREATE INDEX stop_geom_idx ON stop USING GIST (geom);

CREATE TABLE route (
    feed_version_id BIGINT NOT NULL REFERENCES feed_version,
    route_id        TEXT NOT NULL,
    agency_id       TEXT,
    short_name      TEXT, long_name TEXT,
    route_type      SMALLINT NOT NULL,
    PRIMARY KEY (feed_version_id, route_id)
);

CREATE TABLE trip (
    feed_version_id BIGINT NOT NULL REFERENCES feed_version,
    trip_id         TEXT NOT NULL,
    route_id        TEXT NOT NULL,
    service_id      TEXT NOT NULL,
    direction_id    SMALLINT,
    shape_id        TEXT,
    PRIMARY KEY (feed_version_id, trip_id)
);
CREATE INDEX trip_route_idx ON trip (feed_version_id, route_id);

CREATE TABLE stop_time (
    feed_version_id BIGINT NOT NULL REFERENCES feed_version,
    trip_id         TEXT NOT NULL,
    stop_sequence   INT  NOT NULL,
    stop_id         TEXT NOT NULL,
    arrival_seconds  INT,   -- seconds past midnight; MAY exceed 86400 (GTFS >24:00)
    departure_seconds INT,
    PRIMARY KEY (feed_version_id, trip_id, stop_sequence)
);
CREATE INDEX stop_time_stop_idx ON stop_time (feed_version_id, stop_id);

-- 003_telemetry.sql
CREATE TABLE vehicle_position (
    city_id       TEXT NOT NULL,
    vehicle_id    TEXT NOT NULL,
    trip_id       TEXT, route_id TEXT, direction_id SMALLINT,
    ts            TIMESTAMPTZ NOT NULL,
    geom          GEOGRAPHY(POINT, 4326) NOT NULL,
    bearing       REAL,
    speed_mps     REAL,                        -- DERIVED
    stop_id       TEXT, current_stop_sequence INT,
    current_status TEXT,
    matched_segment_id TEXT,
    source_type   TEXT NOT NULL,
    source_name   TEXT NOT NULL,
    quality_score REAL NOT NULL,
    ingest_ts     TIMESTAMPTZ NOT NULL
);
SELECT create_hypertable('vehicle_position', 'ts', chunk_time_interval => INTERVAL '1 day');
CREATE INDEX vp_vehicle_ts_idx ON vehicle_position (city_id, vehicle_id, ts DESC);
CREATE INDEX vp_trip_ts_idx    ON vehicle_position (city_id, trip_id, ts DESC);

CREATE TABLE occupancy_observation (
    city_id     TEXT NOT NULL,
    vehicle_id  TEXT NOT NULL, trip_id TEXT,
    ts          TIMESTAMPTZ NOT NULL,
    onboard     INT, capacity INT,
    occupancy_ratio REAL CHECK (occupancy_ratio BETWEEN 0 AND 1),
    occupancy_class TEXT NOT NULL,             -- includes 'UNKNOWN'
    boardings INT, alightings INT,
    confidence  REAL NOT NULL,
    source_type TEXT NOT NULL, source_name TEXT NOT NULL,
    ingest_ts   TIMESTAMPTZ NOT NULL
);
SELECT create_hypertable('occupancy_observation', 'ts', chunk_time_interval => INTERVAL '1 day');

CREATE TABLE stop_passage (
    city_id TEXT NOT NULL,
    vehicle_id TEXT NOT NULL, trip_id TEXT NOT NULL,
    stop_id TEXT NOT NULL, stop_sequence INT NOT NULL,
    arrival_ts TIMESTAMPTZ, departure_ts TIMESTAMPTZ,
    dwell_seconds REAL,
    schedule_deviation_seconds REAL,
    ts TIMESTAMPTZ NOT NULL                    -- = COALESCE(arrival_ts, departure_ts)
);
SELECT create_hypertable('stop_passage', 'ts', chunk_time_interval => INTERVAL '1 day');

CREATE TABLE segment_travel_time (
    city_id TEXT NOT NULL, segment_id TEXT NOT NULL,
    vehicle_id TEXT NOT NULL, trip_id TEXT,
    start_ts TIMESTAMPTZ NOT NULL, end_ts TIMESTAMPTZ NOT NULL,
    seconds REAL NOT NULL,
    ts TIMESTAMPTZ NOT NULL
);
SELECT create_hypertable('segment_travel_time', 'ts', chunk_time_interval => INTERVAL '1 day');

-- 004_predictions.sql
CREATE TABLE forecast (
    forecast_id   BIGSERIAL PRIMARY KEY,
    city_id       TEXT NOT NULL,
    forecast_type TEXT NOT NULL,               -- 'crowd' | 'eta' | 'delay_risk'
    entity_id     TEXT NOT NULL,               -- trip_id or vehicle_id
    target_stop_id TEXT, target_time TIMESTAMPTZ NOT NULL,
    p10 REAL, p50 REAL, p90 REAL,
    predicted_class TEXT,
    model_version TEXT NOT NULL,
    feature_ts    TIMESTAMPTZ NOT NULL,
    is_fallback   BOOLEAN NOT NULL DEFAULT FALSE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX forecast_lookup_idx ON forecast (city_id, entity_id, target_time DESC);

CREATE TABLE recommendation (
    request_id   UUID NOT NULL,
    candidate_id TEXT NOT NULL,
    rank         INT NOT NULL,
    score        REAL NOT NULL,
    score_terms  JSONB NOT NULL,               -- every weighted term, for explainability
    reasons      TEXT[] NOT NULL,
    prediction_refs BIGINT[],
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (request_id, candidate_id)
);

CREATE TABLE feedback (
    request_id UUID NOT NULL,
    accepted_route TEXT, reported_crowd TEXT,
    observed_outcome JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

**Schema rules:**

- Every telemetry table carries `source_type`, `source_name` and an ingest timestamp. No exceptions.
- `arrival_seconds` / `departure_seconds` are stored as **seconds past service midnight** and may exceed 86400. Never store them as `TIME`.
- All timestamps are `TIMESTAMPTZ` and stored in **UTC**. Local time is a presentation concern only.
- `occupancy_class` is `NOT NULL`; absence is the literal string `'UNKNOWN'`.

## 28. Module specifications

### 28.1 `ingest/gtfs_import.py`

```python
def import_gtfs(zip_path: Path, city_id: str, conn) -> int:
    """Import a GTFS ZIP. Returns feed_version_id. Idempotent by sha256 of the ZIP."""
```

Stops without coordinates are **skipped, not defaulted**. A stop with an invented or zero geometry is worse than an absent one: it silently corrupts every nearest-stop query. See §6.2.1 for the 667 MBTA pathway nodes this affects.

Validates before publishing: referential integrity (every `stop_time.stop_id` exists in
`stops`, every `trip.route_id` in `routes`), coordinate bounds against the city profile's
bounding box, monotonic `stop_sequence` per trip, non-empty service calendar. On any failure,
the transaction rolls back and **nothing** is published.

### 28.2 `ingest/convert.py`

```python
def csv_to_parquet(csv_path: Path, out_dir: Path, kind: Literal["vp","tu"]) -> list[Path]:
    """Convert an append-only recorder CSV into date-partitioned Parquet.

    Output: out_dir/kind=<kind>/date=YYYY-MM-DD/part-NNN.parquet
    Streams in chunks; must never load the whole CSV into memory.
    Deduplicates TripUpdates on (trip_id, stop_id, stop_sequence, arrival_time,
    departure_time) — consecutive polls re-emit near-identical rows (§22).
    """
```

This is the fix for the 864 MB redundancy problem. The raw CSV is retained as the archive; all
downstream reads use Parquet.

**Malformed rows.** The recorder appends continuously, so its CSV is expected to end mid-write:
the final line is routinely truncated. The converter therefore **skips malformed rows and counts
them**, reporting the count alongside the row totals. If malformed rows exceed **0.1% of input**,
the conversion **fails** rather than returning: a torn final line is normal, but widespread
tearing means the capture itself is broken and the output must not be presented as a faithful
archive.

**One writer per file.** The capture format assumes a single appending process. Concurrent
recorders writing the same CSV interleave mid-row and produce torn lines no downstream step can
reconstruct, on top of multiply-recording every observation. Before a long capture, confirm
exactly one recorder is running.

**Positions are never deduplicated.** A stationary vehicle legitimately re-reports the same
position, and collapsing those would destroy dwell time, which is a feature (§9.2). Only
TripUpdates carry a dedup key.

### 28.3 `adapters/replay.py`

```python
class ReplayAdapter(RealtimeAdapter):
    """Replays a recorded corpus through the same canonical event contract as live feeds.

    Guarantees required by §19: deterministic given (corpus, start_ts, speed, seed);
    no network access; emits VehiclePositionEvent identical in shape to the live adapter.
    """
```

The demo depends on this being **indistinguishable downstream** from the live adapter.

### 28.4 Derived speed

```python
def derive_speed(prev: VehiclePositionEvent, cur: VehiclePositionEvent) -> float | None:
    """Great-circle distance / Δt, in m/s.

    Returns None when Δt <= 0, Δt > 300 s, or the implied speed exceeds the city profile's
    max_plausible_speed_mps (the position is then rejected by validate.py).
    """
```

The raw feed `speed` column is populated on ~9.8% of MBTA rows and **must not be used** (§6.2.1).

### 28.5 `features/definitions.py`

Every feature is a pure function registered in one table:

```python
@feature(name="headway_ratio", group="headway", requires=["actual_headway_s","scheduled_headway_s"])
def headway_ratio(ctx: FeatureContext) -> float | None: ...
```

`offline.py` and `online.py` both iterate this registry. `tests/parity/` asserts that, for a
fixed historical timestamp, the online path and the offline path produce **bit-identical**
vectors. A feature implemented in only one path fails the parity test.

### 28.6 `models/` contract

```python
class Forecaster(Protocol):
    model_version: str
    def predict(self, X: pd.DataFrame) -> QuantileFrame: ...   # p10/p50/p90 columns
```

`baseline.SeasonalMedian` implements the same Protocol as `crowd.LightGBMQuantile`. The
orchestrator can substitute the baseline transparently on model failure (§16.1), setting
`is_fallback=True` on the forecast.

### 28.7 `routing/planner.py`

```python
class TripPlanner(Protocol):
    def plan(self, origin: LatLon, destination: LatLon, depart_at: datetime,
             max_transfers: int, max_walk_m: int) -> list[Itinerary]: ...
```

Deterministic. No model imports. Whether the implementation is a hand-written RAPTOR or a
wrapped library is an implementation detail behind this Protocol.

### 28.8 `routing/ranker.py`

```python
def rank(candidates: list[EnrichedItinerary], profile: PreferenceProfile) -> list[RankedItinerary]:
    """Deterministic. Returns candidates ordered by ascending generalized cost (§10.2).

    Every RankedItinerary carries score_terms (each weighted contribution) and reasons
    (human-readable strings derived from the dominant terms). An option without reasons
    is a contract violation (§21 reason coverage).
    """
```

## 29. API request/response schemas

### 29.1 `GET /v1/plan`

Query: `origin=lat,lon` · `destination=lat,lon` · `depart_at` (ISO 8601, optional, default now)
· `preference` ∈ `fastest|least_crowded|most_reliable|balanced` · `max_transfers` (default 2) ·
`max_walk_m` (default 800) · `accessible` (bool, default false).

```json
{
  "request_id": "0e4b...",
  "generated_at": "2026-08-30T12:04:11+05:30",
  "city_id": "mbta",
  "feed_version_id": 7,
  "preference": "balanced",
  "options": [{
    "candidate_id": "c1",
    "rank": 1,
    "legs": [{"mode":"BUS","route_id":"22","trip_id":"...","board_stop_id":"1064",
              "alight_stop_id":"1190","board_time":"...","alight_time":"..."}],
    "travel_time_s": 2340,
    "crowd_at_boarding": {"p10":0.31,"p50":0.42,"p90":0.58,"class":"MANY_SEATS_AVAILABLE"},
    "eta": {"p10":"17:31:00","p50":"17:34:00","p90":"17:39:00"},
    "delay_risk": {"p_gt_10min": 0.12},
    "score": 0.41,
    "score_terms": {"travel":0.18,"wait":0.06,"transfer":0.00,
                    "crowd":0.09,"delay":0.05,"uncertainty":0.03,"walk":0.00},
    "reasons": ["Seats likely at your stop", "Low delay risk", "No transfers"],
    "data_freshness_s": 18,
    "is_fallback": false
  }],
  "departure_advice": {
    "recommended_shift_min": 15,
    "reason": "Predicted crowding drops from 91% to 63% if you leave 15 minutes later",
    "score_improvement": 0.22
  }
}
```

**Response invariants:** `generated_at`, `feed_version_id` and per-option `data_freshness_s`
are always present; `reasons` is never empty; a missing crowd forecast serializes as
`"class": "UNKNOWN"` with a null quantile block, never as zeros.

### 29.2 `POST /v1/occupancy/report`

```json
{"trip_id":"...","vehicle_id":"...","occupancy_class":"STANDING_ROOM_ONLY","reported_at":"..."}
```

Rate-limited per session. Stored with `source_type=CROWDSOURCED` and a confidence derived by
§8.3. Never overrides a fresh `APC` or `REAL_OPERATOR` observation.

### 29.3 Error shape

```json
{"error": {"code": "NO_ROUTE_FOUND", "message": "...", "request_id": "..."}}
```

Codes: `NO_ROUTE_FOUND`, `INVALID_COORDINATES`, `OUT_OF_SERVICE_AREA`, `FEED_UNAVAILABLE`,
`RATE_LIMITED`, `INTERNAL`.

## 30. Configuration and city profiles

### 30.1 City profile (`config/cities/mbta.toml`)

```toml
city_id   = "mbta"
agency_id = "MBTA"
timezone  = "America/New_York"
display_name = "MBTA (Boston)"

[bounds]                     # positions outside this box are rejected
min_lat = 41.2; max_lat = 43.0
min_lon = -71.9; max_lon = -69.9

[feeds]
gtfs_static      = "https://cdn.mbta.com/MBTA_GTFS.zip"
vehicle_positions = "https://cdn.mbta.com/realtime/VehiclePositions.pb"
trip_updates      = "https://cdn.mbta.com/realtime/TripUpdates.pb"
requires_api_key  = false
poll_interval_s   = 20
trip_update_every = 15

[occupancy]
source_type = "REAL_OPERATOR"     # occupancy_status is carried on VehiclePositions
available   = true
coverage_estimate = 0.688

[capacity]                        # fallback when fleet master data is absent
default_bus_capacity = 60
default_rail_capacity = 200

[validation]
max_plausible_speed_mps = 35.0
stale_after_s = 90
```

`config/cities/delhi.toml` mirrors this with `occupancy.available = false`, which switches the
occupancy plane to the simulator or crowdsourcing path and forces every resulting metric to be
labelled non-operator (§2.4).

### 30.2 Preference weights (`config/settings.toml`)

```toml
[preferences.fastest]        wT=1.00; wW=0.40; wX=0.30; wC=0.15; wD=0.35; wU=0.10; wP=0.20
[preferences.least_crowded]  wT=0.40; wW=0.30; wX=0.30; wC=1.00; wD=0.35; wU=0.20; wP=0.20
[preferences.most_reliable]  wT=0.45; wW=0.35; wX=0.35; wC=0.35; wD=0.90; wU=0.70; wP=0.20
[preferences.balanced]       wT=0.70; wW=0.35; wX=0.35; wC=0.70; wD=0.60; wU=0.30; wP=0.20

[departure]
horizons_min = [0, 5, 10, 15, 20]
improvement_threshold = 0.10
waiting_disutility_per_min = 0.012

[reroute]
material_threshold = 0.15
cooldown_s = 180
```

Weights are configuration. **Changing a weight is not a code change and must not require one.**

## 31. Build order with acceptance gates

§20 is the **capability roadmap** -- what the system must eventually do. This section is the
**execution order**, and it is deliberately not the same shape.

A strict P0→P7 march builds every layer to full depth before the next begins, which means
nothing is visible or deployable until most of the work is done. Instead the build proceeds in
**vertical slices**: each slice runs end to end from feed to screen, is deployed, and is
demonstrable on its own. Later slices deepen the layers an earlier slice stubbed. The simplest
component that closes the loop ships first; the sophisticated one replaces it once measured
(ADR-05).

Every gate is an executable test, not an opinion.

### Slice 0 — Data foundation ✅ COMPLETE

| Step | Build | Gate | State |
|---|---|---|---|
| 0.1 | `contracts/`, `config.py`, city profiles | A model missing `provenance` raises `ValidationError`. | ✅ |
| 0.2 | `migrations/001–004`, Compose stack | Migrations apply cleanly from empty: 2 extensions, 12 tables, 4 hypertables. | ✅ |
| 0.3 | `ingest/gtfs_import.py` | 399 routes, **9,630 stops with geometry**, 89,080 trips, 2,221,062 stop-times; re-import returns the same `feed_version_id`. | ✅ |
| 0.4 | `ingest/convert.py` | Corpus converts; TripUpdates drop materially after dedup; malformed rows under 0.1%; peak RSS under 1 GB. | ✅ |

### Slice A — It is alive (first deployable slice)

Live vehicles from the real feed, on the real network, on a public URL. No prediction yet.

| Step | Build | Gate |
|---|---|---|
| A.1 | `adapters/base.py`, `adapters/gtfs_rt.py`, `adapters/mbta.py` | A live poll produces valid `VehiclePositionEvent`s; **zero records lack provenance**; `speed_mps` is left None (§28.4). |
| A.2 | `ingest/validate.py`, `state/redis_state.py` | Out-of-bounds and impossible-speed positions are rejected with a reason; latest-state read < 5 ms; state rebuilds from the database after a Redis restart. |
| A.3 | `api/main.py`, `api/passenger.py` (read-only: `/v1/vehicles/{id}`, `/v1/stops/{id}/departures`), `/v1/health` | Contract tests against §29 shapes; every response carries `generated_at` and freshness. |
| A.4 | `frontend/` live map (§33) | Vehicles move on the correct routes; a stale feed shows the freshness badge; **an unknown occupancy never renders as empty** (§33.3). |
| A.5 | `deploy/` per §14.4 | A clean clone reaches a working public URL by documented runbook; only 80/443 exposed; Postgres and Redis unreachable from outside. |

### Slice B — It predicts

The cheapest honest forecast, end to end, with its uncertainty visible.

| Step | Build | Gate |
|---|---|---|
| B.1 | `ingest/stop_passage.py`, `features/definitions.py`, `features/offline.py`, `features/online.py` | `tests/parity/` -- online and offline vectors identical for a fixed historical timestamp. |
| B.2 | `models/baseline.py` (seasonal median), `models/registry.py` | Trained and scored on a **chronological** split; random splits rejected in review; every prediction records `model_version`. |
| B.3 | `GET /v1/trips/{id}/forecast` + frontend forecast display | Returns p10/p50/p90; a missing forecast serializes as `UNKNOWN` with a null quantile block, and the UI shows "unknown", never a number. |

### Slice C — It decides

| Step | Build | Gate |
|---|---|---|
| C.1 | `routing/planner.py` | Handles transfers, overnight times >24:00, and the no-route case. |
| C.2 | `routing/ranker.py`, `routing/departure.py` | The same origin/destination returns **visibly different orderings** across the four profiles; every option carries reason codes; weights change behaviour without a code change (§30.2). |
| C.3 | `GET /v1/plan` | §29.1 contract test passes; p95 < 2.5 s on the demo dataset. |
| C.4 | Frontend journey planner (§33.2) | Four profiles switchable; each option shows predicted crowd at the boarding stop, delay risk and a plain-language reason. |

### Slice D — It adapts

| Step | Build | Gate |
|---|---|---|
| D.1 | `api/stream.py`, event-triggered re-score | An injected crowd/delay event changes the active recommendation within seconds; hysteresis and cooldown prevent flapping (§10.5). |
| D.2 | Frontend live journey view | The socket reconnects with backoff after a drop; the user is notified only when the preferred route changes. |

### Slice E — Operators

| Step | Build | Gate |
|---|---|---|
| E.1 | `ops/hotspots.py`, `api/admin.py` | A predicted hotspot is reported **before** the capacity threshold is breached, with lead time and supporting evidence. |
| E.2 | Operator dashboard (§33.2) | Hotspot map, route forecast and fleet health with data-freshness flags; RBAC enforced server-side. |

### Slice F — Deepen and harden

Each step replaces something an earlier slice stubbed. **Nothing here ships without beating what
it replaces.**

| Step | Build | Gate |
|---|---|---|
| F.1 | `ingest/mapmatch.py` | Map-match success >95% on a clean replay sample (§21). |
| F.2 | Occupancy pipeline + simulator | `UNKNOWN` never coerces to `EMPTY`; the simulator conserves board/alight and is repeatable by seed. |
| F.3 | `models/crowd.py`, `models/delay.py` (GBDT) | **Beats Slice B's baseline** on threshold-region weighted MAE *and* pinball loss. If it does not, it does not ship. |
| F.4 | `adapters/replay.py`, offline demo | The full five-minute script runs **with networking disabled**. |
| F.5 | Monitoring, `ops/health.py`, docs | §16.2 metrics exposed; `/v1/admin/data-health` reports feed freshness and validation failures. |

### 31.1 Traceability to §20

| §20 phase | Where it is executed |
|---|---|
| P0 Data foundation | Slice 0 |
| P1 Live fleet | A.1–A.2, deepened by F.1 |
| P2 Occupancy pipeline | F.2 |
| P3 Forecasting baseline | B.1–B.2, deepened by F.3 |
| P4 Trip planning/ranking | C.1–C.4 |
| P5 Live adaptation | D.1–D.2 |
| P6 Operator dashboard | E.1–E.2 |
| P7 Hardening | F.4–F.5, plus A.5 for the hosted path |

## 32. Conventions

- **Python 3.12**, formatted with `ruff format`, linted with `ruff check`. Type hints required on all public functions.
- **Timestamps:** UTC everywhere internally, `TIMESTAMPTZ` in the DB, converted only at the presentation edge. The recorder writes `ingest_ts` in UTC while `recorder.log` uses local IST — do not confuse them.
- **IDs:** always `(city_id, entity_id)`. A bare `trip_id` is ambiguous across cities.
- **Migrations:** forward-only, numbered, never edited after being applied.
- **Commits:** conventional prefixes (`feat:`, `fix:`, `chore:`, `docs:`, `test:`). A commit that changes behaviour specified here must reference the section it implements.
- **Dependencies:** pinned in `requirements.txt`. Adding one is a document change if it alters §23.
- **Secrets:** never in the repo. `.env` is git-ignored; `.env.example` documents the keys.
- **Data:** nothing in `data/` is ever hand-edited or committed (§CLAUDE.md).

---

## 33. Frontend specification

The frontend is a **working application against the live API**, not a mockup. It holds no
business logic: it renders what §29 returns and never computes a forecast, a ranking or a crowd
class locally.

### 33.1 Stack

| Concern | Choice |
|---|---|
| Framework | React 18 + TypeScript, built with Vite |
| Map | MapLibre GL JS (no proprietary tile key required) |
| Data fetching | TanStack Query for reads; one WebSocket for live updates (§12.1) |
| Styling | CSS modules or Tailwind -- one, not both |
| Build output | Static assets served by Caddy (§14.4); the frontend is never a Node server in production |

Types are generated from the FastAPI OpenAPI schema, so the client cannot drift from §29.

### 33.2 Screens

| Route | Purpose | Slice |
|---|---|---|
| `/` live map | Vehicles on the real network, with freshness and occupancy state | A.4 |
| `/plan` journey planner | Origin/destination, four preference profiles, ranked options with reasons | C.4 |
| `/journey/:id` live journey | The active trip, re-scored as conditions change | D.2 |
| `/operator` dashboard | Predicted hotspots with lead time, route forecast, fleet health | E.2 |

### 33.3 Data-state rules (binding)

These are the passenger-visible half of §12.4. They are **not** styling preferences, and each has
a gate in §31.

1. **Unknown is never empty.** A missing occupancy renders as "Unknown" in a neutral style. It
   must never appear as 0%, as an empty vehicle, or in the same colour as a genuinely empty one.
2. **Uncertainty is always visible.** Any forecast shown as a number is accompanied by its
   p10–p90 band. A bare point estimate is a defect.
3. **Every ranked option shows its reason.** Reason codes come from the API; the frontend does
   not invent explanations.
4. **Stale data is labelled.** When vehicle state exceeds the city profile's `stale_after_s`, the
   UI shows a "live tracking delayed" badge (§16.1) rather than silently drawing an old position.
5. **Fallbacks are disclosed.** `is_fallback: true` renders as "estimated from history".
6. **Simulated data is marked.** Anything with `source_type=SIMULATED` is visibly tagged and is
   never presented as operator data (§6.5).

### 33.4 Live update behaviour

- One WebSocket per active journey, with exponential backoff and jitter on reconnect.
- On reconnect, refetch state rather than assuming the stream continued.
- Respect the server's hysteresis: the UI does not re-sort on every message, only when the server
  reports that the preferred route changed (§10.5).
- A dropped socket degrades to polling and says so; it never silently freezes.

### 33.5 Non-negotiables

- **No secrets in the bundle.** No feed keys, no database credentials (§15).
- **Keyboard reachable and screen-reader labelled** for the passenger flow. Crowding is never
  conveyed by colour alone -- it always carries a text label, because red/green is the exact
  pairing most affected by colour blindness.
- **Responsive to a phone viewport.** The passenger flow is the mobile case by default.
- The map stays usable at city scale: viewport bounding boxes are requested from the API rather
  than fetching the whole fleet (§12.4 rule 5).

# Appendix A — Example payloads

### A.1 Canonical vehicle-position event

```json
{
  "event_type": "vehicle.position", "schema_version": 1,
  "city_id": "mbta", "agency_id": "MBTA",
  "vehicle_id": "y2075", "trip_id": "76789790", "route_id": "64",
  "timestamp": "2026-08-28T14:03:43+00:00",
  "position": {"lat": 42.364510, "lon": -71.113419},
  "speed_mps": 7.8,
  "matched_segment_id": "seg_1064_1065",
  "source_type": "PUBLIC_FEED", "source_name": "mbta_cdn",
  "quality_score": 0.96
}
```

### A.2 Occupancy observation

```json
{
  "event_type": "occupancy.observation",
  "city_id": "mbta", "vehicle_id": "y2075", "trip_id": "76789790",
  "timestamp": "2026-08-28T14:03:50+00:00",
  "onboard": 37, "capacity": 50, "occupancy_ratio": 0.74,
  "occupancy_class": "STANDING_ROOM_ONLY",
  "source_type": "REAL_OPERATOR", "source_name": "mbta_cdn", "confidence": 0.94
}
```

### A.3 Forecast response

```json
{
  "trip_id": "76789790", "target_stop_id": "1190",
  "target_time": "2026-08-28T17:34:00+00:00",
  "crowd": {"p10": 0.68, "p50": 0.84, "p90": 0.95, "class": "VERY_CROWDED"},
  "eta":   {"p10": "17:31", "p50": "17:34", "p90": "17:39"},
  "model_version": "crowd_gbdt_mbta_2026_08_v1",
  "is_fallback": false
}
```

---

# Appendix B — Judge-facing technical answers

**"Is the crowding data real?"** On the MBTA substrate, yes — `occupancy_status` is
operator-reported and present on ~69% of vehicle observations. The remaining 31% is carried as
`UNKNOWN`, never imputed as empty. Where a city publishes no occupancy, the simulator is used
and every resulting number is tagged `SIMULATED`.

**"Why Boston for an Indian hackathon?"** Delhi publishes no occupancy data, and crowd
prediction is the product. MBTA is the development substrate because it supplies real crowd
labels at no cost; Delhi is the deployment target. All city knowledge is confined to one
adapter and one config file, so the switch is configuration, not a rewrite (§2.4, ADR-08).

**"How do you know the model is any good?"** It is compared against a seasonal-median baseline
on a chronological split, and it does not ship unless it wins on threshold-region weighted MAE
and pinball loss (§31, P3.3). Global accuracy is deliberately not a headline metric because the
label distribution is 61% "many seats" and 0.5% "full".

**"What happens when the feed dies mid-demo?"** The replay adapter emits the identical event
contract from the recorded corpus with no network access. The full demo script is required to
run with networking disabled (§31, P7).

**"Isn't this just Google Maps?"** Google Maps shows current, route-level crowding at best. This
forecasts the load of a specific vehicle at a specific stop at a future time, exposes its
uncertainty, advises departure shifts, and provides an operator product that consumer
navigation apps have no incentive to build.

---

# Appendix C — Change log for this document

| Date | Change | Rationale | Approved |
|---|---|---|---|
| 2026-08-27 | Original architecture document (`.docx`, 25 sections) | Initial design | — |
| 2026-08-30 | Converted to version-controlled Markdown; `.docx` frozen as artefact | Doc-first rule requires reviewable diffs (ADR-09) | Owner |
| 2026-08-30 | §2.4, §6.2 rewritten: Delhi = target, MBTA = development substrate (ADR-08) | Delhi publishes no occupancy; crowd labels are the product | Owner |
| 2026-08-30 | §6.2.1 added: measured field coverage from the recorded corpus | Ground the design in what the data actually contains | Owner |
| 2026-08-30 | §9.2, §28.4: raw feed `speed` prohibited, derived speed mandated | Only 9.8% coverage measured | Owner |
| 2026-08-30 | §9.6, §22: label-imbalance handling made explicit | 0.5% `FULL` makes global accuracy misleading | Owner |
| 2026-08-30 | ADR-10 and §28.2 added: CSV capture → Parquet conversion | 864 MB of near-duplicate TripUpdates rows | Owner |
| 2026-08-30 | **Part II added** (§25–§32): repo layout, contracts, DDL, module specs, API schemas, config, build gates | Makes "built exactly to the document" a checkable claim | Owner |
| 2026-08-30 | §6.2.1, §28.1, §31: stop gate corrected from 10,297 to **9,630 stops with geometry**; 667 coordinate-less `location_type=3` pathway nodes excluded by design | The §31 gate figure (raw row count) contradicted the §27 `geom NOT NULL` schema. Surfaced by the P0.3 integration gate failing. Schema unchanged; the importer refuses to invent coordinates | Owner |
| 2026-08-30 | §28.2, §31: malformed rows skipped and counted, conversion fails above 0.1%; single-writer requirement stated | A live append-only CSV always ends mid-write, so strict failure is unusable; silent skipping would let a broken capture report success. Surfaced when three concurrent recorders produced torn rows | Owner |
| 2026-08-30 | **§31 restructured into vertical slices** (Slice 0/A/B/C/D/E/F) with a §31.1 traceability table back to §20 | A strict P0-P7 march leaves nothing visible or deployable until most of the work is done. Slices ship end to end and deploy early; later slices deepen what earlier ones stubbed | Owner |
| 2026-08-30 | **§33 added: frontend specification** | The frontend was named in §25 and §23 but had no specification and only one incidental gate across 17 phase rows. It is a working application, so its data-state rules (unknown is never empty, uncertainty always visible, reasons always shown) are binding | Owner |
| 2026-08-30 | **§14.4 added: public demo deployment on a single VM** | Deployment was absent from the build order entirely. One VM running the existing Compose stack keeps §27 unchanged, since TimescaleDB is unavailable on most managed free tiers. The offline replay requirement is retained, not replaced | Owner |

> **To propose a change:** add a row here with the date, the change, the rationale and a blank
> Approved column; edit the relevant section; and raise it with the project owner. Do not write
> the corresponding code until the Approved column is filled.
