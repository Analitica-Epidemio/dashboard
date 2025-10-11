/**
 * Eventos API hooks and utilities
 * Uses the typed $api client for all requests
 */

import { $api } from '@/lib/api/client';
import { useQuery } from '@tanstack/react-query';

/**
 * Event filters interface
 */
export interface EventoFilters {
  page?: number;
  page_size?: number;
  search?: string;
  grupo_eno_id?: number; // Single group filter (legacy)
  grupo_eno_ids?: number[]; // Multiple groups filter
  tipo_eno_id?: number; // Single tipo filter (legacy)
  tipo_eno_ids?: number[]; // Multiple tipos filter
  fecha_desde?: string;
  fecha_hasta?: string;
  clasificacion?: string | string[]; // Can be single or multiple
  es_positivo?: boolean;
  provincia_id?: number[]; // Multiple provinces by INDEC code
  tipo_sujeto?: string;
  requiere_revision?: boolean;
  edad_min?: number;
  edad_max?: number;
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
export function extractEventosData(response: unknown) {
  if (typeof response === 'object' && response !== null && 'data' in response) {
    const data = (response as { data?: unknown }).data;
    if (typeof data === 'object' && data !== null && 'data' in data) {
      return (data as { data?: unknown[] }).data || [];
    }
  }
  return [];
}

/**
 * Utility functions for clasificacion display
 */
export function getClasificacionLabel(clasificacion: string | null | undefined): string {
  if (!clasificacion) return "Sin clasificar";

  const labels: Record<string, string> = {
    'CONFIRMADOS': 'Confirmado',
    'SOSPECHOSOS': 'Sospechoso',
    'PROBABLES': 'Probable',
    'DESCARTADOS': 'Descartado',
    'NEGATIVOS': 'Negativo',
    'EN_ESTUDIO': 'En Estudio',
    'REQUIERE_REVISION': 'Requiere Revisión',
    // Legacy lowercase
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
    'CONFIRMADOS': 'destructive',
    'SOSPECHOSOS': 'outline',
    'PROBABLES': 'secondary',
    'DESCARTADOS': 'secondary',
    'NEGATIVOS': 'secondary',
    'EN_ESTUDIO': 'outline',
    'REQUIERE_REVISION': 'destructive',
    // Legacy
    'sospechoso': 'outline',
    'confirmado': 'destructive',
    'descartado': 'secondary',
    'probable': 'secondary',
    'no_conclusivo': 'default',
  };

  return variants[clasificacion] || 'default';
}

/**
 * Obtiene clases de Tailwind para colorear clasificaciones
 */
export function getClasificacionColorClasses(clasificacion: string | null | undefined): string {
  if (!clasificacion) return "bg-muted text-muted-foreground";

  const colors: Record<string, string> = {
    'CONFIRMADOS': 'bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-400 border-red-200 dark:border-red-900',
    'SOSPECHOSOS': 'bg-yellow-100 text-yellow-700 dark:bg-yellow-950 dark:text-yellow-400 border-yellow-200 dark:border-yellow-900',
    'PROBABLES': 'bg-orange-100 text-orange-700 dark:bg-orange-950 dark:text-orange-400 border-orange-200 dark:border-orange-900',
    'DESCARTADOS': 'bg-gray-100 text-gray-700 dark:bg-gray-950 dark:text-gray-400 border-gray-200 dark:border-gray-900',
    'NEGATIVOS': 'bg-green-100 text-green-700 dark:bg-green-950 dark:text-green-400 border-green-200 dark:border-green-900',
    'EN_ESTUDIO': 'bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-400 border-blue-200 dark:border-blue-900',
    'REQUIERE_REVISION': 'bg-purple-100 text-purple-700 dark:bg-purple-950 dark:text-purple-400 border-purple-200 dark:border-purple-900',
  };

  return colors[clasificacion] || "bg-muted text-muted-foreground";
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

/**
 * Hook to fetch grupos ENO (parent categories)
 */
export function useGruposEno() {
  return $api.useQuery(
    'get',
    '/api/v1/grupos_eno/',
    {}
  );
}

/**
 * Hook to fetch tipos ENO (filtered by grupo if provided)
 */
export function useTiposEno(grupoEnoId?: number) {
  return useQuery({
    queryKey: ['tipos_eno', grupoEnoId],
    queryFn: async () => {
      const response = await fetch(
        grupoEnoId
          ? `/api/v1/tipos_eno/?grupo_eno_id=${grupoEnoId}`
          : `/api/v1/tipos_eno/`
      );
      if (!response.ok) throw new Error('Error fetching tipos ENO');
      return response.json();
    },
  });
}
