import {
  formatCompactPercent,
  formatRadarLaneLabel,
  formatRadarReason,
  formatVolumeRatio,
} from '../formatters';
import type { PortfolioPosition, RadarAnomaly, RadarControls } from '../types';
import { SectionShell } from './SectionShell';

interface RadarPanelProps {
  anomalies: RadarAnomaly[];
  watchlist: string[];
  portfolio: PortfolioPosition[];
  controls: RadarControls;
  activeActionKey: string | null;
}

function resolveLaneToneClass(lane: RadarAnomaly['lane']): string {
  if (lane === 'MOMENTUM_WATCH') {
    return 'oracle-chip-positive';
  }

  if (lane === 'EXTENDED_RISK') {
    return 'oracle-chip-danger';
  }

  if (lane === 'IPO_WATCH') {
    return 'oracle-chip-warning';
  }

  return 'oracle-chip-copper';
}

export function RadarPanel({
  anomalies,
  watchlist,
  portfolio,
  controls,
  activeActionKey,
}: RadarPanelProps) {
  const activeTickers = new Set(portfolio.map((position) => position.ticker));
  const visibleAnomalies = anomalies.filter((anomaly) => !activeTickers.has(anomaly.ticker));
  const visibleWatchlist = watchlist.filter((ticker) => !activeTickers.has(ticker));

  return (
    <SectionShell
      header={{
        kicker: 'Radar oracle',
        title: 'Radar sesi berikutnya',
        description:
          'Daftar ini hanya menunjukkan anomali volume untuk sesi berikutnya. Ini bukan janji target akan tercapai besok.',
        tone: 'copper',
      }}
    >
      <div className="space-y-6">
        <div className="rounded-lg border border-white/8 bg-black/20 p-4">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="oracle-kicker">Anomali volume hari ini</p>
              <h3 className="mt-2 font-display text-xl text-white">
                Hasil Oracle Volume Screener
              </h3>
            </div>
            <span className="oracle-chip oracle-chip-copper">Bukan target 1 hari</span>
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            {visibleAnomalies.length > 0 ? (
              visibleAnomalies.map((anomaly) => (
                <article key={anomaly.ticker} className="oracle-radar-card">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <h4 className="font-display text-xl text-white">
                        {anomaly.ticker.replace('.JK', '')}
                      </h4>
                      <p className="mt-2 text-xs leading-5 text-white/58">
                        {formatRadarReason(anomaly.reason)}
                      </p>
                    </div>
                    <span className={`oracle-chip ${resolveLaneToneClass(anomaly.lane)}`}>
                      {formatRadarLaneLabel(anomaly.lane)}
                    </span>
                  </div>

                  <div className="mt-4 grid grid-cols-3 gap-2 text-xs">
                    <div className="oracle-radar-metric">
                      <span>Volume</span>
                      <strong>{formatVolumeRatio(anomaly.volumeRatio)}</strong>
                    </div>
                    <div className="oracle-radar-metric">
                      <span>Change</span>
                      <strong>{formatCompactPercent(anomaly.changePct)}</strong>
                    </div>
                    <div className="oracle-radar-metric">
                      <span>Score</span>
                      <strong>{anomaly.discoveryScore ?? '—'}</strong>
                    </div>
                  </div>
                </article>
              ))
            ) : (
              <p className="text-sm leading-6 text-white/58">
                Belum ada anomali tersisa di luar posisi aktif.
              </p>
            )}
          </div>
        </div>

        <div className="rounded-lg border border-white/8 bg-black/20 p-4">
          <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="oracle-kicker">Watchlist manual</p>
              <h3 className="mt-2 font-display text-xl text-white">Radar pilihan operator</h3>
            </div>

            <form
              className="flex w-full flex-col gap-2 sm:flex-row md:max-w-sm"
              onSubmit={(event) => {
                event.preventDefault();
                void controls.onSubmitWatchlist();
              }}
            >
              <input
                type="text"
                className="oracle-input"
                placeholder="Tambah ticker, contoh BBRI.JK"
                value={controls.watchlistDraft}
                onChange={(event) => controls.onWatchlistDraftChange(event.target.value)}
              />
              <button
                type="submit"
                className="oracle-button oracle-button-primary"
                disabled={activeActionKey === `watchlist:${controls.watchlistDraft.trim().toUpperCase()}`}
              >
                Tambah
              </button>
            </form>
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            {visibleWatchlist.length > 0 ? (
              visibleWatchlist.map((ticker) => (
                <div key={ticker} className="oracle-watchlist-item">
                  <span>{ticker}</span>
                  <button
                    type="button"
                    className="text-white/55 transition hover:text-[var(--color-danger-strong)]"
                    onClick={() => void controls.onRemoveWatchlistTicker(ticker)}
                    disabled={activeActionKey === `watchlist-remove:${ticker}`}
                    aria-label={`Hapus ${ticker} dari watchlist`}
                  >
                    ×
                  </button>
                </div>
              ))
            ) : (
              <p className="text-sm leading-6 text-white/58">
                Watchlist manual kosong atau seluruh ticker-nya sudah masuk portofolio aktif.
              </p>
            )}
          </div>
        </div>

        <div className="rounded-lg border border-white/8 bg-black/20 p-4 text-sm leading-7 text-white/66">
          <p className="oracle-kicker">Catatan operasional</p>
          <p className="mt-2">
            Prediksi durasi target akan ditampilkan dalam hari bursa pada sinyal resmi.
            Monitoring posisi tetap berjalan berkala untuk mendeteksi breach harga atau
            berita berat yang benar-benar merusak tesis.
          </p>
        </div>
      </div>
    </SectionShell>
  );
}
