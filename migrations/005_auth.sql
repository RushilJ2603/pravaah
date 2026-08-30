-- Staff authentication and conductor shifts (SOLUTION.md sections 15.3 and 27).
-- Forward-only: the partial unique index is the concurrency-safe vehicle claim.

CREATE TABLE IF NOT EXISTS app_user (
    user_id       BIGSERIAL PRIMARY KEY,
    username      TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL CHECK (role IN ('CONDUCTOR', 'OPERATOR')),
    city_id       TEXT NOT NULL,
    agency_id     TEXT,
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS conductor_shift (
    shift_id   BIGSERIAL PRIMARY KEY,
    user_id    BIGINT NOT NULL REFERENCES app_user(user_id),
    city_id    TEXT NOT NULL,
    vehicle_id TEXT NOT NULL,
    trip_id    TEXT,
    route_id   TEXT,
    device_id  TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at   TIMESTAMPTZ
);

CREATE UNIQUE INDEX IF NOT EXISTS conductor_shift_one_active
    ON conductor_shift (city_id, vehicle_id) WHERE ended_at IS NULL;
