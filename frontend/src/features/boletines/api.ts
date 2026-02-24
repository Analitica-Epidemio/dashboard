/**
 * Boletines API Layer
 *
 * Semantic hooks for boletin template configuration endpoints.
 * Uses $api client internally - all types from OpenAPI schema.
 *
 * @module features/boletines/api
 */

import { $api } from '@/lib/api/client';
import type { components } from '@/lib/api/types';

// ============================================================================
// TYPES - Re-exported from OpenAPI schema
// ============================================================================

/**
 * Boletin template configuration response
 */
export type BoletinTemplateConfigResponse = components['schemas']['BoletinTemplateConfigResponse'];

// ============================================================================
// QUERY HOOKS - Semantic wrappers over $api
// ============================================================================

/**
 * Fetch boletin template configuration (singleton id=1)
 *
 * @returns Query with template configuration
 *
 * @example
 * ```tsx
 * const { data } = useBoletinTemplateConfig();
 * ```
 */
export function useBoletinTemplateConfig() {
  return $api.useQuery('get', '/api/v1/boletines/config');
}

// ============================================================================
// MUTATION HOOKS - Create, Update, Delete operations
// ============================================================================

/**
 * Update unified boletin template (static content as TipTap JSON)
 */
export function useUpdateBoletinTemplate() {
  return $api.useMutation('put', '/api/v1/boletines/config/static-content');
}

/**
 * Update event section template (TipTap JSON that repeats for each event)
 */
export function useUpdateEventSectionTemplate() {
  return $api.useMutation('put', '/api/v1/boletines/config/event-section-template');
}

/**
 * Update boletin metadata (institution, authorities, logo, etc.)
 */
export function useUpdateBoletinMetadata() {
  return $api.useMutation('put', '/api/v1/boletines/config/metadata');
}

/**
 * Fetch secciones configuration (all sections with their blocks)
 */
export function useSeccionesConfig() {
  return $api.useQuery('get', '/api/v1/boletines/secciones-config');
}

/**
 * Update secciones order and active state
 */
export function useUpdateSeccionesOrder() {
  return $api.useMutation('patch', '/api/v1/boletines/secciones-config');
}

/**
 * Fetch available charts for boletin chart selector
 *
 * @returns Query with available charts configuration
 *
 * @example
 * ```tsx
 * const { data } = useChartsDisponibles();
 * const charts = data?.data?.charts || [];
 * ```
 */
export function useChartsDisponibles() {
  return $api.useQuery('get', '/api/v1/boletines/charts-disponibles', {});
}

// ============================================================================
// PREVIEW HOOKS - Para el generador de boletines
// ============================================================================

/**
 * Fetch preview de datos para un evento específico
 *
 * @param codigo - Código del TipoEno o GrupoEno
 * @param semana - Semana epidemiológica
 * @param anio - Año
 * @param numSemanas - Cantidad de semanas a analizar
 * @param enabled - Si el query debe ejecutarse
 *
 * @example
 * ```tsx
 * const { data } = useEventoPreview({
 *   codigo: "ETI",
 *   semana: 40,
 *   anio: 2025,
 *   numSemanas: 4,
 * });
 * ```
 */
export function useEventoPreview({
  codigo,
  semana,
  anio,
  numSemanas,
  enabled = true,
}: {
  codigo: string;
  semana: number;
  anio: number;
  numSemanas: number;
  enabled?: boolean;
}) {
  return $api.useQuery(
    'get',
    '/api/v1/boletines/preview/evento',
    {
      params: {
        query: {
          codigo,
          semana,
          anio,
          num_semanas: numSemanas,
        },
      },
    },
    {
      enabled: enabled && !!codigo,
    }
  );
}

/**
 * Fetch lista de eventos disponibles para preview
 *
 * @returns Query con lista de TipoEno y GrupoEno con código
 *
 * @example
 * ```tsx
 * const { data } = useEventosDisponibles();
 * const eventos = data?.data || [];
 * ```
 */
export function useEventosDisponibles() {
  return $api.useQuery('get', '/api/v1/boletines/preview/eventos-disponibles');
}

/**
 * Fetch lista de agentes etiológicos disponibles
 *
 * @returns Query con lista de agentes activos
 *
 * @example
 * ```tsx
 * const { data } = useAgentesDisponibles();
 * const agentes = data?.data || [];
 * ```
 */
export function useAgentesDisponibles() {
  return $api.useQuery('get', '/api/v1/boletines/preview/agentes-disponibles');
}
