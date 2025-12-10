/**
 * Metricas Hooks - Sistema de queries con comparación integrada
 *
 * Provee hooks optimizados para:
 * - Queries simples de métricas
 * - Comparación YoY (Year over Year)
 * - Comparación con período anterior
 * - Cache inteligente y deduplicación
 */

import { useMemo } from "react";
import { useQueries } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";
import type { PeriodoFilter, MetricDataRow } from "./api";

// ═══════════════════════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════════════════════

export type ComparisonMode = "none" | "yoy" | "previous_period";

export interface MetricQueryOptions {
    /** Código de la métrica (ej: "casos_clinicos", "ocupacion_camas_ira") */
    metric: string;
    /** Dimensiones para agrupar (ej: ["TIPO_EVENTO", "SEMANA_EPIDEMIOLOGICA"]) */
    dimensions: string[];
    /** Período a consultar */
    periodo: PeriodoFilter;
    /** Filtros adicionales */
    filters?: {
        evento_id?: number;
        evento_ids?: number[];
        agente_id?: number;
        agente_ids?: number[];
        agrupacion_slug?: string;
        provincia_id?: number;
        provincia_nombre?: string;
        departamento_id?: number;
        establecimiento_id?: number;
    };
    /** Modo de comparación */
    comparison?: ComparisonMode;
    /** Compute post-query (ej: "corredor_endemico") */
    compute?: string;
    /** Habilitar/deshabilitar query */
    enabled?: boolean;
}

export interface MetricComparisonResult {
    /** Datos del período actual */
    current: MetricDataRow[];
    /** Datos del período de comparación (si aplica) */
    previous: MetricDataRow[] | null;
    /** Indica si está cargando alguno de los queries */
    isLoading: boolean;
    /** Indica si el período actual está cargando */
    isLoadingCurrent: boolean;
    /** Indica si el período de comparación está cargando */
    isLoadingPrevious: boolean;
    /** Error si hay alguno */
    error: Error | null;
    /** Metadata del query actual */
    metadata: {
        metric: string;
        dimensions: string[];
        total_rows: number;
    } | null;
    /** Período actual */
    currentPeriod: PeriodoFilter;
    /** Período de comparación (si aplica) */
    previousPeriod: PeriodoFilter | null;
    /** Helper para calcular delta entre valores */
    calculateDelta: (currentValue: number, previousValue: number) => {
        diferencia: number;
        porcentaje: number | null;
        tendencia: "up" | "down" | "stable";
    };
    /** Helper para obtener valor del período anterior dado una key */
    getPreviousValue: (key: Record<string, unknown>) => number | null;
}

// ═══════════════════════════════════════════════════════════════════════════════
// HELPERS
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Calcula el número de semanas en un período (soporta multi-año)
 */
function calcularSemanas(periodo: PeriodoFilter): number {
    if (periodo.anio_desde === periodo.anio_hasta) {
        return periodo.semana_hasta - periodo.semana_desde + 1;
    }
    // Cruzando años
    const semanasAnioInicio = 52 - periodo.semana_desde + 1;
    const semanasAnioFin = periodo.semana_hasta;
    const aniosIntermedios = periodo.anio_hasta - periodo.anio_desde - 1;
    return semanasAnioInicio + (aniosIntermedios * 52) + semanasAnioFin;
}

/**
 * Calcula el período de comparación basado en el modo
 * Soporta períodos multi-año
 */
function calculateComparisonPeriod(
    periodo: PeriodoFilter,
    mode: ComparisonMode
): PeriodoFilter | null {
    if (mode === "none") return null;

    if (mode === "yoy") {
        // Mismo período, año anterior (ambos años se reducen en 1)
        return {
            anio_desde: periodo.anio_desde - 1,
            semana_desde: periodo.semana_desde,
            anio_hasta: periodo.anio_hasta - 1,
            semana_hasta: periodo.semana_hasta,
        };
    }

    if (mode === "previous_period") {
        // Período inmediatamente anterior (misma duración)
        const duracion = calcularSemanas(periodo);

        // Calcular nuevo inicio retrocediendo N semanas desde el inicio actual
        let nuevoAnioDesde = periodo.anio_desde;
        let nuevaSemanaDesde = periodo.semana_desde - duracion;

        while (nuevaSemanaDesde < 1) {
            nuevoAnioDesde--;
            nuevaSemanaDesde += 52;
        }

        // El fin del período anterior es justo antes del inicio actual
        let nuevoAnioHasta = periodo.anio_desde;
        let nuevaSemanaHasta = periodo.semana_desde - 1;

        if (nuevaSemanaHasta < 1) {
            nuevoAnioHasta--;
            nuevaSemanaHasta = 52;
        }

        return {
            anio_desde: nuevoAnioDesde,
            semana_desde: nuevaSemanaDesde,
            anio_hasta: nuevoAnioHasta,
            semana_hasta: nuevaSemanaHasta,
        };
    }

    return null;
}

/**
 * Crea una key única para buscar valores en datos de comparación
 */
function createRowKey(row: MetricDataRow, excludeKeys: string[] = []): string {
    const keyParts: string[] = [];
    const excluded = new Set([...excludeKeys, "valor", "anio_epidemiologico", "semana_epidemiologica"]);

    for (const [k, v] of Object.entries(row)) {
        if (!excluded.has(k) && v !== null && v !== undefined) {
            keyParts.push(`${k}:${v}`);
        }
    }

    return keyParts.sort().join("|");
}

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN HOOK
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Hook principal para queries de métricas con comparación integrada
 *
 * @example
 * ```tsx
 * const { current, previous, isLoading, calculateDelta } = useMetricQuery({
 *   metric: "ocupacion_camas_ira",
 *   dimensions: ["TIPO_EVENTO"],
 *   periodo: { anio_desde: 2025, semana_desde: 1, anio_hasta: 2025, semana_hasta: 49 },
 *   comparison: "yoy",
 * });
 *
 * // Renderizar con comparación
 * {current.map(row => {
 *   const prevValue = getPreviousValue({ tipo_evento: row.tipo_evento });
 *   const delta = calculateDelta(row.valor, prevValue);
 *   return <div>{row.tipo_evento}: {row.valor} ({delta.porcentaje}%)</div>
 * })}
 * ```
 */
export function useMetricQuery(options: MetricQueryOptions): MetricComparisonResult {
    const {
        metric,
        dimensions,
        periodo,
        filters = {},
        comparison = "none",
        compute,
        enabled = true,
    } = options;

    // Calcular período de comparación
    const previousPeriod = useMemo(
        () => calculateComparisonPeriod(periodo, comparison),
        [periodo, comparison]
    );

    // Construir body de request
    const buildBody = (p: PeriodoFilter) => ({
        metric,
        dimensions,
        filters: {
            periodo: p,
            ...filters,
        },
        ...(compute && { compute }),
    });

    // Ejecutar queries en paralelo
    const queries = useQueries({
        queries: [
            // Query principal (período actual)
            {
                queryKey: ["metricas", metric, dimensions, periodo, filters, compute],
                queryFn: async () => {
                    const response = await apiClient.POST("/api/v1/metricas/query", {
                        body: buildBody(periodo),
                    });
                    if (response.error) throw new Error("Error fetching metric");
                    return response.data;
                },
                enabled,
                staleTime: 5 * 60 * 1000, // 5 minutos
                gcTime: 30 * 60 * 1000, // 30 minutos en cache
            },
            // Query de comparación (si aplica)
            {
                queryKey: ["metricas", metric, dimensions, previousPeriod, filters, compute],
                queryFn: async () => {
                    if (!previousPeriod) return null;
                    const response = await apiClient.POST("/api/v1/metricas/query", {
                        body: buildBody(previousPeriod),
                    });
                    if (response.error) throw new Error("Error fetching comparison metric");
                    return response.data;
                },
                enabled: enabled && comparison !== "none" && !!previousPeriod,
                staleTime: 5 * 60 * 1000,
                gcTime: 30 * 60 * 1000,
            },
        ],
    });

    const [currentQuery, previousQuery] = queries;

    // Crear mapa de valores anteriores para lookup rápido
    const previousValueMap = useMemo(() => {
        if (!previousQuery.data?.data) return new Map<string, number>();
        const map = new Map<string, number>();
        for (const row of previousQuery.data.data as MetricDataRow[]) {
            const key = createRowKey(row);
            map.set(key, (row.valor as number) ?? 0);
        }
        return map;
    }, [previousQuery.data]);

    // Helper para obtener valor anterior
    const getPreviousValue = (key: Record<string, unknown>): number | null => {
        if (comparison === "none" || !previousQuery.data) return null;
        const keyStr = createRowKey(key as MetricDataRow);
        return previousValueMap.get(keyStr) ?? null;
    };

    // Helper para calcular delta
    const calculateDelta = (currentValue: number, previousValue: number) => {
        const diferencia = currentValue - previousValue;
        const porcentaje = previousValue !== 0
            ? Math.round((diferencia / previousValue) * 1000) / 10
            : null;

        let tendencia: "up" | "down" | "stable" = "stable";
        if (diferencia > 0) tendencia = "up";
        else if (diferencia < 0) tendencia = "down";

        return { diferencia, porcentaje, tendencia };
    };

    return {
        current: (currentQuery.data?.data as MetricDataRow[]) ?? [],
        previous: comparison !== "none"
            ? (previousQuery.data?.data as MetricDataRow[]) ?? null
            : null,
        isLoading: currentQuery.isLoading || (comparison !== "none" && previousQuery.isLoading),
        isLoadingCurrent: currentQuery.isLoading,
        isLoadingPrevious: previousQuery.isLoading,
        error: currentQuery.error ?? previousQuery.error ?? null,
        metadata: currentQuery.data?.metadata ?? null,
        currentPeriod: periodo,
        previousPeriod,
        calculateDelta,
        getPreviousValue,
    };
}

// ═══════════════════════════════════════════════════════════════════════════════
// CONVENIENCE HOOKS
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Hook simplificado para métricas sin comparación
 */
export function useSimpleMetricQuery(
    metric: string,
    dimensions: string[],
    periodo: PeriodoFilter,
    filters?: MetricQueryOptions["filters"],
    enabled = true
) {
    return useMetricQuery({
        metric,
        dimensions,
        periodo,
        filters,
        comparison: "none",
        enabled,
    });
}

/**
 * Hook para corredor endémico
 */
export function useCorredorEndemico(
    metric: string,
    periodo: PeriodoFilter,
    filters?: MetricQueryOptions["filters"],
    enabled = true
) {
    return useMetricQuery({
        metric,
        dimensions: ["SEMANA_EPIDEMIOLOGICA", "ANIO_EPIDEMIOLOGICO"],
        periodo,
        filters,
        comparison: "none",
        compute: "corredor_endemico",
        enabled,
    });
}
