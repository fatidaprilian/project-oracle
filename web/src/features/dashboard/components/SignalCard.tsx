import {
  formatBiasLabel,
  formatClockDate,
  formatDataTimestampLabel,
  formatDurationWindow,
  formatExpiryCountdown,
  formatPrice,
  formatSourceLabel,
  formatTechnicalTags,
} from '../formatters';
import type { DashboardAction, SignalItem } from '../types';

interface SignalCardProps {
  signal: SignalItem;
  activeActionKey: string | null;
  onSignalAction: (ticker: string, action: DashboardAction) => Promise<void>;
}

function resolveBiasToneClass(bias: SignalItem['bias']): string {
  if (bias === 'BUY') {
    return 'oracle-chip-positive';
  }

  if (bias === 'SELL') {
    return 'oracle-chip-warning';
  }

  return 'oracle-chip-danger';
}

export function SignalCard({
  signal,
  activeActionKey,
  onSignalAction,
}: SignalCardProps) {
  const chartSymbol = signal.ticker.endsWith('.JK')
    ? `IDX:${signal.ticker.replace('.JK', '')}`
    : signal.ticker;
  const technicalTags = formatTechnicalTags(signal.technicalSignal);
  const isBuyBusy = activeActionKey === `buy:${signal.ticker}`;
  const isIgnoreBusy = activeActionKey === `ignore:${signal.ticker}`;

  return (
    <article className="oracle-signal-card">
      <div className="flex flex-col gap-4 border-b border-white/8 pb-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-3">
            <h3 className="font-display text-3xl text-white">{signal.ticker}</h3>
            <span className={`oracle-chip ${resolveBiasToneClass(signal.bias)}`}>
              {formatBiasLabel(signal.bias)}
            </span>
            <span className="oracle-chip oracle-chip-neutral">
              {formatSourceLabel(signal.technicalSignal)}
            </span>
          </div>

          <div className="flex flex-wrap gap-2">
            {technicalTags.map((tag) => (
              <span key={tag} className="oracle-chip oracle-chip-neutral">
                {tag}
              </span>
            ))}
          </div>
        </div>

        <div className="space-y-1 text-sm text-white/58 lg:text-right">
          <p>Dibuat {formatClockDate(signal.createdAt)}</p>
          <p>{formatExpiryCountdown(signal.expiresAt)}</p>
          <p>{formatDataTimestampLabel(signal.dataTimestamp)}</p>
        </div>
      </div>

      <div className="grid gap-6 pt-5 xl:grid-cols-[1.15fr_0.85fr]">
        <div className="space-y-5">
          <div className="h-72 overflow-hidden rounded-[24px] border border-white/8 bg-black/30">
            <iframe
              src={`https://s.tradingview.com/widgetembed/?symbol=${chartSymbol}&interval=D&hidesidetoolbar=1&symboledit=1&saveimage=1&toolbarbg=101822&studies=%5B%5D&theme=dark&style=1`}
              title={`Chart ${signal.ticker}`}
              width="100%"
              height="100%"
              frameBorder="0"
              allowFullScreen
              className="h-full w-full"
            />
          </div>

          <div className="rounded-[24px] border border-white/8 bg-black/20 p-4">
            <p className="oracle-kicker">Analisis Oracle</p>
            <p className="mt-3 text-sm leading-7 text-white/78">{signal.aiReasoning}</p>
          </div>
        </div>

        <div className="space-y-5">
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
            <div className="oracle-metric-card">
              <p className="oracle-kicker">Area beli</p>
              <p className="mt-2 font-mono text-2xl text-[var(--color-positive-strong)]">
                {formatPrice(signal.entryPrice)}
              </p>
            </div>
            <div className="oracle-metric-card">
              <p className="oracle-kicker">Target</p>
              <p className="mt-2 font-mono text-2xl text-[var(--color-ice-strong)]">
                {formatPrice(signal.targetPrice)}
              </p>
            </div>
            <div className="oracle-metric-card">
              <p className="oracle-kicker">Stop loss</p>
              <p className="mt-2 font-mono text-2xl text-[var(--color-danger-strong)]">
                {formatPrice(signal.stopLoss)}
              </p>
            </div>
            <div className="oracle-metric-card">
              <p className="oracle-kicker">Perkiraan durasi</p>
              <p className="mt-2 text-lg font-semibold text-white">
                {formatDurationWindow(
                  signal.estimatedDurationMinDays,
                  signal.estimatedDurationMaxDays,
                )}
              </p>
              <p className="mt-2 text-xs leading-5 text-white/52">
                Estimasi menuju target dalam hari bursa, bukan jam pasti.
              </p>
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <button
              type="button"
              className="oracle-button oracle-button-primary"
              onClick={() => void onSignalAction(signal.ticker, 'buy')}
              disabled={isBuyBusy}
            >
              {isBuyBusy ? 'Memproses...' : 'Beli dan lacak'}
            </button>
            <button
              type="button"
              className="oracle-button oracle-button-secondary"
              onClick={() => void onSignalAction(signal.ticker, 'ignore')}
              disabled={isIgnoreBusy}
            >
              {isIgnoreBusy ? 'Memproses...' : 'Abaikan'}
            </button>
          </div>
        </div>
      </div>
    </article>
  );
}
