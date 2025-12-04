/**
 * TipTap extension for Selected Events Placeholder
 * Shows where dynamic events will be inserted with a preview of the event template
 */

import { Node, mergeAttributes } from "@tiptap/core";
import { ReactNodeViewRenderer, NodeViewWrapper, NodeViewProps } from "@tiptap/react";
import type { JSONContent } from "@tiptap/react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { GripVertical, Trash2, Repeat, Eye, BarChart3 } from "lucide-react";
import { cn } from "@/lib/utils";
import { useEventTemplateContextSafe } from "../event-template-context";
import { VARIABLE_META } from "./variable-node";

declare module "@tiptap/core" {
  interface Commands<ReturnType> {
    selectedEventsPlaceholder: {
      insertSelectedEventsPlaceholder: () => ReturnType;
    };
  }
}

// Example event data for preview
const EXAMPLE_EVENT: Record<string, string> = {
  tipo_evento: "Dengue",
  evento_codigo: "A90",
  tendencia_texto: "Se observa un incremento del 25% respecto a la SE anterior (125 → 156 casos)",
  casos_semana_actual: "156",
  porcentaje_cambio: "+24.8%",
  semana_epidemiologica: "45",
  anio: "2024",
  fecha_inicio_semana: "04/11/2024",
  fecha_fin_semana: "10/11/2024",
  provincia: "Buenos Aires",
};

/**
 * Renders JSON content with variables replaced by example data
 */
function renderContentWithVariables(content: JSONContent | null): React.ReactNode {
  if (!content || !content.content) {
    return (
      <p className="text-sm text-gray-500 italic">
        (Template vacío - edita el template de eventos abajo)
      </p>
    );
  }

  return content.content.map((node, index) => renderNode(node, index));
}

function renderNode(node: JSONContent, key: number | string): React.ReactNode {
  if (!node.type) return null;

  switch (node.type) {
    case "heading": {
      const level = node.attrs?.level || 3;
      const className = level === 3
        ? "font-semibold text-base text-gray-900 mb-1"
        : "font-medium text-sm text-gray-800 mb-1";
      return (
        <div key={key} className={className}>
          {renderContent(node.content)}
        </div>
      );
    }
    case "paragraph":
      return (
        <p key={key} className="text-sm text-gray-600 mb-2">
          {renderContent(node.content)}
        </p>
      );
    case "bulletList":
      return (
        <ul key={key} className="list-disc list-inside text-sm text-gray-600 mb-2 ml-2">
          {node.content?.map((item, i) => renderNode(item, `${key}-${i}`))}
        </ul>
      );
    case "orderedList":
      return (
        <ol key={key} className="list-decimal list-inside text-sm text-gray-600 mb-2 ml-2">
          {node.content?.map((item, i) => renderNode(item, `${key}-${i}`))}
        </ol>
      );
    case "listItem":
      return (
        <li key={key}>
          {node.content?.map((child, i) => {
            if (child.type === "paragraph") {
              return <span key={i}>{renderContent(child.content)}</span>;
            }
            return renderNode(child, `${key}-${i}`);
          })}
        </li>
      );
    case "dynamicBlock":
      return (
        <div key={key} className="flex items-center gap-2 my-2">
          <Badge variant="outline" className="text-xs">
            <BarChart3 className="h-3 w-3 mr-1" />
            {node.attrs?.config?.titulo || node.attrs?.queryType || "Bloque dinámico"}
          </Badge>
        </div>
      );
    case "variableNode":
      return renderVariable(node.attrs?.variableKey || "", key);
    default:
      return null;
  }
}

function renderContent(content: JSONContent[] | undefined): React.ReactNode {
  if (!content) return null;

  return content.map((item, index) => {
    if (item.type === "text") {
      let text = item.text || "";
      // Replace mustache-style variables in text
      text = text.replace(/\{\{\s*(\w+)\s*\}\}/g, (_, varKey) => {
        return EXAMPLE_EVENT[varKey] || `{{ ${varKey} }}`;
      });

      const marks = item.marks || [];
      let element: React.ReactNode = text;

      for (const mark of marks) {
        if (mark.type === "bold") {
          element = <strong key={`mark-${index}`}>{element}</strong>;
        } else if (mark.type === "italic") {
          element = <em key={`mark-${index}`}>{element}</em>;
        } else if (mark.type === "underline") {
          element = <u key={`mark-${index}`}>{element}</u>;
        }
      }

      return <span key={index}>{element}</span>;
    }

    if (item.type === "variableNode") {
      return renderVariable(item.attrs?.variableKey || "", index);
    }

    return null;
  });
}

function renderVariable(varKey: string, key: number | string): React.ReactNode {
  const value = EXAMPLE_EVENT[varKey];
  const meta = VARIABLE_META[varKey];

  if (value) {
    return (
      <span key={key} className="font-medium text-violet-700 bg-violet-100 px-1 rounded">
        {value}
      </span>
    );
  }

  return (
    <span key={key} className="text-violet-500 bg-violet-50 px-1 rounded text-xs">
      {meta?.label || varKey}
    </span>
  );
}

// Simple marker node view with preview
function SelectedEventsPlaceholderView({ deleteNode, selected }: NodeViewProps) {
  const context = useEventTemplateContextSafe();
  const eventTemplateContent = context?.eventTemplateContent;

  return (
    <NodeViewWrapper className="my-4">
      <Card className={cn(
        "relative overflow-hidden border-2 border-dashed",
        "border-violet-300 bg-gradient-to-br from-violet-50/50 to-purple-50/30",
        selected && "ring-2 ring-primary ring-offset-2"
      )}>
        {/* Header */}
        <div className="flex items-center gap-3 p-3 border-b border-violet-200/50">
          <div
            className="cursor-grab active:cursor-grabbing opacity-40 hover:opacity-100"
            contentEditable={false}
            data-drag-handle
          >
            <GripVertical className="h-5 w-5" />
          </div>

          <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-violet-500/10 border border-violet-200">
            <Repeat className="h-5 w-5 text-violet-600" />
          </div>

          <div className="flex-1">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-sm text-violet-900">
                Eventos Seleccionados
              </span>
              <Badge variant="secondary" className="text-xs bg-violet-100 text-violet-700">
                Se repite
              </Badge>
            </div>
            <p className="text-xs text-violet-600/80">
              Cada evento que selecciones usará el template definido abajo
            </p>
          </div>

          <div className="flex items-center gap-1" contentEditable={false}>
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0 text-muted-foreground hover:text-destructive"
              onClick={() => deleteNode()}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Preview */}
        <div className="p-3" contentEditable={false}>
          <div className="flex items-center gap-1.5 text-xs text-violet-500 mb-2">
            <Eye className="h-3.5 w-3.5" />
            <span>Vista previa con datos de ejemplo ({EXAMPLE_EVENT.tipo_evento}):</span>
          </div>

          <div className="bg-white/80 border border-violet-200 rounded-md p-3">
            {renderContentWithVariables(eventTemplateContent ?? null)}
          </div>

          <p className="text-[10px] text-violet-400 mt-2 text-center">
            Esto se repetirá para: ETI, Bronquiolitis, y cada evento que selecciones
          </p>
        </div>
      </Card>
    </NodeViewWrapper>
  );
}

// TipTap Extension
export const SelectedEventsPlaceholderExtension = Node.create({
  name: "selectedEventsPlaceholder",
  group: "block",
  atom: true,
  draggable: true,

  parseHTML() {
    return [{ tag: 'div[data-type="selected-events-placeholder"]' }];
  },

  renderHTML({ HTMLAttributes }) {
    return ["div", mergeAttributes(HTMLAttributes, { "data-type": "selected-events-placeholder" })];
  },

  addNodeView() {
    return ReactNodeViewRenderer(SelectedEventsPlaceholderView);
  },

  addCommands() {
    return {
      insertSelectedEventsPlaceholder: () => ({ commands }) => {
        return commands.insertContent({
          type: this.name,
        });
      },
    };
  },
});
