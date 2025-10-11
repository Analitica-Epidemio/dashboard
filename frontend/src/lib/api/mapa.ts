/**
 * Mapa API hooks
 */

import { useQuery } from '@tanstack/react-query';
import { getSession } from 'next-auth/react';
import { env } from '@/env';

export interface EventoMapaItem {
  id: string;
  nombre: string;
  nivel: "provincia" | "departamento" | "localidad";
  total_eventos: number;
  latitud?: number | null;
  longitud?: number | null;
  id_provincia_indec?: number | null;
  id_departamento_indec?: number | null;
  id_localidad_indec?: number | null;
  provincia_nombre?: string | null;
  departamento_nombre?: string | null;
}

export interface EventoMapaResponse {
  items: EventoMapaItem[];
  total: number;
  nivel: "provincia" | "departamento" | "localidad";
}

export interface MapaFilters {
  nivel: "provincia" | "departamento" | "localidad";
  id_provincia_indec?: number | null;
  id_departamento_indec?: number | null;
  id_grupo_eno?: number | null;
  id_tipo_eno?: number | null;
}

/**
 * Hook to fetch eventos grouped by geographic location
 */
export function useEventosMapa(filters: MapaFilters) {
  return useQuery({
    queryKey: ['eventos-mapa', filters],
    queryFn: async () => {
      // Obtener sesión para el token
      const session = await getSession();

      // Construir query params
      const params = new URLSearchParams();
      params.append('nivel', filters.nivel);

      if (filters.id_provincia_indec) {
        params.append('id_provincia_indec', filters.id_provincia_indec.toString());
      }
      if (filters.id_departamento_indec) {
        params.append('id_departamento_indec', filters.id_departamento_indec.toString());
      }
      if (filters.id_grupo_eno) {
        params.append('id_grupo_eno', filters.id_grupo_eno.toString());
      }
      if (filters.id_tipo_eno) {
        params.append('id_tipo_eno', filters.id_tipo_eno.toString());
      }

      // Hacer fetch con autenticación
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };

      if (session?.accessToken) {
        headers['Authorization'] = `Bearer ${session.accessToken}`;
      }

      const url = `${env.NEXT_PUBLIC_API_HOST}/api/v1/eventos/mapa?${params.toString()}`;
      console.log('🌐 Fetching mapa:', url);

      const response = await fetch(url, { headers });

      console.log('📡 Response status:', response.status);

      if (!response.ok) {
        console.error('❌ Error response:', response.status, response.statusText);
        throw new Error('Error fetching mapa data');
      }

      const data = await response.json();
      console.log('✅ Mapa data recibida:', {
        nivel: data?.data?.nivel,
        total: data?.data?.total,
        items_sample: data?.data?.items?.slice(0, 3),
      });

      return data;
    },
  });
}
