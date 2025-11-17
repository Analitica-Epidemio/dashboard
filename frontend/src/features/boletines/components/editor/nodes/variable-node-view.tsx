import { NodeViewWrapper } from "@tiptap/react";
import { NodeViewProps } from "@tiptap/core";

export const VariableNodeView = ({ node }: NodeViewProps) => {
  const variableId = node.attrs.variableId;

  return (
    <NodeViewWrapper
      as="span"
      className="inline-flex items-center px-2 py-0.5 rounded bg-blue-100 text-blue-800 text-sm font-medium"
      data-type="variable"
      data-variable-id={variableId}
    >
      {`{{${variableId}}}`}
    </NodeViewWrapper>
  );
};
