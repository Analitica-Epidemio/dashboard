/**
 * Definiciones y tipos para secciones del boletín epidemiológico
 * Ahora usa endpoint genérico - las secciones son dinámicas basadas en TipoEno/GrupoEno
 */

import type { LucideIcon } from "lucide-react";
import {
  Activity,
  Flame,
  Droplets,
  Heart,
  FileText,
  Bug,
  Thermometer,
  AlertTriangle,
  CircleDot,
} from "lucide-react";

// ============================================================================
// TIPOS BASE
// ============================================================================

export type ZonaEpidemica = "exito" | "seguridad" | "alerta" | "brote";

// ============================================================================
// PREVIEW DATA TYPES (Compatible con backend)
// ============================================================================

export interface CorredorPreview {
  casos_acumulados: number;
  zona_actual: ZonaEpidemica;
  tendencia: "up" | "down" | "stable";
  porcentaje_cambio?: number;
}

export interface SectionPreviewData {
  loading: boolean;
  error?: string;
  evento_codigo?: string;
  evento_nombre?: string;
  evento_tipo?: "tipo_eno" | "grupo_eno";
  summary?: string;
  metrics?: {
    label: string;
    value: string | number;
    trend?: "up" | "down" | "stable";
    trend_value?: number;
    alert?: boolean;
  }[];
  corredor?: CorredorPreview;
  periodo?: {
    semana_inicio: number;
    semana_fin: number;
    anio: number;
    fecha_inicio: string;
    fecha_fin: string;
  };
}

// ============================================================================
// ICONOS SUGERIDOS POR TIPO DE EVENTO
// ============================================================================

// Mapeo de palabras clave a iconos para sugerir iconos automáticamente
const KEYWORD_ICONS: Record<string, LucideIcon> = {
  respiratori: Activity,
  ira: Activity,
  neumonia: Activity,
  bronquiolitis: Activity,
  influenza: Activity,
  eti: Activity,
  covid: CircleDot,
  virus: CircleDot,
  monoxido: Flame,
  co: Flame,
  intoxicacion: Flame,
  diarrea: Droplets,
  gastro: Droplets,
  suh: Heart,
  uremico: Heart,
  hemolitico: Heart,
  dengue: Bug,
  chagas: Bug,
  vector: Bug,
  fiebre: Thermometer,
  meningitis: AlertTriangle,
  brote: AlertTriangle,
};

export function getIconForEvento(nombre: string): LucideIcon {
  const nombreLower = nombre.toLowerCase();

  for (const [keyword, icon] of Object.entries(KEYWORD_ICONS)) {
    if (nombreLower.includes(keyword)) {
      return icon;
    }
  }

  return FileText; // Default icon
}

// ============================================================================
// COLORES POR TIPO DE EVENTO
// ============================================================================

const KEYWORD_COLORS: Record<string, string> = {
  respiratori: "blue",
  ira: "blue",
  neumonia: "blue",
  bronquiolitis: "blue",
  influenza: "blue",
  eti: "blue",
  covid: "purple",
  virus: "purple",
  monoxido: "orange",
  co: "orange",
  intoxicacion: "orange",
  diarrea: "cyan",
  gastro: "cyan",
  suh: "red",
  uremico: "red",
  hemolitico: "red",
  dengue: "amber",
  chagas: "amber",
  vector: "amber",
  fiebre: "rose",
  meningitis: "red",
};

export function getColorForEvento(nombre: string): string {
  const nombreLower = nombre.toLowerCase();

  for (const [keyword, color] of Object.entries(KEYWORD_COLORS)) {
    if (nombreLower.includes(keyword)) {
      return color;
    }
  }

  return "slate"; // Default color
}

// ============================================================================
// HELPERS
// ============================================================================

export function getZonaColor(zona: ZonaEpidemica): string {
  const colors: Record<ZonaEpidemica, string> = {
    exito: "green",
    seguridad: "yellow",
    alerta: "orange",
    brote: "red",
  };
  return colors[zona];
}

export function getZonaLabel(zona: ZonaEpidemica): string {
  const labels: Record<ZonaEpidemica, string> = {
    exito: "Éxito",
    seguridad: "Seguridad",
    alerta: "Alerta",
    brote: "Brote",
  };
  return labels[zona];
}

