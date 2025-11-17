import { NodeViewWrapper } from "@tiptap/react";
import { NodeViewProps } from "@tiptap/core";
import { Table } from "lucide-react";

export const DynamicTableNodeView = ({ node }: NodeViewProps) => {
  const { queryType, title } = node.attrs;

  return (
    <NodeViewWrapper className="my-4">
      <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 bg-gray-50">
        <div className="flex items-center gap-3 text-gray-600">
          <Table className="w-5 h-5" />
          <div>
            <p className="font-semibold text-sm">Tabla Dinámica</p>
            {title && <p className="text-xs text-gray-500 mt-1">{title}</p>}
            <p className="text-xs text-gray-400 mt-1">Query: {queryType}</p>
          </div>
        </div>
      </div>
    </NodeViewWrapper>
  );
};
