import {
  formatBiasLabel,
  formatCalendarDate,
  formatDurationWindow,
  formatPrice,
  formatResolvedActionLabel,
  formatSourceLabel,
} from '../formatters';
import { SectionShell } from './SectionShell';
import type { HistoryEntry } from '../types';

interface HistoryPanelProps {
  history: HistoryEntry[];
}

function resolveHistoryToneClass(action: string | null): string {
  if (action === 'BUY') {
    return 'oracle-chip-positive';
  }

  if (action === 'IGNORE') {
    return 'oracle-chip-danger';
  }

  if (action === 'EXPIRED') {
    return 'oracle-chip-warning';
  }

  return 'oracle-chip-neutral';
}

export function HistoryPanel({ history }: HistoryPanelProps) {
  return (
    <SectionShell
      header={{
        kicker: 'Jejak keputusan',
        title: 'Riwayat sinyal',
        description:
          'Riwayat ini menjaga konteks outcome, source, dan alasan Oracle agar evaluasi tidak terputus dari keputusan awal.',
      }}
    >
      {history.length > 0 ? (
        <>
          <div className="hidden overflow-x-auto lg:block">
            <table className="oracle-table">
              <thead>
                <tr>
                  <th>Saham</th>
                  <th>Sumber</th>
                  <th>Bias</th>
                  <th>Alasan</th>
                  <th>Area beli</th>
                  <th>Target</th>
                  <th>Durasi</th>
                  <th>Outcome</th>
                  <th>Resolusi</th>
                </tr>
              </thead>
              <tbody>
                {history.map((item) => (
                  <tr key={item.id}>
                    <td className="font-semibold text-white">{item.ticker}</td>
                    <td>{formatSourceLabel(item.technicalSignal)}</td>
                    <td>{formatBiasLabel(item.bias)}</td>
                    <td className="max-w-sm truncate">{item.aiReasoning}</td>
                    <td>{formatPrice(item.entryPrice)}</td>
                    <td>{formatPrice(item.targetPrice)}</td>
                    <td>
                      {formatDurationWindow(
                        item.estimatedDurationMinDays,
                        item.estimatedDurationMaxDays,
                      )}
                    </td>
                    <td>
                      <span className={`oracle-chip ${resolveHistoryToneClass(item.resolvedAction)}`}>
                        {formatResolvedActionLabel(item.resolvedAction)}
                      </span>
                    </td>
                    <td>{formatCalendarDate(item.resolvedAt || item.createdAt)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="grid gap-4 lg:hidden">
            {history.map((item) => (
              <article key={item.id} className="oracle-mobile-card">
                <div className="flex flex-wrap items-center gap-3">
                  <h3 className="font-display text-2xl text-white">{item.ticker}</h3>
                  <span className="oracle-chip oracle-chip-neutral">
                    {formatSourceLabel(item.technicalSignal)}
                  </span>
                  <span className={`oracle-chip ${resolveHistoryToneClass(item.resolvedAction)}`}>
                    {formatResolvedActionLabel(item.resolvedAction)}
                  </span>
                </div>

                <p className="mt-4 text-sm leading-7 text-white/72">{item.aiReasoning}</p>

                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  <div className="oracle-mini-metric">
                    <span>Bias</span>
                    <strong>{formatBiasLabel(item.bias)}</strong>
                  </div>
                  <div className="oracle-mini-metric">
                    <span>Resolusi</span>
                    <strong>{formatCalendarDate(item.resolvedAt || item.createdAt)}</strong>
                  </div>
                  <div className="oracle-mini-metric">
                    <span>Area beli</span>
                    <strong>{formatPrice(item.entryPrice)}</strong>
                  </div>
                  <div className="oracle-mini-metric">
                    <span>Target</span>
                    <strong>{formatPrice(item.targetPrice)}</strong>
                  </div>
                  <div className="oracle-mini-metric sm:col-span-2">
                    <span>Perkiraan durasi</span>
                    <strong>
                      {formatDurationWindow(
                        item.estimatedDurationMinDays,
                        item.estimatedDurationMaxDays,
                      )}
                    </strong>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </>
      ) : (
        <div className="oracle-empty-state">
          Riwayat sinyal belum tersedia. Setelah ada sinyal yang selesai, jejaknya akan muncul di sini.
        </div>
      )}
    </SectionShell>
  );
}
