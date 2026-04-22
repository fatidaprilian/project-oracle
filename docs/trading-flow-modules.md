# Project Oracle - Signal Flow per Modul (Stock Pivot)

## 1. Tujuan Dokumen
Dokumen ini merinci tanggung jawab, input/output, dan kontrak antar modul untuk arsitektur *Telegram-Driven Stock Signal*.

## 2. Modul dan Kontrak

### 2.1 Webhook Listener
Tugas:
- Menerima HTTP POST (webhook) dari TradingView atau sumber sinyal eksternal.
- Memvalidasi *payload* dan mendeteksi duplikasi sinyal (via Redis lock).

Input:
- HTTP Request (JSON payload)
  - ticker
  - signal_type (contoh: "MA_CROSS", "MACD_BULLISH")
  - price

Output:
- `RawSignal` object diteruskan ke internal message bus/queue.

### 2.2 News Fetcher Gate
Tugas:
- Menerima `RawSignal` dan melakukan *query* berita terkini untuk *ticker* terkait.
- Menggunakan Free API (contoh: NewsAPI, Yahoo Finance).
- Caching berita (1-4 jam) agar tidak memboroskan kuota API.

Input:
- `RawSignal`

Output:
- `ContextualSignal`
  - ticker
  - signal_type
  - price
  - recent_news (list of strings/headlines)

### 2.3 Oracle Synthesizer (Gemini API)
Tugas:
- Membuat koneksi ke Gemini 3.1 Pro via API.
- Menyuntikkan prompt: "Ada sinyal teknikal X di harga Y untuk saham Z. Berita terbarunya adalah A, B, C. Apakah ini valid untuk dibeli atau harus diabaikan? Berikan alasan maksimal 2 kalimat."

Input:
- `ContextualSignal`

Output:
- `OracleDecision`
  - bias ("BUY" atau "IGNORE")
  - reasoning_text

### 2.4 Telegram Controller
Tugas:
- Mengambil `OracleDecision` dan memformatnya menjadi pesan Markdown Telegram.
- Memasang *Inline Keyboard Buttons*: `[✅ Beli]` dan `[❌ Abaikan]`.
- Mengirim pesan ke chat ID *user*.

Input:
- `OracleDecision`

Output:
- Telegram Message ID (disimpan di database jika butuh update state nanti).

### 2.5 State Management & Callback Handler
Tugas:
- Menangani *callback query* dari Telegram saat *user* menekan tombol.
- Jika "Beli": Masukkan ke tabel `active_tracking`. Edit pesan Telegram menjadi `[🟢 Tracking Active]`.
- Jika "Abaikan": Masukkan ke tabel `ignore_list`. Edit pesan Telegram menjadi `[🔴 Muted]`.

Input:
- Telegram Callback Query (action, ticker, message_id)

Output:
- Database update (`active_tracking` atau `ignore_list`).
- HTTP Response 200 ke Telegram API.

### 2.6 Active Tracker Daemon (Cron Job)
Tugas:
- Berjalan setiap interval tertentu (misal: tiap 4 jam saat market buka).
- Mengambil semua saham dari tabel `active_tracking`.
- Mencari berita *breaking bad news* atau lonjakan harga anomali.
- Jika ada kondisi berbahaya, menembak alert ke Telegram Controller.

Input:
- Tabel `active_tracking`
- News API / Price API

Output:
- Push Alert Telegram (Urgent)
- Catat di tabel `tracking_alerts`.

## 3. Orkestrasi Penuh (End-to-End)
1. TradingView mengirim webhook "AAPL Breakout".
2. Webhook Listener menerima dan memvalidasi `RawSignal`.
3. News Fetcher Gate mengambil headline AAPL 24 jam terakhir.
4. Oracle Synthesizer (Gemini) menggabungkan data: teknikal "Breakout" + berita "Laba naik 20%". Kesimpulan: **BUY**. Reason: "Breakout valid didukung fundamental laporan Q3 positif."
5. Telegram Controller mem-push pesan ke HP User dengan tombol `[Beli]` dan `[Abaikan]`.
6. User menekan `[Beli]`.
7. State Management menyimpan AAPL ke `active_tracking` dan mengedit tombol di chat menjadi `[Tracking Active]`.
8. Active Tracker Daemon memonitor AAPL secara berkala hingga user memutuskan untuk take profit manual di broker mereka.
