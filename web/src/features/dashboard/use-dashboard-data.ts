import { startTransition, useCallback, useEffect, useState } from 'react';

import {
  addDashboardWatchlistTicker,
  executeDashboardAction,
  fetchDashboardSnapshot,
  removeDashboardWatchlistTicker,
  runManualScan,
} from './dashboard-api';
import type {
  DashboardAction,
  DashboardControls,
  DashboardSnapshot,
  DashboardUiState,
} from './types';

const EMPTY_DASHBOARD_SNAPSHOT: DashboardSnapshot = {
  signals: [],
  portfolio: [],
  history: [],
  watchlist: [],
  anomalies: [],
  stats: {
    total: 0,
    wins: 0,
    losses: 0,
    winRate: 0,
    avgPnl: 0,
  },
};

interface DashboardDataState {
  data: DashboardSnapshot;
  uiState: DashboardUiState;
  controls: DashboardControls;
}

export function useDashboardData(): DashboardDataState {
  const [data, setData] = useState<DashboardSnapshot>(EMPTY_DASHBOARD_SNAPSHOT);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [errorText, setErrorText] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [watchlistDraft, setWatchlistDraft] = useState('');
  const [activeActionKey, setActiveActionKey] = useState<string | null>(null);

  const refreshDashboard = useCallback(async (isBackgroundRefresh = false) => {
    if (isBackgroundRefresh) {
      setIsRefreshing(true);
    } else {
      setIsLoading(true);
    }

    try {
      const nextSnapshot = await fetchDashboardSnapshot();
      startTransition(() => {
        setData(nextSnapshot);
        setErrorText(null);
      });
    } catch (error) {
      const nextErrorText =
        error instanceof Error
          ? error.message
          : 'Data dashboard belum bisa dimuat.';
      setErrorText(nextErrorText);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void refreshDashboard(false);

    const intervalId = window.setInterval(() => {
      void refreshDashboard(true);
    }, 60000);

    return () => window.clearInterval(intervalId);
  }, [refreshDashboard]);

  const handleWatchlistDraftChange = useCallback((nextValue: string) => {
    setWatchlistDraft(nextValue.toUpperCase());
  }, []);

  const handleSubmitWatchlist = useCallback(async () => {
    const normalizedTicker = watchlistDraft.trim().toUpperCase();
    if (!normalizedTicker) {
      return;
    }

    setActiveActionKey(`watchlist:${normalizedTicker}`);
    try {
      await addDashboardWatchlistTicker(normalizedTicker);
      setWatchlistDraft('');
      setStatusMessage(`${normalizedTicker} masuk ke watchlist manual.`);
      await refreshDashboard(true);
    } finally {
      setActiveActionKey(null);
    }
  }, [refreshDashboard, watchlistDraft]);

  const handleRemoveWatchlistTicker = useCallback(
    async (ticker: string) => {
      setActiveActionKey(`watchlist-remove:${ticker}`);
      try {
        await removeDashboardWatchlistTicker(ticker);
        setStatusMessage(`${ticker} dihapus dari watchlist manual.`);
        await refreshDashboard(true);
      } finally {
        setActiveActionKey(null);
      }
    },
    [refreshDashboard],
  );

  const handleRunManualScan = useCallback(async () => {
    setActiveActionKey('scan-now');
    try {
      const message = await runManualScan();
      setStatusMessage(message);
      await refreshDashboard(true);
    } finally {
      setActiveActionKey(null);
    }
  }, [refreshDashboard]);

  const handleSignalAction = useCallback(
    async (ticker: string, action: DashboardAction) => {
      setActiveActionKey(`${action}:${ticker}`);
      try {
        await executeDashboardAction(ticker, action);

        if (action === 'buy') {
          setStatusMessage(`Tracking untuk ${ticker} sudah diaktifkan.`);
        } else if (action === 'ignore') {
          setStatusMessage(`${ticker} dimute selama 3 hari.`);
        } else {
          setStatusMessage(`Posisi ${ticker} ditutup.`);
        }

        await refreshDashboard(true);
      } finally {
        setActiveActionKey(null);
      }
    },
    [refreshDashboard],
  );

  return {
    data,
    uiState: {
      isLoading,
      isRefreshing,
      errorText,
      statusMessage,
      activeActionKey,
      watchlistDraft,
    },
    controls: {
      onRefreshDashboard: () => refreshDashboard(true),
      onRunManualScan: handleRunManualScan,
      onWatchlistDraftChange: handleWatchlistDraftChange,
      onSubmitWatchlist: handleSubmitWatchlist,
      onRemoveWatchlistTicker: handleRemoveWatchlistTicker,
      onSignalAction: handleSignalAction,
    },
  };
}
