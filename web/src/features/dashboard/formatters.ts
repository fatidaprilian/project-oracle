export function formatRelativeTime(timestamp: string | null | undefined): string {
  if (!timestamp) {
    return '—';
  }

  const diffMilliseconds = Date.now() - new Date(timestamp).getTime();
  const diffMinutes = Math.max(Math.floor(diffMilliseconds / 60000), 0);

  if (diffMinutes < 1) {
    return 'baru saja';
  }

  if (diffMinutes < 60) {
    return `${diffMinutes} mnt lalu`;
  }

  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24) {
    return `${diffHours} jam lalu`;
  }

  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays} hari lalu`;
}

export function formatExpiryCountdown(timestamp: string | null | undefined): string {
  if (!timestamp) {
    return 'Tanpa batas waktu';
  }

  const diffMilliseconds = new Date(timestamp).getTime() - Date.now();
  if (diffMilliseconds <= 0) {
    return 'Kedaluwarsa';
  }

  const diffHours = Math.floor(diffMilliseconds / 3600000);
  const diffMinutes = Math.floor((diffMilliseconds % 3600000) / 60000);

  if (diffHours <= 0) {
    return `${diffMinutes} menit lagi`;
  }

  return `${diffHours} jam ${diffMinutes} menit lagi`;
}

export function formatPrice(value: number | null | undefined): string {
  if (value == null) {
    return '—';
  }

  return value.toLocaleString('id-ID', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

export function formatSignedPercent(value: number | null | undefined): string {
  if (value == null) {
    return '—';
  }

  const prefix = value > 0 ? '+' : '';
  return `${prefix}${value.toFixed(2)}%`;
}

export function formatDurationWindow(
  minDays: number | null | undefined,
  maxDays: number | null | undefined,
): string {
  if (minDays == null || maxDays == null) {
    return 'Belum ada estimasi';
  }

  if (minDays === maxDays) {
    return `${minDays} hari bursa`;
  }

  return `${minDays}-${maxDays} hari bursa`;
}

export function formatCalendarDate(timestamp: string | null | undefined): string {
  if (!timestamp) {
    return '—';
  }

  return new Intl.DateTimeFormat('id-ID', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  }).format(new Date(timestamp));
}

export function formatClockDate(timestamp: string | null | undefined): string {
  if (!timestamp) {
    return '—';
  }

  return new Intl.DateTimeFormat('id-ID', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(timestamp));
}

export function formatBiasLabel(bias: string): string {
  if (bias === 'BUY') {
    return 'BELI';
  }

  if (bias === 'SELL') {
    return 'JUAL';
  }

  return 'ABAIKAN';
}

export function formatResolvedActionLabel(resolvedAction: string | null | undefined): string {
  if (resolvedAction === 'BUY') {
    return 'DILACAK';
  }

  if (resolvedAction === 'IGNORE') {
    return 'DIMUTE';
  }

  if (resolvedAction === 'EXPIRED') {
    return 'KEDALUWARSA';
  }

  return '—';
}

export function formatSourceLabel(technicalSignal: string | null | undefined): string {
  if (!technicalSignal) {
    return 'Oracle';
  }

  if (technicalSignal.includes('SOURCE_SCANNER')) {
    return 'Scanner';
  }

  if (technicalSignal.includes('SOURCE_WATCHLIST')) {
    return 'Watchlist Manual';
  }

  return 'Oracle';
}

function formatTechnicalToken(rawToken: string): string {
  if (rawToken === 'UPTREND') {
    return 'Tren Naik';
  }

  if (rawToken === 'DOWNTREND') {
    return 'Tren Turun';
  }

  if (rawToken === 'CHOP') {
    return 'Sideways';
  }

  if (rawToken === 'GOLDEN_PULLBACK') {
    return 'Golden Pullback';
  }

  if (rawToken === 'SILENT_PULLBACK') {
    return 'Silent Pullback';
  }

  return rawToken.replace(/_/g, ' ');
}

export function formatTechnicalTags(technicalSignal: string | null | undefined): string[] {
  if (!technicalSignal) {
    return [];
  }

  return technicalSignal
    .split('+')
    .filter((token) => token && token !== 'AI_PRO_SCAN' && !token.startsWith('SOURCE_'))
    .map(formatTechnicalToken);
}

export function formatDataTimestampLabel(dataTimestamp: string | null | undefined): string {
  if (!dataTimestamp) {
    return 'Timestamp data belum tersedia';
  }

  return dataTimestamp
    .replace('End of Day (EOD)', 'Akhir sesi')
    .replace('Closing', 'Penutupan');
}
