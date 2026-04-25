export type SignalBias = 'BUY' | 'SELL' | 'IGNORE';
export type SignalStatus = 'PENDING' | 'TRACKING' | 'IGNORED' | 'EXPIRED';
export type DashboardAction = 'buy' | 'ignore' | 'sell';
export type RadarLane = 'MOMENTUM_WATCH' | 'EXTENDED_RISK' | 'RADAR_ONLY' | 'IPO_WATCH';

export interface RadarAnomaly {
  ticker: string;
  lane: RadarLane;
  discoveryScore: number | null;
  volumeRatio: number | null;
  changePct: number | null;
  closePrice: number | null;
  reason: string | null;
  source: string | null;
  scannedAt: string | null;
}

export interface SignalItem {
  id: string;
  ticker: string;
  technicalSignal: string;
  newsContext: string;
  aiReasoning: string;
  bias: SignalBias;
  entryPrice: number | null;
  targetPrice: number | null;
  stopLoss: number | null;
  estimatedDurationMinDays: number | null;
  estimatedDurationMaxDays: number | null;
  createdAt: string;
  status: SignalStatus;
  resolvedAt: string | null;
  expiresAt: string | null;
  dataTimestamp: string | null;
}

export interface PortfolioPosition {
  id: string;
  ticker: string;
  trackedSince: string;
  lastCheckedAt: string | null;
  entryPrice: number | null;
  targetPrice: number | null;
  stopLoss: number | null;
  estimatedDurationMinDays: number | null;
  estimatedDurationMaxDays: number | null;
  currentPrice: number | null;
  pnlPercent: number | null;
}

export interface HistoryEntry {
  id: string;
  ticker: string;
  bias: SignalBias;
  aiReasoning: string;
  entryPrice: number | null;
  targetPrice: number | null;
  stopLoss: number | null;
  estimatedDurationMinDays: number | null;
  estimatedDurationMaxDays: number | null;
  createdAt: string | null;
  resolvedAt: string | null;
  resolvedAction: string | null;
  technicalSignal: string | null;
}

export interface TradingStats {
  total: number;
  wins: number;
  losses: number;
  winRate: number;
  avgPnl: number;
}

export interface DashboardSnapshot {
  signals: SignalItem[];
  portfolio: PortfolioPosition[];
  history: HistoryEntry[];
  watchlist: string[];
  anomalies: RadarAnomaly[];
  stats: TradingStats;
}

export interface DashboardUiState {
  isLoading: boolean;
  isRefreshing: boolean;
  errorText: string | null;
  statusMessage: string | null;
  activeActionKey: string | null;
  watchlistDraft: string;
}

export interface DashboardControls {
  onRefreshDashboard: () => Promise<void>;
  onRunManualScan: () => Promise<void>;
  onWatchlistDraftChange: (nextValue: string) => void;
  onSubmitWatchlist: () => Promise<void>;
  onRemoveWatchlistTicker: (ticker: string) => Promise<void>;
  onSignalAction: (ticker: string, action: DashboardAction) => Promise<void>;
}

export interface DashboardPageProps {
  data: DashboardSnapshot;
  uiState: DashboardUiState;
  controls: DashboardControls;
}

export interface RadarControls {
  watchlistDraft: string;
  onWatchlistDraftChange: (nextValue: string) => void;
  onSubmitWatchlist: () => Promise<void>;
  onRemoveWatchlistTicker: (ticker: string) => Promise<void>;
}
