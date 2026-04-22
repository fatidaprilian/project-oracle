# Project Oracle - Roadmap (Stock Pivot)

## Status Perubahan Arah (Pivot)
Sistem sebelumnya (Crypto Auto-Trade) dengan 8 fase telah diarsip. Pengembangan sekarang fokus pada pivot menuju *Telegram-Driven Stock Signal Engine* menggunakan arsitektur semi-otomatis (Beli/Abaikan).

Infrastruktur tidak berubah:
- Backend di GCP Cloud Run (Python / FastAPI)
- Frontend di Vercel (React / Vite)
- Database: PostgreSQL

## Fase 1 - Pondasi Webhook & Telegram (Drafting)
Tujuan:
- Menerima sinyal mentah dan merespons via Telegram.

Deliverables:
- Membersihkan tabel database lama (crypto/orders) dan mengaplikasikan schema baru (`signal_history`, `active_tracking`, `ignore_list`).
- Implementasi endpoint FastAPI `/api/v1/webhook/tradingview`.
- Setup bot Telegram dan integrasi `python-telegram-bot` atau request HTTP raw ke API Telegram.

Definition of Done:
- Saat webhook ditembak via Postman, bot Telegram mengirim pesan *dummy* ke user.

## Fase 2 - Oracle Synthesizer (Gemini) & News Gate
Tujuan:
- Menyuntikkan otak (Gemini API) ke dalam alur pesan Telegram.

Deliverables:
- Integrasi Free News API (misal: NewsAPI, Yahoo Finance RSS) ke dalam sistem untuk mengambil berita berdasarkan *ticker*.
- Integrasi Gemini API (`google-genai` atau endpoint Gemini standard).
- Penyusunan prompt AI untuk mengambil keputusan fundamental + teknikal.

Definition of Done:
- Pesan di Telegram bukan lagi *dummy*, melainkan hasil justifikasi/alasan aktual dari Gemini berdasarkan simulasi *ticker* dan beritanya.

## Fase 3 - Interactive State & Dashboard
Tujuan:
- Membuat sistem menjadi interaktif (User bisa merespons sinyal) dan mensinkronisasikan ke Frontend Vercel.

Deliverables:
- Menambahkan *Inline Keyboard Buttons* (Beli / Abaikan) di pesan Telegram.
- Implementasi endpoint penangkap *Callback Query* dari Telegram.
- Penyimpanan status ke tabel `active_tracking` atau `ignore_list`.
- Frontend dashboard menampilkan list saham yang sedang di `active_tracking`.

Definition of Done:
- Tombol di Telegram merespons klik dan meng-update database serta memperbarui teks pesan Telegram secara real-time.
- Vercel Frontend bisa melakukan GET *active tracking* dan menampilkannya.

## Fase 4 - Active Tracking Daemon & Alerts
Tujuan:
- Menjaga posisi "Beli" agar tetap aman dari berita buruk mendadak.

Deliverables:
- Implementasi `APScheduler` (cron job) di backend untuk memeriksa saham-saham di `active_tracking`.
- Pengecekan difokuskan pada perubahan drastis berita / sentimen market.
- Jika terdeteksi anomali, tembak push notification ke Telegram (Urgent Alert).

Definition of Done:
- Sistem dapat otomatis mem-push notifikasi darurat tanpa ada trigger webhook baru, berdasarkan evaluasi berkala dari cron job.
