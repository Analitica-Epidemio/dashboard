/**
 * Mapa API Layer
 *
 * Semantic hooks for map-related endpoints (domicilios and establecimientos).
 * Uses $api client internally - all types from OpenAPI schema.
 *
 * @module features/mapa/api
 */

import { $api } from '@/lib/api/client';
import type { components, operations } from '@/lib/api/types';

// ============================================================================
// TYPES - Re-exported from OpenAPI schema
// ============================================================================

/**
 * Domicilio item for map visualization
 */
export type DomicilioMapaItem = components['schemas']['DomicilioMapaItem'];

/**
 * Domicilio detail with associated cases
 */
export type DomicilioDetalleData = components['schemas']['DomicilioDetalleResponse'];

/**
 * Establecimiento detail with associated persons/events
 */
export type EstablecimientoDetalleData = components['schemas']['EstablecimientoDetalleResponse'];

/**
 * Person related to an establishment
 */
export type PersonaRelacionada = components['schemas']['PersonaRelacionada'];

/**
 * Case detail for domicilio
 */
export type CasoDetalle = components['schemas']['CasoDetalle'];

/**
 * Filters for domicilios map endpoint
 */
export type DomiciliosMapaFilters = operations['get_domicilios_mapa_api_v1_eventos_domicilios_mapa_get']['parameters']['query'];

// ============================================================================
// QUERY HOOKS - Semantic wrappers over $api
// ============================================================================

/**
 * Fetch geocoded domicilios with events for point map visualization
 *
 * Returns domicilios that have been geocoded and have related events,
 * suitable for rendering on a map.
 *
 * @param filters - Geographic and event type filters
 * @returns Query with domicilios map data
 *
 * @example
 * ```tsx
 * const { data } = useDomiciliosMapa({
 *   id_provincia_indec: 82,
 *   id_grupo_eno: 1,
 *   limit: 1000
 * });
 * ```
 */
export function useDomiciliosMapa(filters?: DomiciliosMapaFilters) {
  return $api.useQuery(
    'get',
    '/api/v1/eventos/domicilios/mapa',
    {
      params: {
        query: filters,
      },
    }
  );
}

/**
 * Fetch detailed case information for a specific domicilio
 *
 * Returns all cases (events) associated with a domicilio address,
 * including person and event details.
 *
 * @param idDomicilio - Domicilio ID
 * @param options - Query options (enabled)
 * @returns Query with domicilio details and cases
 *
 * @example
 * ```tsx
 * const { data } = useDomicilioDetalle(123);
 * // Or with conditional fetching:
 * const { data } = useDomicilioDetalle(selectedId, { enabled: !!selectedId });
 * ```
 */
export function useDomicilioDetalle(
  idDomicilio: number | null,
  options?: { enabled?: boolean }
) {
  const enabled = options?.enabled ?? true;

  return $api.useQuery(
    'get',
    '/api/v1/eventos/domicilios/{id_domicilio}',
    {
      params: {
        path: { id_domicilio: idDomicilio || 0 },
      },
    },
    {
      enabled: enabled && !!idDomicilio,
    }
  );
}

/**
 * Fetch detailed persons/events information for a specific establishment
 *
 * Returns all persons and events related to a health establishment,
 * grouped by relationship type (consultation, notification, etc.).
 *
 * @param idEstablecimiento - Establecimiento ID
 * @param options - Query options (enabled)
 * @returns Query with establishment details and related persons
 *
 * @example
 * ```tsx
 * const { data } = useEstablecimientoDetalle(456);
 * // Or with conditional fetching:
 * const { data } = useEstablecimientoDetalle(selectedId, { enabled: !!selectedId });
 * ```
 */
export function useEstablecimientoDetalle(
  idEstablecimiento: number | null,
  options?: { enabled?: boolean }
) {
  const enabled = options?.enabled ?? true;

  return $api.useQuery(
    'get',
    '/api/v1/establecimientos/{id_establecimiento}',
    {
      params: {
        path: { id_establecimiento: idEstablecimiento || 0 },
      },
    },
    {
      enabled: enabled && !!idEstablecimiento,
    }
  );
}
