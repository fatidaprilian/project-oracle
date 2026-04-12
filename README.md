# Project Oracle

Project Oracle adalah kerangka trading intelligence yang memadukan:
- filter teknikal berlapis (Filter Funnel)
- analisis sentimen dan berita real-time
- sniper entry untuk survival leverage tinggi
- exit strategy berbasis aturan objektif
- learning loop mingguan dari trade gagal

Status saat ini: documentation-first. Belum ada modul runtime yang diaktifkan.

## Dokumentasi Utama
- Arsitektur sistem: docs/architecture.md
- Draft data model: docs/data-model.md

## Ruang Lingkup Fase Saat Ini
- definisi arsitektur
- definisi komponen dan state machine
- definisi data model dan governance dasar

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
- scaffold service modular monolith (market, strategy, execution, learning)
- implement paper trading pipeline
- tambah dashboard observability + audit trail

## Governance Singkat
- semua keputusan entry/exit wajib punya reason code
- semua perubahan parameter harus terdokumentasi dan dapat di-audit
- provider AI/sentimen harus melalui adapter agar mudah ganti vendor
