import axios from 'axios';

import type {
  DashboardAction,
  DashboardSnapshot,
  HistoryEntry,
  PortfolioPosition,
  RadarAnomaly,
  SignalItem,
  TradingStats,
} from './types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const dashboardClient = axios.create({
  baseURL: API_BASE,
});

interface RawSignalItem {
  id: string;
  ticker: string;
  technical_signal: string;
  news_context: string;
  ai_reasoning: string;
  bias: SignalItem['bias'];
  entry_price?: number | null;
  target_price?: number | null;
  stop_loss?: number | null;
  estimated_duration_min_days?: number | null;
  estimated_duration_max_days?: number | null;
  created_at: string;
  status: SignalItem['status'];
  resolved_at?: string | null;
  expires_at?: string | null;
  data_timestamp?: string | null;
}

interface RawPortfolioPosition {
  id: string;
  ticker: string;
  tracked_since: string;
  last_checked_at?: string | null;
  entry_price?: number | null;
  target_price?: number | null;
  stop_loss?: number | null;
  estimated_duration_min_days?: number | null;
  estimated_duration_max_days?: number | null;
  current_price?: number | null;
  pnl_percent?: number | null;
}

interface RawHistoryEntry {
  id: string;
  ticker: string;
  bias: HistoryEntry['bias'];
  ai_reasoning: string;
  entry_price?: number | null;
  target_price?: number | null;
  stop_loss?: number | null;
  estimated_duration_min_days?: number | null;
  estimated_duration_max_days?: number | null;
  created_at?: string | null;
  resolved_at?: string | null;
  resolved_action?: string | null;
  technical_signal?: string | null;
}

interface RawStats {
  total?: number;
  wins?: number;
  losses?: number;
  win_rate?: number;
  avg_pnl?: number;
}

interface RawRadarAnomaly {
  ticker: string;
  lane?: RadarAnomaly['lane'] | null;
  discovery_score?: number | null;
  volume_ratio?: number | null;
  change_pct?: number | null;
  close_price?: number | null;
  reason?: string | null;
  source?: string | null;
  scanned_at?: string | null;
}

function mapSignalItem(rawSignal: RawSignalItem): SignalItem {
  return {
    id: rawSignal.id,
    ticker: rawSignal.ticker,
    technicalSignal: rawSignal.technical_signal,
    newsContext: rawSignal.news_context,
    aiReasoning: rawSignal.ai_reasoning,
    bias: rawSignal.bias,
    entryPrice: rawSignal.entry_price ?? null,
    targetPrice: rawSignal.target_price ?? null,
    stopLoss: rawSignal.stop_loss ?? null,
    estimatedDurationMinDays: rawSignal.estimated_duration_min_days ?? null,
    estimatedDurationMaxDays: rawSignal.estimated_duration_max_days ?? null,
    createdAt: rawSignal.created_at,
    status: rawSignal.status,
    resolvedAt: rawSignal.resolved_at ?? null,
    expiresAt: rawSignal.expires_at ?? null,
    dataTimestamp: rawSignal.data_timestamp ?? null,
  };
}

function mapPortfolioPosition(rawPosition: RawPortfolioPosition): PortfolioPosition {
  return {
    id: rawPosition.id,
    ticker: rawPosition.ticker,
    trackedSince: rawPosition.tracked_since,
    lastCheckedAt: rawPosition.last_checked_at ?? null,
    entryPrice: rawPosition.entry_price ?? null,
    targetPrice: rawPosition.target_price ?? null,
    stopLoss: rawPosition.stop_loss ?? null,
    estimatedDurationMinDays: rawPosition.estimated_duration_min_days ?? null,
    estimatedDurationMaxDays: rawPosition.estimated_duration_max_days ?? null,
    currentPrice: rawPosition.current_price ?? null,
    pnlPercent: rawPosition.pnl_percent ?? null,
  };
}

function mapHistoryEntry(rawHistoryEntry: RawHistoryEntry): HistoryEntry {
  return {
    id: rawHistoryEntry.id,
    ticker: rawHistoryEntry.ticker,
    bias: rawHistoryEntry.bias,
    aiReasoning: rawHistoryEntry.ai_reasoning,
    entryPrice: rawHistoryEntry.entry_price ?? null,
    targetPrice: rawHistoryEntry.target_price ?? null,
    stopLoss: rawHistoryEntry.stop_loss ?? null,
    estimatedDurationMinDays: rawHistoryEntry.estimated_duration_min_days ?? null,
    estimatedDurationMaxDays: rawHistoryEntry.estimated_duration_max_days ?? null,
    createdAt: rawHistoryEntry.created_at ?? null,
    resolvedAt: rawHistoryEntry.resolved_at ?? null,
    resolvedAction: rawHistoryEntry.resolved_action ?? null,
    technicalSignal: rawHistoryEntry.technical_signal ?? null,
  };
}

function mapTradingStats(rawStats: RawStats): TradingStats {
  return {
    total: rawStats.total ?? 0,
    wins: rawStats.wins ?? 0,
    losses: rawStats.losses ?? 0,
    winRate: rawStats.win_rate ?? 0,
    avgPnl: rawStats.avg_pnl ?? 0,
  };
}

function mapRadarAnomaly(rawAnomaly: RawRadarAnomaly | string): RadarAnomaly {
  if (typeof rawAnomaly === 'string') {
    return {
      ticker: rawAnomaly,
      lane: 'RADAR_ONLY',
      discoveryScore: null,
      volumeRatio: null,
      changePct: null,
      closePrice: null,
      reason: null,
      source: null,
      scannedAt: null,
    };
  }

  return {
    ticker: rawAnomaly.ticker,
    lane: rawAnomaly.lane ?? 'RADAR_ONLY',
    discoveryScore: rawAnomaly.discovery_score ?? null,
    volumeRatio: rawAnomaly.volume_ratio ?? null,
    changePct: rawAnomaly.change_pct ?? null,
    closePrice: rawAnomaly.close_price ?? null,
    reason: rawAnomaly.reason ?? null,
    source: rawAnomaly.source ?? null,
    scannedAt: rawAnomaly.scanned_at ?? null,
  };
}

export async function fetchDashboardSnapshot(): Promise<DashboardSnapshot> {
  const [
    signalsResponse,
    watchlistResponse,
    portfolioResponse,
    historyResponse,
    anomaliesResponse,
    statsResponse,
  ] = await Promise.all([
    dashboardClient.get<{ signals: RawSignalItem[] }>('/api/v1/dashboard/signals'),
    dashboardClient.get<{ watchlist: string[] }>('/api/v1/dashboard/watchlist'),
    dashboardClient.get<{ portfolio: RawPortfolioPosition[] }>('/api/v1/dashboard/portfolio'),
    dashboardClient.get<{ history: RawHistoryEntry[] }>('/api/v1/dashboard/history'),
    dashboardClient.get<{
      anomalies: string[];
      anomaly_details?: RawRadarAnomaly[];
    }>('/api/v1/dashboard/anomalies'),
    dashboardClient.get<RawStats>('/api/v1/dashboard/stats'),
  ]);

  return {
    signals: (signalsResponse.data.signals || []).map(mapSignalItem),
    watchlist: watchlistResponse.data.watchlist || [],
    portfolio: (portfolioResponse.data.portfolio || []).map(mapPortfolioPosition),
    history: (historyResponse.data.history || []).map(mapHistoryEntry),
    anomalies: (
      anomaliesResponse.data.anomaly_details?.length
        ? anomaliesResponse.data.anomaly_details
        : anomaliesResponse.data.anomalies || []
    ).map(mapRadarAnomaly),
    stats: mapTradingStats(statsResponse.data),
  };
}

export async function executeDashboardAction(
  ticker: string,
  action: DashboardAction,
): Promise<void> {
  await dashboardClient.post('/api/v1/dashboard/action', { ticker, action });
}

export async function addDashboardWatchlistTicker(ticker: string): Promise<void> {
  await dashboardClient.post('/api/v1/dashboard/watchlist', { ticker });
}

export async function removeDashboardWatchlistTicker(ticker: string): Promise<void> {
  await dashboardClient.delete(`/api/v1/dashboard/watchlist/${ticker}`);
}

export async function runManualScan(): Promise<string> {
  const response = await dashboardClient.post<{ message?: string }>(
    '/api/v1/admin/scan-now',
  );

  return response.data.message || 'Scan manual berhasil dijalankan.';
}
