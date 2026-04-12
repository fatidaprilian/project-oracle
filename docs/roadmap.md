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

## Fase 5 - Strategy Intelligence (Done)
Tujuan:
- pembelajaran mingguan semi-otomatis

Deliverables:
- top 10 worst trade selector
- paket input AI analyst
- parameter change request registry
- weekly workflow orchestrator dengan scheduler APScheduler
- REST API untuk governance (summary, list, approve, promote)

Definition of done:
- workflow review mingguan dapat dijalankan end-to-end
- usulan perubahan parameter tercatat dan bisa di-approve

Progress saat ini:
- top 10 worst trade selector: implemented
- paket input AI analyst: implemented (file output)
- parameter change request registry: implemented (jsonl append)
- request validation rules and status governance: implemented
- weekly report governance summary: implemented
- governance CLI (summary/list/approve/reject/promote): implemented
- candidate strategy config promotion from approved valid requests: implemented
- weekly workflow orchestrator (weekly_workflow.py): implemented
- APScheduler daemon (scheduler.py): implemented
- REST API endpoints (FastAPI, api/main.py): implemented
- API tests: implemented (test_api_endpoints.py)

## Fase 6 - API Service and Operations (Done)
Tujuan:
- service API production-ready dan operasi rutin terautomasi

Deliverables:
- API server FastAPI (governance, workflow, health checks)
- scheduler daemon untuk weekly workflow terjadwal
- runbook incident dan kill switch ops
- parameter runtime integration (load promoted configs)
- deployment docs (Railway, environment setup)

Definition of done:
- API server berjalan stabil dengan auth basic (opsional untuk v1)
- weekly workflow dapat dijadwalkan dan dimonitor
- kesiapan operasi mingguan tanpa intervensi manual berat

Progress saat ini:
- API endpoints (FastAPI): implemented
- parameter runtime loading: implemented
- operations runbook: implemented
- deployment guide (Railway + VPS): implemented
- integration tests: implemented (3 tests passing)
- total tests: 38 passing

## Phase 7 - Frontend and Multi-Symbol (In Progress)
Tujuan:
- user interface untuk monitoring dan governance
- support multi-symbol portfolio trading

Deliverables:
- React + Vite frontend dengan layout dan routing
- governance dashboard (request approval, promotion)
- strategy performance KPI display
- multi-symbol support dalam core pipeline
- real-time live updates (SSE/WebSocket)

Definition of done:
- frontend accessible di Railway atau Vercel
- governance approval dapat dilakukan via UI
- multi-symbol replay berjalan tanpa error

Progress saat ini:
- React + Vite frontend dengan routing: implemented
- governance dashboard (request approval, promotion): implemented
- strategy performance KPI display (governance summary + infra connectivity): implemented
- stream update near real-time via SSE endpoint: implemented
- frontend hardening (error boundary, skeleton loading, retry UX): implemented
- role-based view restriction (viewer/operator/admin): implemented
- login flow without register (username/password from DB auth_users -> role token): implemented
- observability frontend baseline (web vitals + error tracking hooks): implemented
- multi-symbol replay guard test: implemented

## Phase 8 - Market Connectivity and Provider Abstraction (Planned)
Tujuan:
- menyiapkan konektivitas market/exchange secara aman tanpa lock-in vendor
- menyiapkan integrasi AI analyst provider yang bisa diganti tanpa ubah core domain

Deliverables:
- exchange adapter interface (vendor-agnostic) dengan mode testnet sebagai default
- implementasi adapter awal untuk Bybit testnet (read/ping + market sanity check)
- health endpoint untuk status koneksi exchange adapter
- AI analyst adapter interface (vendor-agnostic) dengan fallback jika API key belum aktif
- konfigurasi environment standar untuk provider selection (grok/gemini/custom)

Definition of done:
- runtime tetap aman dalam mode paper saat kredensial exchange/provider tidak tersedia
- minimal satu adapter exchange berjalan di testnet tanpa memengaruhi governance flow
- pergantian provider tidak membutuhkan perubahan di modul domain utama
- runbook konfigurasi provider/exchange tersedia

## Status Keseluruhan

Sudah Selesai:
- Phase 0-6: Foundation, Paper Trading, Runtime, Quality Analytics, Persistence, Strategy Intelligence, API Service
- Total: 38 unit tests passing
- Commits: 5b30b2c (latest)

Ready untuk Phase 7 atau parallel frontend development (React + Vite scaffold).

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
