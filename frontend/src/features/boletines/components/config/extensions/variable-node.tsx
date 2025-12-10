/**
 * TipTap extension for Variable Nodes
 * Renders template variables as colored pills with tooltips
 */

import { Node, mergeAttributes } from "@tiptap/core";
import { ReactNodeViewRenderer, NodeViewWrapper, NodeViewProps } from "@tiptap/react";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Hash,
  Calendar,
  TrendingUp,
  Bug,
  Clock,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";

// Variable metadata with examples
// Nombres explícitos y no ambiguos para mejor comprensión
const VARIABLE_META: Record<string, {
  label: string;
  icon: LucideIcon;
  example: string;
  category: "base" | "event";
  description?: string;
}> = {
  // ═══════════════════════════════════════════════════════════════════════════
  // Variables generales del boletín (azul)
  // ═══════════════════════════════════════════════════════════════════════════
  anio_epidemiologico: {
    label: "Año Epidemiológico",
    icon: Calendar,
    example: "2025",
    category: "base",
    description: "Año del período de análisis del boletín"
  },
  semana_epidemiologica_actual: {
    label: "SE Actual",
    icon: Hash,
    example: "45",
    category: "base",
    description: "Semana epidemiológica hasta donde se analiza"
  },
  semana_epidemiologica_inicio: {
    label: "SE Inicio",
    icon: Hash,
    example: "42",
    category: "base",
    description: "Primera semana epidemiológica del período"
  },
  fecha_inicio_semana_epidemiologica: {
    label: "Fecha Inicio SE",
    icon: Calendar,
    example: "04/11/2025",
    category: "base",
    description: "Fecha de inicio del período analizado (DD/MM/YYYY)"
  },
  fecha_fin_semana_epidemiologica: {
    label: "Fecha Fin SE",
    icon: Calendar,
    example: "10/11/2025",
    category: "base",
    description: "Fecha de fin del período analizado (DD/MM/YYYY)"
  },
  num_semanas_analizadas: {
    label: "N° Semanas",
    icon: Clock,
    example: "4",
    category: "base",
    description: "Cantidad de semanas incluidas en el análisis"
  },

  // ═══════════════════════════════════════════════════════════════════════════
  // Variables de evento sanitario (violeta)
  // ═══════════════════════════════════════════════════════════════════════════
  nombre_evento_sanitario: {
    label: "Nombre Evento",
    icon: Bug,
    example: "Dengue",
    category: "event",
    description: "Nombre completo del evento sanitario (ej: Dengue, Tuberculosis)"
  },
  codigo_evento_snvs: {
    label: "Código SNVS",
    icon: Hash,
    example: "A97",
    category: "event",
    description: "Código CIE-10 del evento en el Sistema Nacional de Vigilancia"
  },
  descripcion_tendencia_casos: {
    label: "Tendencia",
    icon: TrendingUp,
    example: "Se observa un incremento del 25% respecto a la SE anterior (120 → 150 casos)",
    category: "event",
    description: "Texto descriptivo comparando casos actuales vs semana anterior"
  },
  casos_semana_actual: {
    label: "Casos SE Actual",
    icon: Hash,
    example: "156",
    category: "event",
    description: "Cantidad de casos notificados en la semana epidemiológica actual"
  },
  casos_semana_anterior: {
    label: "Casos SE Anterior",
    icon: Hash,
    example: "125",
    category: "event",
    description: "Cantidad de casos notificados en la semana anterior para comparación"
  },
  porcentaje_cambio: {
    label: "% Cambio",
    icon: TrendingUp,
    example: "+24.8%",
    category: "event",
    description: "Variación porcentual entre semana actual y anterior"
  },
};

declare module "@tiptap/core" {
  interface Commands<ReturnType> {
    variableNode: {
      insertVariable: (key: string) => ReturnType;
    };
  }
}

// Node View Component
function VariableNodeView({ node }: NodeViewProps) {
  const variableKey = node.attrs.variableKey as string;
  // También leer el ejemplo del attrs si viene desde el seed
  const exampleFromAttrs = node.attrs.example as string | undefined;
  const meta = VARIABLE_META[variableKey];

  if (!meta) {
    // Fallback for unknown variables - mostrar el ejemplo si viene en attrs
    return (
      <NodeViewWrapper as="span" className="inline">
        <TooltipProvider delayDuration={300}>
          <Tooltip>
            <TooltipTrigger asChild>
              <Badge variant="outline" className="mx-0.5 font-mono text-xs">
                {`{{ ${variableKey} }}`}
              </Badge>
            </TooltipTrigger>
            {exampleFromAttrs && (
              <TooltipContent side="top" className="max-w-xs">
                <div className="space-y-1">
                  <p className="font-medium text-xs">Variable desconocida</p>
                  <p className="text-xs text-muted-foreground">
                    Ejemplo: <span className="font-medium text-foreground">{exampleFromAttrs}</span>
                  </p>
                </div>
              </TooltipContent>
            )}
          </Tooltip>
        </TooltipProvider>
      </NodeViewWrapper>
    );
  }

  const Icon = meta.icon;
  const isEvent = meta.category === "event";
  // Usar ejemplo del attrs si existe, sino el de VARIABLE_META
  const example = exampleFromAttrs || meta.example;

  return (
    <NodeViewWrapper as="span" className="inline">
      <TooltipProvider delayDuration={300}>
        <Tooltip>
          <TooltipTrigger asChild>
            <Badge
              variant="secondary"
              className={cn(
                "mx-0.5 cursor-default font-normal gap-1 py-0.5",
                isEvent
                  ? "bg-violet-100 text-violet-700 hover:bg-violet-200 border-violet-200"
                  : "bg-blue-100 text-blue-700 hover:bg-blue-200 border-blue-200"
              )}
            >
              <Icon className="h-3 w-3" />
              <span>{meta.label}</span>
            </Badge>
          </TooltipTrigger>
          <TooltipContent side="top" className="max-w-sm">
            <div className="space-y-1.5">
              <p className="font-medium text-xs">
                {isEvent ? "Variable de evento sanitario" : "Variable general del boletín"}
              </p>
              {meta.description && (
                <p className="text-xs text-muted-foreground">
                  {meta.description}
                </p>
              )}
              <p className="text-xs">
                <span className="text-muted-foreground">Ejemplo: </span>
                <span className="font-medium text-foreground">{example}</span>
              </p>
              <p className="text-[10px] font-mono text-muted-foreground border-t pt-1 mt-1">
                {`{{ ${variableKey} }}`}
              </p>
            </div>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    </NodeViewWrapper>
  );
}

// TipTap Extension
export const VariableNodeExtension = Node.create({
  name: "variableNode",
  group: "inline",
  inline: true,
  atom: true,

  addAttributes() {
    return {
      variableKey: {
        default: "",
      },
      example: {
        default: null,
      },
    };
  },

  parseHTML() {
    return [
      {
        tag: 'span[data-type="variable"]',
        getAttrs: (element) => {
          if (typeof element === "string") return false;
          return {
            variableKey: element.getAttribute("data-variable-key"),
          };
        },
      },
    ];
  },

  renderHTML({ HTMLAttributes }) {
    return [
      "span",
      mergeAttributes(HTMLAttributes, {
        "data-type": "variable",
        "data-variable-key": HTMLAttributes.variableKey,
      }),
      `{{ ${HTMLAttributes.variableKey} }}`,
    ];
  },

  addNodeView() {
    return ReactNodeViewRenderer(VariableNodeView);
  },

  addCommands() {
    return {
      insertVariable:
        (key: string) =>
        ({ commands }) => {
          return commands.insertContent({
            type: this.name,
            attrs: { variableKey: key },
          });
        },
    };
  },
});

// Export metadata for use in dropdowns
export { VARIABLE_META };
