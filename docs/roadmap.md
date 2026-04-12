# Project Oracle Roadmap

## Prinsip Eksekusi
- Urutan fase wajib linear: fase berikutnya dimulai jika fase saat ini sudah memenuhi definition of done.
- Setiap fase harus menghasilkan artefak yang bisa diuji (docs, test pass, atau runtime output).
- Semua perubahan strategy harus terekam reason code dan audit trail.

## Fase 0 - Foundation (Done)
Tujuan:
- pondasi arsitektur dan tata kelola

Deliverables:
- architecture blueprint
- data model draft
- trading flow per modul

Definition of done:
- docs utama tersedia dan sinkron
- repository bootstrap siap dipush

## Fase 1 - Paper Trading Core (Done)
Tujuan:
- pipeline teknikal end-to-end di mode paper

Deliverables:
- structure, zone, confluence, sentiment gate, sniper entry, exit engine
- replay runner multi simbol
- unit test dasar

Definition of done:
- pipeline replay berjalan
- test suite hijau

## Fase 2 - Runtime Wiring (Done)
Tujuan:
- runtime fleksibel dengan adapter opsional

Deliverables:
- runtime bootstrap berdasarkan environment
- optional persistence adapters (PostgreSQL/Redis)
- weekly report generator

Definition of done:
- fallback in-memory tetap jalan
- report mingguan dapat digenerate

## Fase 3 - Quality Analytics (Done)
Tujuan:
- ukur kualitas entry dan outcome secara objektif

Deliverables:
- metrik MAE/MFE per trade
- quality score per closed trade
- weekly report menampilkan ringkasan quality

Definition of done:
- event quality tercatat di journal
- report mingguan menampilkan rata-rata quality score

## Fase 4 - Persistence Hardening (Done)
Tujuan:
- persistence production-ready

Deliverables:
- migrasi schema PostgreSQL formal
- penyimpanan state risk harian di Redis dengan TTL/policy
- fallback dan retry policy pada sink persisten

Definition of done:
- operasi tetap aman saat dependency eksternal gagal
- data audit tidak hilang saat replay berulang

## Fase 5 - Strategy Intelligence (In Progress)
Tujuan:
- pembelajaran mingguan semi-otomatis

Deliverables:
- top 10 worst trade selector
- paket input AI analyst
- parameter change request registry

Definition of done:
- workflow review mingguan dapat dijalankan end-to-end
- usulan perubahan parameter tercatat dan bisa di-approve

Progress saat ini:
- top 10 worst trade selector: implemented
- paket input AI analyst: implemented (file output)
- parameter change request registry: implemented (jsonl append)
- request validation rules and status governance: implemented
- weekly report governance summary: implemented

## Fase 6 - Operations and Release
Tujuan:
- kesiapan operasi rutin

Deliverables:
- scheduler mingguan report + review
- runbook incident dan kill switch ops
- dashboard KPI strategi

Definition of done:
- operasi mingguan berjalan tanpa intervensi manual berat
- KPI utama terpantau stabil

## Urutan Kerja Praktis Mingguan
1. Selesaikan fase aktif dan checklist test-nya.
2. Commit dan push artefak fase.
3. Jalankan replay dan generate weekly report.
4. Review hasil, lalu buka fase berikutnya.

## Roadmap Frontend
Dokumen detail frontend ada di docs/frontend-roadmap.md.

Keputusan saat ini:
- UI stack: React + Vite
- deployment: single Railway dulu

Trigger split Railway + Vercel:
- butuh SEO/edge delivery publik
- cadence release frontend/backend sudah berbeda
- traffic frontend menuntut optimasi CDN/edge khusus
