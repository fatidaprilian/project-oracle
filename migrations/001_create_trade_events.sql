CREATE TABLE IF NOT EXISTS trade_events (
    id BIGSERIAL PRIMARY KEY,
    event_type TEXT NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_trade_events_event_type
    ON trade_events (event_type);

CREATE INDEX IF NOT EXISTS idx_trade_events_created_at
    ON trade_events (created_at DESC);