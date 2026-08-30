-- Dense telemetry (SOLUTION.md sections 11.1, 11.3, 27).
-- Every table carries source_type, source_name and an ingest timestamp.
-- No exceptions: a record without provenance is invalid (section 6.8).

CREATE TABLE IF NOT EXISTS vehicle_position (
    city_id               TEXT NOT NULL,
    vehicle_id            TEXT NOT NULL,
    trip_id               TEXT,
    route_id              TEXT,
    direction_id          SMALLINT,
    ts                    TIMESTAMPTZ NOT NULL,
    geom                  GEOGRAPHY(POINT, 4326) NOT NULL,
    bearing               REAL,
    speed_mps             REAL,  -- DERIVED (section 28.4), never the raw feed field
    stop_id               TEXT,
    current_stop_sequence INT,
    current_status        TEXT,
    matched_segment_id    TEXT,
    source_type           TEXT NOT NULL,
    source_name           TEXT NOT NULL,
    quality_score         REAL NOT NULL,
    ingest_ts             TIMESTAMPTZ NOT NULL
);
SELECT create_hypertable('vehicle_position', 'ts',
                         chunk_time_interval => INTERVAL '1 day',
                         if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS vp_vehicle_ts_idx ON vehicle_position (city_id, vehicle_id, ts DESC);
CREATE INDEX IF NOT EXISTS vp_trip_ts_idx    ON vehicle_position (city_id, trip_id, ts DESC);

CREATE TABLE IF NOT EXISTS occupancy_observation (
    city_id         TEXT NOT NULL,
    vehicle_id      TEXT NOT NULL,
    trip_id         TEXT,
    ts              TIMESTAMPTZ NOT NULL,
    onboard         INT,
    capacity        INT,
    occupancy_ratio REAL CHECK (occupancy_ratio BETWEEN 0 AND 1),
    -- NOT NULL, and absence is the literal string 'UNKNOWN'.
    -- Missing occupancy must never become zero (section 12.4 rule 3).
    occupancy_class TEXT NOT NULL,
    boardings       INT,
    alightings      INT,
    confidence      REAL NOT NULL,
    source_type     TEXT NOT NULL,
    source_name     TEXT NOT NULL,
    ingest_ts       TIMESTAMPTZ NOT NULL
);
SELECT create_hypertable('occupancy_observation', 'ts',
                         chunk_time_interval => INTERVAL '1 day',
                         if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS occ_vehicle_ts_idx
    ON occupancy_observation (city_id, vehicle_id, ts DESC);

CREATE TABLE IF NOT EXISTS stop_passage (
    city_id       TEXT NOT NULL,
    vehicle_id    TEXT NOT NULL,
    trip_id       TEXT NOT NULL,
    stop_id       TEXT NOT NULL,
    stop_sequence INT  NOT NULL,
    arrival_ts    TIMESTAMPTZ,
    departure_ts  TIMESTAMPTZ,
    dwell_seconds REAL,
    schedule_deviation_seconds REAL,
    ts            TIMESTAMPTZ NOT NULL   -- COALESCE(arrival_ts, departure_ts)
);
SELECT create_hypertable('stop_passage', 'ts',
                         chunk_time_interval => INTERVAL '1 day',
                         if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS passage_trip_idx ON stop_passage (city_id, trip_id, stop_sequence);

CREATE TABLE IF NOT EXISTS segment_travel_time (
    city_id    TEXT NOT NULL,
    segment_id TEXT NOT NULL,
    vehicle_id TEXT NOT NULL,
    trip_id    TEXT,
    start_ts   TIMESTAMPTZ NOT NULL,
    end_ts     TIMESTAMPTZ NOT NULL,
    seconds    REAL NOT NULL,
    ts         TIMESTAMPTZ NOT NULL
);
SELECT create_hypertable('segment_travel_time', 'ts',
                         chunk_time_interval => INTERVAL '1 day',
                         if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS stt_segment_idx ON segment_travel_time (city_id, segment_id, ts DESC);
