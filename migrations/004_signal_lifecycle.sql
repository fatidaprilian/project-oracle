-- Migration 004: Signal Lifecycle & Portfolio Tracking
-- Adds expiry, resolution tracking, and enhanced portfolio monitoring.

-- Fix 2: Signal expiry & resolution tracking
ALTER TABLE signal_history ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ;
ALTER TABLE signal_history ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMPTZ;
ALTER TABLE signal_history ADD COLUMN IF NOT EXISTS resolved_action TEXT;

-- Fix 4 & 6: Enhanced active tracking for portfolio monitoring
ALTER TABLE active_tracking ADD COLUMN IF NOT EXISTS entry_price NUMERIC;
ALTER TABLE active_tracking ADD COLUMN IF NOT EXISTS target_price NUMERIC;
ALTER TABLE active_tracking ADD COLUMN IF NOT EXISTS stop_loss NUMERIC;
ALTER TABLE active_tracking ADD COLUMN IF NOT EXISTS current_price NUMERIC;
ALTER TABLE active_tracking ADD COLUMN IF NOT EXISTS pnl_percent NUMERIC DEFAULT 0;
ALTER TABLE active_tracking ADD COLUMN IF NOT EXISTS signal_id UUID;

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_signal_history_expires
ON signal_history (expires_at)
WHERE resolved_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_active_tracking_active
ON active_tracking (is_active)
WHERE is_active = TRUE;
