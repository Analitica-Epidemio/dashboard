import { Node, mergeAttributes } from "@tiptap/core";
import { ReactNodeViewRenderer, NodeViewWrapper, type NodeViewProps } from "@tiptap/react";
import { BarChart3, Loader2, AlertCircle } from "lucide-react";
import { DynamicChart } from "@/features/dashboard/components/charts/dynamic-chart";
import { useDashboardCharts } from "@/features/boletines/api";
import type { DynamicChartAttrs } from '../tiptap';

// Componente React para renderizar el nodo
function DynamicChartComponent({ node, updateAttributes }: NodeViewProps) {
  const attrs = node.attrs as {
    chartId: number;
    chartCode: string;
    title: string;
    grupoIds: string;
    eventoIds: string;
    fechaDesde: string;
    fechaHasta: string;
  };
  const { chartCode, title, grupoIds, eventoIds, fechaDesde, fechaHasta } = attrs;

  // Parse IDs from comma-separated strings
  const selectedGrupoIds = grupoIds ? grupoIds.split(",").filter(Boolean).map(Number) : [];
  const selectedEventoIds = eventoIds ? eventoIds.split(",").filter(Boolean).map(Number) : [];

  // Fetch chart data using the hook
  const { data, isLoading, error } = useDashboardCharts({
    grupo_id: selectedGrupoIds.length > 0 ? selectedGrupoIds[0] : undefined,
    tipo_eno_ids: selectedEventoIds,
    fecha_desde: fechaDesde || undefined,
    fecha_hasta: fechaHasta || undefined,
  });

  // Find the specific chart by code
  const chartData = data?.data?.charts?.find((c) => c.codigo === chartCode);

  const handleEdit = () => {
    // Emit custom event to open config dialog
    const event = new CustomEvent("edit-chart", {
      detail: { node, attrs, updateAttributes },
    });
    window.dispatchEvent(event);
  };

  return (
    <NodeViewWrapper className="my-4">
      <div
        className="border border-blue-100 rounded-lg bg-white shadow-sm hover:border-blue-300 transition-colors cursor-pointer group relative"
        onClick={handleEdit}
      >
        {/* Edit indicator */}
        <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
          <div className="bg-blue-100 text-blue-700 text-xs px-2 py-1 rounded flex items-center gap-1">
            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
            </svg>
            <span>Editar</span>
          </div>
        </div>
        {/* Title */}
        {title && (
          <div className="px-4 pt-4 pb-2">
            <p className="text-sm font-medium text-gray-900">{title}</p>
          </div>
        )}

        {/* Chart Content */}
        {isLoading ? (
          <div className="flex items-center justify-center py-12 px-4">
            <Loader2 className="w-5 h-5 animate-spin text-blue-500 mr-2" />
            <span className="text-sm text-gray-500">Cargando gráfico...</span>
          </div>
        ) : error ? (
          <div className="flex items-center justify-center py-12 px-4">
            <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
            <span className="text-sm text-red-600">Error al cargar el gráfico</span>
          </div>
        ) : chartData ? (
          <DynamicChart
            codigo={chartData.codigo}
            nombre={chartData.nombre}
            descripcion={chartData.descripcion}
            tipo={chartData.tipo}
            data={chartData.data as never}
            config={chartData.config}
          />
        ) : (
          <div className="flex flex-col items-center justify-center py-12 px-4 text-gray-500">
            <BarChart3 className="w-8 h-8 mb-2 text-gray-400" />
            <p className="text-sm">No se encontró el gráfico &quot;{chartCode}&quot;</p>
            <p className="text-xs text-gray-400 mt-1">
              Verifica que los filtros y período sean correctos
            </p>
          </div>
        )}
      </div>
    </NodeViewWrapper>
  );
}

// Definición de la extensión Tiptap
export const DynamicChartExtension = Node.create({
  name: "dynamicChart",

  group: "block",

  atom: true,

  addAttributes() {
    return {
      chartId: {
        default: 0,
      },
      chartCode: {
        default: "",
      },
      title: {
        default: "",
      },
      grupoIds: {
        default: "",
      },
      eventoIds: {
        default: "",
      },
      fechaDesde: {
        default: "",
      },
      fechaHasta: {
        default: "",
      },
    };
  },

  parseHTML() {
    return [
      {
        tag: 'div[data-type="dynamic-chart"]',
      },
    ];
  },

  renderHTML({ HTMLAttributes }) {
    return [
      "div",
      mergeAttributes(HTMLAttributes, { "data-type": "dynamic-chart" }),
    ];
  },

  addNodeView() {
    return ReactNodeViewRenderer(DynamicChartComponent);
  },

  addCommands() {
    return {
      insertDynamicChart:
        (attrs: DynamicChartAttrs) =>
        ({ commands }) => {
          return commands.insertContent({
            type: this.name,
            attrs,
          });
        },
    };
  },
});
