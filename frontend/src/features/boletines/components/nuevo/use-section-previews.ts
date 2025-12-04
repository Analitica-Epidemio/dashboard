"use client";

/**
 * Hook para obtener datos de preview de secciones del boletín
 * Re-exporta hooks de la API central
 */

export { useEventoPreview, useEventosDisponibles } from "@/features/boletines/api";

// Re-export types from section-definitions for convenience
export type {
  SectionPreviewData,
  CorredorPreview,
  ZonaEpidemica,
} from "./section-definitions";
