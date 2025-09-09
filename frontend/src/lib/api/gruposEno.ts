/**
 * API hooks para gestión de grupos ENO
 */

import { $api } from './client'
import type { components } from './types'

// Query keys para react-query
export const gruposEnoKeys = {
  all: ['gruposEno'] as const,
  lists: () => [...gruposEnoKeys.all, 'list'] as const,
  list: (filters: Record<string, unknown> = {}) => [...gruposEnoKeys.lists(), filters] as const,
  details: () => [...gruposEnoKeys.all, 'detail'] as const,
  detail: (id: number) => [...gruposEnoKeys.details(), id] as const,
}

// Tipos de filtros
export interface GrupoEnoFilters {
  page?: number
  per_page?: number
  nombre?: string
}

// Hooks para consultas
export function useGruposEno(filters: GrupoEnoFilters = {}) {
  const { page = 1, per_page = 20, ...restFilters } = filters

  return $api.useQuery(
    'get',
    '/api/v1/gruposEno/',
    {
      params: {
        query: {
          page,
          per_page,
          ...restFilters
        },
      },
    },
  )
}

// Type guard para la respuesta paginada
type GrupoEnoResponse = components['schemas']['PaginatedResponse_GrupoEnoInfo_']

// Helper para extraer datos de respuesta exitosa
export function extractGruposEnoData(response: unknown): GrupoEnoResponse | null {
  const res = response as { data?: GrupoEnoResponse }
  if (!res?.data) return null
  return res.data
}