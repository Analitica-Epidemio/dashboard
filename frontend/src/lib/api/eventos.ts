/**
 * API hooks para gestión de eventos epidemiológicos
 */

import { $api } from './client'
import type { components } from './types'
import { TipoClasificacion } from '../types/clasificacion'

// Query keys para react-query
const eventosKeys = {
  all: ['eventos'] as const,
  lists: () => [...eventosKeys.all, 'list'] as const,
  list: (filters: Record<string, unknown> = {}) => [...eventosKeys.lists(), filters] as const,
  details: () => [...eventosKeys.all, 'detail'] as const,
  detail: (id: number) => [...eventosKeys.details(), id] as const,
  timeline: (id: number) => [...eventosKeys.detail(id), 'timeline'] as const,
}

// Tipos de filtros
export interface EventoFilters {
  page?: number
  page_size?: number
  search?: string
  tipo_eno_id?: number
  fecha_desde?: string
  fecha_hasta?: string
  clasificacion?: string
  es_positivo?: boolean
  provincia?: string
  tipo_sujeto?: 'humano' | 'animal' | 'desconocido'
  requiere_revision?: boolean
  sort_by?: 'fecha_desc' | 'fecha_asc' | 'id_desc' | 'id_asc' | 'tipo_eno'
}

// Hooks para consultas
export function useEventos(filters: EventoFilters = {}) {
  const { page = 1, page_size = 50, ...restFilters } = filters

  return $api.useQuery(
    'get',
    '/api/v1/eventos/',
    {
      params: {
        query: {
          page,
          page_size,
          ...restFilters
        },
      },
    },
  )
}

export function useEvento(eventoId: number) {
  return $api.useQuery(
    'get',
    '/api/v1/eventos/{evento_id}',
    {
      params: {
        path: {
          evento_id: eventoId,
        },
        query: {
          include_relations: true
        }
      },
    },
  )
}

export function useEventoTimeline(eventoId: number) {
  return $api.useQuery(
    'get',
    '/api/v1/eventos/{evento_id}/timeline',
    {
      params: {
        path: {
          evento_id: eventoId,
        },
      },
    },
  )
}

// Utilidades
export function getClasificacionLabel(clasificacion?: string | null) {
  const labels: Record<string, string> = {
    'CONFIRMADOS': 'Confirmado',
    'SOSPECHOSOS': 'Sospechoso',
    'PROBABLES': 'Probable',
    'EN_ESTUDIO': 'En Estudio',
    'NEGATIVOS': 'Negativo',
    'DESCARTADOS': 'Descartado',
    'NOTIFICADOS': 'Notificado',
    'CON_RESULTADO_MORTAL': 'Con Resultado Mortal',
    'SIN_RESULTADO_MORTAL': 'Sin Resultado Mortal',
    'REQUIERE_REVISION': 'Requiere Revisión',
    // Legacy lowercase values for backwards compatibility
    'confirmados': 'Confirmado',
    'sospechosos': 'Sospechoso',
    'probables': 'Probable',
    'en_estudio': 'En Estudio',
    'negativos': 'Negativo',
    'descartados': 'Descartado',
    'notificados': 'Notificado',
    'requiere_revision': 'Requiere Revisión'
  }
  return clasificacion ? (labels[clasificacion] || clasificacion) : 'Sin clasificar'
}

export function getClasificacionVariant(clasificacion?: string | null): 'default' | 'secondary' | 'destructive' | 'outline' {
  const variants: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
    // TipoClasificacion enum values (uppercase)
    'CONFIRMADOS': 'default',
    'SOSPECHOSOS': 'secondary', 
    'PROBABLES': 'secondary',
    'EN_ESTUDIO': 'secondary',
    'NEGATIVOS': 'outline',
    'DESCARTADOS': 'outline',
    'NOTIFICADOS': 'outline',
    'CON_RESULTADO_MORTAL': 'destructive',
    'SIN_RESULTADO_MORTAL': 'default',
    'REQUIERE_REVISION': 'destructive',
    // Legacy lowercase values for backwards compatibility
    'confirmados': 'default',
    'sospechosos': 'secondary',
    'probables': 'secondary',
    'en_estudio': 'secondary',
    'negativos': 'outline',
    'descartados': 'outline',
    'requiere_revision': 'destructive',
    'notificados': 'outline'
  }
  return clasificacion ? (variants[clasificacion] || 'outline') : 'outline'
}

export function getClasificacionEstrategiaColor(clasificacion?: string | null): string {
  const colors: Record<string, string> = {
    // TipoClasificacion enum values with distinct colors
    'CONFIRMADOS': 'bg-green-100 text-green-800 border-green-200 dark:bg-green-900 dark:text-green-100 dark:border-green-700',
    'SOSPECHOSOS': 'bg-yellow-100 text-yellow-800 border-yellow-200 dark:bg-yellow-900 dark:text-yellow-100 dark:border-yellow-700',
    'PROBABLES': 'bg-orange-100 text-orange-800 border-orange-200 dark:bg-orange-900 dark:text-orange-100 dark:border-orange-700',
    'EN_ESTUDIO': 'bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-900 dark:text-blue-100 dark:border-blue-700',
    'NEGATIVOS': 'bg-gray-100 text-gray-800 border-gray-200 dark:bg-gray-900 dark:text-gray-100 dark:border-gray-700',
    'DESCARTADOS': 'bg-gray-100 text-gray-800 border-gray-200 dark:bg-gray-900 dark:text-gray-100 dark:border-gray-700',
    'NOTIFICADOS': 'bg-indigo-100 text-indigo-800 border-indigo-200 dark:bg-indigo-900 dark:text-indigo-100 dark:border-indigo-700',
    'CON_RESULTADO_MORTAL': 'bg-red-100 text-red-800 border-red-200 dark:bg-red-900 dark:text-red-100 dark:border-red-700',
    'SIN_RESULTADO_MORTAL': 'bg-emerald-100 text-emerald-800 border-emerald-200 dark:bg-emerald-900 dark:text-emerald-100 dark:border-emerald-700',
    'REQUIERE_REVISION': 'bg-red-100 text-red-800 border-red-200 dark:bg-red-900 dark:text-red-100 dark:border-red-700',
  }
  return clasificacion ? (colors[clasificacion] || 'bg-gray-100 text-gray-600 border-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600') : 'bg-gray-100 text-gray-600 border-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600'
}

export function getTipoSujetoIcon(tipo?: string | null) {
  switch (tipo) {
    case 'humano':
      return '👤'
    case 'animal':
      return '🐾'
    default:
      return '❓'
  }
}

// Helper para extraer datos de respuesta exitosa
export function extractEventosData<T>(response: any): T | null {
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