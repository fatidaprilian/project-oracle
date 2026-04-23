import type { ReactNode } from 'react';

interface SectionHeader {
  kicker: string;
  title: string;
  description?: string;
  tone?: 'default' | 'copper' | 'ice' | 'emerald';
  actions?: ReactNode;
}

interface SectionShellProps {
  header: SectionHeader;
  children: ReactNode;
}

function resolveToneClass(tone: SectionHeader['tone']): string {
  if (tone === 'copper') {
    return 'section-tone-copper';
  }

  if (tone === 'ice') {
    return 'section-tone-ice';
  }

  if (tone === 'emerald') {
    return 'section-tone-emerald';
  }

  return 'section-tone-default';
}

export function SectionShell({ header, children }: SectionShellProps) {
  return (
    <section className={`oracle-panel ${resolveToneClass(header.tone)}`}>
      <div className="mb-5 flex flex-col gap-4 border-b border-white/8 pb-4 md:flex-row md:items-end md:justify-between">
        <div className="space-y-2">
          <p className="oracle-kicker">{header.kicker}</p>
          <div className="space-y-1">
            <h2 className="font-display text-2xl text-white">{header.title}</h2>
            {header.description ? (
              <p className="max-w-2xl text-sm leading-6 text-white/64">
                {header.description}
              </p>
            ) : null}
          </div>
        </div>
        {header.actions ? <div className="flex flex-wrap gap-3">{header.actions}</div> : null}
      </div>
      {children}
    </section>
  );
}
