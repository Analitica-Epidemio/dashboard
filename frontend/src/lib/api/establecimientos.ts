/**
 * Establecimientos API hooks
 */

import { useQuery } from '@tanstack/react-query';
import { getSession } from 'next-auth/react';
import { env } from '@/env';

// === TIPOS PARA LISTADO ===

export interface EstablecimientoListItem {
  id: number;
  nombre: string;
  codigo_refes?: string | null;
  codigo_snvs?: string | null;
  source?: string | null;
  localidad_nombre?: string | null;
  departamento_nombre?: string | null;
  provincia_nombre?: string | null;
  latitud?: number | null;
  longitud?: number | null;
  total_eventos: number;
  eventos_consulta: number;
  eventos_notificacion: number;
  eventos_carga: number;
  eventos_muestra: number;
  eventos_diagnostico: number;
  eventos_tratamiento: number;
}

export interface EstablecimientosListResponse {
  items: EstablecimientoListItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface EstablecimientosFilters {
  page?: number;
  page_size?: number;
  order_by?: 'eventos_desc' | 'eventos_asc' | 'nombre_asc' | 'source_asc';
  source?: string;
  tiene_eventos?: boolean;
}

// === TIPOS PARA MAPA ===

export interface EstablecimientoMapaItem {
  id: number;
  codigo_refes?: string | null;
  nombre: string;
  latitud: number;
  longitud: number;
  id_localidad_indec?: number | null;
  localidad_nombre?: string | null;
  departamento_nombre?: string | null;
  provincia_nombre?: string | null;
}

export interface EstablecimientosMapaResponse {
  items: EstablecimientoMapaItem[];
  total: number;
}

export interface EstablecimientosMapaFilters {
  id_provincia_indec?: number | null;
  id_departamento_indec?: number | null;
  id_localidad_indec?: number | null;
  limit?: number;
}

/**
 * Hook para obtener establecimientos de salud para el mapa
 */
export function useEstablecimientosMapa(filters: EstablecimientosMapaFilters) {
  return useQuery({
    queryKey: ['establecimientos-mapa', filters],
    queryFn: async () => {
      const session = await getSession();

      // Construir query params
      const params = new URLSearchParams();

      if (filters.limit) {
        params.append('limit', filters.limit.toString());
      }
      if (filters.id_provincia_indec) {
        params.append('id_provincia_indec', filters.id_provincia_indec.toString());
      }
      if (filters.id_departamento_indec) {
        params.append('id_departamento_indec', filters.id_departamento_indec.toString());
      }
      if (filters.id_localidad_indec) {
        params.append('id_localidad_indec', filters.id_localidad_indec.toString());
      }

      // Hacer fetch con autenticación
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };

      if (session?.accessToken) {
        headers['Authorization'] = `Bearer ${session.accessToken}`;
      }

      const url = `${env.NEXT_PUBLIC_API_HOST}/api/v1/establecimientos/mapa?${params.toString()}`;
      const response = await fetch(url, { headers });

      if (!response.ok) {
        throw new Error('Error fetching establecimientos');
      }

      const data = await response.json();
      return data.data as EstablecimientosMapaResponse;
    },
  });
}

/**
 * Hook para obtener lista de establecimientos con eventos
 */
export function useEstablecimientos(filters: EstablecimientosFilters) {
  return useQuery({
    queryKey: ['establecimientos', filters],
    queryFn: async () => {
      const session = await getSession();

      // Construir query params
      const params = new URLSearchParams();

      if (filters.page) {
        params.append('page', filters.page.toString());
      }
      if (filters.page_size) {
        params.append('page_size', filters.page_size.toString());
      }
      if (filters.order_by) {
        params.append('order_by', filters.order_by);
      }
      if (filters.source) {
        params.append('source', filters.source);
      }
      if (filters.tiene_eventos !== undefined) {
        params.append('tiene_eventos', filters.tiene_eventos.toString());
      }

      // Hacer fetch con autenticación
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };

      if (session?.accessToken) {
        headers['Authorization'] = `Bearer ${session.accessToken}`;
      }

      const url = `${env.NEXT_PUBLIC_API_HOST}/api/v1/establecimientos?${params.toString()}`;
      const response = await fetch(url, { headers });

      if (!response.ok) {
        throw new Error('Error fetching establecimientos list');
      }

      const data = await response.json();
      return data;
    },
  });
}

// ============================================================================
// MAPEO SNVS → IGN
// ============================================================================

export interface SugerenciaMapeo {
  id_establecimiento_ign: number;
  nombre_ign: string;
  codigo_refes?: string | null;
  localidad_nombre?: string | null;
  departamento_nombre?: string | null;
  provincia_nombre?: string | null;
  similitud_nombre: number;
  score: number;
  confianza: string; // HIGH, MEDIUM, LOW
  razon: string;
  provincia_match: boolean;
  departamento_match: boolean;
  localidad_match: boolean;
}

export interface EstablecimientoSinMapear {
  id: number;
  nombre: string;
  codigo_snvs?: string | null;
  localidad_nombre?: string | null;
  departamento_nombre?: string | null;
  provincia_nombre?: string | null;
  total_eventos: number;
  sugerencias: SugerenciaMapeo[];
}

export interface EstablecimientosSinMapearResponse {
  items: EstablecimientoSinMapear[];
  total: number;
  sin_mapear_count: number;
  eventos_sin_mapear_count: number;
}

export interface EstablecimientoIGNResult {
  id: number;
  nombre: string;
  codigo_refes?: string | null;
  localidad_nombre?: string | null;
  departamento_nombre?: string | null;
  provincia_nombre?: string | null;
  latitud?: number | null;
  longitud?: number | null;
}

export interface BuscarIGNResponse {
  items: EstablecimientoIGNResult[];
  total: number;
  page: number;
  page_size: number;
}

export interface MapeoInfo {
  id_establecimiento_snvs: number;
  nombre_snvs: string;
  codigo_snvs?: string | null;
  id_establecimiento_ign: number;
  nombre_ign: string;
  codigo_refes?: string | null;
  mapeo_score?: number | null;
  mapeo_similitud_nombre?: number | null;
  mapeo_confianza?: string | null;
  mapeo_razon?: string | null;
  mapeo_es_manual?: boolean | null;
  mapeo_validado?: boolean | null;
  total_eventos: number;
  localidad_nombre_snvs?: string | null;
  localidad_nombre_ign?: string | null;
  provincia_nombre_snvs?: string | null;
  provincia_nombre_ign?: string | null;
}

export interface MapeosListResponse {
  items: MapeoInfo[];
  total: number;
  page: number;
  page_size: number;
}

/**
 * Hook para obtener establecimientos sin mapear con sugerencias
 */
export function useEstablecimientosSinMapear(options?: {
  limit?: number;
  offset?: number;
  con_eventos_solo?: boolean;
  incluir_sugerencias?: boolean;
  enabled?: boolean;
}) {
  return useQuery({
    queryKey: ['establecimientos-sin-mapear', options],
    queryFn: async () => {
      const session = await getSession();

      const params = new URLSearchParams();
      if (options?.limit) params.append('limit', options.limit.toString());
      if (options?.offset) params.append('offset', options.offset.toString());
      if (options?.con_eventos_solo !== undefined) params.append('con_eventos_solo', options.con_eventos_solo.toString());
      if (options?.incluir_sugerencias !== undefined) params.append('incluir_sugerencias', options.incluir_sugerencias.toString());

      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };

      if (session?.accessToken) {
        headers['Authorization'] = `Bearer ${session.accessToken}`;
      }

      const url = `${env.NEXT_PUBLIC_API_HOST}/api/v1/establecimientos/sin-mapear?${params.toString()}`;
      const response = await fetch(url, { headers });

      if (!response.ok) {
        throw new Error('Error fetching establecimientos sin mapear');
      }

      const data = await response.json();
      return data.data as EstablecimientosSinMapearResponse;
    },
    enabled: options?.enabled !== false,
  });
}

/**
 * Hook para buscar establecimientos IGN
 */
export function useBuscarEstablecimientosIGN(options: {
  q?: string;
  provincia?: string;
  departamento?: string;
  page?: number;
  page_size?: number;
  enabled?: boolean;
}) {
  return useQuery({
    queryKey: ['buscar-ign', options],
    queryFn: async () => {
      const session = await getSession();

      const params = new URLSearchParams();
      if (options.q) params.append('q', options.q);
      if (options.provincia) params.append('provincia', options.provincia);
      if (options.departamento) params.append('departamento', options.departamento);
      if (options.page) params.append('page', options.page.toString());
      if (options.page_size) params.append('page_size', options.page_size.toString());

      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };

      if (session?.accessToken) {
        headers['Authorization'] = `Bearer ${session.accessToken}`;
      }

      const url = `${env.NEXT_PUBLIC_API_HOST}/api/v1/establecimientos/ign/buscar?${params.toString()}`;
      const response = await fetch(url, { headers });

      if (!response.ok) {
        throw new Error('Error buscando establecimientos IGN');
      }

      const data = await response.json();
      return data.data as BuscarIGNResponse;
    },
    enabled: options.enabled !== false,
  });
}

/**
 * Hook para listar mapeos existentes
 */
export function useMapeosExistentes(options?: {
  page?: number;
  page_size?: number;
  confianza?: string;
  validados_solo?: boolean;
  manuales_solo?: boolean;
  enabled?: boolean;
}) {
  return useQuery({
    queryKey: ['mapeos-existentes', options],
    queryFn: async () => {
      const session = await getSession();

      const params = new URLSearchParams();
      if (options?.page) params.append('page', options.page.toString());
      if (options?.page_size) params.append('page_size', options.page_size.toString());
      if (options?.confianza) params.append('confianza', options.confianza);
      if (options?.validados_solo !== undefined) params.append('validados_solo', options.validados_solo.toString());
      if (options?.manuales_solo !== undefined) params.append('manuales_solo', options.manuales_solo.toString());

      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };

      if (session?.accessToken) {
        headers['Authorization'] = `Bearer ${session.accessToken}`;
      }

      const url = `${env.NEXT_PUBLIC_API_HOST}/api/v1/establecimientos/mapeos?${params.toString()}`;
      const response = await fetch(url, { headers });

      if (!response.ok) {
        throw new Error('Error fetching mapeos existentes');
      }

      const data = await response.json();
      return data.data as MapeosListResponse;
    },
    enabled: options?.enabled !== false,
  });
}

/**
 * Crear mapeo SNVS → IGN
 */
export async function crearMapeo(data: {
  id_establecimiento_snvs: number;
  id_establecimiento_ign: number;
  razon?: string;
}) {
  const session = await getSession();

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };

  if (session?.accessToken) {
    headers['Authorization'] = `Bearer ${session.accessToken}`;
  }

  const url = `${env.NEXT_PUBLIC_API_HOST}/api/v1/establecimientos/mapeos`;
  const response = await fetch(url, {
    method: 'POST',
    headers,
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Error creando mapeo');
  }

  return response.json();
}

/**
 * Actualizar mapeo existente
 */
export async function actualizarMapeo(
  id_establecimiento_snvs: number,
  data: {
    id_establecimiento_ign_nuevo: number;
    razon?: string;
  }
) {
  const session = await getSession();

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };

  if (session?.accessToken) {
    headers['Authorization'] = `Bearer ${session.accessToken}`;
  }

  const url = `${env.NEXT_PUBLIC_API_HOST}/api/v1/establecimientos/mapeos/${id_establecimiento_snvs}`;
  const response = await fetch(url, {
    method: 'PUT',
    headers,
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Error actualizando mapeo');
  }

  return response.json();
}

/**
 * Eliminar mapeo (desvincular)
 */
export async function eliminarMapeo(id_establecimiento_snvs: number) {
  const session = await getSession();

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };

  if (session?.accessToken) {
    headers['Authorization'] = `Bearer ${session.accessToken}`;
  }

  const url = `${env.NEXT_PUBLIC_API_HOST}/api/v1/establecimientos/mapeos/${id_establecimiento_snvs}`;
  const response = await fetch(url, {
    method: 'DELETE',
    headers,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Error eliminando mapeo');
  }

  return response.json();
}

/**
 * Aceptar múltiples sugerencias en bulk
 */
export async function aceptarSugerenciasBulk(mapeos: Array<{
  id_establecimiento_snvs: number;
  id_establecimiento_ign: number;
  razon?: string;
}>) {
  const session = await getSession();

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };

  if (session?.accessToken) {
    headers['Authorization'] = `Bearer ${session.accessToken}`;
  }

  const url = `${env.NEXT_PUBLIC_API_HOST}/api/v1/establecimientos/mapeos/bulk`;
  const response = await fetch(url, {
    method: 'POST',
    headers,
    body: JSON.stringify({ mapeos }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Error aceptando sugerencias');
  }

  return response.json();
}
