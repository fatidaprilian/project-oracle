import { SectionShell } from './SectionShell';
import { SignalCard } from './SignalCard';
import type { DashboardAction, SignalItem } from '../types';

interface SignalBoardProps {
  signals: SignalItem[];
  activeActionKey: string | null;
  onSignalAction: (ticker: string, action: DashboardAction) => Promise<void>;
}

export function SignalBoard({
  signals,
  activeActionKey,
  onSignalAction,
}: SignalBoardProps) {
  return (
    <SectionShell
      header={{
        kicker: 'Ruang aksi',
        title: 'Sinyal menunggu keputusan',
        description:
          'Hanya sinyal aktif yang butuh keputusan manual ditampilkan di sini. Reason tampil pada sinyal resmi, bukan pada radar screener harian.',
        tone: 'ice',
      }}
    >
      {signals.length > 0 ? (
        <div className="space-y-5">
          {signals.map((signal) => (
            <SignalCard
              key={signal.id}
              signal={signal}
              activeActionKey={activeActionKey}
              onSignalAction={onSignalAction}
            />
          ))}
        </div>
      ) : (
        <div className="oracle-empty-state">
          Belum ada sinyal menunggu aksi. Oracle masih menilai radar hari ini.
        </div>
      )}
    </SectionShell>
  );
}
