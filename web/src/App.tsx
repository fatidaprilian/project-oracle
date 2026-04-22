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
  created_at: string;
  status: 'NONE' | 'TRACKING' | 'IGNORED';
}

function App() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSignals();
  }, []);

  const fetchSignals = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/v1/dashboard/signals`);
      setSignals(res.data.signals || []);
    } catch (err) {
      console.error("Failed to fetch signals", err);
    } finally {
      setLoading(false);
    }
  };

  const handleAction = async (ticker: string, action: 'buy' | 'ignore') => {
    try {
      await axios.post(`${API_BASE}/api/v1/dashboard/action`, { ticker, action });
      // Optimistic update
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

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 font-sans p-6 md:p-12">
      <div className="max-w-6xl mx-auto">
        <header className="mb-12 border-b border-neutral-800 pb-6 flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-extrabold tracking-tight bg-gradient-to-r from-emerald-400 to-cyan-500 bg-clip-text text-transparent">
              Oracle Signals
            </h1>
            <p className="text-neutral-400 mt-2">Live AI-driven stock intelligence.</p>
          </div>
          <button 
            onClick={fetchSignals} 
            className="px-4 py-2 bg-neutral-800 hover:bg-neutral-700 rounded-lg text-sm transition-colors"
          >
            Refresh
          </button>
        </header>

        {loading ? (
          <div className="text-center text-neutral-500 py-20 animate-pulse">Loading signals...</div>
        ) : signals.length === 0 ? (
          <div className="text-center text-neutral-500 py-20 border border-neutral-800 rounded-xl bg-neutral-900/50">
            No signals available. Wait for webhooks!
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {signals.map((signal) => (
              <div key={signal.id} className="bg-neutral-900 border border-neutral-800 rounded-2xl overflow-hidden hover:border-neutral-700 transition-colors shadow-xl flex flex-col">
                <div className="p-5 border-b border-neutral-800/50 flex justify-between items-center bg-neutral-900/80">
                  <div className="flex items-center gap-3">
                    <span className="text-xl font-bold">{signal.ticker}</span>
                    {signal.bias === 'BUY' && (
                      <span className="px-2 py-1 text-xs font-semibold bg-emerald-500/10 text-emerald-400 rounded-md">BUY BIAS</span>
                    )}
                    {signal.bias === 'IGNORE' && (
                      <span className="px-2 py-1 text-xs font-semibold bg-rose-500/10 text-rose-400 rounded-md">IGNORE BIAS</span>
                    )}
                  </div>
                  <span className="text-xs text-neutral-500">
                    {new Date(signal.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                  </span>
                </div>
                
                <div className="p-5 flex-1 flex flex-col gap-4">
                  <div>
                    <h3 className="text-xs text-neutral-500 uppercase tracking-wider mb-1">Technical Signal</h3>
                    <p className="text-sm font-medium">{signal.technical_signal}</p>
                  </div>
                  <div>
                    <h3 className="text-xs text-neutral-500 uppercase tracking-wider mb-1">AI Reasoning</h3>
                    <p className="text-sm text-neutral-300 leading-relaxed">
                      {signal.ai_reasoning}
                    </p>
                  </div>
                </div>

                <div className="p-5 bg-neutral-950/50 border-t border-neutral-800">
                  {signal.status === 'NONE' ? (
                    <div className="flex gap-3">
                      <button 
                        onClick={() => handleAction(signal.ticker, 'buy')}
                        className="flex-1 py-2.5 bg-emerald-500 hover:bg-emerald-400 text-neutral-950 font-bold rounded-lg transition-colors"
                      >
                        ✅ Beli
                      </button>
                      <button 
                        onClick={() => handleAction(signal.ticker, 'ignore')}
                        className="flex-1 py-2.5 bg-neutral-800 hover:bg-neutral-700 text-neutral-300 font-semibold rounded-lg transition-colors border border-neutral-700"
                      >
                        ❌ Abaikan
                      </button>
                    </div>
                  ) : (
                    <div className="text-center py-2.5 font-semibold text-sm">
                      {signal.status === 'TRACKING' ? (
                        <span className="text-emerald-400">🟢 Tracking Active</span>
                      ) : (
                        <span className="text-rose-400">🔴 Muted</span>
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
