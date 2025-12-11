"use client";

/**
 * Main Block Configurations
 *
 * Estos bloques NO se repiten. Son independientes y requieren
 * selección manual de eventos/agentes.
 */

import { Activity, Calendar, Filter, LayoutGrid, Layers, LineChart } from "lucide-react";
import {
  SectionCard,
  ContextBanner,
  OptionSelector,
  ToggleSwitch,
  MultiSelect,
  NumberInput,
} from "./design-system";
import { SeriesEditor } from "./series-editor";
import type { BlockConfigProps } from "./types";

// ════════════════════════════════════════════════════════════════════════════
// TOP ENOS - Ranking de eventos más notificados
// ════════════════════════════════════════════════════════════════════════════

export function TopEnosConfig({ formState }: BlockConfigProps) {
  const { editLimit, setEditLimit, editPeriodo, setEditPeriodo } = formState;

  return (
    <>
      <SectionCard title="Período de los datos" icon={Calendar}>
        <OptionSelector
          label="Casos a incluir en el ranking"
          options={[
            { value: "anual", label: "Año completo", description: "Todos los casos del año del boletín" },
            { value: "seleccionado", label: "Período del boletín", description: "Solo casos dentro del período configurado" },
          ]}
          selected={editPeriodo}
          onChange={setEditPeriodo}
        />
      </SectionCard>

      <SectionCard title="Configuración de tabla" icon={Layers}>
        <NumberInput
          label="Cantidad de eventos a mostrar"
          helpText="Se muestran los eventos con más casos notificados"
          value={editLimit}
          onChange={setEditLimit}
          min={1}
          max={50}
        />
      </SectionCard>
    </>
  );
}

// ════════════════════════════════════════════════════════════════════════════
// COMPARACION PERIODOS GLOBAL - Tendencia general vs período anterior
// ════════════════════════════════════════════════════════════════════════════

export function ComparacionPeriodosGlobalConfig({ formState }: BlockConfigProps) {
  const { editLimit, setEditLimit } = formState;

  return (
    <>
      <SectionCard title="Período de comparación (fijo)" icon={Calendar}>
        <ContextBanner variant="info">
          <div className="space-y-2">
            <p className="text-xs">
              Este bloque compara automáticamente dos períodos:
            </p>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="bg-background/50 rounded p-2">
                <p className="font-medium text-primary">Período actual</p>
                <p className="opacity-70">SE inicio → SE fin del boletín</p>
              </div>
              <div className="bg-background/50 rounded p-2">
                <p className="font-medium text-muted-foreground">Período anterior</p>
                <p className="opacity-70">Mismas SE del año pasado</p>
              </div>
            </div>
            <p className="text-[10px] opacity-60 mt-1">
              Ejemplo: Si el boletín es SE 1-10 de 2025, compara con SE 1-10 de 2024
            </p>
          </div>
        </ContextBanner>
      </SectionCard>

      <SectionCard title="Configuración" icon={Layers}>
        <NumberInput
          label="Cantidad de eventos a mostrar"
          helpText="Se muestran los eventos ordenados por variación porcentual"
          value={editLimit}
          onChange={setEditLimit}
          min={1}
          max={50}
        />
      </SectionCard>
    </>
  );
}

// ════════════════════════════════════════════════════════════════════════════
// CURVA/CORREDOR EVENTO ESPECIFICO - Un solo evento seleccionado
// ════════════════════════════════════════════════════════════════════════════

export function CurvaEventoEspecificoConfig({ formState, data }: BlockConfigProps) {
  const {
    editEventoCodigo,
    setEditEventoCodigo,
    editChartType,
    setEditChartType,
    editSoloConfirmados,
    setEditSoloConfirmados,
    editSoloInternados,
    setEditSoloInternados,
    editPeriodo,
    setEditPeriodo,
  } = formState;
  const { tiposEno } = data;

  return (
    <>
      {!editEventoCodigo && (
        <ContextBanner variant="warning">
          Seleccioná un evento para generar el gráfico
        </ContextBanner>
      )}

      <SectionCard title="Evento a analizar" icon={Activity}>
        <MultiSelect
          label="Seleccionar evento"
          items={tiposEno}
          selected={editEventoCodigo ? [editEventoCodigo] : []}
          onChange={(arr) => setEditEventoCodigo(arr[0] || "")}
          placeholder="Buscar evento..."
          required
        />
      </SectionCard>

      <SectionCard title="Período temporal" icon={Calendar}>
        <OptionSelector
          label="Rango de semanas a mostrar"
          options={[
            { value: "anual", label: "Año completo", description: "Semanas 1 a 52 del año del boletín" },
            { value: "seleccionado", label: "Período del boletín", description: "Desde semana inicio hasta semana fin configuradas" },
          ]}
          selected={editPeriodo}
          onChange={setEditPeriodo}
        />
      </SectionCard>

      <SectionCard title="Visualización" icon={LayoutGrid}>
        <OptionSelector
          label="Tipo de gráfico"
          options={[
            { value: "bar", label: "Barras" },
            { value: "line", label: "Líneas" },
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
        <ToggleSwitch
          label="Solo casos internados"
          checked={editSoloInternados}
          onChange={setEditSoloInternados}
        />
      </SectionCard>
    </>
  );
}

export function CorredorEventoEspecificoConfig({ formState, data }: BlockConfigProps) {
  const { editEventoCodigo, setEditEventoCodigo, editPeriodo, setEditPeriodo } =
    formState;
  const { tiposEno } = data;

  return (
    <>
      {!editEventoCodigo && (
        <ContextBanner variant="warning">
          Seleccioná un evento para generar el corredor
        </ContextBanner>
      )}

      <SectionCard title="Evento a analizar" icon={Activity}>
        <MultiSelect
          label="Seleccionar evento"
          items={tiposEno}
          selected={editEventoCodigo ? [editEventoCodigo] : []}
          onChange={(arr) => setEditEventoCodigo(arr[0] || "")}
          placeholder="Buscar evento..."
          required
        />
      </SectionCard>

      <SectionCard title="Período" icon={Calendar}>
        <OptionSelector
          label="Semanas a mostrar"
          options={[
            { value: "anual", label: "Año completo", description: "52 semanas" },
            { value: "seleccionado", label: "Período del boletín" },
          ]}
          selected={editPeriodo}
          onChange={setEditPeriodo}
        />
      </SectionCard>
    </>
  );
}

// ════════════════════════════════════════════════════════════════════════════
// COMPARAR EVENTOS - Múltiples eventos superpuestos
// ════════════════════════════════════════════════════════════════════════════

export function CurvaCompararEventosConfig({ formState, data }: BlockConfigProps) {
  const {
    editChartType,
    setEditChartType,
    editSoloConfirmados,
    setEditSoloConfirmados,
    editSeries,
    setEditSeries,
    editPeriodo,
    setEditPeriodo,
  } = formState;
  const { tiposEno } = data;

  // Count total eventos selected across all series
  const totalEventosSeleccionados = editSeries.reduce(
    (acc, s) => acc + s.valores.length,
    0
  );

  return (
    <>
      {totalEventosSeleccionados < 2 && (
        <ContextBanner variant="warning">
          Agregá al menos 2 eventos en las series para comparar
        </ContextBanner>
      )}

      <SectionCard title="Series de eventos" icon={LineChart}>
        <SeriesEditor
          series={editSeries}
          onChange={setEditSeries}
          availableItems={tiposEno}
          itemType="evento"
        />
        <p className="text-xs text-muted-foreground mt-2">
          Cada serie agrupa uno o más eventos. Los datos se mostrarán con el
          label y color configurados.
        </p>
      </SectionCard>

      <SectionCard title="Período temporal" icon={Calendar}>
        <OptionSelector
          label="Rango de semanas a mostrar"
          options={[
            { value: "anual", label: "Año completo", description: "Semanas 1 a 52 del año del boletín" },
            { value: "seleccionado", label: "Período del boletín", description: "Desde semana inicio hasta semana fin configuradas" },
          ]}
          selected={editPeriodo}
          onChange={setEditPeriodo}
        />
      </SectionCard>

      <SectionCard title="Visualización" icon={LayoutGrid}>
        <OptionSelector
          label="Tipo de gráfico"
          options={[
            { value: "line", label: "Líneas", description: "Mejor para comparar tendencias" },
            { value: "bar", label: "Barras agrupadas" },
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

export function EdadCompararEventosConfig({ formState, data }: BlockConfigProps) {
  const {
    editChartType,
    setEditChartType,
    editSoloConfirmados,
    setEditSoloConfirmados,
    editSeries,
    setEditSeries,
    editPeriodo,
    setEditPeriodo,
  } = formState;
  const { tiposEno } = data;

  // Count total eventos selected across all series
  const totalEventosSeleccionados = editSeries.reduce(
    (acc, s) => acc + s.valores.length,
    0
  );

  return (
    <>
      {totalEventosSeleccionados < 2 && (
        <ContextBanner variant="warning">
          Agregá al menos 2 eventos en las series para comparar
        </ContextBanner>
      )}

      <SectionCard title="Series de eventos" icon={LineChart}>
        <SeriesEditor
          series={editSeries}
          onChange={setEditSeries}
          availableItems={tiposEno}
          itemType="evento"
        />
        <p className="text-xs text-muted-foreground mt-2">
          Cada serie agrupa uno o más eventos. Los datos se mostrarán con el
          label y color configurados.
        </p>
      </SectionCard>

      <SectionCard title="Período de los datos" icon={Calendar}>
        <OptionSelector
          label="Casos a incluir"
          options={[
            { value: "anual", label: "Año completo", description: "Todos los casos del año del boletín" },
            { value: "seleccionado", label: "Período del boletín", description: "Solo casos dentro del período configurado" },
          ]}
          selected={editPeriodo}
          onChange={setEditPeriodo}
        />
      </SectionCard>

      <SectionCard title="Visualización" icon={LayoutGrid}>
        <OptionSelector
          label="Tipo de gráfico"
          options={[
            { value: "stacked_bar", label: "Barras apiladas" },
            { value: "grouped_bar", label: "Barras agrupadas" },
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
// AGENTES - Análisis de agentes etiológicos
// ════════════════════════════════════════════════════════════════════════════

export function DistribucionAgentesConfig({ formState, data }: BlockConfigProps) {
  const {
    editEventoCodigo,
    setEditEventoCodigo,
    editEventosCodigos,
    setEditEventosCodigos,
    editChartType,
    setEditChartType,
    editSeries,
    setEditSeries,
  } = formState;
  const { tiposEno, agentes } = data;

  // Count total agentes selected across all series
  const totalAgentesSeleccionados = editSeries.reduce(
    (acc, s) => acc + s.valores.length,
    0
  );

  const hasEventos =
    editEventosCodigos.length > 0 || editEventoCodigo.length > 0;

  return (
    <>
      <SectionCard title="Eventos fuente" icon={Activity}>
        <MultiSelect
          label="Eventos a analizar"
          helpText="Los agentes se buscarán en estos eventos"
          items={tiposEno}
          selected={
            editEventosCodigos.length > 0
              ? editEventosCodigos
              : editEventoCodigo
                ? [editEventoCodigo]
                : []
          }
          onChange={(arr) => {
            setEditEventosCodigos(arr);
            setEditEventoCodigo(arr[0] || "");
          }}
          placeholder="Buscar eventos..."
          required
        />
      </SectionCard>

      {!hasEventos && (
        <ContextBanner variant="warning">
          Seleccioná al menos un evento fuente
        </ContextBanner>
      )}

      {hasEventos && totalAgentesSeleccionados === 0 && (
        <ContextBanner variant="warning">
          Agregá al menos un agente en las series
        </ContextBanner>
      )}

      {hasEventos && (
        <SectionCard title="Series de agentes" icon={LineChart}>
          <SeriesEditor
            series={editSeries}
            onChange={setEditSeries}
            availableItems={agentes}
            itemType="agente"
          />
          <p className="text-xs text-muted-foreground mt-2">
            Cada serie agrupa uno o más agentes. Los datos se mostrarán con el
            label y color configurados.
          </p>
        </SectionCard>
      )}

      <SectionCard title="Visualización" icon={LayoutGrid}>
        <OptionSelector
          label="Tipo de gráfico"
          options={[
            { value: "bar", label: "Barras" },
            { value: "pie", label: "Torta" },
          ]}
          selected={editChartType}
          onChange={setEditChartType}
        />
      </SectionCard>
    </>
  );
}

export function CurvaPorAgenteConfig({ formState, data }: BlockConfigProps) {
  const {
    editEventoCodigo,
    setEditEventoCodigo,
    editEventosCodigos,
    setEditEventosCodigos,
    editChartType,
    setEditChartType,
    editSoloConfirmados,
    setEditSoloConfirmados,
    editSeries,
    setEditSeries,
    editPeriodo,
    setEditPeriodo,
  } = formState;
  const { tiposEno, agentes } = data;

  // Count total agentes selected across all series
  const totalAgentesSeleccionados = editSeries.reduce(
    (acc, s) => acc + s.valores.length,
    0
  );

  const hasEventos =
    editEventosCodigos.length > 0 || editEventoCodigo.length > 0;

  return (
    <>
      <SectionCard title="Eventos fuente" icon={Activity}>
        <MultiSelect
          label="Eventos a analizar"
          helpText="Los agentes se buscarán en estos eventos"
          items={tiposEno}
          selected={
            editEventosCodigos.length > 0
              ? editEventosCodigos
              : editEventoCodigo
                ? [editEventoCodigo]
                : []
          }
          onChange={(arr) => {
            setEditEventosCodigos(arr);
            setEditEventoCodigo(arr[0] || "");
          }}
          placeholder="Buscar eventos..."
          required
        />
      </SectionCard>

      {!hasEventos && (
        <ContextBanner variant="warning">
          Seleccioná al menos un evento fuente
        </ContextBanner>
      )}

      {hasEventos && totalAgentesSeleccionados === 0 && (
        <ContextBanner variant="warning">
          Agregá al menos un agente en las series
        </ContextBanner>
      )}

      {hasEventos && (
        <SectionCard title="Series de agentes" icon={LineChart}>
          <SeriesEditor
            series={editSeries}
            onChange={setEditSeries}
            availableItems={agentes}
            itemType="agente"
          />
          <p className="text-xs text-muted-foreground mt-2">
            Cada serie agrupa uno o más agentes. Los datos se mostrarán con el
            label y color configurados.
          </p>
        </SectionCard>
      )}

      <SectionCard title="Período temporal" icon={Calendar}>
        <OptionSelector
          label="Rango de semanas a mostrar"
          options={[
            { value: "anual", label: "Año completo", description: "Semanas 1 a 52 del año del boletín" },
            { value: "seleccionado", label: "Período del boletín", description: "Desde semana inicio hasta semana fin configuradas" },
          ]}
          selected={editPeriodo}
          onChange={setEditPeriodo}
        />
      </SectionCard>

      <SectionCard title="Visualización" icon={LayoutGrid}>
        <OptionSelector
          label="Tipo de gráfico"
          options={[
            { value: "stacked_bar", label: "Apiladas" },
            { value: "line", label: "Líneas" },
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

export function EdadPorAgenteConfig({ formState, data }: BlockConfigProps) {
  const {
    editEventoCodigo,
    setEditEventoCodigo,
    editEventosCodigos,
    setEditEventosCodigos,
    editChartType,
    setEditChartType,
    editSoloConfirmados,
    setEditSoloConfirmados,
    editSeries,
    setEditSeries,
    editPeriodo,
    setEditPeriodo,
  } = formState;
  const { tiposEno, agentes } = data;

  // Count total agentes selected across all series
  const totalAgentesSeleccionados = editSeries.reduce(
    (acc, s) => acc + s.valores.length,
    0
  );

  const hasEventos =
    editEventosCodigos.length > 0 || editEventoCodigo.length > 0;

  return (
    <>
      <SectionCard title="Eventos fuente" icon={Activity}>
        <MultiSelect
          label="Eventos a analizar"
          helpText="Los agentes se buscarán en estos eventos"
          items={tiposEno}
          selected={
            editEventosCodigos.length > 0
              ? editEventosCodigos
              : editEventoCodigo
                ? [editEventoCodigo]
                : []
          }
          onChange={(arr) => {
            setEditEventosCodigos(arr);
            setEditEventoCodigo(arr[0] || "");
          }}
          placeholder="Buscar eventos..."
          required
        />
      </SectionCard>

      {!hasEventos && (
        <ContextBanner variant="warning">
          Seleccioná al menos un evento fuente
        </ContextBanner>
      )}

      {hasEventos && totalAgentesSeleccionados === 0 && (
        <ContextBanner variant="warning">
          Agregá al menos un agente en las series
        </ContextBanner>
      )}

      {hasEventos && (
        <SectionCard title="Series de agentes" icon={LineChart}>
          <SeriesEditor
            series={editSeries}
            onChange={setEditSeries}
            availableItems={agentes}
            itemType="agente"
          />
          <p className="text-xs text-muted-foreground mt-2">
            Cada serie agrupa uno o más agentes. Los datos se mostrarán con el
            label y color configurados.
          </p>
        </SectionCard>
      )}

      <SectionCard title="Período de los datos" icon={Calendar}>
        <OptionSelector
          label="Casos a incluir"
          options={[
            { value: "anual", label: "Año completo", description: "Todos los casos del año del boletín" },
            { value: "seleccionado", label: "Período del boletín", description: "Solo casos dentro del período configurado" },
          ]}
          selected={editPeriodo}
          onChange={setEditPeriodo}
        />
      </SectionCard>

      <SectionCard title="Visualización" icon={LayoutGrid}>
        <OptionSelector
          label="Tipo de gráfico"
          options={[
            { value: "stacked_bar", label: "Apiladas" },
            { value: "line", label: "Líneas" },
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
// DEFAULT CONFIG - For unknown blocks
// ════════════════════════════════════════════════════════════════════════════

export function DefaultBlockConfig() {
  return (
    <ContextBanner variant="info">
      Este bloque no tiene opciones de configuración adicionales
    </ContextBanner>
  );
}

// ════════════════════════════════════════════════════════════════════════════
// REGISTRY - Map block types to their config components
// ════════════════════════════════════════════════════════════════════════════

export const MAIN_BLOCK_CONFIGS: Record<
  string,
  React.ComponentType<BlockConfigProps>
> = {
  top_enos: TopEnosConfig,
  comparacion_periodos_global: ComparacionPeriodosGlobalConfig,
  curva_evento_especifico: CurvaEventoEspecificoConfig,
  corredor_evento_especifico: CorredorEventoEspecificoConfig,
  curva_comparar_eventos: CurvaCompararEventosConfig,
  edad_comparar_eventos: EdadCompararEventosConfig,
  distribucion_agentes: DistribucionAgentesConfig,
  curva_por_agente: CurvaPorAgenteConfig,
  edad_por_agente: EdadPorAgenteConfig,
};
