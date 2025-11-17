import { Node, mergeAttributes } from "@tiptap/core";
import { ReactNodeViewRenderer, NodeViewWrapper } from "@tiptap/react";
import { FileText } from "lucide-react";
import '../tiptap';

// Componente React para renderizar el nodo
function PageBreakComponent() {
  return (
    <NodeViewWrapper className="my-12">
      <div className="border-t-2 border-dashed border-blue-400 py-3 flex items-center justify-center gap-2">
        <FileText className="h-4 w-4 text-blue-600" />
        <span className="text-sm font-medium text-blue-600">Salto de página manual</span>
      </div>
    </NodeViewWrapper>
  );
}

// Definición de la extensión Tiptap
export const PageBreakExtension = Node.create({
  name: "pageBreak",

  group: "block",

  atom: true,

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
      mergeAttributes(HTMLAttributes, {
        "data-type": "page-break",
        class: "page-break",
      }),
    ];
  },

  addNodeView() {
    return ReactNodeViewRenderer(PageBreakComponent);
  },

  addCommands() {
    return {
      insertPageBreak:
        () =>
        ({ commands }) => {
          return commands.insertContent({
            type: this.name,
          });
        },
    };
  },
});
