/**
 * Hook para fetch de agrupaciones de agentes etiológicos.
 * 
 * Permite obtener agrupaciones por categoría (respiratorio, enterico, etc.)
 * para usar en charts dinámicos del dashboard.
 * 
 * Uses the typed $api client following project patterns.
 */

import { $api } from "@/lib/api/client";
import type { components } from "@/lib/api/types";

// ═══════════════════════════════════════════════════════════════════════════════
// TYPE EXPORTS from OpenAPI
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Agrupacion list item - extracted from API types
 */
export type Agrupacion = components["schemas"]["AgrupacionListItem"];

/**
 * Agrupacion detail with agents - extracted from API types
 */
export type AgrupacionDetail = components["schemas"]["AgrupacionDetailResponse"];

/**
 * Agrupaciones list response
 */
export type AgrupacionesListResponse = components["schemas"]["AgrupacionesListResponse"];

// ═══════════════════════════════════════════════════════════════════════════════
// HOOKS
// ═══════════════════════════════════════════════════════════════════════════════

interface UseAgrupacionesOptions {
    categoria?: string;
    enabled?: boolean;
}

/**
 * Fetch lista de agrupaciones, opcionalmente filtradas por categoría.
 * 
 * @example
 * const { data: respiratorios } = useAgrupaciones({ categoria: "respiratorio" });
 */
export function useAgrupaciones(options: UseAgrupacionesOptions = {}) {
    const { categoria, enabled = true } = options;

    return $api.useQuery(
        "get",
        "/api/v1/agrupaciones/",
        {
            params: {
                query: categoria ? { categoria } : undefined,
            },
        },
        { enabled }
    );
}

/**
 * Fetch detalle de una agrupación específica con sus agentes.
 * 
 * @example
 * const { data: fluA } = useAgrupacionDetail("influenza-a");
 */
export function useAgrupacionDetail(slug: string, options: { enabled?: boolean } = {}) {
    const { enabled = true } = options;

    return $api.useQuery(
        "get",
        "/api/v1/agrupaciones/{slug}",
        {
            params: {
                path: { slug },
            },
        },
        { enabled: enabled && !!slug }
    );
}

/**
 * Fetch solo los IDs de agentes de una agrupación.
 * Útil para construir filtros de métricas.
 * 
 * @example
 * const { data } = useAgrupacionAgenteIds("influenza-a");
 * // data.agente_ids = [1, 2, 3]
 */
export function useAgrupacionAgenteIds(slug: string, options: { enabled?: boolean } = {}) {
    const { enabled = true } = options;

    return $api.useQuery(
        "get",
        "/api/v1/agrupaciones/{slug}/agente-ids",
        {
            params: {
                path: { slug },
            },
        },
        { enabled: enabled && !!slug }
    );
}
