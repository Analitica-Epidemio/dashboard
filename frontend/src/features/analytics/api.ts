/**
 * Analytics API - Types and hooks for analytics endpoints
 */

import { $api, apiClient } from '@/lib/api/client';
import { useMutation } from '@tanstack/react-query';
import type { components } from '@/lib/api/types';

// Legacy types
export type PeriodType = components["schemas"]["PeriodType"];
export type ComparisonType = components["schemas"]["ComparisonType"];
export type PeriodInfo = components["schemas"]["PeriodInfo"];
export type MetricValue = components["schemas"]["MetricValue"];
export type CasosMetrics = components["schemas"]["CasosMetrics"];
export type CoberturaMetrics = components["schemas"]["CoberturaMetrics"];
export type PerformanceMetrics = components["schemas"]["PerformanceMetrics"];
export type AnalyticsResponse = components["schemas"]["AnalyticsResponse"];
export type TopWinnerLoser = components["schemas"]["TopWinnerLoser"];
export type TopWinnersLosersResponse = components["schemas"]["TopWinnersLosersResponse"];

export interface AnalyticsFilters {
  period_type?: PeriodType;
  fecha_desde?: string;
  fecha_hasta?: string;
  comparison_type?: ComparisonType;
  fecha_referencia?: string;
  grupo_id?: number;
  tipo_eno_ids?: number[];
  clasificaciones?: string[];
  provincia_id?: number;
}

export interface TopWinnersLosersFilters extends AnalyticsFilters {
  metric_type?: "departamentos" | "tipo_eno" | "provincias";
  limit?: number;
}

// New types for bulletin generation
export type TopChangesByGroupResponse = components['schemas']['SuccessResponse_TopChangesByGroupResponse_'];
export type CalculateChangesRequest = components['schemas']['CalculateChangesRequest'];
export type CalculateChangesResponse = components['schemas']['SuccessResponse_CalculateChangesResponse_'];
export type EventoDetailsResponse = components['schemas']['SuccessResponse_EventoDetailsResponse_'];
export type GenerateDraftRequest = components['schemas']['GenerateDraftRequest'];
export type GenerateDraftResponse = components['schemas']['SuccessResponse_GenerateDraftResponse_'];

export type EventoCambio = components['schemas']['EventoCambio'];

// ============================================================================
// QUERY HOOKS - Analytics data
// ============================================================================

/**
 * Fetch top changes by epidemiological group
 */
export function useTopChangesByGroup(params: {
  semana_actual: number;
  anio_actual: number;
  num_semanas?: number;
  limit?: number;
}) {
  return $api.useQuery(
    'get',
    '/api/v1/analytics/top-changes-by-group',
    {
      params: {
        query: {
          semana_actual: params.semana_actual,
          anio_actual: params.anio_actual,
          num_semanas: params.num_semanas || 4,
          limit: params.limit || 10,
        },
      },
    },
    {
      enabled: !!params.semana_actual && !!params.anio_actual,
    }
  );
}

/**
 * Fetch event details
 */
export function useEventoDetails(params: {
  tipo_eno_id: number;
  semana_actual: number;
  anio_actual: number;
  num_semanas?: number;
}) {
  return $api.useQuery(
    'get',
    '/api/v1/analytics/evento-details/{tipo_eno_id}',
    {
      params: {
        path: {
          tipo_eno_id: params.tipo_eno_id,
        },
        query: {
          semana_actual: params.semana_actual,
          anio_actual: params.anio_actual,
          num_semanas: params.num_semanas || 4,
        },
      },
    },
    {
      enabled: !!params.tipo_eno_id && !!params.semana_actual && !!params.anio_actual,
    }
  );
}

// ============================================================================
// MUTATION HOOKS - Analytics actions
// ============================================================================

/**
 * Calculate changes for custom selected events
 */
export function useCalculateChanges() {
  return useMutation({
    mutationFn: async (request: CalculateChangesRequest) => {
      const response = await apiClient.POST('/api/v1/analytics/calculate-changes', {
        body: request,
      });
      return response.data;
    },
  });
}

/**
 * Generate draft bulletin
 */
export function useGenerateDraft() {
  return useMutation({
    mutationFn: async (request: GenerateDraftRequest) => {
      const response = await apiClient.POST('/api/v1/boletines/generate-draft', {
        body: request,
      });
      return response.data;
    },
  });
}
