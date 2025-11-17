"use client";

import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { GripVertical, Trash2, AlignLeft, AlignCenter, AlignRight } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { TiptapTemplateEditor } from "@/features/boletines/components/editor/tiptap-template-editor";
import type { ParagraphBlock } from "./types";

interface ParagraphBlockEditorProps {
  block: ParagraphBlock;
  onChange: (block: ParagraphBlock) => void;
  onDelete: (id: string) => void;
}

export function ParagraphBlockEditor({ block, onChange, onDelete }: ParagraphBlockEditorProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: block.id,
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const updateField = <K extends keyof ParagraphBlock>(field: K, value: ParagraphBlock[K]) => {
    onChange({ ...block, [field]: value });
  };

  return (
    <Card ref={setNodeRef} style={style} className="p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start gap-3">
        {/* Drag Handle */}
        <button
          {...attributes}
          {...listeners}
          className="mt-2 cursor-grab active:cursor-grabbing text-gray-400 hover:text-gray-600"
        >
          <GripVertical className="h-5 w-5" />
        </button>

        {/* Content */}
        <div className="flex-1 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono text-muted-foreground">#{block.orden}</span>
              <span className="text-xs font-semibold text-green-600">PARAGRAPH</span>
            </div>

            {/* Alignment */}
            <div className="flex gap-1">
              <Button
                variant={block.align === "left" || !block.align ? "default" : "outline"}
                size="sm"
                onClick={() => updateField("align", "left")}
              >
                <AlignLeft className="h-4 w-4" />
              </Button>
              <Button
                variant={block.align === "center" ? "default" : "outline"}
                size="sm"
                onClick={() => updateField("align", "center")}
              >
                <AlignCenter className="h-4 w-4" />
              </Button>
              <Button
                variant={block.align === "right" ? "default" : "outline"}
                size="sm"
                onClick={() => updateField("align", "right")}
              >
                <AlignRight className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* Rich text editor */}
          <TiptapTemplateEditor
            initialHtml={block.content}
            onChange={(html) => updateField("content", html)}
          />
        </div>

        {/* Delete button */}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onDelete(block.id)}
          className="text-red-500 hover:text-red-700 hover:bg-red-50"
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      </div>
    </Card>
  );
}
