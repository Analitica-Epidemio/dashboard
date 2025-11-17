import { Node, mergeAttributes } from "@tiptap/core";
import { ReactNodeViewRenderer } from "@tiptap/react";
import { DynamicTableNodeView } from "./dynamic-table-node-view";
import '../tiptap';

export interface DynamicTableOptions {
  HTMLAttributes: Record<string, unknown>;
}

export const DynamicTableNode = Node.create<DynamicTableOptions>({
  name: "dynamicTable",

  group: "block",

  atom: true,

  addOptions() {
    return {
      HTMLAttributes: {},
    };
  },

  addAttributes() {
    return {
      queryType: {
        default: null,
        parseHTML: (element) => element.getAttribute("data-query-type"),
        renderHTML: (attributes) => {
          if (!attributes.queryType) {
            return {};
          }

          return {
            "data-query-type": attributes.queryType,
          };
        },
      },
      title: {
        default: null,
        parseHTML: (element) => element.getAttribute("data-title"),
        renderHTML: (attributes) => {
          if (!attributes.title) {
            return {};
          }

          return {
            "data-title": attributes.title,
          };
        },
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
      mergeAttributes(this.options.HTMLAttributes, HTMLAttributes, {
        "data-type": "dynamic-table",
      }),
    ];
  },

  addNodeView() {
    return ReactNodeViewRenderer(DynamicTableNodeView);
  },

  addCommands() {
    return {
      setDynamicTable:
        (config) =>
        ({ commands }) => {
          return commands.insertContent({
            type: this.name,
            attrs: config,
          });
        },
    };
  },
});
