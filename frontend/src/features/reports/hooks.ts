/**
 * Reports Hooks using openapi-react-query
 * PDF/ZIP generation with proper library usage
 */

import { $api } from '@/lib/api/client';

/**
 * Hook for generating PDF reports
 */
export function useGenerateReport() {
  return $api.useMutation('post', '/api/v1/reports/generate', {
    onSuccess: (data) => {
      // Auto-download the PDF if it's a blob
      if (data?.data instanceof Blob) {
        const url = URL.createObjectURL(data.data);
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
 * Hook for generating ZIP reports
 */
export function useGenerateZipReport() {
  return $api.useMutation('post', '/api/v1/reports/generate-zip', {
    onSuccess: (data) => {
      // Auto-download the ZIP
      if (data?.data instanceof Blob) {
        const url = URL.createObjectURL(data.data);
        const link = document.createElement('a');
        link.href = url;
        link.download = `reporte_epidemiologico_${new Date().toISOString().slice(0, 10)}.zip`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
      }
    },
  });
}

/**
 * Hook for report preview
 */
export function useReportPreview(request: any, enabled: boolean = false) {
  return $api.useQuery(
    'post',
    '/api/v1/reports/preview',
    {
      body: request,
    },
    {
      enabled: enabled && request?.combinations?.length > 0,
      staleTime: 30 * 1000,
    }
  );
}

/**
 * Hook for report preview mutation (manual control)
 */
export function useReportPreviewMutation() {
  return $api.useMutation('post', '/api/v1/reports/preview');
}

/**
 * Hook for generating signed URLs for SSR reports
 */
export function useGenerateSignedUrl() {
  return $api.useMutation('post', '/api/v1/reports/generate-signed-url');
}