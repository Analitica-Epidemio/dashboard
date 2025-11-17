/**
 * Reports API Layer
 *
 * Semantic hooks for report generation, preview, and chart data endpoints.
 * Uses $api client internally - all types from OpenAPI schema.
 *
 * @module features/reports/api
 */

import { $api } from '@/lib/api/client';
import type { components } from '@/lib/api/types';

// ============================================================================
// TYPES - Re-exported from OpenAPI schema
// ============================================================================

// Charts types
export type ChartDisponibleItem = components['schemas']['ChartDisponibleItem'];
export type ChartsDisponiblesResponse = components['schemas']['ChartsDisponiblesResponse'];
export type DashboardChartsResponse = components['schemas']['DashboardChartsResponse'];

// Chart filters interface
export interface ChartFilters {
  grupo_id?: number;
  tipo_eno_ids?: number[];
  fecha_desde?: string;
  fecha_hasta?: string;
  clasificaciones?: string[];
  provincia_id?: number;
}

// ============================================================================
// QUERY HOOKS - Chart data for reports
// ============================================================================

/**
 * Fetch available chart catalog
 *
 * Returns list of all available charts that can be embedded in reports and boletines.
 * Used by the chart config dialog for chart selection.
 *
 * @returns Query with available charts
 *
 * @example
 * ```tsx
 * const { data } = useChartsDisponibles();
 * const charts = data?.data?.charts || [];
 * ```
 */
export function useChartsDisponibles() {
  return $api.useQuery(
    'get',
    '/api/v1/charts/disponibles',
    {},
    {
      staleTime: 5 * 60 * 1000, // Cache for 5 minutes
    }
  );
}

/**
 * Fetch dashboard charts with filters
 *
 * Returns chart data based on applied filters (groups, events, dates, etc.).
 * Used by comparative reports and boletin editor.
 *
 * @param params - Chart filters (grupo_id, tipo_eno_ids, dates, etc.)
 * @returns Query with filtered chart data
 *
 * @example
 * ```tsx
 * const { data } = useDashboardCharts({
 *   grupo_id: 5,
 *   tipo_eno_ids: [1, 2, 3],
 *   fecha_desde: '2024-01-01',
 *   fecha_hasta: '2024-12-31'
 * });
 * const charts = data?.data?.charts || [];
 * ```
 */
export function useDashboardCharts(params: ChartFilters) {
  return $api.useQuery(
    'get',
    '/api/v1/charts/dashboard',
    {
      params: {
        query: params,
      },
    },
    {
      enabled: !!params.grupo_id, // Only fetch when grupo_id is provided
    }
  );
}

/**
 * Fetch dashboard indicators
 *
 * Returns key indicators and metrics for reports.
 *
 * @param filters - Optional chart filters
 * @returns Query with indicators data
 *
 * @example
 * ```tsx
 * const { data } = useIndicadores({ grupo_id: 5 });
 * ```
 */
export function useIndicadores(filters?: ChartFilters) {
  return $api.useQuery(
    'get',
    '/api/v1/charts/indicadores',
    {
      params: {
        query: filters,
      },
    },
    {
      staleTime: 2 * 60 * 1000,
    }
  );
}

// ============================================================================
// QUERY HOOKS - Report preview
// ============================================================================

/**
 * Preview report with given filters (as query)
 *
 * Returns a preview of the report data based on the provided filters.
 * Can be used to show users what data will be included before generating.
 *
 * @param request - Report configuration (date_range, combinations, format)
 * @param enabled - Whether to enable the query
 * @returns Query with report preview data
 *
 * @example
 * ```tsx
 * const { data } = useReportPreview(
 *   {
 *     date_range: { start: '2024-01-01', end: '2024-12-31' },
 *     combinations: [...],
 *     format: 'pdf'
 *   },
 *   true
 * );
 * ```
 */
export function useReportPreview(
  request: {
    date_range: Record<string, string>;
    combinations: Array<Record<string, unknown>>;
    format: string;
  } | null,
  enabled: boolean = false
) {
  return $api.useQuery(
    'post',
    '/api/v1/reports/preview',
    {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      body: request as any,
    },
    {
      enabled: enabled && !!request && request.combinations.length > 0,
      staleTime: 30 * 1000,
    }
  );
}

// ============================================================================
// MUTATION HOOKS - Report generation
// ============================================================================

/**
 * Generate PDF report with auto-download
 *
 * Generates a PDF report based on provided filters and automatically
 * downloads it to the user's device.
 *
 * @returns Mutation to generate PDF report
 *
 * @example
 * ```tsx
 * const generatePdf = useGenerateReport();
 * await generatePdf.mutateAsync({
 *   body: {
 *     date_range: { start: '2024-01-01', end: '2024-12-31' },
 *     combinations: [...]
 *   }
 * });
 * ```
 */
export function useGenerateReport() {
  return $api.useMutation('post', '/api/v1/reports/generate', {
    onSuccess: (data) => {
      // Auto-download the PDF if it's a blob
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      if ((data as any)?.data instanceof Blob) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const url = URL.createObjectURL((data as any).data);
        const link = document.createElement('a');
        link.href = url;
        link.download = `reporte_epidemiologico_${new Date().toISOString().slice(0, 10)}.pdf`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
      }
    },
  });
}

/**
 * Generate ZIP report with auto-download
 *
 * Generates a ZIP archive containing multiple reports and automatically
 * downloads it to the user's device.
 *
 * @returns Mutation to generate ZIP report
 *
 * @example
 * ```tsx
 * const generateZip = useGenerateZipReport();
 * await generateZip.mutateAsync({
 *   body: {
 *     date_range: { start: '2024-01-01', end: '2024-12-31' },
 *     combinations: [...]
 *   }
 * });
 * ```
 */
export function useGenerateZipReport() {
  return $api.useMutation('post', '/api/v1/reports/generate-zip', {
    onSuccess: (data) => {
      // Auto-download the ZIP if it's a blob
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      if ((data as any)?.data instanceof Blob) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const url = URL.createObjectURL((data as any).data);
        const link = document.createElement('a');
        link.href = url;
        link.download = `reporte_epidemiologico_${new Date().toISOString().slice(0, 10)}.zip`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
      }
    },
    onError: (error) => {
      console.error('Error generating ZIP report:', error);
      alert('Error al generar el reporte ZIP. Por favor intente nuevamente.');
    },
  });
}

/**
 * Preview report data (as mutation for manual control)
 *
 * Same as useReportPreview but as a mutation, giving you manual control
 * over when to fetch the preview.
 *
 * @returns Mutation to preview report
 *
 * @example
 * ```tsx
 * const preview = useReportPreviewMutation();
 * await preview.mutateAsync({
 *   body: {
 *     date_range: { start: '2024-01-01', end: '2024-12-31' },
 *     combinations: [...]
 *   }
 * });
 * ```
 */
export function useReportPreviewMutation() {
  return $api.useMutation('post', '/api/v1/reports/preview');
}

/**
 * Generate signed URL for server-side rendered reports
 *
 * Creates a time-limited signed URL that can be used to access
 * a pre-generated report without authentication.
 *
 * @returns Mutation to generate signed URL
 *
 * @example
 * ```tsx
 * const generateUrl = useGenerateSignedUrl();
 * const result = await generateUrl.mutateAsync({
 *   body: { report_id: '123', expires_in: 3600 }
 * });
 * ```
 */
export function useGenerateSignedUrl() {
  return $api.useMutation('post', '/api/v1/reports/generate-signed-url');
}
