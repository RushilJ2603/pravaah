# PRAVAAH Flutter App: Structure & Page Options

This document outlines the proposed page structures for the PRAVAAH Flutter application, separating the **Passenger (User)** and **Operator (Admin)** experiences. 

Instead of exposing every individual feature (Live Map, Journey Planner, etc.) as a top-level navigation item, we can nest them intuitively inside a clean **4-Tab Navigation Bar**.

---

## 1. Passenger (User) Role

The passenger experience should feel consumer-friendly, similar to modern transit apps (like Citymapper or Transit). Here are two options for the 4 main navigation tabs:

### Option A: The "Action-First" Dashboard Approach (Recommended)
This matches your idea of having a top-level "Dashboard" that nests the specific features.

1. **Tab 1: Dashboard (Home)**
   - **What it is:** The starting point of the app.
   - **Internal Pages/Content:** 
     - A "Where to?" search bar that immediately drops you into the *Journey Planner*.
     - A mini "Live Map" widget showing nearby buses.
     - Pinned/Favorite stops and recent destinations.
2. **Tab 2: Journey**
   - **What it is:** The dedicated travel tab.
   - **Internal Pages/Content:**
     - *Planning Mode:* Origin, destination, preference profiles (Fastest vs Least Crowded), and ranked options.
     - *Active Mode:* When a trip is started, this tab becomes the **Live Journey** tracker, showing the live progress bar, ETAs, and dynamic crowd forecasting.
3. **Tab 3: Saved & Alerts (The missing "smthg")**
   - **What it is:** Personalized transit data.
   - **Internal Pages/Content:** Saved offline schedules for frequent routes, active network disruptions, and push-notification alerts for the user's daily commute.
4. **Tab 4: Profile**
   - **What it is:** Account and settings.
   - **Internal Pages/Content:** Accessibility preferences (crucial for visual/motor impairments), theme settings, and a "Switch to Operator" toggle.

### Option B: The "Map-Centric" Approach
This approach puts the map at the absolute center of the experience, similar to Uber.

1. **Tab 1: Live Map** (Full-screen map always visible; search bar floats on top).
2. **Tab 2: Routes** (A directory of all bus lines and their current health).
3. **Tab 3: Activity** (Past trips and currently active journeys).
4. **Tab 4: Account** (Settings and profile).

---

## 2. Operator (Admin) Role

The Operator role is focused on fleet management, predictive analytics, and system health. The navigation here might use a bottom bar on phones, or a side-rail on tablets. 

### Proposed 4 Tabs for Operators:

1. **Tab 1: Fleet Command (Live Map)**
   - **What it is:** A bird's-eye view of the city.
   - **Internal Pages/Content:** A live map showing all active vehicles. Crucially, it highlights anomalies—buses that are severely delayed or overcrowded glow red, while healthy routes are muted.
2. **Tab 2: Prediction Hotspots**
   - **What it is:** The core AI value proposition of PRAVAAH.
   - **Internal Pages/Content:** A prioritized inbox of *future* problems. E.g., "Stop 1064 will exceed capacity in 45 minutes." Operators can click into a hotspot to see the granular forecast and reasons.
3. **Tab 3: Route Diagnostics**
   - **What it is:** Deep dives into specific transit lines.
   - **Internal Pages/Content:** Headway tracking (are buses bunching together?), historical reliability for the day, and active driver status.
4. **Tab 4: System / Profile**
   - **What it is:** Administrative tools.
   - **Internal Pages/Content:** Shift management, API/data feed health (showing if the GTFS feed is stale), and logout.

---

## Decision Required

Please review the options above. 

1. For the **User Role**, do you prefer **Option A (Dashboard approach)**, **Option B (Map-centric)**, or a mix of both?
2. For the **Operator Role**, do the proposed 4 tabs (Fleet, Hotspots, Diagnostics, Profile) cover everything you need?

Once you select your preferred 4 tabs for each role, we will lock this in as our official UI architecture.

I have officially updated the project architecture to adopt your idea!

As you can see in the new Walkthrough artifact, I've modified docs/SOLUTION.md across several sections. Most importantly:

We now have a formal requirement for a new backend endpoint: POST /v1/telemetry/conductor.
The UI specs have been updated to include a "Conductor Mode" for the Flutter app.
We added strict security requirements: while the passenger app stays open, the conductor endpoints must require Authentication (JWT/API Keys) to prevent random people from spoofing bus locations.
This officially solves the Delhi "Cold Start" problem on an architectural level. Everything is perfectly documented and ready to be built. Let me know what you'd like to tackle next (and if you're ready to lift the "NO CODE" restriction)!

# Architectural Analysis: The Conductor Role

This document analyzes the impact of introducing a **Conductor App** to crowd-source live bus locations (GPS) and occupancy data, replacing or supplementing public transit data feeds.

---

## 1. How it works right now (The Current Reality)

In our current architecture (built around the MBTA dataset):
- **Live Location:** We do not track individual phones. The city's transit authority (MBTA) has GPS hardware installed on their buses. They aggregate this and publish a bulk `GTFS-Realtime` file on the internet. Our backend polls that file every 15-30 seconds, parses it, and updates our database.
- **Occupancy:** The MBTA buses have Automated Passenger Counters (APCs)—laser sensors on the doors that count people entering and exiting. This data is included in the GTFS feed.
- **The Problem:** As stated in `SOLUTION.md` Appendix B, **Delhi publishes no occupancy data**. Without occupancy data, our AI model cannot be trained to predict crowds. 

---

## 2. The "Conductor App" Proposal

Your idea to use the conductor's smartphone as both the GPS tracker and the occupancy reporter is **brilliant**. In fact, for a deployment target like Delhi (or any developing city without smart buses), this is the exact missing link. It turns standard buses into "smart" buses instantly with zero hardware cost.

### Feasibility: Is it possible?
Yes, absolutely. The entire architecture was actually built to support multiple data sources. The backend data structures (`VehiclePositionEvent` and `OccupancyObservation`) have a `source_type` field specifically designed to differentiate between public feeds (`PUBLIC_FEED`), simulations (`SIMULATED`), and real manual inputs (`REAL_OPERATOR` / `CONDUCTOR_APP`).

---

## 3. Impact on the Architecture & Application

Introducing this changes our system from a "Read-Only Consumer" of transit data into a "Two-Way Transit Platform". Here is exactly how it affects everything:

### A. Frontend (The Flutter App)
We will need to introduce a **3rd Role: Conductor** (or merge it into a specialized Operator view).
- **UI:** A massive, high-contrast, distraction-free screen with 3-4 simple buttons for the conductor to tap: "Empty", "Few Seats", "Standing Only", "Full". 
- **Hardware Integration:** The app must request **Background Location Permissions**. It will poll the phone's GPS every 10-15 seconds.
- **Network:** It will continually fire POST requests to our backend with the current coordinates and the last tapped occupancy status.

### B. Backend (FastAPI)
Currently, our passenger API only has `GET` endpoints. 
- We will need to build a new ingest endpoint: `POST /v1/telemetry/conductor`.
- When the conductor's phone hits this endpoint, the backend skips the GTFS importer and injects the data directly into our Redis cache and TimescaleDB tables.

### C. The Data Pipeline & AI Models
- **Provenance:** The incoming data will be tagged with `source_name: "conductor_app"`. 
- **Priority:** If a city *does* happen to have a public feed, our system will prioritize the conductor's manual override over the public feed (because the conductor is literally standing inside the bus).
- **Model Training:** This manual input creates the perfect "Ground Truth" labels we need to train the Machine Learning crowding models.

### D. Security & Auth (The Biggest Change)
Currently, `SOLUTION.md` explicitly states "no secrets in the bundle" for the passenger app. However, if conductors can update the actual position of city buses:
- We **must** implement authentication (Login/Passwords or JWT tokens) for the Conductor role. 
- Without auth, a malicious user could download the app and spoof bus locations, ruining the city's entire transit map.

---

## 4. Conclusion

Adding a Conductor Role fundamentally solves the "Cold Start" problem for cities like Delhi. 

It does not require a rewrite of our database or models; it just requires a new flutter screen, a background GPS task, a new API endpoint, and basic login security. For a hackathon, showing that you can *generate* the data rather than just *consume* it is a massive competitive advantage.

### Decision Required
Do you want to formally adopt the **Conductor App** as part of our core architecture for this project? If so, I will update the official `SOLUTION.md` to reflect this new role and the required `POST /v1/telemetry` endpoint.


<!-- below is the gemini xml prompt for probable fallbacks on the design do consider while planing out -->


<?xml version="1.0" encoding="UTF-8"?>
<TransitAppSpecification project="Pravaah">
    <SystemOverview>
        <Description>
            Production-grade, battery-efficient mobile transit application featuring core REST endpoints for discovery/routing and persistent streaming protocols (WebSockets/SSE) for real-time tracking and trip progress.
        </Description>
    </SystemOverview>

    <APIEndpoints>
        <Category name="Discovery &amp; Geospatial Map">
            <Endpoint method="GET" path="/api/v1/transit/stops/nearby">
                <Description>Fetches transit stops within a geographic radius with upcoming departures and real-time arrival estimates.</Description>
                <QueryParams>lat (float), lng (float), radius_m (int, default: 500), mode (string, optional)</QueryParams>
                <ResponsePayload><![CDATA[
{
  "stops": [{
    "stop_id": "ST_DL_042",
    "stop_name": "Kashmere Gate ISBT",
    "lat": 28.6675, "lng": 77.2285,
    "distance_m": 120.5,
    "departures": [{
      "trip_id": "TRIP_502_UP",
      "route_short_name": "502",
      "realtime_arrival": "2026-08-30T11:47:30Z",
      "crowding_level": "medium"
    }]
  }]
}
                ]]></ResponsePayload>
            </Endpoint>
            
            <Endpoint method="GET" path="/api/v1/transit/routes/{route_id}/live">
                <Description>Retrieves the complete shape polyline for a route alongside all actively running vehicles.</Description>
                <QueryParams>include_stops (boolean, default: true)</QueryParams>
            </Endpoint>

            <Endpoint method="GET" path="/api/v1/transit/viewport/vehicles">
                <Description>Fetches a lightweight list of vehicles within the map viewport bounding box.</Description>
                <QueryParams>min_lat, min_lng, max_lat, max_lng</QueryParams>
            </Endpoint>
        </Category>

        <Category name="Routing &amp; Intelligence">
            <Endpoint method="POST" path="/api/v1/routing/plan">
                <Description>Calculates optimal routes balancing travel time, transfers, and crowding.</Description>
                <RequestPayload><![CDATA[
{
  "origin": {"lat": 28.6139, "lng": 77.2090},
  "destination": {"lat": 28.5355, "lng": 77.3910},
  "preferences": {
    "optimize_for": "balanced",
    "crowding_tolerance_threshold": "high"
  }
}
                ]]></RequestPayload>
            </Endpoint>

            <Endpoint method="GET" path="/api/v1/trips/{trip_id}/occupancy-profile">
                <Description>Returns station-by-station occupancy curve for a specific trip.</Description>
            </Endpoint>
        </Category>

        <Category name="Streaming &amp; Crowdsourcing">
            <Endpoint method="WS" path="/ws/v1/live-tracking">
                <Description>Bidirectional WebSocket for live vehicle coordinates and ETAs.</Description>
                <StreamPayload><![CDATA[
{
  "type": "VEHICLE_UPDATE",
  "vehicle_id": "DL-1PC-4091",
  "lat": 28.6421, "lng": 77.2205,
  "crowding_delta": "steady",
  "stops_away": 2
}
                ]]></StreamPayload>
            </Endpoint>

            <Endpoint method="POST" path="/api/v1/feedback/crowding-report">
                <Description>Enables passenger reporting to update Bayesian priors on vehicle occupancy.</Description>
            </Endpoint>
        </Category>
    </APIEndpoints>

    <SystemBottlenecksAndFallbacks>
        <Issue name="Telemetry Ingestion Lag">
            <CurrentFallback>Periodic polling of GTFS-RT feeds (15-30s cron).</CurrentFallback>
            <Problem>Causes erratic ETA jumps and "ghost buses" due to delayed telemetry processing.</Problem>
        </Issue>
        <Issue name="Cold-Start Crowding Data">
            <CurrentFallback>Static time-of-day tables or dwell-time inference when APC data is absent.</CurrentFallback>
            <Problem>Dwell times fluctuate from traffic, leading to false high-crowding classifications.</Problem>
        </Issue>
        <Issue name="DB Spatial Bottlenecks">
            <CurrentFallback>Running PostGIS ST_DWithin queries on relational tables for viewport pans.</CurrentFallback>
            <Problem>CPU lockup and I/O bottlenecks during peak rush hour.</Problem>
        </Issue>
        <Issue name="Mobile Battery Drain">
            <CurrentFallback>Native REST polling every 5 seconds.</CurrentFallback>
            <Problem>Prevents radio state dormancy, draining battery and spiking bandwidth.</Problem>
        </Issue>
    </SystemBottlenecksAndFallbacks>

    <TargetArchitecture>
        <Component layer="Routing Algorithm">
            <Baseline>DB-based Dijkstra / A* over road network</Baseline>
            <Optimized>McRAPTOR (Multi-criteria Round-Based Public Transit Routing)</Optimized>
            <Benefit>50x faster queries; computes Pareto-optimal sets in &lt;15ms.</Benefit>
        </Component>
        <Component layer="Real-time State Store">
            <Baseline>Relational DB updates / Simple Redis Keys</Baseline>
            <Optimized>Redis Geospatial (GEOADD/GEORADIUS) + Redis Streams</Optimized>
            <Benefit>Zero DB load for live telemetry; instant spatial proximity queries.</Benefit>
        </Component>
        <Component layer="Mobile Transport">
            <Baseline>Frequent HTTP JSON Polling</Baseline>
            <Optimized>WebSocket / Server-Sent Events (SSE) with Protobuf</Optimized>
            <Benefit>Up to 80% bandwidth reduction; sub-second live bus animation.</Benefit>
        </Component>
        <Component layer="Crowding Inference">
            <Baseline>Static heuristics / Dwell-time rules</Baseline>
            <Optimized>Multi-tier Hierarchical ML Inference Model</Optimized>
            <Benefit>Robust predictions despite missing physical sensor feeds.</Benefit>
        </Component>
        <Component layer="Mobile Client Storage">
            <Baseline>Ephemeral in-memory state</Baseline>
            <Optimized>Offline-First Embedded Engine (SQLite)</Optimized>
            <Benefit>Instant UI render from local static GTFS cache; tolerates network drops.</Benefit>
        </Component>
    </TargetArchitecture>

    <ImplementationStrategy>
        <Step number="1" title="Real-time Ingestion &amp; Spatial Partitioning">
            <Action>Build high-throughput ingestion using Redis Streams and Geohash clustering.</Action>
            <Details>Update GEOADD with a 60-second TTL on GPS push. Map mobile client bounding boxes to geohash buckets to stream only relevant deltas.</Details>
        </Step>
        
        <Step number="2" title="Multi-Tier Crowding Inference Engine">
            <Action>Implement a 4-tier fallback inference pipeline.</Action>
            <Details>
                1. Direct Telemetry (APC/AFC)
                2. ML Feature Fusion (LightGBM on historical + real-time variables)
                3. Historical Baseline (Time-of-day matrices)
                4. Crowdsourced Correction (Dynamic Bayesian updates)
            </Details>
        </Step>

        <Step number="3" title="Mobile Client Optimizations">
            <Action>Implement offline-first capabilities and smooth UI rendering.</Action>
            <Details>Bundle compressed static GTFS SQLite caches. Animate vehicle markers using cubic spline interpolation. Use OS background geofencing for "Prepare to Alight" alarms to function offline.</Details>
        </Step>
    </ImplementationStrategy>
</TransitAppSpecification>