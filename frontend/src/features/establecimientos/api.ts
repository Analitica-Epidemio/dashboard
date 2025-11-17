/**
 * Establecimientos API Layer
 *
 * Semantic hooks for health establishments (establecimientos) endpoints.
 * Uses $api client internally - all types from OpenAPI schema.
 *
 * @module features/establecimientos/api
 */

import { $api } from '@/lib/api/client';
import type { components, operations } from '@/lib/api/types';

// ============================================================================
// TYPES - Re-exported from OpenAPI schema
// ============================================================================

/**
 * Establecimiento list item with event counts
 */
export type EstablecimientoListItem = components['schemas']['EstablecimientoListItem'];

/**
 * Establecimiento for map visualization
 */
export type EstablecimientoMapaItem = components['schemas']['EstablecimientoMapaItem'];

/**
 * Establecimiento without mapping to IGN
 */
export type EstablecimientoSinMapear = components['schemas']['EstablecimientoSinMapear'];

/**
 * Mapping suggestion from SNVS to IGN
 */
export type SugerenciaMapeo = components['schemas']['SugerenciaMapeo'];

/**
 * IGN establishment search result
 */
export type EstablecimientoIGNResult = components['schemas']['EstablecimientoIGNResult'];

/**
 * Mapping information between SNVS and IGN
 */
export type MapeoInfo = components['schemas']['MapeoInfo'];

/**
 * Filters for establecimientos list endpoint
 */
export type EstablecimientosFilters = operations['list_establecimientos_con_eventos_api_v1_establecimientos_get']['parameters']['query'];

/**
 * Filters for establecimientos map endpoint
 */
export type EstablecimientosMapaFilters = operations['get_establecimientos_mapa_api_v1_establecimientos_mapa_get']['parameters']['query'];

// ============================================================================
// QUERY HOOKS - Semantic wrappers over $api
// ============================================================================

/**
 * Fetch establecimientos for map visualization
 *
 * Returns geocoded health establishments to display on a map.
 *
 * @param filters - Geographic and limit filters
 * @param options - Query options (enabled, etc.)
 * @returns Query with establecimientos for map
 *
 * @example
 * ```tsx
 * const { data } = useEstablecimientosMapa({
 *   id_provincia_indec: 82,
 *   limit: 100
 * });
 * ```
 */
export function useEstablecimientosMapa(
  filters?: EstablecimientosMapaFilters,
  options?: { enabled?: boolean }
) {
  return $api.useQuery(
    'get',
    '/api/v1/establecimientos/mapa',
    {
      params: {
        query: filters,
      },
    },
    {
      enabled: options?.enabled ?? true,
    }
  );
}

/**
 * Fetch establecimientos list with event counts
 *
 * Returns paginated list of health establishments with related event statistics.
 *
 * @param filters - Pagination, ordering, and filtering options
 * @returns Query with paginated establecimientos list
 *
 * @example
 * ```tsx
 * const { data } = useEstablecimientos({
 *   page: 1,
 *   page_size: 20,
 *   order_by: 'eventos_desc',
 *   tiene_eventos: true
 * });
 * ```
 */
export function useEstablecimientos(filters?: EstablecimientosFilters) {
  return $api.useQuery(
    'get',
    '/api/v1/establecimientos',
    {
      params: {
        query: filters,
      },
    }
  );
}

/**
 * Fetch single establecimiento details
 *
 * @param idEstablecimiento - Establecimiento ID
 * @returns Query with establecimiento details
 *
 * @example
 * ```tsx
 * const { data } = useEstablecimiento(123);
 * ```
 */
export function useEstablecimiento(idEstablecimiento: number) {
  return $api.useQuery(
    'get',
    '/api/v1/establecimientos/{id_establecimiento}',
    {
      params: {
        path: { id_establecimiento: idEstablecimiento },
      },
    },
    {
      enabled: !!idEstablecimiento,
    }
  );
}

/**
 * Fetch establecimientos without SNVS → IGN mapping
 *
 * Returns SNVS establishments that haven't been mapped to IGN,
 * with automatic suggestions prioritized by impact (event count).
 *
 * @param options - Filters and query options
 * @returns Query with unmapped establecimientos and suggestions
 *
 * @example
 * ```tsx
 * const { data } = useEstablecimientosSinMapear({
 *   limit: 50,
 *   con_eventos_solo: true,
 *   incluir_sugerencias: true
 * });
 * ```
 */
export function useEstablecimientosSinMapear(options?: {
  limit?: number;
  offset?: number;
  con_eventos_solo?: boolean;
  incluir_sugerencias?: boolean;
  enabled?: boolean;
}) {
  const { enabled = true, ...filters } = options || {};

  return $api.useQuery(
    'get',
    '/api/v1/establecimientos/sin-mapear',
    {
      params: {
        query: filters,
      },
    },
    {
      enabled,
    }
  );
}

/**
 * Search IGN establishments by name or REFES code
 *
 * @param options - Search query and geographic filters
 * @returns Query with IGN search results
 *
 * @example
 * ```tsx
 * const { data } = useBuscarEstablecimientosIGN({
 *   q: 'Hospital',
 *   provincia: 'Salta',
 *   page: 1,
 *   page_size: 20
 * });
 * ```
 */
export function useBuscarEstablecimientosIGN(options?: {
  q?: string;
  provincia?: string;
  departamento?: string;
  page?: number;
  page_size?: number;
  enabled?: boolean;
}) {
  const { enabled = true, ...filters } = options || {};

  return $api.useQuery(
    'get',
    '/api/v1/establecimientos/ign/buscar',
    {
      params: {
        query: filters,
      },
    },
    {
      enabled: enabled && (!!filters.q || !!filters.provincia || !!filters.departamento),
    }
  );
}

/**
 * Fetch existing SNVS → IGN establishment mappings
 *
 * @param options - Filters for mappings (confidence, validation status, etc.)
 * @returns Query with existing mappings
 *
 * @example
 * ```tsx
 * const { data } = useMapeosEstablecimientos({
 *   confianza: 'HIGH',
 *   validados_solo: true,
 *   page: 1
 * });
 * ```
 */
export function useMapeosEstablecimientos(options?: {
  page?: number;
  page_size?: number;
  confianza?: string;
  validados_solo?: boolean;
  manuales_solo?: boolean;
  enabled?: boolean;
}) {
  const { enabled = true, ...filters } = options || {};

  return $api.useQuery(
    'get',
    '/api/v1/establecimientos/mapeos',
    {
      params: {
        query: filters,
      },
    },
    {
      enabled,
    }
  );
}

// ============================================================================
// MUTATION HOOKS - Create, Update, Delete operations
// ============================================================================

/**
 * Create SNVS → IGN establishment mapping
 *
 * @returns Mutation to create a new establishment mapping
 *
 * @example
 * ```tsx
 * const createMapeo = useCrearMapeoEstablecimiento();
 *
 * await createMapeo.mutateAsync({
 *   body: {
 *     id_establecimiento_snvs: 123,
 *     id_establecimiento_ign: 456,
 *     razon: 'Manual mapping - verified by admin'
 *   }
 * });
 * ```
 */
export function useCrearMapeoEstablecimiento() {
  return $api.useMutation('post', '/api/v1/establecimientos/mapeos');
}

/**
 * Update existing SNVS → IGN establishment mapping
 *
 * @returns Mutation to update an establishment mapping
 *
 * @example
 * ```tsx
 * const updateMapeo = useActualizarMapeoEstablecimiento();
 *
 * await updateMapeo.mutateAsync({
 *   params: { path: { id_establecimiento_snvs: 123 } },
 *   body: {
 *     id_establecimiento_ign_nuevo: 789,
 *     razon: 'Corrected mapping'
 *   }
 * });
 * ```
 */
export function useActualizarMapeoEstablecimiento() {
  return $api.useMutation('put', '/api/v1/establecimientos/mapeos/{id_establecimiento_snvs}');
}

/**
 * Delete SNVS → IGN establishment mapping (unlink)
 *
 * @returns Mutation to delete an establishment mapping
 *
 * @example
 * ```tsx
 * const deleteMapeo = useEliminarMapeoEstablecimiento();
 *
 * await deleteMapeo.mutateAsync({
 *   params: { path: { id_establecimiento_snvs: 123 } }
 * });
 * ```
 */
export function useEliminarMapeoEstablecimiento() {
  return $api.useMutation('delete', '/api/v1/establecimientos/mapeos/{id_establecimiento_snvs}');
}

/**
 * Accept multiple establishment mapping suggestions in bulk
 *
 * Creates multiple SNVS → IGN mappings at once from automatic suggestions.
 *
 * @returns Mutation to create multiple establishment mappings
 *
 * @example
 * ```tsx
 * const acceptBulk = useAceptarMapeosEstablecimientosBulk();
 *
 * await acceptBulk.mutateAsync({
 *   body: {
 *     mapeos: [
 *       { id_establecimiento_snvs: 1, id_establecimiento_ign: 10 },
 *       { id_establecimiento_snvs: 2, id_establecimiento_ign: 20 },
 *     ]
 *   }
 * });
 * ```
 */
export function useAceptarMapeosEstablecimientosBulk() {
  return $api.useMutation('post', '/api/v1/establecimientos/mapeos/bulk');
}
