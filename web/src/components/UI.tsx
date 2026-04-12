interface CardProps {
  children: React.ReactNode
  className?: string
}

export function Card({ children, className = '' }: CardProps) {
  return (
    <div className={`card ${className}`}>
      {children}
    </div>
  )
}

interface StatProps {
  label: string
  value: string | number
  trend?: 'up' | 'down' | 'neutral'
}

export function Stat({ label, value, trend }: StatProps) {
  const trendColor = {
    up: 'text-green-400',
    down: 'text-red-400',
    neutral: 'text-slate-400'
  }[trend || 'neutral']
  
  return (
    <div className="space-y-2">
      <p className="text-sm text-slate-400">{label}</p>  
      <p className={`text-3xl font-bold ${trendColor}`}>{value}</p>
    </div>
  )
}

interface BadgeProps {
  status: 'pending' | 'approved' | 'rejected' | 'promoted'
}

export function Badge({ status }: BadgeProps) {
  const colors = {
    pending: 'bg-yellow-900 text-yellow-200',
    approved: 'bg-green-900 text-green-200',
    rejected: 'bg-red-900 text-red-200',
    promoted: 'bg-blue-900 text-blue-200'
  }
  
  return (
    <span className={`px-3 py-1 rounded-full text-sm font-medium ${colors[status]}`}>
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  )
}

interface LoadingProps {
  message?: string
}

export function Loading({ message = 'Loading...' }: LoadingProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      <p className="mt-4 text-slate-400">{message}</p>
    </div>
  )
}

interface ErrorProps {
  message: string
}

export function Error({ message }: ErrorProps) {
  return (
    <div className="p-4 bg-red-900/20 border border-red-800 rounded-lg text-red-200">
      {message}
    </div>
  )
}
