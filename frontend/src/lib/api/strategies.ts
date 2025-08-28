/**
 * API hooks para gestión de estrategias de clasificación
 */

import { useQueryClient } from '@tanstack/react-query'
import { $api } from './client'
import type { components } from './types'

// Tipos extraídos del schema OpenAPI generado
export type EventStrategy = components['schemas']['EventStrategyResponse']
export type EventStrategyCreate = components['schemas']['EventStrategyCreate']
export type EventStrategyUpdate = components['schemas']['EventStrategyUpdate']
export type ClassificationRule = components['schemas']['ClassificationRuleResponse']
export type FilterCondition = components['schemas']['FilterConditionResponse']
export type StrategyTestRequest = components['schemas']['StrategyTestRequest']
export type StrategyTestResponse = components['schemas']['StrategyTestResponse']
export type AuditLogEntry = components['schemas']['AuditLogResponse']

// Query keys para react-query
const strategiesKeys = {
  all: ['strategies'] as const,
  lists: () => [...strategiesKeys.all, 'list'] as const,
  list: (filters: Record<string, unknown> = {}) => [...strategiesKeys.lists(), filters] as const,
  details: () => [...strategiesKeys.all, 'detail'] as const,
  detail: (id: number) => [...strategiesKeys.details(), id] as const,
  audit: (id: number) => [...strategiesKeys.detail(id), 'audit'] as const,
}

// Hooks para consultas
export function useStrategies(filters?: { active_only?: boolean; tipo_eno_id?: number }) {
  return $api.useQuery(
    'get',
    '/api/v1/estrategias/',
    {
      params: {
        query: filters || {},
      },
    },
  )
}

export function useStrategy(strategyId: number) {
  return $api.useQuery(
    'get',
    '/api/v1/estrategias/{strategy_id}',
    {
      params: {
        path: {
          strategy_id: strategyId,
        },
      },
    },
    {
      queryKey: strategiesKeys.detail(strategyId),
      enabled: !!strategyId && strategyId > 0,
    }
  )
}

export function useStrategyAuditLog(strategyId: number, limit = 50) {
  return $api.useQuery(
    'get',
    '/api/v1/estrategias/{strategy_id}/audit',
    {
      params: {
        path: {
          strategy_id: strategyId,
        },
        query: {
          limit,
        },
      },
    },
    {
      queryKey: strategiesKeys.audit(strategyId),
      enabled: !!strategyId && strategyId > 0,
    }
  )
}

// Hooks para mutaciones
export function useCreateStrategy() {
  const queryClient = useQueryClient()

  return $api.useMutation(
    'post',
    '/api/v1/estrategias/',
    {
      onSuccess: (data) => {
        // Invalidar queries relacionadas
        queryClient.invalidateQueries({ queryKey: strategiesKeys.lists() })
        // Actualizar cache de la estrategia específica
        if (data?.data?.id) {
          queryClient.setQueryData(strategiesKeys.detail(data.data.id), data)
        }
      },
    }
  )
}

export function useUpdateStrategy() {
  const queryClient = useQueryClient()

  return $api.useMutation(
    'put',
    '/api/v1/estrategias/{strategy_id}',
    {
      onSuccess: (data, { params }) => {
        const strategyId = params?.path?.strategy_id
        if (strategyId && data?.data) {
          // Actualizar cache específico
          queryClient.setQueryData(strategiesKeys.detail(strategyId), data)
          // Invalidar listas para refrescar
          queryClient.invalidateQueries({ queryKey: strategiesKeys.lists() })
        }
      },
    }
  )
}

export function useDeleteStrategy() {
  const queryClient = useQueryClient()

  return $api.useMutation(
    'delete',
    '/api/v1/estrategias/{strategy_id}',
    {
      onSuccess: (_, { params }) => {
        const strategyId = params?.path?.strategy_id
        if (strategyId) {
          // Remover de cache específico
          queryClient.removeQueries({ queryKey: strategiesKeys.detail(strategyId) })
          // Invalidar listas
          queryClient.invalidateQueries({ queryKey: strategiesKeys.lists() })
        }
      },
    }
  )
}

export function useActivateStrategy() {
  const queryClient = useQueryClient()

  return $api.useMutation(
    'post',
    '/api/v1/estrategias/{strategy_id}/activate',
    {
      onSuccess: (data, { params }) => {
        const strategyId = params?.path?.strategy_id
        if (strategyId && data?.data) {
          // Actualizar cache específico
          queryClient.setQueryData(strategiesKeys.detail(strategyId), data)
          // Invalidar todas las listas porque la activación puede afectar otras estrategias
          queryClient.invalidateQueries({ queryKey: strategiesKeys.lists() })
        }
      },
    }
  )
}

export function useTestStrategy() {
  return $api.useMutation('post', '/api/v1/estrategias/{strategy_id}/test')
}

// Utilidades
export function getStrategyStatusLabel(status: EventStrategy['status']) {
  const labels: Record<string, string> = {
    active: 'Activa',
    draft: 'Borrador',
    pending_review: 'Pendiente de Revisión'
  }
  return labels[status] || status
}

export function getStrategyStatusVariant(status: EventStrategy['status']) {
  const variants: Record<string, 'default' | 'secondary' | 'outline'> = {
    active: 'default' as const,
    draft: 'secondary' as const,
    pending_review: 'outline' as const
  }
  return variants[status] || 'outline' as const
}

export function isStrategyEditable(strategy: EventStrategy): boolean {
  return !strategy.active || strategy.status === 'draft'
}

export function canActivateStrategy(strategy: EventStrategy): boolean {
  return !strategy.active && strategy.classification_rules.length > 0
}

// Helper para extraer datos de respuesta exitosa
export function extractSuccessData<T>(response: any): T | null {
  // La respuesta del API viene envuelta en SuccessResponse con estructura { data: T, meta?: any }
  // Pero el hook ya retorna el contenido completo, necesitamos acceder a response.data.data
  if (!response) return null
  
  // Si la respuesta tiene la estructura SuccessResponse
  if (response?.data?.data !== undefined) {
    return response.data.data
  }
  
  // Si la respuesta ya es el data directo (para compatibilidad)
  if (response?.data !== undefined) {
    return response.data
  }
  
  return null
}

// Helper para manejar errores de API
export function getApiErrorMessage(error: unknown): string {
  if (error && typeof error === 'object') {
    if ('error' in error && error.error && typeof error.error === 'object' && 'message' in error.error) {
      return String(error.error.message)
    }
    if ('message' in error) {
      return String(error.message)
    }
  }
  return 'Error desconocido'
}