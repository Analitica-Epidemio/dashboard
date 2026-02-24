/**
 * Utilidades compartidas para clasificaciones epidemiológicas
 */

import type { TipoClasificacion } from "@/features/eventos/api";

export function getClasificacionLabel(clasificacion: TipoClasificacion | string | null | undefined): string {
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

export function getClasificacionVariant(clasificacion: TipoClasificacion | string | null | undefined): "default" | "destructive" | "secondary" | "outline" {
  if (!clasificacion) return "default";

  const variants: Record<string, "default" | "destructive" | "secondary" | "outline"> = {
    'CONFIRMADOS': 'destructive',
    'SOSPECHOSOS': 'outline',
    'PROBABLES': 'secondary',
    'DESCARTADOS': 'secondary',
    'NEGATIVOS': 'secondary',
    'EN_ESTUDIO': 'outline',
    'REQUIERE_REVISION': 'outline',
  };

  return variants[clasificacion] || "default";
}

export function getClasificacionColorClasses(clasificacion: TipoClasificacion | string | null | undefined): string {
  if (!clasificacion) return "bg-muted text-muted-foreground";

  const colors: Record<string, string> = {
    'CONFIRMADOS': 'bg-red-100 text-red-700 border-red-200',
    'SOSPECHOSOS': 'bg-yellow-100 text-yellow-700 border-yellow-200',
    'PROBABLES': 'bg-orange-100 text-orange-700 border-orange-200',
    'DESCARTADOS': 'bg-gray-100 text-gray-700 border-gray-200',
    'NEGATIVOS': 'bg-green-100 text-green-700 border-green-200',
    'EN_ESTUDIO': 'bg-blue-100 text-blue-700 border-blue-200',
    'REQUIERE_REVISION': 'bg-purple-100 text-purple-700 border-purple-200',
  };

  return colors[clasificacion] || "bg-muted text-muted-foreground";
}

export function getClasificacionEstrategiaColor(clasificacion: string | null | undefined): string {
  if (!clasificacion) return "text-gray-500";

  const colors: Record<string, string> = {
    'sospechoso': 'text-yellow-600',
    'confirmado': 'text-red-600',
    'descartado': 'text-green-600',
    'probable': 'text-blue-600',
    'no_conclusivo': 'text-gray-600',
  };

  return colors[clasificacion] || "text-gray-500";
}
