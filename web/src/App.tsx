import { useEffect, useState } from 'react';
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
  status: 'NONE' | 'TRACKING' | 'IGNORED';
}

function App() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [watchlist, setWatchlist] = useState<string[]>([]);
  const [newTicker, setNewTicker] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [sigRes, watchRes] = await Promise.all([
        axios.get(`${API_BASE}/api/v1/dashboard/signals`),
        axios.get(`${API_BASE}/api/v1/dashboard/watchlist`)
      ]);
      setSignals(sigRes.data.signals || []);
      setWatchlist(watchRes.data.watchlist || []);
    } catch (err) {
      console.error("Failed to fetch data", err);
    } finally {
      setLoading(false);
    }
  };

  const handleAction = async (ticker: string, action: 'buy' | 'ignore') => {
    try {
      await axios.post(`${API_BASE}/api/v1/dashboard/action`, { ticker, action });
      setSignals(prev => prev.map(s => {
        if (s.ticker === ticker) {
          return { ...s, status: action === 'buy' ? 'TRACKING' : 'IGNORED' };
        }
        return s;
      }));
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
      fetchData(); // refresh
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

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 font-sans p-6 md:p-12">
      <div className="max-w-7xl mx-auto">
        <header className="mb-12 border-b border-neutral-800 pb-6 flex flex-col md:flex-row md:items-center justify-between gap-6">
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
          <div className="mb-10 p-4 bg-neutral-900 border border-neutral-800 rounded-xl">
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

        {loading ? (
          <div className="text-center text-neutral-500 py-20 animate-pulse">Scanning the markets...</div>
        ) : signals.length === 0 ? (
          <div className="text-center text-neutral-500 py-20 border border-neutral-800 rounded-xl bg-neutral-900/50">
            No signals available. Oracle is analyzing the watchlist.
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {signals.map((signal) => (
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
                  <span className="text-xs text-neutral-500 font-mono">
                    {new Date(signal.created_at).toLocaleString([], {hour: '2-digit', minute:'2-digit', day: 'numeric', month: 'short'})}
                  </span>
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
                  {signal.status === 'NONE' ? (
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
                  ) : (
                    <div className="text-center py-3 font-semibold text-sm bg-neutral-900 rounded-xl border border-neutral-800">
                      {signal.status === 'TRACKING' ? (
                        <span className="text-emerald-400 flex items-center justify-center gap-2">🟢 Position Active & Tracked</span>
                      ) : (
                        <span className="text-rose-400 flex items-center justify-center gap-2">🔴 Ignored by User</span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
