"use client";

/**
 * Block Config Panel - Main Component
 *
 * Panel de configuración para bloques dinámicos del editor de boletines.
 * Detecta automáticamente si el bloque es de loop o principal y muestra
 * las opciones correspondientes.
 */

import { useState, useEffect, useMemo, useCallback, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Check, Settings2, X, ChevronRight, Sparkles, Palette } from "lucide-react";
import { cn } from "@/lib/utils";
import { useSelectedBlock } from "../selected-block-context";
import { useEventosDisponibles, useAgentesDisponibles } from "@/features/boletines/api";
import { VariableTitleEditor } from "../variable-title-editor";

// Internal imports
import { getBlockMeta, isLoopBlock } from "./block-metadata";
import { SectionCard } from "./design-system";
import { LOOP_BLOCK_CONFIGS } from "./loop-block-configs";
import { MAIN_BLOCK_CONFIGS, DefaultBlockConfig } from "./main-block-configs";
import type { BlockConfigFormState, BlockConfigData, SerieConfig } from "./types";

// ════════════════════════════════════════════════════════════════════════════
// INITIAL VALUES - For tracking changes
// ════════════════════════════════════════════════════════════════════════════

interface InitialValues {
  title: string;
  limit: string;
  periodo: string;
  chartType: string;
  eventoCodigo: string;
  eventosCodigos: string[];
  agentesCodigos: string[];
  soloConfirmados: boolean;
  soloInternados: boolean;
  series: SerieConfig[];
  agruparPor: "evento" | "agente";
}

// ════════════════════════════════════════════════════════════════════════════
// MAIN COMPONENT
// ════════════════════════════════════════════════════════════════════════════

export function BlockConfigPanel() {
  const { selectedBlock, clearSelection } = useSelectedBlock();

  // Data hooks
  const { data: eventosData } = useEventosDisponibles();
  const { data: agentesData } = useAgentesDisponibles();

  const eventos = useMemo(() => eventosData?.data || [], [eventosData]);
  const agentes = useMemo(() => agentesData?.data || [], [agentesData]);
  const tiposEno = useMemo(
    () => eventos.filter((e) => e.tipo === "tipo_eno"),
    [eventos]
  );

  // Form state
  const [editTitle, setEditTitle] = useState("");
  const [editLimit, setEditLimit] = useState("10");
  const [editPeriodo, setEditPeriodo] = useState("anual");
  const [editChartType, setEditChartType] = useState("bar");
  const [editEventoCodigo, setEditEventoCodigo] = useState("");
  const [editEventosCodigos, setEditEventosCodigos] = useState<string[]>([]);
  const [editAgentesCodigos, setEditAgentesCodigos] = useState<string[]>([]);
  const [editSoloConfirmados, setEditSoloConfirmados] = useState(false);
  const [editSoloInternados, setEditSoloInternados] = useState(false);
  const [editSeries, setEditSeries] = useState<SerieConfig[]>([]);
  const [editAgruparPor, setEditAgruparPor] = useState<"evento" | "agente">("evento");

  // Initial values ref for change tracking
  const initialValuesRef = useRef<InitialValues | null>(null);

  // Initialize form when block changes
  useEffect(() => {
    if (selectedBlock) {
      const { config, queryParams } = selectedBlock;
      const title = (config?.titulo as string) || "";
      const limit = ((queryParams?.limit as number) || 10).toString();
      const periodo = (queryParams?.periodo as string) || "anual";
      const chartType = (config?.chart_type as string) || "bar";
      const eventoCodigo = (queryParams?.evento_codigo as string) || "";
      const eventosCodigos = (queryParams?.eventos_codigos as string[]) || [];
      const agentesCodigos = (queryParams?.agentes_codigos as string[]) || [];
      const soloConfirmados = (queryParams?.resultado as string) === "positivo";
      const soloInternados = (queryParams?.solo_internados as boolean) || false;
      const series = (config?.series as SerieConfig[]) || [];
      const agruparPor = (queryParams?.agrupar_por as "evento" | "agente") || "evento";

      // Set form state
      setEditTitle(title);
      setEditLimit(limit);
      setEditPeriodo(periodo);
      setEditChartType(chartType);
      setEditEventoCodigo(eventoCodigo);
      setEditEventosCodigos(eventosCodigos);
      setEditAgentesCodigos(agentesCodigos);
      setEditSoloConfirmados(soloConfirmados);
      setEditSoloInternados(soloInternados);
      setEditSeries(series);
      setEditAgruparPor(agruparPor);

      // Store initial values
      initialValuesRef.current = {
        title,
        limit,
        periodo,
        chartType,
        eventoCodigo,
        eventosCodigos,
        agentesCodigos,
        soloConfirmados,
        soloInternados,
        series,
        agruparPor,
      };
    } else {
      initialValuesRef.current = null;
    }
  }, [selectedBlock]);

  // Compute hasChanges by comparing current values against initial
  const hasChanges = useMemo(() => {
    const initial = initialValuesRef.current;
    if (!initial) return false;

    const arraysEqual = (a: string[], b: string[]) => {
      if (a.length !== b.length) return false;
      const sortedA = [...a].sort();
      const sortedB = [...b].sort();
      return sortedA.every((val, i) => val === sortedB[i]);
    };

    const seriesEqual = (a: SerieConfig[], b: SerieConfig[]) => {
      if (a.length !== b.length) return false;
      return a.every((serie, i) => {
        const other = b[i];
        return (
          serie.label === other.label &&
          serie.color === other.color &&
          arraysEqual(serie.valores, other.valores)
        );
      });
    };

    return (
      editTitle !== initial.title ||
      editLimit !== initial.limit ||
      editPeriodo !== initial.periodo ||
      editChartType !== initial.chartType ||
      editEventoCodigo !== initial.eventoCodigo ||
      !arraysEqual(editEventosCodigos, initial.eventosCodigos) ||
      !arraysEqual(editAgentesCodigos, initial.agentesCodigos) ||
      editSoloConfirmados !== initial.soloConfirmados ||
      editSoloInternados !== initial.soloInternados ||
      !seriesEqual(editSeries, initial.series) ||
      editAgruparPor !== initial.agruparPor
    );
  }, [
    editTitle,
    editLimit,
    editPeriodo,
    editChartType,
    editEventoCodigo,
    editEventosCodigos,
    editAgentesCodigos,
    editSoloConfirmados,
    editSoloInternados,
    editSeries,
    editAgruparPor,
  ]);

  // Save changes
  const handleSave = useCallback(() => {
    if (!selectedBlock) return;

    const { blockType, config, queryParams, updateAttributes } = selectedBlock;
    const newConfig = { ...config };
    const newParams = { ...queryParams };

    // Title (always)
    if (editTitle.trim()) {
      newConfig.titulo = editTitle.trim();
    } else {
      delete newConfig.titulo;
    }

    // Handle by blockType
    switch (blockType) {
      case "corredor_loop":
        newParams.periodo = editPeriodo;
        break;

      case "curva_loop":
      case "edad_loop":
        newConfig.chart_type = editChartType;
        if (editSoloConfirmados) newParams.resultado = "positivo";
        else delete newParams.resultado;
        if (editSoloInternados) newParams.solo_internados = true;
        else delete newParams.solo_internados;
        break;

      case "mapa_loop":
        break;

      case "comparacion_anual_loop":
        if (editSoloConfirmados) newParams.resultado = "positivo";
        else delete newParams.resultado;
        break;

      case "agentes_loop":
      case "edad_por_agente_loop":
        if (editAgentesCodigos.length > 0)
          newParams.agentes_codigos = editAgentesCodigos;
        else delete newParams.agentes_codigos;
        newConfig.chart_type = editChartType;
        if (editSoloConfirmados) newParams.resultado = "positivo";
        else delete newParams.resultado;
        break;

      case "top_enos": {
        const limit = parseInt(editLimit);
        if (!isNaN(limit) && limit > 0) newParams.limit = limit;
        newParams.periodo = editPeriodo;
        break;
      }

      case "comparacion_periodos_global": {
        const limit2 = parseInt(editLimit);
        if (!isNaN(limit2) && limit2 > 0) newParams.limit = limit2;
        // Este bloque siempre compara período del boletín vs mismo período año anterior
        // No tiene período configurable - está fijo en la lógica del backend
        break;
      }

      case "curva_evento_especifico":
        if (editEventoCodigo) newParams.evento_codigo = editEventoCodigo;
        newConfig.chart_type = editChartType;
        newParams.periodo = editPeriodo; // Período temporal
        if (editSoloConfirmados) newParams.resultado = "positivo";
        else delete newParams.resultado;
        if (editSoloInternados) newParams.solo_internados = true;
        else delete newParams.solo_internados;
        break;

      case "corredor_evento_especifico":
        if (editEventoCodigo) newParams.evento_codigo = editEventoCodigo;
        newParams.periodo = editPeriodo;
        break;

      case "curva_comparar_eventos": {
        // Derive eventos_codigos from series
        const eventosCodigos = editSeries.flatMap((s) => s.valores);
        if (eventosCodigos.length > 0) {
          newParams.eventos_codigos = eventosCodigos;
        } else {
          delete newParams.eventos_codigos;
        }
        newConfig.chart_type = editChartType;
        newParams.periodo = editPeriodo; // Período temporal
        if (editSoloConfirmados) newParams.resultado = "positivo";
        else delete newParams.resultado;
        // Series configuration
        if (editSeries.length > 0) {
          newConfig.series = editSeries;
          newParams.agrupar_por = "evento";
        } else {
          delete newConfig.series;
          delete newParams.agrupar_por;
        }
        break;
      }

      case "edad_comparar_eventos": {
        // Derive eventos_codigos from series
        const eventosCodigos2 = editSeries.flatMap((s) => s.valores);
        if (eventosCodigos2.length > 0) {
          newParams.eventos_codigos = eventosCodigos2;
        } else {
          delete newParams.eventos_codigos;
        }
        newConfig.chart_type = editChartType;
        newParams.periodo = editPeriodo; // Período de los datos
        if (editSoloConfirmados) newParams.resultado = "positivo";
        else delete newParams.resultado;
        // Series configuration
        if (editSeries.length > 0) {
          newConfig.series = editSeries;
          newParams.agrupar_por = "evento";
        } else {
          delete newConfig.series;
          delete newParams.agrupar_por;
        }
        break;
      }

      case "distribucion_agentes": {
        // Eventos fuente (filter - kept separate)
        if (editEventoCodigo) newParams.evento_codigo = editEventoCodigo;
        if (editEventosCodigos.length > 0)
          newParams.eventos_codigos = editEventosCodigos;
        // Derive agentes_codigos from series
        const agentesCodigos0 = editSeries.flatMap((s) => s.valores);
        if (agentesCodigos0.length > 0) {
          newParams.agentes_codigos = agentesCodigos0;
        } else {
          delete newParams.agentes_codigos;
        }
        newConfig.chart_type = editChartType;
        if (editSoloConfirmados) newParams.resultado = "positivo";
        else delete newParams.resultado;
        // Series configuration (for agent-based charts)
        if (editSeries.length > 0) {
          newConfig.series = editSeries;
          newParams.agrupar_por = "agente";
        } else {
          delete newConfig.series;
          delete newParams.agrupar_por;
        }
        break;
      }

      case "edad_por_agente": {
        // Eventos fuente (filter - kept separate)
        if (editEventoCodigo) newParams.evento_codigo = editEventoCodigo;
        if (editEventosCodigos.length > 0)
          newParams.eventos_codigos = editEventosCodigos;
        // Derive agentes_codigos from series
        const agentesCodigos = editSeries.flatMap((s) => s.valores);
        if (agentesCodigos.length > 0) {
          newParams.agentes_codigos = agentesCodigos;
        } else {
          delete newParams.agentes_codigos;
        }
        newConfig.chart_type = editChartType;
        newParams.periodo = editPeriodo; // Período de los datos
        if (editSoloConfirmados) newParams.resultado = "positivo";
        else delete newParams.resultado;
        // Series configuration (for agent-based charts)
        if (editSeries.length > 0) {
          newConfig.series = editSeries;
          newParams.agrupar_por = "agente";
        } else {
          delete newConfig.series;
          delete newParams.agrupar_por;
        }
        break;
      }

      case "curva_por_agente": {
        // Eventos fuente (filter - kept separate)
        if (editEventoCodigo) newParams.evento_codigo = editEventoCodigo;
        if (editEventosCodigos.length > 0)
          newParams.eventos_codigos = editEventosCodigos;
        // Derive agentes_codigos from series
        const agentesCodigos2 = editSeries.flatMap((s) => s.valores);
        if (agentesCodigos2.length > 0) {
          newParams.agentes_codigos = agentesCodigos2;
        } else {
          delete newParams.agentes_codigos;
        }
        newConfig.chart_type = editChartType;
        newParams.periodo = editPeriodo; // Período temporal
        if (editSoloConfirmados) newParams.resultado = "positivo";
        else delete newParams.resultado;
        // Series configuration (for agent-based charts)
        if (editSeries.length > 0) {
          newConfig.series = editSeries;
          newParams.agrupar_por = "agente";
        } else {
          delete newConfig.series;
          delete newParams.agrupar_por;
        }
        break;
      }
    }

    updateAttributes({ config: newConfig, queryParams: newParams });

    // Update initial values to current (so hasChanges becomes false)
    initialValuesRef.current = {
      title: editTitle,
      limit: editLimit,
      periodo: editPeriodo,
      chartType: editChartType,
      eventoCodigo: editEventoCodigo,
      eventosCodigos: editEventosCodigos,
      agentesCodigos: editAgentesCodigos,
      soloConfirmados: editSoloConfirmados,
      soloInternados: editSoloInternados,
      series: editSeries,
      agruparPor: editAgruparPor,
    };
  }, [
    selectedBlock,
    editTitle,
    editLimit,
    editPeriodo,
    editChartType,
    editEventoCodigo,
    editEventosCodigos,
    editAgentesCodigos,
    editSoloConfirmados,
    editSoloInternados,
    editSeries,
    editAgruparPor,
  ]);

  // ══════════════════════════════════════════════════════════════════════════
  // EMPTY STATE
  // ══════════════════════════════════════════════════════════════════════════

  if (!selectedBlock) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-center p-8 bg-gradient-to-b from-muted/30 to-background border-l">
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-muted to-muted/50 flex items-center justify-center mb-6 shadow-inner">
          <Settings2 className="h-8 w-8 text-muted-foreground/50" />
        </div>
        <h3 className="text-base font-semibold text-foreground mb-2">
          Panel de Configuración
        </h3>
        <p className="text-sm text-muted-foreground max-w-[220px] leading-relaxed">
          Seleccioná un bloque dinámico en el editor para personalizar sus opciones
        </p>
        <div className="flex items-center gap-2 mt-6 text-xs text-muted-foreground">
          <ChevronRight className="h-4 w-4" />
          <span>Click en cualquier bloque</span>
        </div>
      </div>
    );
  }

  // ══════════════════════════════════════════════════════════════════════════
  // RENDER
  // ══════════════════════════════════════════════════════════════════════════

  const { blockType, isInEventLoop } = selectedBlock;
  const metadata = getBlockMeta(blockType);
  const Icon = metadata.icon;
  const isLoop = isLoopBlock(blockType);

  // Get the config component for this block type
  const ConfigComponent =
    LOOP_BLOCK_CONFIGS[blockType] ||
    MAIN_BLOCK_CONFIGS[blockType] ||
    DefaultBlockConfig;

  // Build form state and data props
  const formState: BlockConfigFormState = {
    editTitle,
    setEditTitle,
    editLimit,
    setEditLimit,
    editPeriodo,
    setEditPeriodo,
    editChartType,
    setEditChartType,
    editEventoCodigo,
    setEditEventoCodigo,
    editEventosCodigos,
    setEditEventosCodigos,
    editAgentesCodigos,
    setEditAgentesCodigos,
    editSoloConfirmados,
    setEditSoloConfirmados,
    editSoloInternados,
    setEditSoloInternados,
    editSeries,
    setEditSeries,
    editAgruparPor,
    setEditAgruparPor,
  };

  const data: BlockConfigData = { tiposEno, agentes };

  return (
    <div className="h-full flex flex-col border-l bg-background overflow-hidden">
      {/* Header */}
      <div className="shrink-0 border-b">
        <div className={cn("h-1.5 bg-gradient-to-r", metadata.gradient)} />
        <div className="p-4">
          <div className="flex items-start gap-3">
            <div
              className={cn(
                "flex items-center justify-center w-11 h-11 rounded-xl shrink-0 shadow-sm",
                "bg-gradient-to-br",
                metadata.gradient
              )}
            >
              <Icon className="h-5 w-5 text-white" />
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-base">{metadata.title}</h3>
              <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">
                {metadata.description}
              </p>
              {/* Show badge for loop blocks */}
              {(isLoop || isInEventLoop) && (
                <Badge className="mt-2 text-[10px] bg-violet-100 text-violet-700 hover:bg-violet-100 border-0">
                  <Sparkles className="h-3 w-3 mr-1" />
                  Se repite por evento
                </Badge>
              )}
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0 shrink-0 hover:bg-muted"
              onClick={clearSelection}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 min-h-0 overflow-y-auto">
        <div className="p-4 space-y-4">
          {/* Title Editor - Hidden for insight blocks (they're auto-generated text) */}
          {!blockType.startsWith("insight_") && (
            <SectionCard title="Título del gráfico" icon={Palette}>
              <VariableTitleEditor
                value={editTitle}
                onChange={setEditTitle}
                placeholder={metadata.title}
                label=""
                showEventVariables={isLoop || isInEventLoop}
                showBaseVariables={true}
              />
              <p className="text-xs text-muted-foreground">
                Usá {"{{ nombre_evento }}"} para insertar el nombre del evento
                automáticamente
              </p>
            </SectionCard>
          )}

          {/* Block-specific configuration */}
          <ConfigComponent formState={formState} data={data} />
        </div>
      </div>

      {/* Footer */}
      <div className="p-4 border-t shrink-0 bg-muted/30">
        <Button
          onClick={handleSave}
          className={cn(
            "w-full transition-all",
            hasChanges
              ? "bg-primary hover:bg-primary/90"
              : "bg-muted text-muted-foreground hover:bg-muted"
          )}
          disabled={!hasChanges}
        >
          {hasChanges ? (
            <>
              <Check className="h-4 w-4 mr-2" />
              Aplicar cambios
            </>
          ) : (
            "Sin cambios pendientes"
          )}
        </Button>
      </div>
    </div>
  );
}

// Re-export for convenience
export { getBlockMeta, isLoopBlock, isMainBlock } from "./block-metadata";
export type { BlockConfigFormState, BlockConfigData } from "./types";
