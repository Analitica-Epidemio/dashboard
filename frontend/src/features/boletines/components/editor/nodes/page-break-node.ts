import { Node, mergeAttributes } from "@tiptap/core";
import { ReactNodeViewRenderer } from "@tiptap/react";
import { PageBreakNodeView } from "./page-break-node-view";
import '../tiptap';

export interface PageBreakOptions {
  HTMLAttributes: Record<string, unknown>;
}

export const PageBreakNode = Node.create<PageBreakOptions>({
  name: "pageBreak",

  group: "block",

  atom: true,

  addOptions() {
    return {
      HTMLAttributes: {},
    };
  },

  parseHTML() {
    return [
      {
        tag: 'div[data-type="page-break"]',
      },
    ];
  },

  renderHTML({ HTMLAttributes }) {
    return [
      "div",
      mergeAttributes(this.options.HTMLAttributes, HTMLAttributes, {
        "data-type": "page-break",
      }),
    ];
  },

  addNodeView() {
    return ReactNodeViewRenderer(PageBreakNodeView);
  },

  addCommands() {
    return {
      setPageBreak:
        () =>
        ({ commands }) => {
          return commands.insertContent({
            type: this.name,
          });
        },
    };
  },
});
