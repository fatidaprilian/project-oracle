import { useEffect, useState } from 'react'
import { api, RequestRecord, SymbolInfo } from '../api/client'
import { Card, Badge, Error, RetryNotice, SkeletonCard } from '../components/UI'
import { withRetry } from '../api/retry'
import { AppRole } from '../auth/session'
import { getAccessByRole } from '../config/access'

interface RequestsProps {
  role: AppRole
}

export default function Requests({ role }: RequestsProps) {
  const [symbols, setSymbols] = useState<SymbolInfo[]>([])
  const [selectedSymbol, setSelectedSymbol] = useState<string>('')
  const [requests, setRequests] = useState<RequestRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>('')

  const access = getAccessByRole(role)
  const canApproveRequests = access.canApproveRequests

  useEffect(() => {
    loadSymbols()
  }, [])

  useEffect(() => {
    loadRequests()
  }, [selectedSymbol])

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

  const loadRequests = async () => {
    try {
      setLoading(true)
      const { data } = await withRetry(() => api.getRequests(selectedSymbol), 2, 400)
      setRequests(data)
      setError('')
    } catch (err) {
      setError('Failed to load requests')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const approveRequest = async (requestId: string) => {
    if (!canApproveRequests) {
      setError('Current role cannot approve requests')
      return
    }

    try {
      await api.approveRequest(requestId, 'approved')
      await loadRequests()
    } catch (err) {
      setError('Failed to approve request')
      console.error(err)
    }
  }

  const rejectRequest = async (requestId: string) => {
    if (!canApproveRequests) {
      setError('Current role cannot reject requests')
      return
    }

    try {
      await api.approveRequest(requestId, 'rejected')
      await loadRequests()
    } catch (err) {
      setError('Failed to reject request')
      console.error(err)
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-3xl font-bold text-white mb-2">Parameter Change Requests</h2>
        <p className="text-slate-400">Approve, reject, or promote strategy parameter changes</p>
        {!canApproveRequests && (
          <p className="text-xs text-amber-300 mt-2">
            Current role is read-only for approval actions.
          </p>
        )}
      </div>

      {error && <Error message={error} />}
      {error && (
        <RetryNotice
          message="Request list failed to load. Retry now."
          onRetry={() => {
            void loadRequests()
          }}
        />
      )}

      <Card>
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Filter by Symbol
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
      </Card>

      {loading ? (
        <div className="space-y-4">
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </div>
      ) : requests.length === 0 ? (
        <Card>
          <p className="text-slate-400 text-center py-8">No requests found</p>
        </Card>
      ) : (
        <div className="space-y-4">
          {requests.map(req => (
            <Card key={req.request_id} className="space-y-4">
              <div className="flex items-start justify-between">
                <div className="space-y-2">
                  <div className="flex items-center gap-3">
                    <code className="text-sm font-mono text-slate-400">
                      {req.request_id.substring(0, 8)}...
                    </code>
                    <Badge status={req.status as any} />
                    {req.is_valid !== undefined && (
                      <span className={`text-sm ${req.is_valid ? 'text-green-400' : 'text-red-400'}`}>
                        {req.is_valid ? 'Valid' : 'Invalid'}
                      </span>
                    )}
                    {req.promoted && (
                      <span className="text-sm text-blue-400">Promoted</span>
                    )}
                  </div>
                  {req.symbol && (
                    <p className="text-sm text-slate-400">Symbol: {req.symbol}</p>
                  )}
                </div>
              </div>

              {req.status === 'pending' && canApproveRequests && (
                <div className="flex gap-2 pt-2 border-t border-slate-800">
                  <button
                    onClick={() => approveRequest(req.request_id)}
                    className="btn-primary text-sm"
                  >
                    Approve
                  </button>
                  <button
                    onClick={() => rejectRequest(req.request_id)}
                    className="btn-secondary text-sm"
                  >
                    Reject
                  </button>
                </div>
              )}
              {req.status === 'pending' && !canApproveRequests && (
                <div className="pt-2 border-t border-slate-800 text-xs text-amber-300">
                  Role {access.role} cannot change request status.
                </div>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
