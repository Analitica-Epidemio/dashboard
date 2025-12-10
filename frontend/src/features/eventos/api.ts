/**
 * Eventos API Layer
 *
 * Semantic hooks for epidemiological events (eventos) and related entities.
 * Uses $api client internally - all types from OpenAPI schema.
 *
 * @module features/eventos/api
 */

import { $api } from '@/lib/api/client';
import type { operations, components } from '@/lib/api/types';

// ============================================================================
// TYPES - Re-exported from OpenAPI schema
// ============================================================================

/**
 * Event filters for list queries
 */
export type EventoFilters = operations["list_eventos_api_v1_eventos__get"]["parameters"]["query"];

/**
 * Tipos ENO filters
 */
export type TiposEnoFilters = operations["list_tipos_eno_api_v1_tiposEno__get"]["parameters"]["query"];

/**
 * Event classification type
 */
export type TipoClasificacion = components["schemas"]["TipoClasificacion"];

/**
 * Event detail with full information
 */
export type EventoDetail = components["schemas"]["CasoEpidemiologicoDetailResponse"];

/**
 * Event list item (summary)
 */
export type EventoListItem = components["schemas"]["CasoEpidemiologicoListItem"];

// ============================================================================
// QUERY HOOKS - Semantic wrappers over $api
// ============================================================================

/**
 * Fetch single event by ID with full details
 *
 * Returns complete event information including person, location, and classification data.
 *
 * @param eventoId - Event ID
 * @returns Query with event details
 *
 * @example
 * ```tsx
 * const { data } = useEvento(123);
 * ```
 */
export function useEvento(eventoId: number | null) {
  return $api.useQuery(
    'get',
    '/api/v1/eventos/{evento_id}',
    {
      params: {
        path: { evento_id: eventoId || 0 },
      },
    },
    {
      enabled: !!eventoId,
    }
  );
}

/**
 * Fetch event timeline with all related activities
 *
 * Returns chronological list of all activities, changes, and events
 * related to this event.
 *
 * @param eventoId - Event ID
 * @returns Query with timeline data
 *
 * @example
 * ```tsx
 * const { data } = useEventoTimeline(123);
 * ```
 */
export function useEventoTimeline(eventoId: number | null) {
  return $api.useQuery(
    'get',
    '/api/v1/eventos/{evento_id}/timeline',
    {
      params: {
        path: { evento_id: eventoId || 0 },
      },
    },
    {
      enabled: !!eventoId,
    }
  );
}

/**
 * Fetch events list with optional filters
 *
 * Returns paginated list of events. Supports filtering by classification,
 * location, event type, date ranges, and more.
 *
 * @param params - Event filters (pagination, clasificacion, ubicacion, etc.)
 * @returns Query with events list
 *
 * @example
 * ```tsx
 * const { data } = useEventos({
 *   clasificacion: 'CONFIRMADOS',
 *   id_provincia_indec: 82,
 *   limit: 50
 * });
 * ```
 */
export function useEventos(params?: EventoFilters) {
  return $api.useQuery(
    'get',
    '/api/v1/eventos/',
    {
      params: {
        query: params,
      },
    }
  );
}

/**
 * Fetch grupos ENO (event type categories)
 *
 * Returns list of parent event categories (e.g., Zoonosis, Vectoriales).
 *
 * @returns Query with grupos ENO list
 *
 * @example
 * ```tsx
 * const { data } = useGruposEno();
 * ```
 */
export function useGruposEno() {
  return $api.useQuery(
    'get',
    '/api/v1/gruposEno/',
    {}
  );
}

/**
 * Fetch tipos ENO (event types) optionally filtered by grupo
 *
 * Returns list of specific event types (e.g., Dengue, Leptospirosis).
 * Can be filtered by parent grupo_id.
 *
 * @param params - Optional filters (grupo_id, grupos, nombre, pagination)
 * @returns Query with tipos ENO list
 *
 * @example
 * ```tsx
 * // All tipos
 * const { data } = useTiposEno();
 *
 * // Filtered by grupo
 * const { data } = useTiposEno({ grupo_id: 5 });
 *
 * // Multiple grupos
 * const { data } = useTiposEno({ grupos: [1, 2, 3] });
 * ```
 */
export function useTiposEno(params?: TiposEnoFilters) {
  return $api.useQuery(
    'get',
    '/api/v1/tiposEno/',
    {
      params: {
        query: params,
      },
    }
  );
}

// ============================================================================
// DASHBOARD HELPERS - Simplified hooks for dashboard/filters
// ============================================================================

/**
 * Get all grupos ENO for dashboard (with data transformation)
 *
 * Returns grupos with simplified structure for dashboard usage.
 * This is a convenience wrapper over useGruposEno.
 *
 * @returns Query with transformed grupos data
 *
 * @example
 * ```tsx
 * const { data: groups } = useGroups();
 * ```
 */
export function useGroups() {
  const query = useGruposEno();

  const mappedData = query.data?.data?.map((grupo) => ({
    id: String(grupo.id),
    name: grupo.nombre,
    description: grupo.descripcion
  }));

  return {
    ...query,
    data: mappedData
  };
}

/**
 * Get all tipos ENO for dashboard (with data transformation)
 *
 * Returns all event types with simplified structure for dashboard usage.
 * This is a convenience wrapper over useTiposEno.
 *
 * @returns Query with transformed tipos data
 *
 * @example
 * ```tsx
 * const { data: events } = useAllEvents();
 * ```
 */
export function useAllEvents() {
  const query = useTiposEno({ per_page: 100 });

  const mappedData = query.data?.data?.map((tipo) => {
    const primerGrupo = tipo.grupos?.[0];

    return {
      id: String(tipo.id),
      name: tipo.nombre,
      groupId: primerGrupo ? String(primerGrupo.id) : null,
      description: tipo.descripcion,
      groupName: primerGrupo?.nombre
    };
  });

  return {
    ...query,
    data: mappedData
  };
}

/**
 * Get tipos ENO filtered by grupo (with data transformation)
 *
 * Returns event types for a specific grupo with simplified structure.
 * This is a convenience wrapper over useTiposEno.
 *
 * @param groupId - Grupo ID to filter by
 * @returns Query with transformed tipos data
 *
 * @example
 * ```tsx
 * const { data: events } = useEventsByGroup('5');
 * ```
 */
export function useEventsByGroup(groupId: string | null) {
  const query = useTiposEno(
    {
      per_page: 100,
      grupo_id: groupId ? Number(groupId) : undefined
    }
  );

  const mappedData = query.data?.data?.map((tipo) => {
    const primerGrupo = tipo.grupos?.[0];

    return {
      id: String(tipo.id),
      name: tipo.nombre,
      groupId: primerGrupo ? String(primerGrupo.id) : null,
      description: tipo.descripcion,
      groupName: primerGrupo?.nombre
    };
  });

  return {
    ...query,
    data: mappedData,
    enabled: !!groupId
  };
}

// ============================================================================
// UTILITY FUNCTIONS - Display helpers
// ============================================================================

/**
 * Utility functions for clasificacion display
 */
export function getClasificacionLabel(clasificacion: TipoClasificacion | string | null | undefined): string {
  if (!clasificacion) return "Sin clasificar";

  const labels: Record<string, string> = {
    'CONFIRMADOS': 'Confirmado',
    'SOSPECHOSOS': 'Sospechoso',
    'PROBABLES': 'Probable',
    'DESCARTADOS': 'Descartado',
    'NEGATIVOS': 'Negativo',
    'EN_ESTUDIO': 'En Estudio',
    'REQUIERE_REVISION': 'Requiere Revisión',
    // Legacy lowercase
    'sospechoso': 'Sospechoso',
    'confirmado': 'Confirmado',
    'descartado': 'Descartado',
    'probable': 'Probable',
    'no_conclusivo': 'No conclusivo',
  };

  return labels[clasificacion] || clasificacion;
}

export function getClasificacionVariant(clasificacion: TipoClasificacion | string | null | undefined): "default" | "destructive" | "secondary" | "outline" {
  if (!clasificacion) return "default";

  const variants: Record<string, "default" | "destructive" | "secondary" | "outline"> = {
    'CONFIRMADOS': 'destructive',
    'SOSPECHOSOS': 'outline',
    'PROBABLES': 'secondary',
    'DESCARTADOS': 'secondary',
    'NEGATIVOS': 'secondary',
    'EN_ESTUDIO': 'outline',
    'REQUIERE_REVISION': 'destructive',
    // Legacy
    'sospechoso': 'outline',
    'confirmado': 'destructive',
    'descartado': 'secondary',
    'probable': 'secondary',
    'no_conclusivo': 'default',
  };

  return variants[clasificacion] || 'default';
}

/**
 * Obtiene clases de Tailwind para colorear clasificaciones
 */
export function getClasificacionColorClasses(clasificacion: TipoClasificacion | string | null | undefined): string {
  if (!clasificacion) return "bg-muted text-muted-foreground";

  const colors: Record<string, string> = {
    'CONFIRMADOS': 'bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-400 border-red-200 dark:border-red-900',
    'SOSPECHOSOS': 'bg-yellow-100 text-yellow-700 dark:bg-yellow-950 dark:text-yellow-400 border-yellow-200 dark:border-yellow-900',
    'PROBABLES': 'bg-orange-100 text-orange-700 dark:bg-orange-950 dark:text-orange-400 border-orange-200 dark:border-orange-900',
    'DESCARTADOS': 'bg-gray-100 text-gray-700 dark:bg-gray-950 dark:text-gray-400 border-gray-200 dark:border-gray-900',
    'NEGATIVOS': 'bg-green-100 text-green-700 dark:bg-green-950 dark:text-green-400 border-green-200 dark:border-green-900',
    'EN_ESTUDIO': 'bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-400 border-blue-200 dark:border-blue-900',
    'REQUIERE_REVISION': 'bg-purple-100 text-purple-700 dark:bg-purple-950 dark:text-purple-400 border-purple-200 dark:border-purple-900',
  };

  return colors[clasificacion] || "bg-muted text-muted-foreground";
}

/**
 * Get color for clasificacion estrategica
 */
export function getClasificacionEstrategiaColor(clasificacion: string | null | undefined): string {
  if (!clasificacion) return "text-gray-500";

  const colors: Record<string, string> = {
    'sospechoso': 'text-yellow-600',
    'confirmado': 'text-red-600',
    'descartado': 'text-green-600',
    'probable': 'text-blue-600',
    'no_conclusivo': 'text-gray-600',
  };

  return colors[clasificacion] || 'text-gray-500';
}
