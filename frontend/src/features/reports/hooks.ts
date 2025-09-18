/**
 * Reports Hooks using openapi-react-query
 * PDF/ZIP generation with proper library usage
 */

import { $api } from '@/lib/api/client';
import { useMutation } from '@tanstack/react-query';
import { getSession } from 'next-auth/react';
import { env } from '@/env';

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
  const { mutate, mutateAsync, ...rest } = useMutation({
    mutationFn: async (request) => {
      // Get session for auth token
      const session = await getSession();

      const response = await fetch(`${env.NEXT_PUBLIC_API_HOST}/api/v1/reports/generate-zip`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(session?.accessToken && { 'Authorization': `Bearer ${session.accessToken}` }),
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`Failed to generate ZIP: ${response.statusText}`);
      }

      // Get the blob directly
      return await response.blob();
    },
    onSuccess: (blob) => {
      // Auto-download the ZIP
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `reporte_epidemiologico_${new Date().toISOString().slice(0, 10)}.zip`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    },
    onError: (error) => {
      console.error('Error generating ZIP report:', error);
      alert('Error al generar el reporte ZIP. Por favor intente nuevamente.');
    },
  });

  // Wrap mutate to match expected API
  const wrappedMutate = (params: { body: any }) => {
    mutate(params.body);
  };

  return {
    mutate: wrappedMutate,
    mutateAsync,
    ...rest,
  };
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