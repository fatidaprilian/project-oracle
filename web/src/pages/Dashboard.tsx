import { useEffect, useState } from 'react'
import { api, SymbolInfo, GovernanceSummary } from '../api/client'
import { Card, Stat, Loading, Error } from '../components/UI'

export default function Dashboard() {
  const [symbols, setSymbols] = useState<SymbolInfo[]>([])
  const [selectedSymbol, setSelectedSymbol] = useState<string>('')
  const [summary, setSummary] = useState<GovernanceSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>('')

  useEffect(() => {
    loadSymbols()
  }, [])

  useEffect(() => {
    loadSummary()
  }, [selectedSymbol])

  const loadSymbols = async () => {
    try {
      const { data } = await api.getSymbols()
      setSymbols(data)
      if (data.length > 0) {
        setSelectedSymbol(data[0].symbol)
      }
    } catch (err) {
      setError('Failed to load symbols')
      console.error(err)
    }
  }

  const loadSummary = async () => {
    try {
      setLoading(true)
      const { data } = await api.getGovernanceSummary(selectedSymbol)
      setSummary(data)
      setError('')
    } catch (err) {
      setError('Failed to load summary')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const triggerWorkflow = async () => {
    try {
      setLoading(true)
      await api.triggerWorkflow(selectedSymbol)
      await new Promise(r => setTimeout(r, 1000))
      await loadSummary()
    } catch (err) {
      setError('Failed to trigger workflow')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const promoteRequests = async () => {
    try {
      setLoading(true)
      await api.promoteRequests()
      await loadSummary()
    } catch (err) {
      setError('Failed to promote requests')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-3xl font-bold text-white mb-2">Strategy Dashboard</h2>
        <p className="text-slate-400">Real-time governance and parameter management</p>
      </div>

      {error && <Error message={error} />}

      <Card>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Select Symbol
            </label>
            <select
              value={selectedSymbol}
              onChange={(e) => setSelectedSymbol(e.target.value)}
              className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
            >
              {symbols.map(s => (
                <option key={s.symbol} value={s.symbol}>
                  {s.symbol} ({s.total_requests} requests)
                </option>
              ))}
            </select>
          </div>

          <div className="flex gap-3">
            <button
              onClick={triggerWorkflow}
              disabled={loading}
              className="btn-primary disabled:opacity-50"
            >
              {loading ? 'Running...' : 'Trigger Workflow'}
            </button>
            <button
              onClick={promoteRequests}
              disabled={loading || !summary?.ready_to_promote}
              className="btn-secondary disabled:opacity-50"
            >
              Promote ({summary?.ready_to_promote || 0})
            </button>
          </div>
        </div>
      </Card>

      {loading && summary === null ? (
        <Loading message="Loading dashboard..." />
      ) : summary ? (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <Card>
            <Stat label="Total Requests" value={summary.total} />
          </Card>
          <Card>
            <Stat label="Pending" value={summary.pending} trend="neutral" />
          </Card>
          <Card>
            <Stat label="Approved" value={summary.approved} trend="up" />
          </Card>
          <Card>
            <Stat label="Rejected" value={summary.rejected} trend="down" />
          </Card>
          <Card>
            <Stat label="Ready to Promote" value={summary.ready_to_promote} trend="up" />
          </Card>
        </div>
      ) : null}

      <Card>
        <div className="card-header">Workflow Status</div>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-slate-300">Last Workflow Run</span>
            <span className="text-slate-400">Check in Requests tab</span>
          </div>
        </div>
      </Card>
    </div>
  )
}
