/**
 * TipTap extension for dynamic blocks
 * Allows inserting data-driven sections within the content flow
 */

import { Node, mergeAttributes } from "@tiptap/core";
import { ReactNodeViewRenderer } from "@tiptap/react";
import { DynamicBlockNodeView } from "./dynamic-block-node-view";

export interface DynamicBlockAttributes {
  blockId: string;
  queryType: string;
  /** Specific block type for config panel (e.g., 'curva_loop', 'curva_comparar_eventos') */
  blockType: string;
  renderType: string;
  queryParams: Record<string, unknown>;
  config: Record<string, unknown>;
  /** Whether this block is inside the event loop template */
  isInEventLoop?: boolean;
}

export interface DynamicBlockOptions {
  /** Whether blocks in this editor are inside the event loop template */
  isInEventLoop: boolean;
}

declare module "@tiptap/core" {
  interface Commands<ReturnType> {
    dynamicBlock: {
      insertDynamicBlock: (attrs: DynamicBlockAttributes) => ReturnType;
      updateDynamicBlock: (attrs: Partial<DynamicBlockAttributes>) => ReturnType;
      /** Mark all dynamic blocks as being in event loop */
      markBlocksAsEventLoop: () => ReturnType;
    };
  }
}

export const DynamicBlockExtension = Node.create<DynamicBlockOptions>({
  name: "dynamicBlock",
  group: "block",
  atom: true, // Cannot have content inside
  draggable: true,

  addOptions() {
    return {
      isInEventLoop: false,
    };
  },

  addAttributes() {
    return {
      blockId: {
        default: "",
      },
      isInEventLoop: {
        default: false,
        parseHTML: (element) => element.getAttribute("data-in-event-loop") === "true",
        renderHTML: (attributes) => {
          if (attributes.isInEventLoop) {
            return { "data-in-event-loop": "true" };
          }
          return {};
        },
      },
      queryType: {
        default: "",
      },
      blockType: {
        default: "",
      },
      renderType: {
        default: "table",
      },
      queryParams: {
        default: {},
        parseHTML: (element) => {
          const value = element.getAttribute("data-query-params");
          return value ? JSON.parse(value) : {};
        },
        renderHTML: (attributes) => {
          return {
            "data-query-params": JSON.stringify(attributes.queryParams),
          };
        },
      },
      config: {
        default: {},
        parseHTML: (element) => {
          const value = element.getAttribute("data-config");
          return value ? JSON.parse(value) : {};
        },
        renderHTML: (attributes) => {
          return {
            "data-config": JSON.stringify(attributes.config),
          };
        },
      },
    };
  },

  parseHTML() {
    return [
      {
        tag: 'div[data-type="dynamic-block"]',
      },
    ];
  },

  renderHTML({ HTMLAttributes }) {
    return [
      "div",
      mergeAttributes(HTMLAttributes, { "data-type": "dynamic-block" }),
    ];
  },

  addNodeView() {
    const isInEventLoop = this.options.isInEventLoop;
    return ReactNodeViewRenderer(DynamicBlockNodeView, {
      as: "div",
      className: isInEventLoop ? "is-in-event-loop" : undefined,
    });
  },


  addCommands() {
    return {
      insertDynamicBlock:
        (attrs) =>
        ({ commands }) => {
          return commands.insertContent({
            type: this.name,
            attrs,
          });
        },
      updateDynamicBlock:
        (attrs) =>
        ({ commands, state }) => {
          const { selection } = state;
          const node = state.doc.nodeAt(selection.from);
          if (node?.type.name === this.name) {
            return commands.updateAttributes(this.name, attrs);
          }
          return false;
        },
      markBlocksAsEventLoop:
        () =>
        ({ tr, state, dispatch }) => {
          let modified = false;
          state.doc.descendants((node, pos) => {
            if (node.type.name === "dynamicBlock" && !node.attrs.isInEventLoop) {
              tr.setNodeMarkup(pos, undefined, {
                ...node.attrs,
                isInEventLoop: true,
              });
              modified = true;
            }
          });
          if (modified && dispatch) {
            dispatch(tr);
          }
          return modified;
        },
    };
  },
});
