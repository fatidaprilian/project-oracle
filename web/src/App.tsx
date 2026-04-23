import { useEffect, useState, useCallback } from 'react';
import axios from 'axios';
import './index.css';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface Signal {
  id: string;
  ticker: string;
  technical_signal: string;
  news_context: string;
  ai_reasoning: string;
  bias: string;
  entry_price?: number | null;
  target_price?: number | null;
  stop_loss?: number | null;
  created_at: string;
  status: 'PENDING' | 'TRACKING' | 'IGNORED' | 'EXPIRED';
  resolved_at?: string | null;
  expires_at?: string | null;
  data_timestamp?: string | null;
}

interface PortfolioItem {
  id: string;
  ticker: string;
  tracked_since: string;
  last_checked_at?: string | null;
  entry_price?: number | null;
  target_price?: number | null;
  stop_loss?: number | null;
  current_price?: number | null;
  pnl_percent?: number | null;
}

interface HistoryItem {
  id: string;
  ticker: string;
  bias: string;
  ai_reasoning: string;
  entry_price?: number | null;
  target_price?: number | null;
  stop_loss?: number | null;
  created_at: string;
  resolved_at?: string | null;
  resolved_action?: string | null;
}

type TabKey = 'signals' | 'portfolio' | 'history';

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

function expiryCountdown(expiresAt: string | null | undefined): string {
  if (!expiresAt) return '';
  const diff = new Date(expiresAt).getTime() - Date.now();
  if (diff <= 0) return 'Expired';
  const hrs = Math.floor(diff / 3600000);
  const mins = Math.floor((diff % 3600000) / 60000);
  return `${hrs}h ${mins}m left`;
}

function App() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [portfolio, setPortfolio] = useState<PortfolioItem[]>([]);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [watchlist, setWatchlist] = useState<string[]>([]);
  const [newTicker, setNewTicker] = useState('');
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<TabKey>('signals');

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [sigRes, watchRes, portRes, histRes] = await Promise.all([
        axios.get(`${API_BASE}/api/v1/dashboard/signals`),
        axios.get(`${API_BASE}/api/v1/dashboard/watchlist`),
        axios.get(`${API_BASE}/api/v1/dashboard/portfolio`),
        axios.get(`${API_BASE}/api/v1/dashboard/history`),
      ]);
      setSignals(sigRes.data.signals || []);
      setWatchlist(watchRes.data.watchlist || []);
      setPortfolio(portRes.data.portfolio || []);
      setHistory(histRes.data.history || []);
    } catch (err) {
      console.error("Failed to fetch data", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 60000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleAction = async (ticker: string, action: 'buy' | 'ignore' | 'sell') => {
    try {
      await axios.post(`${API_BASE}/api/v1/dashboard/action`, { ticker, action });
      fetchData();
    } catch (err) {
      console.error("Action failed", err);
    }
  };

  const addWatchlist = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTicker.trim()) return;
    try {
      await axios.post(`${API_BASE}/api/v1/dashboard/watchlist`, { ticker: newTicker.trim() });
      setNewTicker('');
      fetchData();
    } catch (err) {
      console.error("Failed to add to watchlist", err);
    }
  };

  const removeWatchlist = async (ticker: string) => {
    try {
      await axios.delete(`${API_BASE}/api/v1/dashboard/watchlist/${ticker}`);
      fetchData();
    } catch (err) {
      console.error("Failed to remove from watchlist", err);
    }
  };

  const pendingSignals = signals.filter(s => s.status === 'PENDING');

  const tabs: { key: TabKey; label: string; count: number }[] = [
    { key: 'signals', label: '📡 Pending Signals', count: pendingSignals.length },
    { key: 'portfolio', label: '💼 Active Portfolio', count: portfolio.length },
    { key: 'history', label: '📜 History', count: history.length },
  ];

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 font-sans p-6 md:p-12">
      <div className="max-w-7xl mx-auto">
        <header className="mb-10 border-b border-neutral-800 pb-6 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <h1 className="text-4xl font-extrabold tracking-tight bg-gradient-to-r from-emerald-400 to-cyan-500 bg-clip-text text-transparent">
              Oracle Pro 2026
            </h1>
            <p className="text-neutral-400 mt-2">AI-Driven Quantitative Intelligence.</p>
          </div>

          <div className="flex gap-4 items-end">
            <form onSubmit={addWatchlist} className="flex gap-2">
              <input
                type="text"
                placeholder="Add Ticker (e.g. AAPL, GOTO.JK)"
                value={newTicker}
                onChange={e => setNewTicker(e.target.value.toUpperCase())}
                className="bg-neutral-900 border border-neutral-700 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-emerald-500 uppercase"
              />
              <button type="submit" className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 rounded-lg text-sm font-semibold transition-colors">
                Track
              </button>
            </form>
            <button
              onClick={fetchData}
              className="px-4 py-2 bg-neutral-800 hover:bg-neutral-700 rounded-lg text-sm transition-colors border border-neutral-700"
            >
              Refresh
            </button>
          </div>
        </header>

        {watchlist.length > 0 && (
          <div className="mb-8 p-4 bg-neutral-900 border border-neutral-800 rounded-xl">
            <h2 className="text-xs text-neutral-500 uppercase tracking-wider mb-3">Active Watchlist Radar</h2>
            <div className="flex flex-wrap gap-2">
              {watchlist.map(t => (
                <div key={t} className="flex items-center gap-2 bg-neutral-950 border border-neutral-700 px-3 py-1.5 rounded-md text-sm">
                  <span className="font-mono">{t}</span>
                  <button onClick={() => removeWatchlist(t)} className="text-neutral-500 hover:text-rose-400">&times;</button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tab Navigation */}
        <div className="flex gap-1 mb-8 bg-neutral-900 p-1 rounded-xl border border-neutral-800">
          {tabs.map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex-1 py-3 px-4 rounded-lg text-sm font-semibold transition-all ${
                activeTab === tab.key
                  ? 'bg-neutral-800 text-white shadow-lg border border-neutral-700'
                  : 'text-neutral-500 hover:text-neutral-300 hover:bg-neutral-800/50'
              }`}
            >
              {tab.label}
              {tab.count > 0 && (
                <span className={`ml-2 px-2 py-0.5 rounded-full text-xs ${
                  activeTab === tab.key ? 'bg-emerald-500/20 text-emerald-400' : 'bg-neutral-800 text-neutral-500'
                }`}>
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="text-center text-neutral-500 py-20 animate-pulse">Scanning the markets...</div>
        ) : (
          <>
            {/* Pending Signals Tab */}
            {activeTab === 'signals' && (
              pendingSignals.length === 0 ? (
                <div className="text-center text-neutral-500 py-20 border border-neutral-800 rounded-xl bg-neutral-900/50">
                  No pending signals. Oracle is analyzing the watchlist.
                </div>
              ) : (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                  {pendingSignals.map((signal) => (
                    <div key={signal.id} className="bg-neutral-900 border border-neutral-800 rounded-2xl overflow-hidden hover:border-neutral-700 transition-colors shadow-2xl flex flex-col">
                      <div className="p-5 border-b border-neutral-800/50 flex justify-between items-center bg-neutral-900/80">
                        <div className="flex items-center gap-3">
                          <span className="text-2xl font-black tracking-tight">{signal.ticker}</span>
                          {signal.bias === 'BUY' && (
                            <span className="px-2 py-1 text-xs font-bold bg-emerald-500/10 text-emerald-400 rounded-md uppercase">BUY SIGNAL</span>
                          )}
                          {signal.bias === 'SELL' && (
                            <span className="px-2 py-1 text-xs font-bold bg-amber-500/10 text-amber-400 rounded-md uppercase">SELL SIGNAL</span>
                          )}
                          {signal.bias === 'IGNORE' && (
                            <span className="px-2 py-1 text-xs font-bold bg-rose-500/10 text-rose-400 rounded-md uppercase">IGNORE</span>
                          )}
                        </div>
                        <div className="text-right">
                          <span className="text-xs text-neutral-500 font-mono block">
                            {new Date(signal.created_at).toLocaleString([], {hour: '2-digit', minute:'2-digit', day: 'numeric', month: 'short'})}
                          </span>
                          {signal.expires_at && (
                            <span className="text-[10px] text-amber-500 font-mono">
                              ⏳ {expiryCountdown(signal.expires_at)}
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Embedded TradingView Chart */}
                      <div className="h-64 border-b border-neutral-800 bg-neutral-950">
                        <iframe
                          src={`https://s.tradingview.com/widgetembed/?symbol=${signal.ticker.replace('.JK', '')}&interval=D&hidesidetoolbar=1&symboledit=1&saveimage=1&toolbarbg=f1f3f6&studies=%5B%5D&theme=dark&style=1`}
                          width="100%"
                          height="100%"
                          frameBorder="0"
                          allowFullScreen
                          className="opacity-90 hover:opacity-100 transition-opacity"
                        ></iframe>
                      </div>

                      <div className="p-6 flex-1 flex flex-col gap-6">
                        <div className="flex flex-wrap gap-2 items-center">
                          {signal.data_timestamp && (
                            <span className="text-xs text-neutral-500 font-mono bg-neutral-950 px-3 py-1.5 rounded-lg border border-neutral-800">
                              📊 {signal.data_timestamp}
                            </span>
                          )}
                          {signal.technical_signal && signal.technical_signal.split('+').slice(1).map((tag, i) => {
                            const isStrategy = tag.includes('PULLBACK');
                            const isRegime = ['UPTREND', 'DOWNTREND', 'CHOP'].includes(tag);
                            const color = isStrategy
                              ? 'bg-violet-500/10 text-violet-400 border-violet-500/20'
                              : isRegime && tag === 'UPTREND'
                              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                              : isRegime && tag === 'DOWNTREND'
                              ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                              : 'bg-neutral-500/10 text-neutral-400 border-neutral-500/20';
                            return (
                              <span key={i} className={`text-[10px] font-bold uppercase px-2 py-1 rounded-md border ${color}`}>
                                {tag.replace(/_/g, ' ')}
                              </span>
                            );
                          })}
                        </div>

                        {signal.entry_price && (
                          <div className="grid grid-cols-3 gap-4 bg-neutral-950 p-4 rounded-xl border border-neutral-800">
                            <div>
                              <div className="text-[10px] text-neutral-500 uppercase font-bold tracking-wider mb-1">Entry</div>
                              <div className="text-lg font-mono font-medium text-emerald-400">{signal.entry_price}</div>
                            </div>
                            <div>
                              <div className="text-[10px] text-neutral-500 uppercase font-bold tracking-wider mb-1">Target</div>
                              <div className="text-lg font-mono font-medium text-cyan-400">{signal.target_price}</div>
                            </div>
                            <div>
                              <div className="text-[10px] text-neutral-500 uppercase font-bold tracking-wider mb-1">Stop Loss</div>
                              <div className="text-lg font-mono font-medium text-rose-400">{signal.stop_loss}</div>
                            </div>
                          </div>
                        )}

                        <div>
                          <h3 className="text-xs text-neutral-500 uppercase font-bold tracking-wider mb-2">Oracle Analysis</h3>
                          <p className="text-sm text-neutral-300 leading-relaxed font-serif">
                            {signal.ai_reasoning}
                          </p>
                        </div>
                      </div>

                      <div className="p-5 bg-neutral-950/80 border-t border-neutral-800">
                        <div className="flex gap-3">
                          <button
                            onClick={() => handleAction(signal.ticker, 'buy')}
                            className="flex-1 py-3 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-xl transition-all shadow-lg hover:shadow-emerald-900/50"
                          >
                            ✅ Execute Trade
                          </button>
                          <button
                            onClick={() => handleAction(signal.ticker, 'ignore')}
                            className="flex-1 py-3 bg-neutral-800 hover:bg-neutral-700 text-neutral-300 font-semibold rounded-xl transition-colors border border-neutral-700"
                          >
                            ❌ Ignore
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )
            )}

            {/* Active Portfolio Tab */}
            {activeTab === 'portfolio' && (
              portfolio.length === 0 ? (
                <div className="text-center text-neutral-500 py-20 border border-neutral-800 rounded-xl bg-neutral-900/50">
                  No active positions. Buy a signal to start tracking.
                </div>
              ) : (
                <div className="bg-neutral-900 border border-neutral-800 rounded-2xl overflow-hidden shadow-2xl">
                  <div className="p-5 border-b border-neutral-800 bg-neutral-900/80">
                    <h2 className="text-lg font-bold">Active Positions</h2>
                    <p className="text-xs text-neutral-500 mt-1">Live monitoring. Prices update every cycle.</p>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-neutral-800 text-neutral-500 text-xs uppercase tracking-wider">
                          <th className="text-left p-4">Ticker</th>
                          <th className="text-right p-4">Entry</th>
                          <th className="text-right p-4">Current</th>
                          <th className="text-right p-4">Target</th>
                          <th className="text-right p-4">Stop Loss</th>
                          <th className="text-right p-4">PnL</th>
                          <th className="text-right p-4">Since</th>
                          <th className="text-center p-4">Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {portfolio.map(pos => {
                          const pnl = pos.pnl_percent ?? 0;
                          const pnlColor = pnl > 0 ? 'text-emerald-400' : pnl < 0 ? 'text-rose-400' : 'text-neutral-400';
                          return (
                            <tr key={pos.id} className="border-b border-neutral-800/50 hover:bg-neutral-800/30 transition-colors">
                              <td className="p-4">
                                <span className="font-bold font-mono text-base">{pos.ticker}</span>
                              </td>
                              <td className="p-4 text-right font-mono text-neutral-300">
                                {pos.entry_price?.toFixed(2) ?? '—'}
                              </td>
                              <td className="p-4 text-right font-mono text-white font-semibold">
                                {pos.current_price?.toFixed(2) ?? '—'}
                              </td>
                              <td className="p-4 text-right font-mono text-cyan-400">
                                {pos.target_price?.toFixed(2) ?? '—'}
                              </td>
                              <td className="p-4 text-right font-mono text-rose-400">
                                {pos.stop_loss?.toFixed(2) ?? '—'}
                              </td>
                              <td className={`p-4 text-right font-mono font-bold ${pnlColor}`}>
                                {pnl > 0 ? '+' : ''}{pnl.toFixed(2)}%
                              </td>
                              <td className="p-4 text-right text-xs text-neutral-500">
                                {pos.tracked_since ? timeAgo(pos.tracked_since) : '—'}
                              </td>
                              <td className="p-4 text-center">
                                <button
                                  onClick={() => handleAction(pos.ticker, 'sell')}
                                  className="px-4 py-2 bg-rose-600/20 hover:bg-rose-600/40 text-rose-400 font-semibold rounded-lg text-xs transition-colors border border-rose-600/30"
                                >
                                  Close Position
                                </button>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                  {/* Portfolio Summary */}
                  <div className="p-5 border-t border-neutral-800 bg-neutral-950/50">
                    <div className="grid grid-cols-3 gap-6">
                      <div>
                        <div className="text-[10px] text-neutral-500 uppercase font-bold tracking-wider mb-1">Total Positions</div>
                        <div className="text-2xl font-bold text-white">{portfolio.length}</div>
                      </div>
                      <div>
                        <div className="text-[10px] text-neutral-500 uppercase font-bold tracking-wider mb-1">Avg PnL</div>
                        {(() => {
                          const totalPnl = portfolio.reduce((sum, p) => sum + (p.pnl_percent ?? 0), 0);
                          const avg = portfolio.length > 0 ? totalPnl / portfolio.length : 0;
                          const color = avg > 0 ? 'text-emerald-400' : avg < 0 ? 'text-rose-400' : 'text-neutral-400';
                          return <div className={`text-2xl font-bold font-mono ${color}`}>{avg > 0 ? '+' : ''}{avg.toFixed(2)}%</div>;
                        })()}
                      </div>
                      <div>
                        <div className="text-[10px] text-neutral-500 uppercase font-bold tracking-wider mb-1">Profitable</div>
                        <div className="text-2xl font-bold text-emerald-400">
                          {portfolio.filter(p => (p.pnl_percent ?? 0) > 0).length}/{portfolio.length}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )
            )}

            {/* History Tab */}
            {activeTab === 'history' && (
              history.length === 0 ? (
                <div className="text-center text-neutral-500 py-20 border border-neutral-800 rounded-xl bg-neutral-900/50">
                  No signal history yet.
                </div>
              ) : (
                <div className="bg-neutral-900 border border-neutral-800 rounded-2xl overflow-hidden shadow-2xl">
                  <div className="p-5 border-b border-neutral-800 bg-neutral-900/80">
                    <h2 className="text-lg font-bold">Signal History</h2>
                    <p className="text-xs text-neutral-500 mt-1">Past signals and their outcomes.</p>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-neutral-800 text-neutral-500 text-xs uppercase tracking-wider">
                          <th className="text-left p-4">Ticker</th>
                          <th className="text-left p-4">Bias</th>
                          <th className="text-left p-4">Reasoning</th>
                          <th className="text-right p-4">Entry</th>
                          <th className="text-right p-4">Target</th>
                          <th className="text-center p-4">Outcome</th>
                          <th className="text-right p-4">Date</th>
                        </tr>
                      </thead>
                      <tbody>
                        {history.map(item => {
                          const actionColor =
                            item.resolved_action === 'BUY' ? 'text-emerald-400 bg-emerald-500/10' :
                            item.resolved_action === 'IGNORE' ? 'text-rose-400 bg-rose-500/10' :
                            item.resolved_action === 'EXPIRED' ? 'text-amber-400 bg-amber-500/10' :
                            'text-neutral-400 bg-neutral-500/10';
                          return (
                            <tr key={item.id} className="border-b border-neutral-800/50 hover:bg-neutral-800/30 transition-colors">
                              <td className="p-4 font-bold font-mono">{item.ticker}</td>
                              <td className="p-4">
                                <span className={`px-2 py-1 text-xs font-bold rounded-md uppercase ${
                                  item.bias === 'BUY' ? 'bg-emerald-500/10 text-emerald-400' :
                                  item.bias === 'SELL' ? 'bg-amber-500/10 text-amber-400' :
                                  'bg-rose-500/10 text-rose-400'
                                }`}>
                                  {item.bias}
                                </span>
                              </td>
                              <td className="p-4 text-neutral-400 text-xs max-w-xs truncate">{item.ai_reasoning}</td>
                              <td className="p-4 text-right font-mono text-neutral-300">{item.entry_price?.toFixed(2) ?? '—'}</td>
                              <td className="p-4 text-right font-mono text-cyan-400">{item.target_price?.toFixed(2) ?? '—'}</td>
                              <td className="p-4 text-center">
                                <span className={`px-2 py-1 text-xs font-bold rounded-md uppercase ${actionColor}`}>
                                  {item.resolved_action || '—'}
                                </span>
                              </td>
                              <td className="p-4 text-right text-xs text-neutral-500 font-mono">
                                {item.resolved_at ? new Date(item.resolved_at).toLocaleDateString([], {day: 'numeric', month: 'short'}) : '—'}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default App;
