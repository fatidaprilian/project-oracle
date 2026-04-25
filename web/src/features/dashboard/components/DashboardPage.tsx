import { HistoryPanel } from './HistoryPanel';
import { OverviewStrip } from './OverviewStrip';
import { PortfolioPanel } from './PortfolioPanel';
import { RadarPanel } from './RadarPanel';
import { SignalBoard } from './SignalBoard';
import type { DashboardPageProps } from '../types';

function DashboardLoadingState() {
  return (
    <div className="grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
      <div className="space-y-4">
        <div className="oracle-loading-block h-72" />
        <div className="oracle-loading-block h-64" />
      </div>
      <div className="oracle-loading-block h-[32rem]" />
    </div>
  );
}

export function DashboardPage({ data, uiState, controls }: DashboardPageProps) {
  const pendingSignals = data.signals.filter((signal) => signal.status === 'PENDING');

  return (
    <main className="oracle-shell">
      <div className="oracle-grid">
        <header className="oracle-command-band">
          <div className="space-y-4">
            <p className="oracle-kicker">Risk console oracle</p>
            <div className="space-y-3">
              <h1 className="font-display text-4xl text-white md:text-6xl">
                Oracle Proteksi Modal
              </h1>
              <p className="max-w-3xl text-sm leading-7 text-white/66 md:text-base">
                Dashboard ini sekarang mengutamakan seleksi defensif. Radar tetap
                memantau anomali, tetapi ruang aksi hanya menerima setup yang lolos
                entry plan kuantitatif dan konfirmasi berita.
              </p>
            </div>
          </div>

          <div className="flex flex-col items-stretch gap-3 md:flex-row md:flex-wrap md:justify-end">
            <button
              type="button"
              className="oracle-button oracle-button-primary"
              onClick={() => void controls.onRunManualScan()}
              disabled={uiState.activeActionKey === 'scan-now'}
            >
              {uiState.activeActionKey === 'scan-now' ? 'Menjalankan scan...' : 'Jalankan scan manual'}
            </button>
            <button
              type="button"
              className="oracle-button oracle-button-secondary"
              onClick={() => void controls.onRefreshDashboard()}
              disabled={uiState.isRefreshing}
            >
              {uiState.isRefreshing ? 'Memuat ulang...' : 'Muat ulang data'}
            </button>
          </div>
        </header>

        {uiState.statusMessage ? (
          <div className="oracle-status-banner oracle-status-banner-positive">
            {uiState.statusMessage}
          </div>
        ) : null}

        {uiState.errorText ? (
          <div className="oracle-status-banner oracle-status-banner-danger">
            {uiState.errorText}
          </div>
        ) : null}

        <OverviewStrip
          stats={data.stats}
          pendingSignalCount={pendingSignals.length}
          activePositionCount={data.portfolio.length}
          anomalyCount={data.anomalies.length}
        />

        {uiState.isLoading ? (
          <DashboardLoadingState />
        ) : (
          <>
            <section className="grid gap-6 xl:grid-cols-[0.92fr_1.08fr]">
              <RadarPanel
                anomalies={data.anomalies}
                watchlist={data.watchlist}
                portfolio={data.portfolio}
                controls={{
                  watchlistDraft: uiState.watchlistDraft,
                  onWatchlistDraftChange: controls.onWatchlistDraftChange,
                  onSubmitWatchlist: controls.onSubmitWatchlist,
                  onRemoveWatchlistTicker: controls.onRemoveWatchlistTicker,
                }}
                activeActionKey={uiState.activeActionKey}
              />

              <SignalBoard
                signals={pendingSignals}
                activeActionKey={uiState.activeActionKey}
                onSignalAction={controls.onSignalAction}
              />
            </section>

            <section className="grid gap-6">
              <PortfolioPanel
                portfolio={data.portfolio}
                activeActionKey={uiState.activeActionKey}
                onSignalAction={controls.onSignalAction}
              />
              <HistoryPanel history={data.history} />
            </section>
          </>
        )}
      </div>
    </main>
  );
}
