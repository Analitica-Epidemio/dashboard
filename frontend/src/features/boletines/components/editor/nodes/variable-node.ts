import { Node, mergeAttributes } from "@tiptap/core";
import { ReactNodeViewRenderer } from "@tiptap/react";
import { VariableNodeView } from "./variable-node-view";
import '../tiptap';

export interface VariableOptions {
  HTMLAttributes: Record<string, unknown>;
}

export const VariableNode = Node.create<VariableOptions>({
  name: "variable",

  group: "inline",

  inline: true,

  atom: true,

  addOptions() {
    return {
      HTMLAttributes: {},
    };
  },

  addAttributes() {
    return {
      variableId: {
        default: null,
        parseHTML: (element) => element.getAttribute("data-variable-id"),
        renderHTML: (attributes) => {
          if (!attributes.variableId) {
            return {};
          }

          return {
            "data-variable-id": attributes.variableId,
          };
        },
      },
    };
  },

  parseHTML() {
    return [
      {
        tag: 'span[data-type="variable"]',
      },
    ];
  },

  renderHTML({ HTMLAttributes }) {
    return [
      "span",
      mergeAttributes(this.options.HTMLAttributes, HTMLAttributes, {
        "data-type": "variable",
      }),
      0,
    ];
  },

  addNodeView() {
    return ReactNodeViewRenderer(VariableNodeView);
  },

  addCommands() {
    return {
      setVariable:
        (variableId: string) =>
        ({ commands }) => {
          return commands.insertContent({
            type: this.name,
            attrs: { variableId },
          });
        },
    };
  },
});
