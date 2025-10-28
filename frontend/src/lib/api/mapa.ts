/**
 * Mapa API hooks
 */

import { useQuery } from '@tanstack/react-query';
import { getSession } from 'next-auth/react';
import { env } from '@/env';

export interface DomicilioMapaItem {
  id: string;
  nombre: string;
  total_eventos: number;
  latitud: number;
  longitud: number;
  id_provincia_indec: number;
  id_departamento_indec?: number | null;
  id_localidad_indec: number;
  provincia_nombre: string;
  departamento_nombre?: string | null;
  localidad_nombre: string;
}

export interface DomicilioMapaResponse {
  items: DomicilioMapaItem[];
  total: number;
  total_eventos: number;
}

export interface MapaFilters {
  id_provincia_indec?: number | null;
  id_departamento_indec?: number | null;
  id_localidad_indec?: number | null;
  id_grupo_eno?: number | null;
  id_tipo_eno?: number | null;
  limit?: number;
}

/**
 * Hook to fetch domicilios geocodificados con eventos para mapa de puntos
 */
export function useDomiciliosMapa(filters: MapaFilters) {
  return useQuery({
    queryKey: ['domicilios-mapa', filters],
    queryFn: async () => {
      // Obtener sesión para el token
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
      if (filters.id_grupo_eno) {
        params.append('id_grupo_eno', filters.id_grupo_eno.toString());
      }
      if (filters.id_tipo_eno) {
        params.append('id_tipo_eno', filters.id_tipo_eno.toString());
      }
      if (filters.fecha_hasta) {
        params.append('fecha_hasta', filters.fecha_hasta);
      }

      // Hacer fetch con autenticación
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };

      if (session?.accessToken) {
        headers['Authorization'] = `Bearer ${session.accessToken}`;
      }

      const url = `${env.NEXT_PUBLIC_API_HOST}/api/v1/eventos/domicilios/mapa?${params.toString()}`;
      console.log('🌐 Fetching mapa:', url);

      const response = await fetch(url, { headers });

      console.log('📡 Response status:', response.status);

      if (!response.ok) {
        console.error('❌ Error response:', response.status, response.statusText);
        throw new Error('Error fetching mapa data');
      }

      const data = await response.json();
      console.log('✅ Mapa data recibida:', {
        total: data?.data?.total,
        total_eventos: data?.data?.total_eventos,
        items_sample: data?.data?.items?.slice(0, 3),
      });

      return data;
    },
  });
}
