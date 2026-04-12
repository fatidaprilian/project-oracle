# Project Oracle - Trading Flow per Modul

## 1. Tujuan Dokumen
Dokumen ini merinci tanggung jawab, input/output, dan kontrak antar modul untuk fase 1 paper trading pipeline.

## 2. Modul dan Kontrak

### 2.1 Market Ingestor
Tugas:
- menerima snapshot market per simbol dan timeframe
- menormalkan data OHLCV
- menambahkan metadata waktu pemrosesan

Input:
- raw candle stream

Output:
- MarketSnapshot

### 2.2 Structure Engine
Tugas:
- klasifikasi regime: uptrend, downtrend, chop
- validasi struktur HH/HL atau LH/LL

Input:
- MarketSnapshot

Output:
- StructureSignal
  - market_regime
  - structure_strength
  - is_tradeable

### 2.3 Zone Engine
Tugas:
- deteksi order block aktif
- deteksi supply/demand zone yang masih fresh

Input:
- MarketSnapshot
- StructureSignal

Output:
- ZoneSignal
  - zone_low
  - zone_high
  - zone_type
  - freshness_score

### 2.4 Confluence Engine
Tugas:
- hitung fib retracement pada swing valid
- hitung overlap dengan zone dan S/R
- hasilkan confluence score

Input:
- MarketSnapshot
- ZoneSignal

Output:
- ConfluenceSignal
  - confluence_score
  - fib_618_price
  - cluster_price
  - is_valid

### 2.5 Sentiment and News Gate
Tugas:
- ambil bias sentimen eksternal
- cek event berisiko tinggi
- aktif/nonaktifkan news shield

Input:
- symbol
- optional social/news feed

Output:
- SentimentSignal
  - sentiment_bias
  - event_risk_level
  - shield_status

### 2.6 Sniper Entry Engine
Tugas:
- validasi setup limit entry
- validasi liquidity sweep dan rejection
- hitung stop loss dan size plan

Input:
- ConfluenceSignal
- SentimentSignal
- MarketSnapshot

Output:
- EntryPlan
  - should_place_order
  - entry_price
  - stop_loss
  - take_profit_primary
  - take_profit_secondary
  - reason_codes

### 2.7 Paper Execution Gateway
Tugas:
- simulasi lifecycle order limit
- transisi candidate -> pending -> filled/expired
- simpan event keputusan

Input:
- EntryPlan
- current price stream

Output:
- PaperOrder
- PositionState

### 2.8 Exit Engine
Tugas:
- aktifkan breakeven di R >= 1.0
- close di fib extension
- forced exit saat structural shift

Input:
- PositionState
- MarketSnapshot

Output:
- ExitDecision
  - should_close
  - exit_reason
  - updated_stop_loss

### 2.9 Journal and Learning Feed
Tugas:
- simpan trade event dan final journal
- tandai trade gagal untuk review mingguan

Input:
- PositionState
- ExitDecision

Output:
- TradeJournalEntry
- LearningCandidate

## 3. Orkestrasi Fase 1 (Paper)
1. Ambil snapshot market.
2. Jalankan Structure -> Zone -> Confluence.
3. Jalankan Sentiment Gate.
4. Jika shield aktif, batalkan setup.
5. Jika valid, buat EntryPlan limit.
6. Simulasikan eksekusi paper order.
7. Kelola exit: breakeven, fib TP, structural shift.
8. Simpan journal + reason codes.

## 4. Reason Code Minimum
- REGIME_NOT_TRADEABLE
- ZONE_NOT_FRESH
- LOW_CONFLUENCE
- NEWS_SHIELD_ACTIVE
- SWEEP_NOT_CONFIRMED
- LIMIT_NOT_FILLED
- BREAK_EVEN_ARMED
- FIB_EXTENSION_TP_HIT
- STRUCTURAL_SHIFT_EXIT

## 5. Definition of Ready Fase Implementasi
- semua modul punya interface input/output yang typed
- semua keputusan mengembalikan reason codes
- pipeline bisa dijalankan untuk satu simbol secara replay
