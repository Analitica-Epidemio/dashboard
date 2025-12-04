/**
 * React component for rendering dynamic blocks in TipTap editor
 * Simplified version - config is handled by BlockConfigPanel in sidebar
 */

import { NodeViewWrapper, NodeViewProps } from "@tiptap/react";
import { useEffect, useRef } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  GripVertical,
  Settings2,
  Trash2,
  BarChart3,
  MapPin,
  Users,
  TrendingUp,
  Activity,
  Building2,
  Bug,
  Calendar,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useSelectedBlock } from "../selected-block-context";

// Block type metadata
const BLOCK_METADATA: Record<
  string,
  {
    title: string;
    description: string;
    icon: LucideIcon;
    color: string;
    bgGradient: string;
  }
> = {
  top_enos: {
    title: "Top Eventos",
    description: "Rankings de eventos más frecuentes",
    icon: BarChart3,
    color: "text-blue-600",
    bgGradient: "from-blue-500/10 to-blue-600/5",
  },
  eventos_agrupados: {
    title: "Corredor Endémico",
    description: "Análisis de corredor endémico semanal",
    icon: TrendingUp,
    color: "text-emerald-600",
    bgGradient: "from-emerald-500/10 to-emerald-600/5",
  },
  corredor_endemico_chart: {
    title: "Corredor Endémico (Gráfico)",
    description: "Gráfico de corredor endémico con zonas epidémicas",
    icon: TrendingUp,
    color: "text-emerald-600",
    bgGradient: "from-emerald-500/10 to-emerald-600/5",
  },
  curva_epidemiologica: {
    title: "Curva Epidemiológica",
    description: "Casos por semana epidemiológica",
    icon: Activity,
    color: "text-blue-600",
    bgGradient: "from-blue-500/10 to-blue-600/5",
  },
  evento_detail: {
    title: "Detalle de Evento",
    description: "Análisis detallado de un evento específico",
    icon: Bug,
    color: "text-purple-600",
    bgGradient: "from-purple-500/10 to-purple-600/5",
  },
  capacidad_hospitalaria: {
    title: "Capacidad Hospitalaria",
    description: "Ocupación de camas por UGD",
    icon: Building2,
    color: "text-red-600",
    bgGradient: "from-red-500/10 to-red-600/5",
  },
  virus_respiratorios: {
    title: "Virus Respiratorios",
    description: "Vigilancia de virus circulantes",
    icon: Activity,
    color: "text-amber-600",
    bgGradient: "from-amber-500/10 to-amber-600/5",
  },
  distribucion_geografica: {
    title: "Mapa de Casos",
    description: "Distribución geográfica de casos",
    icon: MapPin,
    color: "text-cyan-600",
    bgGradient: "from-cyan-500/10 to-cyan-600/5",
  },
  distribucion_edad: {
    title: "Distribución por Edad",
    description: "Casos por grupo etario",
    icon: Users,
    color: "text-pink-600",
    bgGradient: "from-pink-500/10 to-pink-600/5",
  },
  distribucion_agentes: {
    title: "Distribución de Agentes",
    description: "Totales por agente etiológico",
    icon: Bug,
    color: "text-orange-600",
    bgGradient: "from-orange-500/10 to-orange-600/5",
  },
  comparacion_periodos: {
    title: "Comparación Temporal",
    description: "Tendencias vs período anterior",
    icon: Calendar,
    color: "text-indigo-600",
    bgGradient: "from-indigo-500/10 to-indigo-600/5",
  },
  comparacion_anual: {
    title: "Comparación Interanual",
    description: "Comparación acumulada año del boletín vs anterior",
    icon: Calendar,
    color: "text-violet-600",
    bgGradient: "from-violet-500/10 to-violet-600/5",
  },
  insight_distribucion_edad: {
    title: "Insight de Edad",
    description: "Texto auto-generado sobre distribución etaria",
    icon: Users,
    color: "text-pink-600",
    bgGradient: "from-pink-500/10 to-pink-600/5",
  },
  insight_distribucion_geografica: {
    title: "Insight Geográfico",
    description: "Texto auto-generado sobre distribución geográfica",
    icon: MapPin,
    color: "text-cyan-600",
    bgGradient: "from-cyan-500/10 to-cyan-600/5",
  },
};

export function DynamicBlockNodeView({
  node,
  deleteNode,
  updateAttributes,
  selected,
}: NodeViewProps) {
  const { blockId, queryType, blockType, config, queryParams, isInEventLoop: attrIsInEventLoop } = node.attrs;
  const { selectedBlock, selectBlock, clearSelection } = useSelectedBlock();

  const metadata = BLOCK_METADATA[queryType] || {
    title: "Bloque",
    description: queryType,
    icon: BarChart3,
    color: "text-gray-600",
    bgGradient: "from-gray-500/10 to-gray-600/5",
  };

  const Icon = metadata.icon;
  const isSelected = selectedBlock?.blockId === blockId;

  // Detect if this block is inside the event loop template (from node attribute)
  const isInEventLoop = Boolean(attrIsInEventLoop);

  // Use refs to hold latest values without causing re-renders
  const blockDataRef = useRef({
    blockId,
    queryType,
    blockType: blockType || queryType,
    queryParams: queryParams || {},
    config: config || {},
    isInEventLoop,
    updateAttributes,
  });

  // Keep ref up to date
  blockDataRef.current = {
    blockId,
    queryType,
    blockType: blockType || queryType,
    queryParams: queryParams || {},
    config: config || {},
    isInEventLoop,
    updateAttributes,
  };

  // Track if we already triggered selection to prevent loops
  const hasTriggeredSelectionRef = useRef(false);

  // When node is selected in editor, also select it in the panel
  useEffect(() => {
    if (selected && !isSelected && !hasTriggeredSelectionRef.current) {
      hasTriggeredSelectionRef.current = true;
      selectBlock(blockDataRef.current);
    } else if (!selected) {
      // Reset when deselected
      hasTriggeredSelectionRef.current = false;
    }
  }, [selected, isSelected, selectBlock]);

  // Handle click to select block
  const handleSelect = () => {
    if (isSelected) {
      clearSelection();
    } else {
      selectBlock(blockDataRef.current);
    }
  };

  // Build detailed config info
  interface SeriesInfo {
    label: string;
    color: string;
    valores: string[];
  }

  const series: SeriesInfo[] = config?.series && Array.isArray(config.series)
    ? (config.series as SeriesInfo[])
    : [];

  // Period label
  const getPeriodLabel = () => {
    if (!queryParams?.periodo) return null;
    if (queryParams.periodo === "anual") return "Año completo (SE 1-52)";
    return "Período del boletín";
  };

  // Chart type label
  const getChartLabel = () => {
    if (!config?.chart_type) return null;
    const labels: Record<string, string> = {
      bar: "Gráfico de barras",
      line: "Gráfico de líneas",
      stacked_bar: "Barras apiladas",
      grouped_bar: "Barras agrupadas",
      pie: "Gráfico de torta",
    };
    return labels[config.chart_type as string] || config.chart_type;
  };

  // Filters
  const filters: string[] = [];
  if (queryParams?.resultado === "positivo") filters.push("Solo casos confirmados");
  if (queryParams?.solo_internados) filters.push("Solo internados");

  // Events/Agents source
  const getDataSource = () => {
    if (queryParams?.evento_codigo) {
      return `Evento: ${queryParams.evento_codigo}`;
    }
    if (queryParams?.eventos_codigos?.length) {
      const eventos = queryParams.eventos_codigos as string[];
      if (eventos.length <= 3) {
        return `Eventos: ${eventos.join(", ")}`;
      }
      return `Eventos: ${eventos.slice(0, 2).join(", ")} y ${eventos.length - 2} más`;
    }
    return null;
  };

  // Check if block has meaningful config
  // Blocks in event loop get their config dynamically from the loop context
  const hasConfig = isInEventLoop || series.length > 0 || queryParams?.periodo || queryParams?.evento_codigo ||
                    queryParams?.eventos_codigos?.length || queryParams?.limit;

  return (
    <NodeViewWrapper className="my-3">
      <Card
        className={cn(
          "relative overflow-hidden transition-all border-2 cursor-pointer",
          isSelected && "ring-2 ring-primary ring-offset-2 border-primary",
          selected && !isSelected && "ring-1 ring-muted-foreground/30",
          "hover:shadow-md hover:border-primary/50"
        )}
        onClick={handleSelect}
      >
        {/* Gradient background */}
        <div
          className={cn(
            "absolute inset-0 bg-gradient-to-br opacity-50",
            metadata.bgGradient
          )}
        />

        <div className="relative flex items-center gap-3 p-4">
          {/* Drag handle */}
          <div
            className="cursor-grab active:cursor-grabbing opacity-40 hover:opacity-100 transition-opacity"
            contentEditable={false}
            data-drag-handle
            onClick={(e) => e.stopPropagation()}
          >
            <GripVertical className="h-5 w-5" />
          </div>

          {/* Icon */}
          <div
            className={cn(
              "flex items-center justify-center w-10 h-10 rounded-lg shrink-0",
              "bg-white/80 shadow-sm border"
            )}
          >
            <Icon className={cn("h-5 w-5", metadata.color)} />
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            {/* Title row */}
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-semibold text-sm">
                {config?.titulo || metadata.title}
              </span>
              {isSelected && (
                <Badge variant="default" className="text-xs px-1.5 py-0">
                  Editando
                </Badge>
              )}
            </div>

            {/* Config details */}
            {hasConfig ? (
              <div className="mt-2 space-y-1.5 text-xs">
                {/* Period & Chart type row */}
                <div className="flex items-center gap-3 text-muted-foreground">
                  {getPeriodLabel() && (
                    <span className="flex items-center gap-1">
                      <Calendar className="h-3 w-3" />
                      {getPeriodLabel()}
                    </span>
                  )}
                  {getChartLabel() && (
                    <span className="flex items-center gap-1">
                      <BarChart3 className="h-3 w-3" />
                      {getChartLabel()}
                    </span>
                  )}
                  {queryParams?.limit && (
                    <span>Top {queryParams.limit}</span>
                  )}
                </div>

                {/* Data source */}
                {getDataSource() && (
                  <p className="text-muted-foreground">{getDataSource()}</p>
                )}

                {/* Series with colors */}
                {series.length > 0 && (
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-muted-foreground">Series:</span>
                    {series.map((s, i) => (
                      <span key={i} className="inline-flex items-center gap-1">
                        <span
                          className="w-2.5 h-2.5 rounded-full shrink-0"
                          style={{ backgroundColor: s.color }}
                        />
                        <span className="text-foreground">{s.label}</span>
                        {i < series.length - 1 && <span className="text-muted-foreground">,</span>}
                      </span>
                    ))}
                  </div>
                )}

                {/* Filters */}
                {filters.length > 0 && (
                  <div className="flex items-center gap-2">
                    <span className="text-muted-foreground">Filtros:</span>
                    {filters.map((f, i) => (
                      <Badge key={i} variant="outline" className="text-[10px] px-1.5 py-0 h-4">
                        {f}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="mt-1.5">
                <p className="text-xs text-muted-foreground">{metadata.description}</p>
                <p className="text-[10px] text-amber-600 mt-1 flex items-center gap-1">
                  <span>⚠</span>
                  <span>Sin configuración - haz clic para configurar</span>
                </p>
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="flex items-center gap-1 shrink-0" contentEditable={false}>
            <Button
              variant={isSelected ? "default" : "ghost"}
              size="sm"
              className="h-8 w-8 p-0"
              onClick={(e) => {
                e.stopPropagation();
                handleSelect();
              }}
            >
              <Settings2 className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0 text-muted-foreground hover:text-destructive"
              onClick={(e) => {
                e.stopPropagation();
                if (isSelected) clearSelection();
                deleteNode();
              }}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </Card>
    </NodeViewWrapper>
  );
}
