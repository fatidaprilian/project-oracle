from __future__ import annotations

from datetime import datetime


def format_daily_broadcast_message(
    anomalies: list[str],
    now_wib: datetime,
) -> str:
    days_id = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    months_id = [
        "Januari",
        "Februari",
        "Maret",
        "April",
        "Mei",
        "Juni",
        "Juli",
        "Agustus",
        "September",
        "Oktober",
        "November",
        "Desember",
    ]

    day_str = days_id[now_wib.weekday()]
    month_str = months_id[now_wib.month - 1]
    date_str = f"{day_str}, {now_wib.day} {month_str} {now_wib.year}"
    ticker_list = "\n".join([f"• {ticker.replace('.JK', '')}" for ticker in anomalies])

    return (
        "🔍 *RADAR ORACLE SESI BERIKUTNYA*\n"
        f"_{date_str}_\n\n"
        "Hasil Oracle Volume Screener sore ini menemukan anomali volume pada saham "
        "berikut untuk sesi berikutnya:\n\n"
        f"{ticker_list}\n\n"
        "_Daftar ini adalah radar pantauan awal, bukan target pergerakan satu hari. "
        "Sinyal resmi akan dikirim otomatis jika momentum entry memenuhi syarat._"
    )
