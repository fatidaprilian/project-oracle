# Project Oracle

Project Oracle adalah kerangka trading intelligence yang memadukan:
- filter teknikal berlapis (Filter Funnel)
- analisis sentimen dan berita real-time
- sniper entry untuk survival leverage tinggi
- exit strategy berbasis aturan objektif
- learning loop mingguan dari trade gagal

Status saat ini: phase 0-8 implementasi inti sudah aktif, API production berjalan di Cloud Run, dan frontend berjalan di Vercel.

## Dokumentasi Utama
- Arsitektur sistem: docs/architecture.md
- Draft data model: docs/data-model.md
- Trading flow per modul: docs/trading-flow-modules.md
- Roadmap eksekusi: docs/roadmap.md
- Roadmap frontend: docs/frontend-roadmap.md
- Deployment guide (single source): docs/deployment.md
- API contract dan endpoint detail: docs/api.md
- Persistence recovery runbook: docs/persistence-recovery.md

## Layout Repositori

- `src/` - core domain, application, infrastructure, dan entrypoint backend
- `services/` - boundary service untuk API dan worker scheduler
- `web/` - frontend app yang akan dipindah/deploy ke Vercel
- `apps/` - penanda boundary aplikasi tingkat atas
- `scripts/` - tooling deployment dan bootstrap
- `docs/` - blueprint, roadmap, dan runbook

## Ruang Lingkup Fase Saat Ini
- operasi production paper mode (Cloud Run + Vercel)
- governance workflow berbasis API (summary, requests, approve, promote)
- connectivity checks untuk exchange adapter dan AI analyst adapter
- hardening observability frontend dan role-based access

## Struktur Kode Fase 1
- src/main.py
- src/oracle/domain/models.py
- src/oracle/modules/structure_engine.py
- src/oracle/modules/zone_engine.py
- src/oracle/modules/confluence_engine.py
- src/oracle/modules/sentiment_gate.py
- src/oracle/modules/sniper_entry.py
- src/oracle/modules/exit_engine.py
- src/oracle/application/paper_pipeline.py
- src/oracle/infrastructure/journal.py

## Menjalankan Demo Paper Cycle

```bash
set PYTHONPATH=src
python src/main.py
```

Runtime akan otomatis memilih adapter berdasarkan environment:
- ORACLE_SENTIMENT_BASE_URL + ORACLE_SENTIMENT_API_KEY -> external sentiment provider
- ORACLE_POSTGRES_DSN + ORACLE_ENABLE_POSTGRES=true -> persist journal ke PostgreSQL
- ORACLE_REDIS_URL + ORACLE_ENABLE_REDIS=true -> simpan state risk ke Redis

## Menjalankan Replay Multi Simbol

```bash
set PYTHONPATH=src
python src/replay.py
```

Dataset contoh replay:
- data/replay/sample_snapshots.jsonl

## Menjalankan Unit Test

```bash
set PYTHONPATH=src
python -m unittest discover -s tests -p "test_*.py"
```

## Generate AI Strategy Review Packet

```bash
set PYTHONPATH=src
python src/strategy_review.py
```

Output:
- reports/ai-review/<ISO-week>-ai-review.json
- registry/parameter_change_requests.jsonl

## Strategy Governance CLI

```bash
set PYTHONPATH=src
python src/strategy_governance.py summary
python src/strategy_governance.py list
python src/strategy_governance.py set-status --request-id <REQUEST_ID> --status approved
python src/strategy_governance.py promote
```

Output promosi config kandidat:
- reports/strategy-configs/<version>.json

## Generate Weekly Report

```bash
set PYTHONPATH=src
python src/weekly_report.py
```

Output report:
- reports/weekly/<ISO-week>.md

Weekly report dibangun dari event replay dan bisa dijalankan sebagai artefak mingguan.

## Adapter Sentiment Eksternal
File adapter:
- src/oracle/infrastructure/external_sentiment_provider.py

Adapter persistence:
- src/oracle/infrastructure/postgres_journal_repository.py
- src/oracle/infrastructure/redis_risk_repository.py

Risk guard dan circuit breaker:
- src/oracle/application/risk_controls.py

Environment variable:
- ORACLE_SENTIMENT_BASE_URL
- ORACLE_SENTIMENT_API_KEY
- ORACLE_SENTIMENT_TIMEOUT

Opsional environment untuk persistence:
- ORACLE_POSTGRES_DSN
- ORACLE_REDIS_URL
- ORACLE_ENABLE_POSTGRES
- ORACLE_ENABLE_REDIS
- ORACLE_PERSISTENCE_MAX_RETRIES
- ORACLE_PERSISTENCE_RETRY_DELAY_SECONDS
- ORACLE_REDIS_RISK_TTL_SECONDS
- ORACLE_PERSISTENCE_FALLBACK_FILE

## Provider dan Environment yang Dipakai
- AI provider: vendor-agnostic (default di env example = gemini, bisa diganti grok/custom)
- exchange environment: testnet dulu (belum live trading)
- runtime mode default: paper

Catatan eksekusi saat ini:
- backend API long-running aktif via FastAPI service
- scheduler worker untuk weekly workflow tersedia via service boundary
- frontend governance dashboard aktif dan terhubung ke API

File referensi konfigurasi:
- .env.example

## Quick Start Repository (WSL)

1. Buka terminal WSL di folder proyek.
2. Inisialisasi git jika belum:

```bash
git init
git branch -M main
```

3. Tambahkan remote:

```bash
git remote add origin https://github.com/fatidaprilian/project-oracle.git
```

4. Cek status:

```bash
git status
```

Catatan: push ke remote bisa dilakukan setelah token tersedia.

## Rencana Tahap Berikutnya
- fase aktif saat ini: hardening operasional post-Phase 8
- optional: enable Redis runtime store untuk risk-state cache
- optional: integrasi sentiment provider saat API key/provider siap
- lanjut ekspansi symbol universe bertahap via governance flow

## Keputusan Frontend Saat Ini
- stack UI: React + Vite
- deployment frontend: Vercel
- backend service: Cloud Run / worker service terpisah
- frontend memakai boundary `web/` sekarang, dengan target deploy terpisah ke Vercel

## Checklist Implementasi Mingguan
- [ ] Monday: review parameter aktif dan risk limit
- [ ] Tuesday: validasi kualitas data market feed
- [ ] Wednesday: review kandidat trade yang dibatalkan shield
- [ ] Thursday: audit reason code entry/exit
- [ ] Friday: kirim 10 trade terburuk ke AI analyst
- [ ] Saturday: evaluasi usulan perubahan parameter
- [ ] Sunday: freeze parameter dan publish weekly summary

## Governance Singkat
- semua keputusan entry/exit wajib punya reason code
- semua perubahan parameter harus terdokumentasi dan dapat di-audit
- provider AI/sentimen harus melalui adapter agar mudah ganti vendor
