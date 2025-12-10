/**
 * Metricas API hooks and utilities
 * Uses the typed $api client for all requests
 */

import { $api } from "@/lib/api/client";
import type { components } from "@/lib/api/types";

// ═══════════════════════════════════════════════════════════════════════════════
// TYPE EXPORTS
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Metric query request - extracted from API types
 */
export type MetricQueryRequest = components["schemas"]["MetricQueryRequest"];

/**
 * Metric query response - extracted from API types
 */
export type MetricQueryResponse = components["schemas"]["MetricQueryResponse"];

/**
 * Metric data row - typed row with all possible dimension fields
 */
export type MetricDataRow = components["schemas"]["MetricDataRow"];

/**
 * Metric filters - extracted from API types
 */
export type MetricFilters = components["schemas"]["MetricFilters"];

/**
 * Periodo filter - extracted from API types
 */
export type PeriodoFilter = components["schemas"]["PeriodoFilter"];

/**
 * Metric info response from /disponibles endpoint
 */
export type MetricInfoResponse = components["schemas"]["MetricInfoResponse"];

// ═══════════════════════════════════════════════════════════════════════════════
// HOOKS
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Hook to fetch available metrics schema
 */
export function useMetricasDisponibles() {
    return $api.useQuery("get", "/api/v1/metricas/disponibles");
}

/**
 * Hook to query metrics - uses POST mutation pattern
 * 
 * @example
 * const queryMetric = useQueryMetric();
 * 
 * // Simple query for lab positives in 2025
 * const result = await queryMetric.mutateAsync({
 *   metric: "muestras_positivas",
 *   dimensions: [],
 *   filters: {
 *     periodo: { anio: 2025, semana_desde: 1, semana_hasta: 52 }
 *   }
 * });
 */
export function useQueryMetric() {
    return $api.useMutation("post", "/api/v1/metricas/query");
}

/**
 * Hook to get metrics schema (list of cubes)
 */
export function useMetricasSchema() {
    return $api.useQuery("get", "/api/v1/metricas/schema");
}

/**
 * Hook to get cube detail
 */
export function useCubeDetail(cubeId: string, enabled = true) {
    return $api.useQuery(
        "get",
        "/api/v1/metricas/schema/{cube_id}",
        { params: { path: { cube_id: cubeId } } },
        { enabled }
    );
}

// ═══════════════════════════════════════════════════════════════════════════════
// HELPER FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Creates a periodo filter for the entire year
 */
export function createYearFilter(anio: number): PeriodoFilter {
    return {
        anio_desde: anio,
        semana_desde: 1,
        anio_hasta: anio,
        semana_hasta: 52,
    };
}

/**
 * Extracts total value from metric response
 * Assumes a single-row aggregation (no dimensions)
 */
export function extractTotalValue(response: MetricQueryResponse | undefined): number {
    if (!response?.data?.length) return 0;
    const row = response.data[0];
    // Common field names for values
    return (row?.valor as number) ||
        (row?.total as number) ||
        (row?.count as number) ||
        0;
}
