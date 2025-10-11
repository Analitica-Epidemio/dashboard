/**
 * Dashboard API - Resumen y estadísticas
 */

import { apiClient } from "./client";

export interface TablaResumen {
  total_eventos: number;
  total_confirmados: number;
  total_sospechosos: number;
  total_negativos: number;
  total_personas_afectadas: number;
  fecha_primer_evento: string | null;
  fecha_ultimo_evento: string | null;
}

export interface EventoStats {
  tipo_eno: string;
  codigo_tipo: string | null;
  total: number;
  clasificaciones: Record<string, number>;
}

export interface GrupoStats {
  grupo_eno: string;
  codigo_grupo: string | null;
  total: number;
  tipos: Array<{
    tipo: string;
    total: number;
  }>;
}

export interface PiramidePoblacional {
  age: string;
  sex: "M" | "F";
  value: number;
}

export interface TerritorioAfectado {
  nivel: "provincia" | "departamento" | "localidad";
  nombre: string;
  codigo_indec: number | null;
  total_eventos: number;
  hijos?: Array<Record<string, unknown>> | null;
}

export interface DashboardResumen {
  tabla_resumen: TablaResumen;
  eventos_mas_tipicos: EventoStats[];
  grupos_mas_tipicos: GrupoStats[];
  piramide_poblacional: PiramidePoblacional[];
  territorios_afectados: TerritorioAfectado[];
}

export interface DashboardResumenParams {
  fecha_desde?: string;
  fecha_hasta?: string;
  grupo_id?: number;
  tipo_eno_ids?: number[];
  clasificacion?: string;
  provincia_id?: number;
}

/**
 * Obtiene el resumen del dashboard con estadísticas
 */
export async function getDashboardResumen(
  params?: DashboardResumenParams
): Promise<DashboardResumen> {
  const response = await apiClient.GET("/api/v1/dashboard/resumen", {
    params: { query: params },
  });

  if (response.error) {
    console.error("Error from API:", response.error);
    throw new Error(JSON.stringify(response.error));
  }

  // El backend devuelve SuccessResponse[DashboardResumen]
  // que tiene estructura: { success: true, data: DashboardResumen }
  const responseData = response.data as any;

  console.log("Raw response:", responseData);

  // Si viene envuelto en SuccessResponse, extraer data
  if (responseData && typeof responseData === 'object' && 'data' in responseData) {
    return responseData.data as DashboardResumen;
  }

  // Si viene directo, retornar tal cual
  return responseData as DashboardResumen;
}
