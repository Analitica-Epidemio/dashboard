import { Node, mergeAttributes } from "@tiptap/core";
import { ReactNodeViewRenderer } from "@tiptap/react";
import { DynamicChartNodeView } from "./dynamic-chart-node-view";
import type { DynamicChartAttrs } from '../tiptap';

export interface DynamicChartOptions {
  HTMLAttributes: Record<string, unknown>;
}

export const DynamicChartNode = Node.create<DynamicChartOptions>({
  name: "dynamicChart",

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
      chartType: {
        default: "line",
        parseHTML: (element) => element.getAttribute("data-chart-type"),
        renderHTML: (attributes) => {
          return {
            "data-chart-type": attributes.chartType,
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
      height: {
        default: "400",
        parseHTML: (element) => element.getAttribute("data-height"),
        renderHTML: (attributes) => {
          return {
            "data-height": attributes.height,
          };
        },
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
      mergeAttributes(this.options.HTMLAttributes, HTMLAttributes, {
        "data-type": "dynamic-chart",
      }),
    ];
  },

  addNodeView() {
    return ReactNodeViewRenderer(DynamicChartNodeView);
  },

  addCommands() {
    return {
      setDynamicChart:
        (config: DynamicChartAttrs) =>
        ({ commands }) => {
          return commands.insertContent({
            type: this.name,
            attrs: config,
          });
        },
    };
  },
});
