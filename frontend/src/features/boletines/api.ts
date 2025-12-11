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
 * Update static content template (TipTap JSON)
 *
 * @returns Mutation for updating static content
 *
 * @example
 * ```tsx
 * const updateMutation = useUpdateStaticContent();
 * await updateMutation.mutateAsync({
 *   body: { content: { type: "doc", content: [...] } }
 * });
 * ```
 */
export function useUpdateStaticContent() {
  return $api.useMutation('put', '/api/v1/boletines/config/static-content');
}

// NOTE: Dynamic blocks endpoints removed - now using BoletinSeccion/BoletinBloque
// database models managed via BloqueQueryAdapter. See backend/app/domains/boletines/

/**
 * Update unified boletin template (content + embedded dynamic blocks)
 * Uses the static content endpoint but stores the full unified structure
 *
 * @returns Mutation for updating unified content
 *
 * @example
 * ```tsx
 * const updateMutation = useUpdateBoletinTemplate();
 * await updateMutation.mutateAsync({
 *   body: { unified_content: { type: "doc", content: [...] } }
 * });
 * ```
 */
export function useUpdateBoletinTemplate() {
  // For now, we reuse the static content endpoint
  // The unified_content will be stored as static_content_template
  // and dynamic blocks will be extracted from it on the backend
  return $api.useMutation('put', '/api/v1/boletines/config/static-content');
}

/**
 * Update event section template (TipTap JSON that repeats for each event)
 *
 * @returns Mutation for updating event section template
 *
 * @example
 * ```tsx
 * const updateMutation = useUpdateEventSectionTemplate();
 * await updateMutation.mutateAsync({
 *   body: { content: { type: "doc", content: [...] } }
 * });
 * ```
 */
export function useUpdateEventSectionTemplate() {
  return $api.useMutation('put', '/api/v1/boletines/config/event-section-template');
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
  return $api.useQuery('get', '/api/v1/boletines/charts-disponibles');
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
