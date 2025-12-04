"use client";

/**
 * Loop Block Configurations
 *
 * Estos bloques se repiten automáticamente por cada evento seleccionado en el boletín.
 * El evento viene del contexto del loop, no se selecciona manualmente.
 */

import { Calendar, Filter, LayoutGrid, Bug } from "lucide-react";
import {
  SectionCard,
  ContextBanner,
  OptionSelector,
  ToggleSwitch,
  MultiSelect,
} from "./design-system";
import type { BlockConfigProps } from "./types";

// ════════════════════════════════════════════════════════════════════════════
// CORREDOR LOOP - Corredor endémico del evento actual
// ════════════════════════════════════════════════════════════════════════════

export function CorredorLoopConfig({ formState }: BlockConfigProps) {
  const { editPeriodo, setEditPeriodo } = formState;

  return (
    <>
      <ContextBanner variant="success">
        El corredor se genera automáticamente para cada evento seleccionado en el boletín
      </ContextBanner>

      <SectionCard title="Período de visualización" icon={Calendar}>
        <OptionSelector
          label="¿Qué semanas mostrar?"
          options={[
            {
              value: "anual",
              label: "Año completo",
              description: "Muestra las 52 semanas epidemiológicas",
            },
            {
              value: "seleccionado",
              label: "Período del boletín",
              description: "Solo las semanas seleccionadas",
            },
          ]}
          selected={editPeriodo}
          onChange={setEditPeriodo}
        />
      </SectionCard>
    </>
  );
}

// ════════════════════════════════════════════════════════════════════════════
// CURVA LOOP - Curva epidemiológica del evento actual
// ════════════════════════════════════════════════════════════════════════════

export function CurvaLoopConfig({ formState }: BlockConfigProps) {
  const {
    editChartType,
    setEditChartType,
    editSoloConfirmados,
    setEditSoloConfirmados,
    editSoloInternados,
    setEditSoloInternados,
  } = formState;

  return (
    <>
      <ContextBanner variant="info">
        Muestra la evolución de casos por semana epidemiológica
      </ContextBanner>

      <SectionCard title="Visualización" icon={LayoutGrid}>
        <OptionSelector
          label="Tipo de gráfico"
          options={[
            { value: "bar", label: "Barras", description: "Mejor para comparar períodos" },
            { value: "line", label: "Líneas", description: "Mejor para ver tendencias" },
          ]}
          selected={editChartType}
          onChange={setEditChartType}
        />
      </SectionCard>

      <SectionCard title="Filtros de datos" icon={Filter}>
        <ToggleSwitch
          label="Solo casos confirmados"
          description="Excluye sospechosos y probables"
          checked={editSoloConfirmados}
          onChange={setEditSoloConfirmados}
        />
        <ToggleSwitch
          label="Solo casos internados"
          description="Filtra por condición de internación"
          checked={editSoloInternados}
          onChange={setEditSoloInternados}
        />
      </SectionCard>
    </>
  );
}

// ════════════════════════════════════════════════════════════════════════════
// EDAD LOOP - Distribución por edad del evento actual
// ════════════════════════════════════════════════════════════════════════════

export function EdadLoopConfig({ formState }: BlockConfigProps) {
  const {
    editChartType,
    setEditChartType,
    editSoloConfirmados,
    setEditSoloConfirmados,
    editSoloInternados,
    setEditSoloInternados,
  } = formState;

  return (
    <>
      <ContextBanner variant="info">
        Distribución de casos por grupos etarios estándar
      </ContextBanner>

      <SectionCard title="Visualización" icon={LayoutGrid}>
        <OptionSelector
          label="Tipo de gráfico"
          options={[
            {
              value: "bar",
              label: "Barras verticales",
              description: "Clásico para distribuciones",
            },
            {
              value: "horizontal_bar",
              label: "Barras horizontales",
              description: "Mejor legibilidad de etiquetas",
            },
          ]}
          selected={editChartType}
          onChange={setEditChartType}
        />
      </SectionCard>

      <SectionCard title="Filtros de datos" icon={Filter}>
        <ToggleSwitch
          label="Solo casos confirmados"
          checked={editSoloConfirmados}
          onChange={setEditSoloConfirmados}
        />
        <ToggleSwitch
          label="Solo casos internados"
          checked={editSoloInternados}
          onChange={setEditSoloInternados}
        />
      </SectionCard>
    </>
  );
}

// ════════════════════════════════════════════════════════════════════════════
// MAPA LOOP - Mapa geográfico del evento actual
// ════════════════════════════════════════════════════════════════════════════

export function MapaLoopConfig() {
  return (
    <ContextBanner variant="success">
      El mapa muestra automáticamente la distribución geográfica de casos del evento
      actual. No requiere configuración adicional.
    </ContextBanner>
  );
}

// ════════════════════════════════════════════════════════════════════════════
// COMPARACION ANUAL LOOP - Comparación interanual del evento actual
// ════════════════════════════════════════════════════════════════════════════

export function ComparacionAnualLoopConfig({ formState }: BlockConfigProps) {
  const { editSoloConfirmados, setEditSoloConfirmados } = formState;

  return (
    <>
      <ContextBanner variant="info">
        Compara el acumulado del período actual con el mismo período del año anterior
      </ContextBanner>

      <SectionCard title="Filtros de datos" icon={Filter}>
        <ToggleSwitch
          label="Solo casos confirmados"
          description="Mejora la precisión de la comparación"
          checked={editSoloConfirmados}
          onChange={setEditSoloConfirmados}
        />
      </SectionCard>
    </>
  );
}

// ════════════════════════════════════════════════════════════════════════════
// AGENTES LOOP - Agentes detectados del evento actual
// ════════════════════════════════════════════════════════════════════════════

export function AgentesLoopConfig({ formState, data }: BlockConfigProps) {
  const {
    editAgentesCodigos,
    setEditAgentesCodigos,
    editChartType,
    setEditChartType,
  } = formState;
  const { agentes } = data;

  return (
    <>
      <ContextBanner variant="info">
        Muestra los agentes etiológicos detectados para el evento actual
      </ContextBanner>

      <SectionCard title="Agentes a incluir" icon={Bug}>
        <MultiSelect
          label="Filtrar agentes"
          helpText="Dejá vacío para mostrar todos los detectados"
          items={agentes}
          selected={editAgentesCodigos}
          onChange={setEditAgentesCodigos}
          placeholder="Buscar agente..."
        />
      </SectionCard>

      <SectionCard title="Visualización" icon={LayoutGrid}>
        <OptionSelector
          label="Tipo de gráfico"
          options={[
            { value: "bar", label: "Barras", description: "Comparar cantidades" },
            { value: "pie", label: "Torta", description: "Ver proporciones" },
          ]}
          selected={editChartType}
          onChange={setEditChartType}
        />
      </SectionCard>
    </>
  );
}

// ════════════════════════════════════════════════════════════════════════════
// EDAD POR AGENTE LOOP - Perfil etario por agente del evento actual
// ════════════════════════════════════════════════════════════════════════════

export function EdadPorAgenteLoopConfig({ formState, data }: BlockConfigProps) {
  const {
    editAgentesCodigos,
    setEditAgentesCodigos,
    editChartType,
    setEditChartType,
    editSoloConfirmados,
    setEditSoloConfirmados,
  } = formState;
  const { agentes } = data;

  return (
    <>
      <ContextBanner variant="info">
        Distribución etaria desglosada por agente etiológico
      </ContextBanner>

      <SectionCard title="Agentes a comparar" icon={Bug}>
        <MultiSelect
          label="Seleccionar agentes"
          helpText="Cada agente se mostrará como una serie en el gráfico"
          items={agentes}
          selected={editAgentesCodigos}
          onChange={setEditAgentesCodigos}
          placeholder="Buscar agente..."
          required
        />
      </SectionCard>

      <SectionCard title="Visualización" icon={LayoutGrid}>
        <OptionSelector
          label="Tipo de gráfico"
          options={[
            {
              value: "stacked_bar",
              label: "Barras apiladas",
              description: "Ver total y composición",
            },
            {
              value: "grouped_bar",
              label: "Barras agrupadas",
              description: "Comparar directamente",
            },
          ]}
          selected={editChartType}
          onChange={setEditChartType}
        />
      </SectionCard>

      <SectionCard title="Filtros" icon={Filter}>
        <ToggleSwitch
          label="Solo casos confirmados"
          checked={editSoloConfirmados}
          onChange={setEditSoloConfirmados}
        />
      </SectionCard>
    </>
  );
}

// ════════════════════════════════════════════════════════════════════════════
// INSIGHT BLOCKS - Texto auto-generado, no requieren configuración
// ════════════════════════════════════════════════════════════════════════════

export function InsightEdadConfig() {
  return (
    <ContextBanner variant="success">
      Este bloque genera automáticamente un párrafo descriptivo sobre la
      distribución por edad de los casos. No requiere configuración adicional.
    </ContextBanner>
  );
}

export function InsightGeograficoConfig() {
  return (
    <ContextBanner variant="success">
      Este bloque genera automáticamente un párrafo descriptivo sobre la
      distribución geográfica de los casos. No requiere configuración adicional.
    </ContextBanner>
  );
}

// ════════════════════════════════════════════════════════════════════════════
// REGISTRY - Map block types to their config components
// ════════════════════════════════════════════════════════════════════════════

export const LOOP_BLOCK_CONFIGS: Record<
  string,
  React.ComponentType<BlockConfigProps>
> = {
  corredor_loop: CorredorLoopConfig,
  curva_loop: CurvaLoopConfig,
  edad_loop: EdadLoopConfig,
  mapa_loop: MapaLoopConfig as React.ComponentType<BlockConfigProps>,
  comparacion_anual_loop: ComparacionAnualLoopConfig,
  agentes_loop: AgentesLoopConfig,
  edad_por_agente_loop: EdadPorAgenteLoopConfig,
  insight_distribucion_edad: InsightEdadConfig as React.ComponentType<BlockConfigProps>,
  insight_distribucion_geografica: InsightGeograficoConfig as React.ComponentType<BlockConfigProps>,
};
