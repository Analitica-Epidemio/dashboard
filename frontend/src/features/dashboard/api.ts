/**
 * Dashboard API - Solo tipos
 */

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
