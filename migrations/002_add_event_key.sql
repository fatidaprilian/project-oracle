ALTER TABLE trade_events
    ADD COLUMN IF NOT EXISTS event_key TEXT;

UPDATE trade_events
SET event_key = md5(event_type || payload::text || created_at::text)
WHERE event_key IS NULL;

ALTER TABLE trade_events
    ALTER COLUMN event_key SET NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_trade_events_event_key
    ON trade_events (event_key);