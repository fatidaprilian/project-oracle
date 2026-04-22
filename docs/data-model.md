# Project Oracle - Data Model (Stock Pivot)

## 1. Tujuan
Dokumen ini mendefinisikan struktur data minimum untuk mendukung arsitektur Telegram-Driven Stock Signal:
- pencatatan riwayat sinyal dari indikator
- penyimpanan status *tracking* posisi (Beli/Abaikan)
- audit log alasan (reasoning) AI

## 2. Entitas PostgreSQL

### 2.1 signal_history
Menyimpan riwayat sinyal teknikal dan hasil analisis fundamental dari AI.

Kolom utama:
- id (uuid, pk)
- ticker (text)
- technical_signal (text) - contoh: "MA_CROSSOVER", "BREAKOUT"
- news_context (text) - ringkasan berita yang diambil
- ai_reasoning (text) - justifikasi dari Gemini
- bias (text) - "BUY", "IGNORE"
- created_at (timestamptz)

### 2.2 active_tracking
Menyimpan daftar saham yang di-klik "Beli" oleh user di Telegram.

Kolom utama:
- id (uuid, pk)
- signal_id (uuid, fk -> signal_history.id)
- ticker (text)
- target_price (numeric) - opsional
- is_active (boolean) - true jika masih dipantau
- tracked_since (timestamptz)
- last_checked_at (timestamptz)

### 2.3 ignore_list
Menyimpan daftar saham yang di-klik "Abaikan" agar tidak meng-spam notifikasi Telegram untuk beberapa waktu.

Kolom utama:
- id (uuid, pk)
- ticker (text)
- reason (text) - opsional, misal "too volatile"
- expires_at (timestamptz) - kapan saham ini boleh di-alert lagi
- created_at (timestamptz)

### 2.4 tracking_alerts
Menyimpan riwayat *push notification* anomali/peringatan yang dikirim ke user (misal: ada berita buruk saat *active tracking*).

Kolom utama:
- id (uuid, pk)
- tracking_id (uuid, fk -> active_tracking.id)
- alert_type (text) - "BAD_NEWS", "PRICE_DROP"
- message (text)
- sent_at (timestamptz)

## 3. Redis Keys (Opsional untuk Caching)
- `oracle:news_cache:{ticker}` -> menyimpan sentimen berita terkini (TTL 1-4 jam) agar tidak spam News API
- `oracle:webhook_lock:{ticker}` -> mencegah *duplicate* pemrosesan webhook dalam waktu bersamaan

## 4. Indexing Guidance
- signal_history(created_at desc, ticker)
- active_tracking(is_active, last_checked_at)
- ignore_list(expires_at, ticker)
