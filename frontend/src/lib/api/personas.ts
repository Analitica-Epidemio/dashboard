/**
 * Personas API hooks and utilities (PERSON-CENTERED)
 * Uses the typed $api client for all requests
 */

import { $api } from '@/lib/api/client';

/**
 * Persona filters interface
 * Filtra personas por características de sus eventos asociados
 *
 * IMPORTANTE: provincia_id filtra por ESTABLECIMIENTO DE NOTIFICACIÓN de los eventos,
 * no por domicilio de la persona
 */
export interface PersonaFilters {
  page?: number;
  page_size?: number;
  search?: string;
  tipo_sujeto?: 'humano' | 'animal' | 'todos';
  provincia_id?: number[];  // Backend alias para provincia_ids_establecimiento_notificacion
  tipo_eno_ids?: number[];  // IDs de tipos de eventos
  grupo_eno_ids?: number[];  // IDs de grupos de eventos
  tiene_multiples_eventos?: boolean;
  edad_min?: number;
  edad_max?: number;
  sort_by?: 'nombre_asc' | 'nombre_desc' | 'eventos_desc' | 'eventos_asc' | 'ultimo_evento_desc' | 'ultimo_evento_asc';
}

/**
 * Hook to fetch personas list with filters
 */
export function usePersonas(params?: PersonaFilters) {
  return $api.useQuery(
    'get',
    '/api/v1/personas/',
    {
      params: {
        query: params,
      },
    }
  );
}

/**
 * Hook to fetch a single persona by ID
 */
export function usePersona(tipoSujeto: 'humano' | 'animal', personaId: number) {
  return $api.useQuery(
    'get',
    '/api/v1/personas/{tipo_sujeto}/{persona_id}',
    {
      params: {
        path: { tipo_sujeto: tipoSujeto, persona_id: personaId },
      },
    },
    {
      enabled: !!personaId && !!tipoSujeto,
    }
  );
}

/**
 * Hook to fetch persona timeline
 */
export function usePersonaTimeline(tipoSujeto: 'humano' | 'animal', personaId: number) {
  return $api.useQuery(
    'get',
    '/api/v1/personas/{tipo_sujeto}/{persona_id}/timeline',
    {
      params: {
        path: { tipo_sujeto: tipoSujeto, persona_id: personaId },
      },
    },
    {
      enabled: !!personaId && !!tipoSujeto,
    }
  );
}

/**
 * Extract personas data from API response
 */
export function extractPersonasData(response: any) {
  return response?.data?.data || [];
}

/**
 * Utility functions for tipo_sujeto display
 */
export function getTipoSujetoLabel(tipo: string | null | undefined): string {
  if (!tipo) return "Desconocido";

  const labels: Record<string, string> = {
    'humano': 'Humano',
    'animal': 'Animal',
    'desconocido': 'Desconocido',
  };

  return labels[tipo] || tipo;
}

export function getTipoSujetoIcon(tipo: string | null | undefined): string {
  if (!tipo) return "help-circle";

  const icons: Record<string, string> = {
    'humano': 'user',
    'animal': 'paw',
    'desconocido': 'help-circle',
  };

  return icons[tipo] || 'help-circle';
}

/**
 * Format edad (age) display
 */
export function formatEdad(edad: number | null | undefined): string {
  if (!edad) return "N/A";
  return `${edad} años`;
}

/**
 * Get badge variant for evento count
 */
export function getEventoCountVariant(count: number): "default" | "destructive" | "secondary" | "outline" {
  if (count === 0) return "secondary";
  if (count === 1) return "outline";
  if (count >= 5) return "destructive";
  return "default";
}
