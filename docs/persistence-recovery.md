# Persistence Recovery Runbook

## Tujuan
Dokumen ini menjelaskan recovery saat PostgreSQL/Redis sempat gagal, lalu koneksi pulih.

## Mekanisme yang Sudah Aktif
- Postgres journal sink menggunakan retry.
- Jika masih gagal, event disimpan ke fallback file JSONL.
- Saat save berikutnya, fallback file dibaca ulang dan dicoba dipersist lagi.
- Event memakai idempotency key (`event_key`), jadi replay tidak menyebabkan duplikasi.

## Lokasi Fallback File
Default:
- runtime-fallback/journal-events.jsonl

Konfigurasi via environment:
- ORACLE_PERSISTENCE_FALLBACK_FILE

## Prosedur Recovery Operasional
1. Pastikan PostgreSQL kembali sehat.
2. Jalankan runtime seperti biasa (`src/main.py` atau `src/replay.py`).
3. Sistem akan mencoba flush fallback events otomatis pada save berikutnya.
4. Verifikasi fallback file berkurang/hilang setelah sinkronisasi sukses.

## Verifikasi SQL
Gunakan query berikut untuk cek duplikasi:

```sql
SELECT event_key, COUNT(*)
FROM trade_events
GROUP BY event_key
HAVING COUNT(*) > 1;
```

Hasil normal: 0 rows.

## Failure Mode yang Ditangani
- psycopg belum terpasang
- koneksi PostgreSQL timeout/intermiten
- Redis down sementara

## Batasan Saat Ini
- fallback replay terjadi saat ada save baru (belum ada daemon khusus).
- monitor manual masih dibutuhkan untuk file fallback yang terlalu besar.