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
  tipo_eno_ids?: number[]; // Array of event IDs
  fecha_desde?: string;
  fecha_hasta?: string;
  clasificaciones?: string[];
  provincia_id?: number; // INDEC province code (26 = Chubut)
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