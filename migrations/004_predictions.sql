-- Forecasts, recommendations and feedback (SOLUTION.md sections 11.2, 27).

CREATE TABLE IF NOT EXISTS forecast (
    forecast_id    BIGSERIAL PRIMARY KEY,
    city_id        TEXT NOT NULL,
    forecast_type  TEXT NOT NULL,   -- 'crowd' | 'eta' | 'delay_risk'
    entity_id      TEXT NOT NULL,   -- trip_id or vehicle_id
    target_stop_id TEXT,
    target_time    TIMESTAMPTZ NOT NULL,
    p10 REAL,
    p50 REAL,
    p90 REAL,
    predicted_class TEXT,
    model_version  TEXT NOT NULL,   -- every prediction records it (section 8)
    feature_ts     TIMESTAMPTZ NOT NULL,
    is_fallback    BOOLEAN NOT NULL DEFAULT FALSE,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    -- Quantiles must not cross; mirrors the Quantiles contract (section 26.3).
    CONSTRAINT forecast_quantiles_ordered
        CHECK (p10 IS NULL OR p50 IS NULL OR p90 IS NULL OR (p10 <= p50 AND p50 <= p90))
);
CREATE INDEX IF NOT EXISTS forecast_lookup_idx ON forecast (city_id, entity_id, target_time DESC);

CREATE TABLE IF NOT EXISTS recommendation (
    request_id      UUID NOT NULL,
    candidate_id    TEXT NOT NULL,
    rank            INT  NOT NULL,
    score           REAL NOT NULL,
    score_terms     JSONB NOT NULL,  -- every weighted term, for explainability
    reasons         TEXT[] NOT NULL,
    prediction_refs BIGINT[],
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (request_id, candidate_id),
    -- Reason coverage is an acceptance criterion (section 21), so the database
    -- refuses an unexplained recommendation rather than trusting the caller.
    CONSTRAINT recommendation_has_reasons CHECK (cardinality(reasons) > 0)
);

CREATE TABLE IF NOT EXISTS feedback (
    request_id       UUID NOT NULL,
    accepted_route   TEXT,
    reported_crowd   TEXT,
    observed_outcome JSONB,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
