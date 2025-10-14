"use client";

import { Node, mergeAttributes } from "@tiptap/core";
import { NodeViewWrapper, ReactNodeViewRenderer, Editor } from "@tiptap/react";

interface VariableAttributes {
  variableKey: string;
  variableLabel: string;
  variableEmoji?: string;
  variableType?: "basic" | "stat" | "chart";
}

// Colores por tipo de variable
const VARIABLE_COLORS = {
  basic: {
    bg: "bg-blue-100 dark:bg-blue-900",
    text: "text-blue-800 dark:text-blue-200",
    border: "border-blue-200 dark:border-blue-700",
  },
  stat: {
    bg: "bg-green-100 dark:bg-green-900",
    text: "text-green-800 dark:text-green-200",
    border: "border-green-200 dark:border-green-700",
  },
  chart: {
    bg: "bg-orange-100 dark:bg-orange-900",
    text: "text-orange-800 dark:text-orange-200",
    border: "border-orange-200 dark:border-orange-700",
  },
};

// Componente React para renderizar la variable
const VariableComponent = ({ node }: { node: { attrs: VariableAttributes } }) => {
  const { variableLabel, variableEmoji, variableType = "basic" } = node.attrs;
  const colors = VARIABLE_COLORS[variableType];

  return (
    <NodeViewWrapper
      as="span"
      className={`inline-flex items-center gap-1 px-2 py-0.5 mx-0.5 rounded-md ${colors.bg} ${colors.text} text-sm border ${colors.border} cursor-default font-medium`}
      title={`Campo dinámico: ${variableLabel}\nSe reemplazará automáticamente con el valor real al generar el reporte.`}
      contentEditable={false}
      draggable
    >
      <span className="text-base">{variableEmoji || "📊"}</span>
      <span>{variableLabel}</span>
    </NodeViewWrapper>
  );
};

// Extensión de Tiptap para variables
export const VariableExtension = Node.create({
  name: "variable",

  group: "inline",

  inline: true,

  atom: true,

  addAttributes() {
    return {
      variableKey: {
        default: "",
      },
      variableLabel: {
        default: "",
      },
      variableEmoji: {
        default: "📊",
      },
      variableType: {
        default: "basic",
      },
    };
  },

  parseHTML() {
    return [
      {
        tag: "span[data-variable]",
        getAttrs: (element) => {
          const dom = element as HTMLElement;
          return {
            variableKey: dom.getAttribute("data-variable"),
            variableLabel: dom.getAttribute("data-label"),
            variableEmoji: dom.getAttribute("data-emoji") || "📊",
            variableType: dom.getAttribute("data-type") || "basic",
          };
        },
      },
    ];
  },

  renderHTML({ node }) {
    return [
      "span",
      {
        "data-variable": node.attrs.variableKey,
        class: "variable-placeholder",
        "data-label": node.attrs.variableLabel,
        "data-emoji": node.attrs.variableEmoji,
        "data-type": node.attrs.variableType,
      },
      `{{${node.attrs.variableKey}}}`,
    ];
  },

  addNodeView() {
    return ReactNodeViewRenderer(VariableComponent);
  },
});

// Helper para insertar una variable
export const insertVariable = (
  editor: Editor,
  variableKey: string,
  variableLabel: string,
  variableEmoji: string = "📊",
  variableType: "basic" | "stat" | "chart" = "basic"
) => {
  editor
    .chain()
    .focus()
    .insertContent({
      type: "variable",
      attrs: {
        variableKey,
        variableLabel,
        variableEmoji,
        variableType,
      },
    })
    .run();
};
