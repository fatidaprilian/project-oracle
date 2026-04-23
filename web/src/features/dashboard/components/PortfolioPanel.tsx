import {
  formatDurationWindow,
  formatPrice,
  formatRelativeTime,
  formatSignedPercent,
} from '../formatters';
import { SectionShell } from './SectionShell';
import type { DashboardAction, PortfolioPosition } from '../types';

interface PortfolioPanelProps {
  portfolio: PortfolioPosition[];
  activeActionKey: string | null;
  onSignalAction: (ticker: string, action: DashboardAction) => Promise<void>;
}

function resolvePnlToneClass(value: number | null): string {
  if (value == null) {
    return 'text-white';
  }

  if (value > 0) {
    return 'text-[var(--color-positive-strong)]';
  }

  if (value < 0) {
    return 'text-[var(--color-danger-strong)]';
  }

  return 'text-white';
}

export function PortfolioPanel({
  portfolio,
  activeActionKey,
  onSignalAction,
}: PortfolioPanelProps) {
  return (
    <SectionShell
      header={{
        kicker: 'Posisi hidup',
        title: 'Portofolio aktif',
        description:
          'Panel ini memadukan harga terkini, risk plan, durasi target, dan jejak monitoring terbaru.',
        tone: 'emerald',
      }}
    >
      {portfolio.length > 0 ? (
        <>
          <div className="hidden overflow-x-auto lg:block">
            <table className="oracle-table">
              <thead>
                <tr>
                  <th>Saham</th>
                  <th>Area beli</th>
                  <th>Harga kini</th>
                  <th>Target</th>
                  <th>Stop loss</th>
                  <th>Durasi</th>
                  <th>PnL</th>
                  <th>Dipantau sejak</th>
                  <th>Review terakhir</th>
                  <th>Aksi</th>
                </tr>
              </thead>
              <tbody>
                {portfolio.map((position) => (
                  <tr key={position.id}>
                    <td className="font-semibold text-white">{position.ticker}</td>
                    <td>{formatPrice(position.entryPrice)}</td>
                    <td className="text-white">{formatPrice(position.currentPrice)}</td>
                    <td>{formatPrice(position.targetPrice)}</td>
                    <td>{formatPrice(position.stopLoss)}</td>
                    <td>
                      {formatDurationWindow(
                        position.estimatedDurationMinDays,
                        position.estimatedDurationMaxDays,
                      )}
                    </td>
                    <td className={resolvePnlToneClass(position.pnlPercent)}>
                      {formatSignedPercent(position.pnlPercent)}
                    </td>
                    <td>{formatRelativeTime(position.trackedSince)}</td>
                    <td>{formatRelativeTime(position.lastCheckedAt)}</td>
                    <td>
                      <button
                        type="button"
                        className="oracle-button oracle-button-danger"
                        onClick={() => void onSignalAction(position.ticker, 'sell')}
                        disabled={activeActionKey === `sell:${position.ticker}`}
                      >
                        Tutup posisi
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="grid gap-4 lg:hidden">
            {portfolio.map((position) => (
              <article key={position.id} className="oracle-mobile-card">
                <div className="flex items-center justify-between gap-3">
                  <h3 className="font-display text-2xl text-white">{position.ticker}</h3>
                  <span className={`text-lg font-bold ${resolvePnlToneClass(position.pnlPercent)}`}>
                    {formatSignedPercent(position.pnlPercent)}
                  </span>
                </div>

                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  <div className="oracle-mini-metric">
                    <span>Area beli</span>
                    <strong>{formatPrice(position.entryPrice)}</strong>
                  </div>
                  <div className="oracle-mini-metric">
                    <span>Harga kini</span>
                    <strong>{formatPrice(position.currentPrice)}</strong>
                  </div>
                  <div className="oracle-mini-metric">
                    <span>Target</span>
                    <strong>{formatPrice(position.targetPrice)}</strong>
                  </div>
                  <div className="oracle-mini-metric">
                    <span>Stop loss</span>
                    <strong>{formatPrice(position.stopLoss)}</strong>
                  </div>
                  <div className="oracle-mini-metric sm:col-span-2">
                    <span>Perkiraan durasi</span>
                    <strong>
                      {formatDurationWindow(
                        position.estimatedDurationMinDays,
                        position.estimatedDurationMaxDays,
                      )}
                    </strong>
                  </div>
                </div>

                <div className="mt-4 flex flex-wrap gap-4 text-sm text-white/58">
                  <span>Dipantau {formatRelativeTime(position.trackedSince)}</span>
                  <span>Review {formatRelativeTime(position.lastCheckedAt)}</span>
                </div>

                <button
                  type="button"
                  className="oracle-button oracle-button-danger mt-5 w-full"
                  onClick={() => void onSignalAction(position.ticker, 'sell')}
                  disabled={activeActionKey === `sell:${position.ticker}`}
                >
                  Tutup posisi
                </button>
              </article>
            ))}
          </div>
        </>
      ) : (
        <div className="oracle-empty-state">
          Belum ada posisi aktif. Saat sinyal dibeli, posisinya akan muncul di sini.
        </div>
      )}
    </SectionShell>
  );
}
