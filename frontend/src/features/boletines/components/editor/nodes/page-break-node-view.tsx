import { NodeViewWrapper } from "@tiptap/react";
import { Scissors } from "lucide-react";

export const PageBreakNodeView = () => {
  return (
    <NodeViewWrapper className="my-6">
      <div className="flex items-center gap-2 text-gray-400">
        <div className="flex-1 h-px bg-gray-300" />
        <div className="flex items-center gap-2 px-3 py-1 bg-gray-100 rounded-full text-xs">
          <Scissors className="w-3 h-3" />
          <span>Salto de Página</span>
        </div>
        <div className="flex-1 h-px bg-gray-300" />
      </div>
    </NodeViewWrapper>
  );
};
