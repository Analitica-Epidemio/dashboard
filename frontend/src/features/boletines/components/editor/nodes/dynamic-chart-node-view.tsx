import { NodeViewWrapper } from "@tiptap/react";
import { NodeViewProps } from "@tiptap/core";
import { BarChart3 } from "lucide-react";

export const DynamicChartNodeView = ({ node }: NodeViewProps) => {
  const { queryType, chartType, title, height } = node.attrs;

  return (
    <NodeViewWrapper className="my-4">
      <div
        className="border-2 border-dashed border-blue-300 rounded-lg p-6 bg-blue-50"
        style={{ minHeight: `${height}px` }}
      >
        <div className="flex items-center gap-3 text-blue-600">
          <BarChart3 className="w-5 h-5" />
          <div>
            <p className="font-semibold text-sm">Gráfico Dinámico</p>
            {title && <p className="text-xs text-blue-500 mt-1">{title}</p>}
            <p className="text-xs text-blue-400 mt-1">
              Query: {queryType} | Tipo: {chartType}
            </p>
          </div>
        </div>
      </div>
    </NodeViewWrapper>
  );
};
