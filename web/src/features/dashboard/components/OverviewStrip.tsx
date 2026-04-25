import type { TradingStats } from '../types';

interface OverviewStripProps {
  stats: TradingStats;
  pendingSignalCount: number;
  activePositionCount: number;
  anomalyCount: number;
}

function resolvePnlTone(value: number): string {
  if (value > 0) {
    return 'text-[var(--color-positive-strong)]';
  }

  if (value < 0) {
    return 'text-[var(--color-danger-strong)]';
  }

  return 'text-white';
}

export function OverviewStrip({
  stats,
  pendingSignalCount,
  activePositionCount,
  anomalyCount,
}: OverviewStripProps) {
  const isDefensiveMode = stats.total >= 3 && (stats.avgPnl < 0 || stats.winRate < 40);
  const riskModeLabel = isDefensiveMode ? 'Mode defensif aktif' : 'Mode seleksi normal';
  const riskModeDescription = isDefensiveMode
    ? 'Generator sekarang menunggu entry plan kuantitatif valid sebelum meminta konfirmasi AI.'
    : 'Sinyal tetap melewati gate kuantitatif sebelum masuk ruang aksi.';

  return (
    <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
      <article className="oracle-risk-console md:col-span-2 xl:col-span-5">
        <div>
          <p className="oracle-kicker">Kontrol risiko 2026</p>
          <h2 className="mt-2 text-2xl font-black text-white">{riskModeLabel}</h2>
        </div>
        <p className="max-w-3xl text-sm leading-6 text-white/68">
          {riskModeDescription} Radar boleh ramai, tapi sinyal aksi hanya naik ketika
          pullback, confluence, dan price plan sudah sejalan.
        </p>
      </article>

      <article className="oracle-stat-card">
        <p className="oracle-kicker">Fokus saat ini</p>
        <h2 className="mt-3 text-4xl font-black text-white">{pendingSignalCount}</h2>
        <p className="mt-2 text-sm text-white/62">Sinyal menunggu aksi manual</p>
      </article>

      <article className="oracle-stat-card">
        <p className="oracle-kicker">Radar sesi berikutnya</p>
        <h2 className="mt-3 text-4xl font-black text-white">{anomalyCount}</h2>
        <p className="mt-2 text-sm text-white/62">Anomali volume hasil screener</p>
      </article>

      <article className="oracle-stat-card">
        <p className="oracle-kicker">Portofolio aktif</p>
        <h2 className="mt-3 text-4xl font-black text-white">{activePositionCount}</h2>
        <p className="mt-2 text-sm text-white/62">Posisi yang sedang dipantau</p>
      </article>

      <article className="oracle-stat-card">
        <p className="oracle-kicker">Rasio menang</p>
        <h2 className="mt-3 text-4xl font-black text-white">{stats.winRate}%</h2>
        <p className="mt-2 text-sm text-white/62">
          {stats.wins} menang / {stats.losses} kalah
        </p>
      </article>

      <article className="oracle-stat-card">
        <p className="oracle-kicker">Rata-rata PnL</p>
        <h2 className={`mt-3 text-4xl font-black ${resolvePnlTone(stats.avgPnl)}`}>
          {stats.avgPnl > 0 ? '+' : ''}
          {stats.avgPnl}%
        </h2>
        <p className="mt-2 text-sm text-white/62">{stats.total} transaksi tercatat</p>
      </article>
    </section>
  );
}
