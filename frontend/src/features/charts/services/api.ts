/**
 * API hooks para la nueva arquitectura Browse-First de charts
 */

import { $api } from '@/lib/api/client'

/**
 * Hook para obtener todos los templates de charts
 * Browse-First: Muestra todos inmediatamente
 */
export function useChartTemplates() {
  return $api.useQuery('get', '/api/v1/charts/templates')
}

/**
 * Hook para obtener filtros disponibles globalmente
 */
export function useAvailableFilters() {
  return $api.useQuery('get', '/api/v1/charts/filters')
}

/**
 * Hook para obtener información completa de disponibilidad
 */
export function useChartAvailability(tipoEnoCodigo?: string) {
  return $api.useQuery('get', '/api/v1/charts/availability', {
    params: {
      query: tipoEnoCodigo ? { tipo_eno_codigo: tipoEnoCodigo } : {}
    }
  })
}

/**
 * Función para ejecutar un chart (no hook, se usa directamente)
 */
export async function executeChart(request: {
  chart_codigo: string
  filtros?: Record<string, any>
  parametros?: Record<string, any>
  usar_cache?: boolean
}) {
  const response = await fetch('/api/v1/charts/execute', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      chart_codigo: request.chart_codigo,
      filtros: request.filtros || {},
      parametros: request.parametros || {},
      usar_cache: request.usar_cache ?? true,
      formato_respuesta: 'json'
    })
  })

  if (!response.ok) {
    throw new Error(`Error ejecutando chart: ${response.statusText}`)
  }

  return response.json()
}