# Project Oracle Frontend Roadmap

## 1. Keputusan Stack
Pilihan final untuk fase awal:
- Framework UI: React
- Build tool: Vite
- Styling: Tailwind CSS + design tokens
- State server data: TanStack Query
- Charting: Lightweight Charts atau ECharts

Alasan memilih React untuk kondisi saat ini:
- ekosistem dashboard trading dan real-time component lebih luas
- integrasi library charting dan table advanced lebih matang
- tim umumnya lebih mudah cari resource dan contoh implementasi
- cocok untuk admin/ops dashboard yang butuh iterasi cepat

Catatan:
- Vue tetap opsi valid, tetapi untuk percepatan delivery fase awal React memberi risiko integrasi lebih rendah.

## 2. Keputusan Deployment
Pilihan final untuk fase awal:
- Single platform dulu: Railway
- Tidak perlu split Railway + Vercel di tahap sekarang

Alasan single Railway cukup saat ini:
- produk masih fokus internal dashboard dan operasional strategy
- trafik awal belum butuh edge optimization khusus frontend
- operasional lebih sederhana (1 platform, 1 observability path)
- biaya dan kompleksitas deployment lebih rendah

## 3. Trigger Kapan Perlu Split Railway + Vercel
Pindah ke arsitektur split jika minimal 2 kondisi terpenuhi:
1. Frontend public-facing butuh SEO kuat dan edge delivery global.
2. Build/deploy frontend lebih cepat jika dipisah dari siklus backend.
3. Traffic frontend tumbuh signifikan dan perlu CDN/edge cache agresif.
4. Tim frontend dan backend sudah berjalan paralel dengan release cadence berbeda.

## 4. Arsitektur Frontend (Phase Starter)
- app shell dashboard
- auth/session guard
- watchlist dan market overview
- trade candidate board (reason code aware)
- position monitor + exit signal panel
- weekly report viewer

Data flow:
- REST polling untuk fase awal
- tambah stream channel (SSE dulu, lalu WebSocket jika perlu bidirectional)

## 5. Roadmap Frontend per Fase

### F-0: UX Blueprint and Design System
Deliverables:
- information architecture
- wireframe dashboard utama
- design token (color, spacing, typography)

Definition of done:
- disetujui untuk implementasi sprint

### F-1: Frontend Scaffold
Deliverables:
- React + Vite project bootstrap
- layout utama (sidebar, topbar, workspace)
- auth guard placeholder

Definition of done:
- halaman dashboard dapat jalan lokal

### F-2: Core Monitoring Views
Deliverables:
- candidate table + status badge
- position panel + risk panel
- reason code timeline

Definition of done:
- data mock dapat divisualkan end-to-end

### F-3: Report and Analytics Views
Deliverables:
- weekly report viewer
- MAE/MFE dan quality score charts
- filter simbol/timeframe

Definition of done:
- user ops bisa review performa mingguan dari UI

### F-4: Real-Time and Alerting
Deliverables:
- stream channel untuk update posisi dan event (SSE/WebSocket)
- alert drawer untuk shield/risk lock

Definition of done:
- dashboard update near real-time stabil

### F-5: Production Hardening
Deliverables:
- error boundary, loading skeleton, retry UX
- role-based view restriction
- observability frontend (error tracking + web vitals)

Definition of done:
- siap dipakai operasional harian

## 6. Urutan Eksekusi yang Disarankan
1. F-0 dan F-1 selesai terlebih dahulu.
2. Integrasikan F-2 dengan API paper pipeline.
3. Lanjut F-3 agar weekly review berpindah dari teks ke UI.
4. Aktifkan F-4 jika backend event stream sudah siap.
5. Tutup dengan F-5 sebelum scale user internal.
