-- Canonical GTFS model (SOLUTION.md sections 11.2, 27).
-- Every table is scoped by feed_version_id so importing a new feed never
-- mutates history and never invalidates a running query.

CREATE TABLE IF NOT EXISTS feed_version (
    feed_version_id  BIGSERIAL PRIMARY KEY,
    city_id          TEXT NOT NULL,
    feed_hash        TEXT NOT NULL,   -- sha256 of the ZIP; import is idempotent on this
    published_at     TIMESTAMPTZ,
    valid_from       DATE,
    valid_to         DATE,
    imported_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (city_id, feed_hash)
);

CREATE TABLE IF NOT EXISTS stop (
    feed_version_id     BIGINT NOT NULL REFERENCES feed_version ON DELETE CASCADE,
    stop_id             TEXT NOT NULL,
    name                TEXT NOT NULL,
    geom                GEOGRAPHY(POINT, 4326) NOT NULL,
    parent_station      TEXT,
    wheelchair_boarding SMALLINT,
    PRIMARY KEY (feed_version_id, stop_id)
);
CREATE INDEX IF NOT EXISTS stop_geom_idx ON stop USING GIST (geom);

CREATE TABLE IF NOT EXISTS route (
    feed_version_id BIGINT NOT NULL REFERENCES feed_version ON DELETE CASCADE,
    route_id        TEXT NOT NULL,
    agency_id       TEXT,
    short_name      TEXT,
    long_name       TEXT,
    route_type      SMALLINT NOT NULL,
    PRIMARY KEY (feed_version_id, route_id)
);

CREATE TABLE IF NOT EXISTS trip (
    feed_version_id BIGINT NOT NULL REFERENCES feed_version ON DELETE CASCADE,
    trip_id         TEXT NOT NULL,
    route_id        TEXT NOT NULL,
    service_id      TEXT NOT NULL,
    direction_id    SMALLINT,
    shape_id        TEXT,
    PRIMARY KEY (feed_version_id, trip_id)
);
CREATE INDEX IF NOT EXISTS trip_route_idx ON trip (feed_version_id, route_id);

CREATE TABLE IF NOT EXISTS stop_time (
    feed_version_id   BIGINT NOT NULL REFERENCES feed_version ON DELETE CASCADE,
    trip_id           TEXT NOT NULL,
    stop_sequence     INT  NOT NULL,
    stop_id           TEXT NOT NULL,
    -- Seconds past SERVICE midnight. MAY exceed 86400 (GTFS allows >24:00).
    -- Never store these as TIME (SOLUTION.md section 27, schema rules).
    arrival_seconds   INT,
    departure_seconds INT,
    PRIMARY KEY (feed_version_id, trip_id, stop_sequence)
);
CREATE INDEX IF NOT EXISTS stop_time_stop_idx ON stop_time (feed_version_id, stop_id);
