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

## 3. Conductor Role

The Conductor role is focused on generating the ground-truth data (live GPS and manual occupancy overrides). This role requires authentication to prevent abuse.

### Proposed 4 Tabs for Conductors:

1. **Tab 1: Active Duty (Main Screen)**
   - **What it is:** The primary interface while driving/working.
   - **Internal Pages/Content:** A massive, high-contrast, distraction-free screen with 3-4 simple buttons ("Empty", "Few Seats", "Standing", "Full"). Tapping these updates the system instantly. A background process continuously polls GPS.
2. **Tab 2: My Route**
   - **What it is:** Current trip information.
   - **Internal Pages/Content:** The scheduled stops for the current trip and distance to the next stop.
3. **Tab 3: Dispatch Alerts**
   - **What it is:** Communication from the Operator.
   - **Internal Pages/Content:** Messages from the control room (e.g., "Wait 2 minutes at next stop for connection").
4. **Tab 4: Shift / Profile**
   - **What it is:** Duty and assignment management.
   - **Internal Pages/Content:** 
     - **Bus Selection Flow:** Before going "Active", the conductor selects their Route (e.g., Route 64) and current Trip/Direction from the official database schedule, and inputs their physical Vehicle Number (e.g., Bus #105). 
     - **Clock-in/out Toggle:** This binds their phone's GPS to the selected bus and controls when tracking is active.

---

## Decision Required

Please review the options above. 

1. For the **Passenger Role**, do you prefer **Option A (Dashboard approach)**, **Option B (Map-centric)**, or a mix of both?
2. For the **Operator Role**, do the proposed 4 tabs (Fleet, Hotspots, Diagnostics, Profile) cover everything you need?
3. For the **Conductor Role**, does the focus on a distraction-free manual override screen match your vision?

Once you select your preferred 4 tabs for each role, we will lock this in as our official UI architecture.
