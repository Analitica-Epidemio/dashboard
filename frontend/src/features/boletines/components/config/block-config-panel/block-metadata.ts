/**
 * Block Metadata - Define metadata for each block type
 * Separates loop blocks from main/principal blocks
 */

import {
  BarChart3,
  MapPin,
  Users,
  TrendingUp,
  Activity,
  Bug,
  Calendar,
  FileText,
  type LucideIcon,
} from "lucide-react";

export type BlockCategory = "loop" | "summary" | "chart" | "comparison" | "agent" | "insight";

export interface BlockMeta {
  title: string;
  description: string;
  icon: LucideIcon;
  gradient: string;
  category: BlockCategory;
}

// ════════════════════════════════════════════════════════════════════════════
// LOOP BLOCKS - Se repiten automáticamente por cada evento seleccionado
// ════════════════════════════════════════════════════════════════════════════

export const LOOP_BLOCK_METADATA: Record<string, BlockMeta> = {
  corredor_loop: {
    title: "Corredor Endémico",
    description: "Visualiza el comportamiento histórico del evento",
    icon: TrendingUp,
    gradient: "from-emerald-500 to-teal-600",
    category: "loop",
  },
  curva_loop: {
    title: "Curva Epidemiológica",
    description: "Evolución temporal de casos por semana",
    icon: Activity,
    gradient: "from-blue-500 to-indigo-600",
    category: "loop",
  },
  edad_loop: {
    title: "Distribución por Edad",
    description: "Análisis demográfico por grupos etarios",
    icon: Users,
    gradient: "from-pink-500 to-rose-600",
    category: "loop",
  },
  mapa_loop: {
    title: "Mapa de Casos",
    description: "Distribución geográfica en el territorio",
    icon: MapPin,
    gradient: "from-cyan-500 to-blue-600",
    category: "loop",
  },
  comparacion_anual_loop: {
    title: "Comparación Interanual",
    description: "Contraste entre períodos equivalentes",
    icon: Calendar,
    gradient: "from-violet-500 to-purple-600",
    category: "loop",
  },
  agentes_loop: {
    title: "Agentes Detectados",
    description: "Patógenos identificados en el evento",
    icon: Bug,
    gradient: "from-amber-500 to-orange-600",
    category: "loop",
  },
  edad_por_agente_loop: {
    title: "Edad por Agente",
    description: "Perfil etario según agente etiológico",
    icon: Users,
    gradient: "from-amber-500 to-orange-600",
    category: "loop",
  },
  // Insight blocks - Texto auto-generado
  insight_distribucion_edad: {
    title: "Insight de Edad",
    description: "Texto automático sobre distribución etaria",
    icon: FileText,
    gradient: "from-pink-500 to-rose-600",
    category: "insight",
  },
  insight_distribucion_geografica: {
    title: "Insight Geográfico",
    description: "Texto automático sobre distribución territorial",
    icon: FileText,
    gradient: "from-cyan-500 to-blue-600",
    category: "insight",
  },
};

// ════════════════════════════════════════════════════════════════════════════
// MAIN/PRINCIPAL BLOCKS - Bloques independientes, no se repiten
// ════════════════════════════════════════════════════════════════════════════

export const MAIN_BLOCK_METADATA: Record<string, BlockMeta> = {
  // Summary blocks
  top_enos: {
    title: "Top Eventos",
    description: "Ranking de eventos con más notificaciones",
    icon: BarChart3,
    gradient: "from-blue-500 to-indigo-600",
    category: "summary",
  },
  comparacion_periodos_global: {
    title: "Comparación Global",
    description: "Tendencia general respecto al período anterior",
    icon: TrendingUp,
    gradient: "from-indigo-500 to-violet-600",
    category: "comparison",
  },

  // Chart blocks - Evento específico
  curva_evento_especifico: {
    title: "Curva de Evento",
    description: "Selecciona un evento específico para analizar",
    icon: Activity,
    gradient: "from-emerald-500 to-teal-600",
    category: "chart",
  },
  corredor_evento_especifico: {
    title: "Corredor de Evento",
    description: "Corredor endémico de un evento específico",
    icon: TrendingUp,
    gradient: "from-emerald-500 to-teal-600",
    category: "chart",
  },

  // Comparison blocks - Múltiples eventos
  curva_comparar_eventos: {
    title: "Comparar Eventos",
    description: "Superpone múltiples eventos en una curva",
    icon: Activity,
    gradient: "from-indigo-500 to-violet-600",
    category: "comparison",
  },
  edad_comparar_eventos: {
    title: "Edad Comparada",
    description: "Perfil etario de múltiples eventos",
    icon: Users,
    gradient: "from-indigo-500 to-violet-600",
    category: "comparison",
  },

  // Agent blocks
  distribucion_agentes: {
    title: "Distribución de Agentes",
    description: "Total de detecciones por agente",
    icon: Bug,
    gradient: "from-amber-500 to-orange-600",
    category: "agent",
  },
  curva_por_agente: {
    title: "Evolución por Agente",
    description: "Tendencia temporal de cada agente",
    icon: Activity,
    gradient: "from-amber-500 to-orange-600",
    category: "agent",
  },
  edad_por_agente: {
    title: "Edad por Agente",
    description: "Distribución etaria según patógeno",
    icon: Users,
    gradient: "from-amber-500 to-orange-600",
    category: "agent",
  },
};

// Combined metadata for easy lookup
export const BLOCK_METADATA: Record<string, BlockMeta> = {
  ...LOOP_BLOCK_METADATA,
  ...MAIN_BLOCK_METADATA,
};

// Helper to check if a block is a loop block
export function isLoopBlock(blockType: string): boolean {
  return blockType in LOOP_BLOCK_METADATA;
}

// Helper to check if a block is a main block
export function isMainBlock(blockType: string): boolean {
  return blockType in MAIN_BLOCK_METADATA;
}

// Default metadata for unknown blocks
export const DEFAULT_BLOCK_META: BlockMeta = {
  title: "Bloque",
  description: "Bloque dinámico",
  icon: BarChart3,
  gradient: "from-gray-500 to-gray-600",
  category: "chart",
};

// Get metadata with fallback
export function getBlockMeta(blockType: string): BlockMeta {
  return BLOCK_METADATA[blockType] || DEFAULT_BLOCK_META;
}
