import { Node, mergeAttributes } from "@tiptap/core";
import { ReactNodeViewRenderer, NodeViewWrapper } from "@tiptap/react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { BarChart3, Settings } from "lucide-react";

// Queries disponibles para graficos
const AVAILABLE_CHART_QUERIES = [
  {
    id: "corredor_ira",
    nombre: "Corredor Endemico IRA",
    descripcion: "Corredor de ETI/Neumonia/Bronquiolitis",
  },
  {
    id: "virus_respiratorios",
    nombre: "Virus Respiratorios",
    descripcion: "Deteccion de virus por semana",
  },
  {
    id: "intoxicacion_co",
    nombre: "Intoxicacion CO",
    descripcion: "Casos por UGD comparando años",
  },
];

const CHART_TYPES = [
  { id: "line", nombre: "Lineas" },
  { id: "bar", nombre: "Barras" },
  { id: "corridor", nombre: "Corredor endemico" },
];

// Componente React para renderizar el nodo
function DynamicChartComponent(props: { node: { attrs: { queryType: string; chartType: string; title: string; height: number } }; updateAttributes: (attrs: Record<string, string | number>) => void }) {
  const [isEditing, setIsEditing] = useState(false);
  const { node, updateAttributes } = props;
  const { queryType, chartType, title, height } = node.attrs;

  const selectedQuery = AVAILABLE_CHART_QUERIES.find((q) => q.id === queryType);
  const selectedChartType = CHART_TYPES.find((t) => t.id === chartType);

  if (isEditing) {
    return (
      <NodeViewWrapper className="my-4">
        <div className="border-2 border-orange-500 rounded-lg p-4 bg-orange-50">
          <div className="flex items-center gap-2 mb-3">
            <BarChart3 className="h-5 w-5 text-orange-600" />
            <span className="font-semibold text-orange-900">
              Configurar Grafico Dinamico
            </span>
          </div>

          <div className="space-y-3">
            <div>
              <Label className="text-sm">Titulo (opcional)</Label>
              <input
                type="text"
                value={title || ""}
                onChange={(e) => updateAttributes({ title: e.target.value })}
                placeholder="Ej: Grafico N 1. Corredor endemico..."
                className="w-full mt-1 px-3 py-2 border rounded-md text-sm"
              />
            </div>

            <div>
              <Label className="text-sm">Tipo de grafico</Label>
              <Select
                value={chartType}
                onValueChange={(value) => updateAttributes({ chartType: value })}
              >
                <SelectTrigger className="mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {CHART_TYPES.map((t) => (
                    <SelectItem key={t.id} value={t.id}>
                      {t.nombre}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label className="text-sm">Tipo de query</Label>
              <Select
                value={queryType}
                onValueChange={(value) => updateAttributes({ queryType: value })}
              >
                <SelectTrigger className="mt-1">
                  <SelectValue placeholder="Selecciona una query..." />
                </SelectTrigger>
                <SelectContent>
                  {AVAILABLE_CHART_QUERIES.map((q) => (
                    <SelectItem key={q.id} value={q.id}>
                      {q.nombre}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {selectedQuery && (
                <p className="text-xs text-muted-foreground mt-1">
                  {selectedQuery.descripcion}
                </p>
              )}
            </div>

            <div>
              <Label className="text-sm">Altura (px)</Label>
              <Input
                type="number"
                value={height || 300}
                onChange={(e) =>
                  updateAttributes({ height: parseInt(e.target.value) })
                }
                className="mt-1"
              />
            </div>

            <Button
              size="sm"
              onClick={() => setIsEditing(false)}
              className="w-full"
            >
              Listo
            </Button>
          </div>
        </div>
      </NodeViewWrapper>
    );
  }

  return (
    <NodeViewWrapper className="my-4">
      <div className="border border-orange-200 rounded p-3 bg-orange-50/30 group relative hover:bg-orange-50/50 transition-colors">
        <button
          onClick={() => setIsEditing(true)}
          className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity p-1.5 hover:bg-orange-100 rounded-md"
          contentEditable={false}
        >
          <Settings className="h-3.5 w-3.5 text-orange-600" />
        </button>

        <div className="flex items-center gap-2 mb-1.5">
          <BarChart3 className="h-3.5 w-3.5 text-orange-600" />
          <span className="text-xs font-medium text-orange-900">
            Gráfico Dinámico: {selectedQuery?.nombre || queryType} (
            {selectedChartType?.nombre || chartType})
          </span>
        </div>

        {title && (
          <p className="text-xs text-gray-600 mb-2 ml-5">{title}</p>
        )}

        <div
          className="border border-dashed border-orange-200 rounded flex items-center justify-center bg-white/50"
          style={{ height: `${height || 300}px` }}
        >
          <div className="text-center px-4">
            <p className="text-xs text-orange-700">
              {selectedQuery?.descripcion || "Query no configurada"}
            </p>
            <p className="text-[10px] mt-1 text-orange-500">
              El gráfico se generará al crear el reporte
            </p>
          </div>
        </div>
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
      queryType: {
        default: "corredor_ira",
      },
      chartType: {
        default: "line",
      },
      title: {
        default: "",
      },
      height: {
        default: 300,
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
        (attrs) =>
        ({ commands }) => {
          return commands.insertContent({
            type: this.name,
            attrs,
          });
        },
    };
  },
});
