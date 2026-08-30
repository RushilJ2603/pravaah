-- Query indexes required by the forecast, planner, and operator endpoints.
--
-- These indexes were proven against the Delhi synthetic schedule while
-- diagnosing the hotspot query, but were initially created only in the live
-- database. Keeping them in a forward-only migration makes fresh environments
-- match the verified deployment.

CREATE INDEX IF NOT EXISTS stop_time_feed_arrival_idx
    ON stop_time (feed_version_id, arrival_seconds);

CREATE INDEX IF NOT EXISTS stop_time_feed_trip_idx
    ON stop_time (feed_version_id, trip_id);
