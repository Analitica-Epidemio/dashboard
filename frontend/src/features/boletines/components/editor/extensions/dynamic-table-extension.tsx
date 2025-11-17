import { Node, mergeAttributes } from "@tiptap/core";
import { ReactNodeViewRenderer, NodeViewWrapper, type NodeViewProps } from "@tiptap/react";
import { useState } from "react";
import '../tiptap';
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Database, Settings } from "lucide-react";

// Queries disponibles para tablas
const AVAILABLE_TABLE_QUERIES = [
  {
    id: "top_enos",
    nombre: "Top ENOs",
    descripcion: "Tabla de eventos mas frecuentes",
  },
  {
    id: "capacidad_hospitalaria",
    nombre: "Capacidad Hospitalaria",
    descripcion: "Dotacion de camas por hospital",
  },
  {
    id: "casos_suh",
    nombre: "Casos de SUH",
    descripcion: "Descripcion de casos SUH confirmados",
  },
];

// Componente React para renderizar el nodo
function DynamicTableComponent({ node, updateAttributes }: NodeViewProps) {
  const [isEditing, setIsEditing] = useState(false);
  const queryType = node.attrs.queryType as string;
  const title = node.attrs.title as string;

  const selectedQuery = AVAILABLE_TABLE_QUERIES.find((q) => q.id === queryType);

  if (isEditing) {
    return (
      <NodeViewWrapper className="my-4">
        <div className="border-2 border-blue-500 rounded-lg p-4 bg-blue-50">
          <div className="flex items-center gap-2 mb-3">
            <Database className="h-5 w-5 text-blue-600" />
            <span className="font-semibold text-blue-900">
              Configurar Tabla Dinamica
            </span>
          </div>

          <div className="space-y-3">
            <div>
              <Label className="text-sm">Titulo (opcional)</Label>
              <input
                type="text"
                value={title || ""}
                onChange={(e) => updateAttributes({ title: e.target.value })}
                placeholder="Ej: Tabla N 1. Casos confirmados..."
                className="w-full mt-1 px-3 py-2 border rounded-md text-sm"
              />
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
                  {AVAILABLE_TABLE_QUERIES.map((q) => (
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
      <div className="border border-blue-200 rounded p-3 bg-blue-50/30 group relative hover:bg-blue-50/50 transition-colors">
        <button
          onClick={() => setIsEditing(true)}
          className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity p-1.5 hover:bg-blue-100 rounded-md"
          contentEditable={false}
        >
          <Settings className="h-3.5 w-3.5 text-blue-600" />
        </button>

        <div className="flex items-center gap-2 mb-1.5">
          <Database className="h-3.5 w-3.5 text-blue-600" />
          <span className="text-xs font-medium text-blue-900">
            Tabla Dinámica: {selectedQuery?.nombre || queryType}
          </span>
        </div>

        {title && (
          <p className="text-xs text-gray-600 mb-2 ml-5">{title}</p>
        )}

        <div className="border border-dashed border-blue-200 rounded p-4 text-center bg-white/50">
          <p className="text-xs text-blue-700">
            {selectedQuery?.descripcion || "Query no configurada"}
          </p>
          <p className="text-[10px] mt-1 text-blue-500">
            Los datos se generarán al crear el reporte
          </p>
        </div>
      </div>
    </NodeViewWrapper>
  );
}

// Definición de la extensión Tiptap
export const DynamicTableExtension = Node.create({
  name: "dynamicTable",

  group: "block",

  atom: true,

  addAttributes() {
    return {
      queryType: {
        default: "top_enos",
      },
      title: {
        default: "",
      },
    };
  },

  parseHTML() {
    return [
      {
        tag: 'div[data-type="dynamic-table"]',
      },
    ];
  },

  renderHTML({ HTMLAttributes }) {
    return [
      "div",
      mergeAttributes(HTMLAttributes, { "data-type": "dynamic-table" }),
    ];
  },

  addNodeView() {
    return ReactNodeViewRenderer(DynamicTableComponent);
  },

  addCommands() {
    return {
      insertDynamicTable:
        (attrs: { queryType?: string; title?: string }) =>
        ({ commands }) => {
          return commands.insertContent({
            type: this.name,
            attrs,
          });
        },
    };
  },
});
