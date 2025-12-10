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
export type EventoDetailsResponse = components["schemas"]["SuccessResponse_CasoEpidemiologicoDetailsResponse_"];
export type GenerateDraftRequest = components['schemas']['GenerateDraftRequest'];
export type GenerateDraftResponse = components['schemas']['SuccessResponse_GenerateDraftResponse_'];

export type EventoCambio = components["schemas"]["CasoEpidemiologicoCambio"];

// ============================================================================
// Local types for analytics cards (not in OpenAPI)
// These match the actual data structure used by the components
// ============================================================================

export interface AgenteSemanaData {
  agente_nombre: string;
  semana_epidemiologica: number;
  positivas: number;
  estudiadas: number;
}

export interface AgenteEdadData {
  agente_nombre: string;
  grupo_etario: string;
  positivas: number;
}

export interface CorredorEndemicoData {
  semana_epidemiologica: number;
  valor_actual: number;
  zona_exito: number;
  zona_seguridad: number;
  zona_alerta: number;
  zona_brote: number;
  corredor_valido: boolean;
}

export interface OcupacionCamasData {
  establecimiento_nombre: string;
  semana_epidemiologica: number;
  camas_ira: number;
  camas_uti: number;
}

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

// ============================================================================
// SECCIONES CONFIG - Para mostrar qué datos se van a generar
// ============================================================================

// Types from OpenAPI
export type RangoTemporalInfo = components["schemas"]["RangoTemporalInfo"];
export type BloqueConfigResponse = components["schemas"]["BloqueConfigResponse"];
export type SeccionConfigResponse = components["schemas"]["SeccionConfigResponse"];
export type SeccionesConfigResponse = components["schemas"]["SeccionesConfigResponse"];

// Aliases for backwards compatibility
export type BloqueConfig = BloqueConfigResponse;
export type SeccionConfig = SeccionConfigResponse;

/**
 * Fetch secciones configuration with temporal ranges info
 */
export function useSeccionesConfig(params: {
  semana: number;
  anio: number;
}) {
  return $api.useQuery(
    'get',
    '/api/v1/boletines/secciones-config',
    {
      params: {
        query: {
          semana: params.semana,
          anio: params.anio,
        },
      },
    },
    {
      enabled: !!params.semana && !!params.anio,
    }
  );
}

// ============================================================================
// NOTA: Los datos de vigilancia agregada (CLI_P26, LAB_P26, CLI_P26_INT) se
// consultan directamente via POST /api/v1/metricas/query usando MetricService.
// Ver /app/dashboard/analytics/page.tsx para ejemplos de uso.
// ============================================================================
