import axios from 'axios'

export const API_BASE_URL =
  import.meta.env.VITE_API_URL || 'http://localhost:8000'
let runtimeToken = import.meta.env.VITE_API_TOKEN || ''

export function setApiAuthToken(token: string | null): void {
  runtimeToken = token || ''
}

export function buildGovernanceStreamUrl(symbol?: string): string {
  const url = new URL('/api/v1/governance/stream', API_BASE_URL)
  if (symbol) {
    url.searchParams.set('symbol', symbol)
  }
  url.searchParams.set('interval_seconds', '5')
  return url.toString()
}

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

apiClient.interceptors.request.use((config) => {
  if (runtimeToken) {
    config.headers.Authorization = `Bearer ${runtimeToken}`
  }
  return config
})

export interface HealthResponse {
  status: string
  version: string
}

export interface WorkflowResponse {
  success: boolean
  ai_review_packet_path?: string
  weekly_report_path?: string
  promoted_config_path?: string
  error?: string
  details: string[]
}

export interface GovernanceSummary {
  total: number
  pending: number
  approved: number
  rejected: number
  ready_to_promote: number
}

export interface RequestRecord {
  request_id: string
  status: string
  is_valid?: boolean
  promoted: boolean
  symbol?: string
}

export interface SymbolInfo {
  symbol: string
  total_requests: number
  pending: number
  approved: number
  rejected: number
  ready_to_promote: number
}

export interface ServiceConnectionStatus {
  enabled: boolean
  configured: boolean
  reachable: boolean
  detail: string
}

export interface ConfigConnections {
  postgres: ServiceConnectionStatus
  redis: ServiceConnectionStatus
}

export interface ExchangeConnection {
  provider: string
  enabled: boolean
  configured: boolean
  reachable: boolean
  detail: string
  server_time?: string
}

export interface ExchangeAccountConnection {
  provider: string
  enabled: boolean
  configured: boolean
  reachable: boolean
  detail: string
  account_type?: string
}

export interface AIAnalystConnection {
  provider: string
  enabled: boolean
  configured: boolean
  reachable: boolean
  detail: string
}

export interface AuthLoginResponse {
  access_token: string
  token_type: string
  username: string
  role: 'viewer' | 'operator' | 'admin'
}

export interface AuthMeResponse {
  username: string
  role: 'viewer' | 'operator' | 'admin'
  auth_source: string
}

export const api = {
  login: (username: string, password: string) =>
    apiClient.post<AuthLoginResponse>('/api/v1/auth/login', {
      username,
      password,
    }),

  me: () =>
    apiClient.get<AuthMeResponse>('/api/v1/auth/me'),

  health: () => apiClient.get<HealthResponse>('/health'),
  
  triggerWorkflow: (symbol?: string) => 
    apiClient.post<WorkflowResponse>('/api/v1/weekly-workflow', null, {
      params: { symbol }
    }),
  
  getGovernanceSummary: (symbol?: string) =>
    apiClient.get<GovernanceSummary>('/api/v1/governance/summary', {
      params: { symbol }
    }),
  
  getRequests: (symbol?: string) =>
    apiClient.get<RequestRecord[]>('/api/v1/governance/requests', {
      params: { symbol }
    }),
  
  getSymbols: (refresh = false) =>
    apiClient.get<SymbolInfo[]>('/api/v1/symbols', {
      params: { refresh }
    }),

  getConnections: () =>
    apiClient.get<ConfigConnections>('/api/v1/config/connections'),

  getExchangeConnection: () =>
    apiClient.get<ExchangeConnection>('/api/v1/config/exchange'),

  getExchangeAccountConnection: () =>
    apiClient.get<ExchangeAccountConnection>('/api/v1/config/exchange/account'),

  getAiAnalystConnection: () =>
    apiClient.get<AIAnalystConnection>('/api/v1/config/ai-analyst'),
  
  approveRequest: (requestId: string, status: string) =>
    apiClient.post('/api/v1/governance/approve', {
      request_id: requestId,
      status
    }),
  
  promoteRequests: () =>
    apiClient.post('/api/v1/governance/promote'),
}
