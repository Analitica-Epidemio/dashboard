/**
 * Personas API hooks and utilities (PERSON-CENTERED)
 * Uses the typed $api client for all requests
 */

import { $api } from '@/lib/api/client';
import type { operations, components } from '@/lib/api/types';

/**
 * Persona filters - extracted from API types
 * IMPORTANTE: provincia_id filtra por ESTABLECIMIENTO DE NOTIFICACIÓN de los eventos,
 * no por domicilio de la persona
 */
export type PersonaFilters = operations["list_personas_api_v1_personas__get"]["parameters"]["query"];

/**
 * Persona detail response - extracted from API types
 */
export type PersonaDetail = components["schemas"]["PersonaDetailResponse"];

/**
 * Persona list item - extracted from API types
 */
export type PersonaListItem = components["schemas"]["PersonaListItem"];

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
