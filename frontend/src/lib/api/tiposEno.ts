/**
 * API hooks para gestión de tipos ENO
 */

import { $api } from './client'
import type { components } from './types'

// Query keys para react-query
export const tiposEnoKeys = {
  all: ['tiposEno'] as const,
  lists: () => [...tiposEnoKeys.all, 'list'] as const,
  list: (filters: Record<string, unknown> = {}) => [...tiposEnoKeys.lists(), filters] as const,
  byGroup: (groupId: number) => [...tiposEnoKeys.all, 'byGroup', groupId] as const,
  details: () => [...tiposEnoKeys.all, 'detail'] as const,
  detail: (id: number) => [...tiposEnoKeys.details(), id] as const,
}

// Tipos de filtros
export interface TipoEnoFilters {
  page?: number
  per_page?: number
  nombre?: string
  grupo_id?: number
  grupos?: number[]
}

// Hooks para consultas
export function useTiposEno(filters: TipoEnoFilters = {}) {
  const { page = 1, per_page = 20, ...restFilters } = filters

  return $api.useQuery(
    'get',
    '/api/v1/tiposEno/',
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

// Hook para obtener tipos ENO filtrados por grupo
export function useTiposEnoByGrupo(grupoId: number | null, filters: Omit<TipoEnoFilters, 'grupo_id'> = {}) {
  const { page = 1, per_page = 100, ...restFilters } = filters

  return $api.useQuery(
    'get',
    '/api/v1/tiposEno/',
    {
      params: {
        query: {
          page,
          per_page,
          grupo_id: grupoId,
          ...restFilters
        },
      },
    },
    {
      enabled: !!grupoId,
      queryKey: tiposEnoKeys.byGroup(grupoId || 0)
    }
  )
}

// Hook para obtener tipos ENO por múltiples grupos
export function useTiposEnoByGrupos(grupoIds: number[], filters: Omit<TipoEnoFilters, 'grupos'> = {}) {
  const { page = 1, per_page = 100, ...restFilters } = filters

  return $api.useQuery(
    'get',
    '/api/v1/tiposEno/',
    {
      params: {
        query: {
          page,
          per_page,
          grupos: grupoIds,
          ...restFilters
        },
      },
    },
    {
      enabled: grupoIds.length > 0
    }
  )
}

// Type guard para la respuesta paginada
type TipoEnoResponse = components['schemas']['PaginatedResponse_TipoEnoInfo_']

// Helper para extraer datos de respuesta exitosa
export function extractTiposEnoData(response: unknown): any[] | null {
  // La respuesta viene como { data: [...], meta: {...}, links: {...} }
  const res = response as { data?: any[] };
  if (res?.data && Array.isArray(res.data)) {
    return res.data;
  }
  return null;
}