import { useEffect, useState } from 'react'
import {
  api,
  SymbolInfo,
  GovernanceSummary,
  ConfigConnections,
  buildGovernanceStreamUrl,
} from '../api/client'
import { AppRole } from '../auth/session'
import { getAccessByRole } from '../config/access'
import {
  Card,
  Stat,
  Loading,
  Error,
  RetryNotice,
  SkeletonCard,
  LiveStatusBadge,
} from '../components/UI'
import { withRetry } from '../api/retry'

interface DashboardProps {
  role: AppRole
}

export default function Dashboard({ role }: DashboardProps) {
  const [symbols, setSymbols] = useState<SymbolInfo[]>([])
  const [selectedSymbol, setSelectedSymbol] = useState<string>('')
  const [summary, setSummary] = useState<GovernanceSummary | null>(null)
  const [connections, setConnections] = useState<ConfigConnections | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>('')
  const [liveStatus, setLiveStatus] = useState<'connected' | 'reconnecting' | 'stale'>('reconnecting')
  const [lastLiveUpdateAt, setLastLiveUpdateAt] = useState<number>(0)

  const access = getAccessByRole(role)
  const canTriggerWorkflow = access.canTriggerWorkflow
  const canPromoteRequests = access.canPromoteRequests

  useEffect(() => {
    loadSymbols()
    loadConnections()
  }, [])

  useEffect(() => {
    loadSummary()
  }, [selectedSymbol])

  useEffect(() => {
    if (!selectedSymbol) {
      return
    }

    const streamUrl = buildGovernanceStreamUrl(selectedSymbol)
    const source = new EventSource(streamUrl)

    source.onopen = () => {
      setLiveStatus('connected')
    }

    source.addEventListener('governance', (event) => {
      try {
        const payload = JSON.parse((event as MessageEvent).data) as {
          summary?: GovernanceSummary
          connections?: ConfigConnections
        }
        if (payload.summary) {
          setSummary(payload.summary)
        }
        if (payload.connections) {
          setConnections(payload.connections)
        }
        setLastLiveUpdateAt(Date.now())
        setLiveStatus('connected')
      } catch (err) {
        console.error('Failed to parse stream payload', err)
      }
    })

    source.onerror = () => {
      setLiveStatus('reconnecting')
    }

    return () => {
      source.close()
    }
  }, [selectedSymbol])

  useEffect(() => {
    if (!lastLiveUpdateAt) {
      return
    }

    const timer = window.setInterval(() => {
      const ageMs = Date.now() - lastLiveUpdateAt
      if (ageMs > 15000) {
        setLiveStatus('stale')
      }
    }, 3000)

    return () => {
      window.clearInterval(timer)
    }
  }, [lastLiveUpdateAt])

  const loadSymbols = async () => {
    try {
      const { data } = await withRetry(() => api.getSymbols())
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
      const { data } = await withRetry(
        () => api.getGovernanceSummary(selectedSymbol),
        2,
        400,
      )
      setSummary(data)
      setError('')
    } catch (err) {
      setError('Failed to load summary')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const loadConnections = async () => {
    try {
      const { data } = await withRetry(() => api.getConnections())
      setConnections(data)
    } catch (err) {
      console.error(err)
    }
  }

  const triggerWorkflow = async () => {
    if (!canTriggerWorkflow) {
      setError('Current role cannot trigger workflow')
      return
    }

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
    if (!canPromoteRequests) {
      setError('Current role cannot promote requests')
      return
    }

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
        <div className="flex items-center gap-3">
          <p className="text-slate-400">Real-time governance and parameter management</p>
          <LiveStatusBadge status={liveStatus} />
        </div>
      </div>

      {error && <Error message={error} />}
      {error && (
        <RetryNotice
          message="Request failed. Retry the latest dashboard fetch."
          onRetry={() => {
            void loadSummary()
            void loadConnections()
          }}
        />
      )}

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
              disabled={loading || !canTriggerWorkflow}
              className="btn-primary disabled:opacity-50"
            >
              {canTriggerWorkflow ? (loading ? 'Running...' : 'Trigger Workflow') : 'Read-only role'}
            </button>
            <button
              onClick={promoteRequests}
              disabled={loading || !summary?.ready_to_promote || !canPromoteRequests}
              className="btn-secondary disabled:opacity-50"
            >
              Promote ({summary?.ready_to_promote || 0})
            </button>
          </div>
          {(!canTriggerWorkflow || !canPromoteRequests) && (
            <p className="text-xs text-amber-300">
              Role {access.role} has limited write permissions in governance actions.
            </p>
          )}
        </div>
      </Card>

      {loading && summary === null ? (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </div>
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
            {loading ? (
              <Loading message="Syncing status..." />
            ) : (
              <span className="text-slate-400">Check in Requests tab</span>
            )}
          </div>
        </div>
      </Card>

      <Card>
        <div className="card-header">Infrastructure Connections</div>
        {connections ? (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-slate-300">PostgreSQL</span>
              <span className={connections.postgres.reachable ? 'text-green-400' : 'text-red-400'}>
                {connections.postgres.reachable ? 'Connected' : connections.postgres.detail}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-300">Redis</span>
              <span className={connections.redis.reachable ? 'text-green-400' : 'text-red-400'}>
                {connections.redis.reachable ? 'Connected' : connections.redis.detail}
              </span>
            </div>
          </div>
        ) : (
          <span className="text-slate-400">Connection status unavailable</span>
        )}
      </Card>
    </div>
  )
}
