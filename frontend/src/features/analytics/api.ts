/**
 * Analytics API - Solo tipos
 */

import type { components } from '@/lib/api/types';

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
