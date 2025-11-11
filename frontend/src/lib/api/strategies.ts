import { $api } from './client'
import { paths } from './types';

// Types
export type EventStrategy = paths['/api/v1/estrategias/{strategy_id}']['get']['responses']['200']['content']['application/json']['data'];

// Helper function to extract data from API responses
export const extractSuccessData = <T>(response: { data?: T; success?: boolean } | undefined): T | null => {
  if (!response) return null
  return response.data || null
}

// Hooks using $api directly
export const useStrategies = (params?: { page?: number; page_size?: number; active_only?: boolean; tipo_eno_id?: number }) => {
  return $api.useQuery('get', '/api/v1/estrategias/', {
    params: {
      query: params || {}
    }
  })
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
