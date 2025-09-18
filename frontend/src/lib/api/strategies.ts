import { $api } from './client'

// Types
export interface EventStrategy {
  id: number
  tipo_evento_id: number
  tipo_evento_nombre?: string
  strategy_config: {
    condition: string
    value: any
  }
  is_active: boolean
  created_at: string
  updated_at: string
  created_by?: string
  updated_by?: string
}

export interface AuditLogEntry {
  id: number
  strategy_id: number
  action: string
  timestamp: string
  user?: string
  details?: any
}

// Helper function to extract data from API responses
export const extractSuccessData = <T>(response: { data?: T; success?: boolean } | undefined): T | null => {
  if (!response) return null
  return response.data || null
}

// Hooks using $api directly
export const useStrategies = () => {
  return $api.useQuery('get', '/api/v1/estrategias/')
}

export const useStrategy = (strategyId: number | null) => {
  return $api.useQuery('get', '/api/v1/estrategias/{strategy_id}', {
    params: {
      path: {
        strategy_id: strategyId!
      }
    },
    enabled: !!strategyId
  })
}

export const useCreateStrategy = () => {
  return $api.useMutation('post', '/api/v1/estrategias/')
}

export const useUpdateStrategy = () => {
  return $api.useMutation('put', '/api/v1/estrategias/{strategy_id}')
}

export const useDeleteStrategy = () => {
  return $api.useMutation('delete', '/api/v1/estrategias/{strategy_id}')
}

export const useActivateStrategy = () => {
  return $api.useMutation('post', '/api/v1/estrategias/{strategy_id}/activate')
}

export const useTestStrategy = () => {
  return $api.useMutation('post', '/api/v1/estrategias/{strategy_id}/test')
}
