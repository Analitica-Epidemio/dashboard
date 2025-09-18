/**
 * Charts Hooks using openapi-react-query
 * Proper implementation using the library's built-in hooks
 */

import { $api } from '@/lib/api/client';

/**
 * Chart filters interface
 */
export interface ChartFilters {
  grupo_id?: number;
  evento_id?: number;
  fecha_desde?: string;
  fecha_hasta?: string;
  clasificaciones?: string[];
}

/**
 * Hook for dashboard charts
 */
export function useDashboardCharts(filters?: ChartFilters) {
  return $api.useQuery(
    'get',
    '/api/v1/charts/dashboard',
    {
      params: {
        query: filters,
      },
    },
    {
      staleTime: 2 * 60 * 1000,
    }
  );
}

/**
 * Hook for dashboard indicators
 */
export function useIndicadores(filters?: ChartFilters) {
  return $api.useQuery(
    'get',
    '/api/v1/charts/indicadores',
    {
      params: {
        query: filters,
      },
    },
    {
      staleTime: 2 * 60 * 1000,
    }
  );
}

/**
 * Hook for available charts
 */
export function useChartsDisponibles() {
  return $api.useQuery(
    'get',
    '/api/v1/charts/disponibles',
    undefined,
    {
      staleTime: 10 * 60 * 1000,
    }
  );
}