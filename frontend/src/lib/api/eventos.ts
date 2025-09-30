/**
 * Eventos API hooks and utilities
 * Uses the typed $api client for all requests
 */

import { $api } from '@/lib/api/client';

/**
 * Event filters interface
 */
export interface EventoFilters {
  page?: number;
  page_size?: number;
  search?: string;
  tipo_eno_id?: number;
  fecha_desde?: string;
  fecha_hasta?: string;
  clasificacion?: string;
  es_positivo?: boolean;
  provincia?: string;
  tipo_sujeto?: string;
  requiere_revision?: boolean;
  sort_by?: 'fecha_desc' | 'fecha_asc' | 'id_desc' | 'id_asc' | 'tipo_eno';
}

/**
 * Hook to fetch a single evento by ID
 */
export function useEvento(eventoId: number) {
  return $api.useQuery(
    'get',
    '/api/v1/eventos/{evento_id}',
    {
      params: {
        path: { evento_id: eventoId },
      },
    },
    {
      enabled: !!eventoId,
    }
  );
}

/**
 * Hook to fetch evento timeline
 */
export function useEventoTimeline(eventoId: number) {
  return $api.useQuery(
    'get',
    '/api/v1/eventos/{evento_id}/timeline',
    {
      params: {
        path: { evento_id: eventoId },
      },
    },
    {
      enabled: !!eventoId,
    }
  );
}

/**
 * Hook to fetch eventos list with filters
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
 * Extract eventos data from API response
 */
export function extractEventosData(response: any) {
  return response?.data?.data || [];
}

/**
 * Utility functions for clasificacion display
 */
export function getClasificacionLabel(clasificacion: string | null | undefined): string {
  if (!clasificacion) return "Sin clasificar";

  const labels: Record<string, string> = {
    'sospechoso': 'Sospechoso',
    'confirmado': 'Confirmado',
    'descartado': 'Descartado',
    'probable': 'Probable',
    'no_conclusivo': 'No conclusivo',
  };

  return labels[clasificacion] || clasificacion;
}

export function getClasificacionVariant(clasificacion: string | null | undefined): "default" | "destructive" | "secondary" | "outline" {
  if (!clasificacion) return "default";

  const variants: Record<string, "default" | "destructive" | "secondary" | "outline"> = {
    'sospechoso': 'outline', // Era 'warning', cambiado a 'outline'
    'confirmado': 'destructive',
    'descartado': 'secondary', // Era 'success', cambiado a 'secondary'
    'probable': 'secondary',
    'no_conclusivo': 'default',
  };

  return variants[clasificacion] || 'default';
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
