/**
 * Boletines API Layer
 *
 * Semantic hooks for boletines (bulletins) templates and instances.
 * Uses $api client internally - all types from OpenAPI schema.
 *
 * NOTE: Chart-related hooks are in @/features/reports/api
 *
 * @module features/boletines/api
 */

import type { components } from '@/lib/api/types';

// ============================================================================
// TYPES - Re-exported from OpenAPI schema
// ============================================================================

// Boletines types
export type BoletinTemplate = components['schemas']['BoletinTemplateResponse'];
export type BoletinInstance = components['schemas']['BoletinInstanceResponse'];
export type CreateTemplateRequest = components['schemas']['BoletinTemplateCreate'];
export type UpdateTemplateRequest = components['schemas']['BoletinTemplateUpdate'];
export type CreateInstanceRequest = components['schemas']['BoletinGenerateRequest'];

// Re-export chart types and hooks from reports for convenience
export type { ChartDisponibleItem, ChartsDisponiblesResponse, DashboardChartsResponse, ChartFilters } from '@/features/reports/api';
export { useChartsDisponibles, useDashboardCharts, useIndicadores } from '@/features/reports/api';
