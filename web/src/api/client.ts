import axios from 'axios'

const API_BASE_URL =
  import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
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

export const api = {
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
  
  getSymbols: () =>
    apiClient.get<SymbolInfo[]>('/api/v1/symbols'),
  
  approveRequest: (requestId: string, status: string) =>
    apiClient.post('/api/v1/governance/approve', {
      request_id: requestId,
      status
    }),
  
  promoteRequests: () =>
    apiClient.post('/api/v1/governance/promote'),
}
