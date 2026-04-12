# Project Oracle - Data Model Draft

## 1. Tujuan
Dokumen ini mendefinisikan struktur data minimum untuk mendukung:
- audit keputusan entry/exit
- evaluasi performa strategi
- loop pembelajaran mingguan

## 2. Entitas PostgreSQL

### 2.1 strategy_parameters
Menyimpan konfigurasi aktif strategi.

Kolom utama:
- id (uuid, pk)
- version (text, unique)
- market_structure_window (int)
- min_confluence_score (numeric)
- min_volume_threshold (numeric)
- sweep_tolerance_bps (int)
- breakeven_r_multiple (numeric)
- fib_tp_primary (numeric)
- fib_tp_secondary (numeric)
- is_active (boolean)
- created_at (timestamptz)
- approved_by (text)

### 2.2 trade_candidates
Snapshot kandidat setelah lolos filter.

Kolom utama:
- id (uuid, pk)
- symbol (text)
- timeframe (text)
- market_regime (text)
- structure_score (numeric)
- order_block_zone (jsonb)
- fib_levels (jsonb)
- confluence_score (numeric)
- sentiment_bias (text)
- event_risk_level (text)
- shield_status (boolean)
- candidate_state (text)
- created_at (timestamptz)
- expires_at (timestamptz)

### 2.3 orders
Rencana dan hasil eksekusi order.

Kolom utama:
- id (uuid, pk)
- candidate_id (uuid, fk -> trade_candidates.id)
- exchange_order_id (text)
- order_type (text)
- side (text)
- price (numeric)
- size (numeric)
- leverage (numeric)
- status (text)
- rejection_reason (text)
- created_at (timestamptz)
- updated_at (timestamptz)

### 2.4 positions
Posisi aktif dan histori close.

Kolom utama:
- id (uuid, pk)
- order_id (uuid, fk -> orders.id)
- symbol (text)
- side (text)
- entry_price (numeric)
- stop_loss (numeric)
- take_profit_primary (numeric)
- take_profit_secondary (numeric)
- break_even_armed (boolean)
- status (text)
- closed_at (timestamptz)

### 2.5 trade_events
Event detail selama lifecycle.

Kolom utama:
- id (bigserial, pk)
- position_id (uuid, fk -> positions.id)
- event_type (text)
- payload (jsonb)
- created_at (timestamptz)

### 2.6 trade_journal
Ringkasan hasil final per trade.

Kolom utama:
- id (uuid, pk)
- position_id (uuid, fk -> positions.id)
- pnl_usd (numeric)
- r_multiple (numeric)
- max_adverse_excursion (numeric)
- max_favorable_excursion (numeric)
- exit_reason (text)
- reason_codes (text[])
- snapshot_ref (text)
- created_at (timestamptz)

### 2.7 learning_reviews
Output analisis mingguan dari AI.

Kolom utama:
- id (uuid, pk)
- week_key (text)
- reviewed_trade_ids (uuid[])
- findings (jsonb)
- suggested_parameter_changes (jsonb)
- confidence_score (numeric)
- status (text)
- created_at (timestamptz)

### 2.8 parameter_change_requests
Workflow perubahan parameter.

Kolom utama:
- id (uuid, pk)
- source_review_id (uuid, fk -> learning_reviews.id)
- change_set (jsonb)
- impact_estimate (jsonb)
- approval_status (text)
- approved_by (text)
- applied_version (text)
- created_at (timestamptz)

## 3. Redis Keys (Draft)
- oracle:candidate:{symbol}:{tf} -> candidate state (ttl pendek)
- oracle:lock:execution:{symbol} -> distributed lock
- oracle:risk:daily_loss -> running daily loss
- oracle:sentiment:latest:{symbol} -> sentiment snapshot
- oracle:news:shield:{symbol} -> shield flag

## 4. Indexing Guidance
- trade_candidates(symbol, timeframe, created_at desc)
- orders(status, created_at desc)
- positions(status, symbol)
- trade_journal(created_at desc, pnl_usd)
- learning_reviews(week_key)

## 5. Audit and Traceability
Setiap record kritikal harus punya:
- correlation_id
- strategy_version
- provider_metadata (untuk sentimen/berita)
- exchange_latency_ms
