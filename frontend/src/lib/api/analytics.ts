/**
 * API client for analytics endpoints
 */

import { apiClient } from "./client";
import type { components } from "./types";

// Re-export tipos generados de OpenAPI
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

export interface DateRangeResponse {
  fecha_minima: string;
  fecha_maxima: string;
  total_eventos: number;
}

/**
 * Obtiene las métricas de analytics comparando dos períodos
 */
export async function getAnalytics(
  filters?: AnalyticsFilters
): Promise<AnalyticsResponse> {
  const response = await apiClient.GET("/api/v1/analytics", {
    params: {
      query: filters,
    },
  });

  if (response.error) {
    console.error("Error from API:", response.error);
    throw new Error(JSON.stringify(response.error));
  }

  const responseData = response.data as
    | components["schemas"]["SuccessResponse_AnalyticsResponse_"]
    | AnalyticsResponse
    | undefined;

  // Si viene envuelto en SuccessResponse, extraer data
  if (responseData && typeof responseData === "object" && "data" in responseData) {
    return responseData.data;
  }

  return responseData as AnalyticsResponse;
}

/**
 * Obtiene los top winners y losers (entidades con mayor cambio)
 */
export async function getTopWinnersLosers(
  filters?: TopWinnersLosersFilters
): Promise<TopWinnersLosersResponse> {
  const response = await apiClient.GET("/api/v1/analytics/top-winners-losers", {
    params: {
      query: filters,
    },
  });

  if (response.error) {
    console.error("Error from API:", response.error);
    throw new Error(JSON.stringify(response.error));
  }

  const responseData = response.data as
    | components["schemas"]["SuccessResponse_TopWinnersLosersResponse_"]
    | TopWinnersLosersResponse
    | undefined;

  // Si viene envuelto en SuccessResponse, extraer data
  if (responseData && typeof responseData === "object" && "data" in responseData) {
    return responseData.data;
  }

  return responseData as TopWinnersLosersResponse;
}

/**
 * Obtiene el rango de fechas con datos disponibles
 */
export async function getDateRange(): Promise<DateRangeResponse> {
  const response = await apiClient.GET("/api/v1/analytics/date-range");

  if (response.error) {
    console.error("Error from API:", response.error);
    throw new Error(JSON.stringify(response.error));
  }

  const responseData = response.data as any;

  // Si viene envuelto en SuccessResponse, extraer data
  if (responseData && typeof responseData === "object" && "data" in responseData) {
    return responseData.data;
  }

  return responseData as DateRangeResponse;
}
