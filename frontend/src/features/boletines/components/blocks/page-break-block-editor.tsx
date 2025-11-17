"use client";

import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { GripVertical, Trash2, FileText } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import type { PageBreakBlock } from "./types";

interface PageBreakBlockEditorProps {
  block: PageBreakBlock;
  onDelete: (id: string) => void;
}

export function PageBreakBlockEditor({ block, onDelete }: PageBreakBlockEditorProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: block.id,
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <Card ref={setNodeRef} style={style} className="p-4 hover:shadow-md transition-shadow bg-amber-50">
      <div className="flex items-center gap-3">
        {/* Drag Handle */}
        <button
          {...attributes}
          {...listeners}
          className="cursor-grab active:cursor-grabbing text-gray-400 hover:text-gray-600"
        >
          <GripVertical className="h-5 w-5" />
        </button>

        {/* Content */}
        <div className="flex-1 flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-muted-foreground">#{block.orden}</span>
            <span className="text-xs font-semibold text-amber-600">PAGE BREAK</span>
          </div>
          <div className="flex-1 border-t-2 border-dashed border-amber-400 flex items-center justify-center">
            <FileText className="h-4 w-4 text-amber-500" />
          </div>
          <span className="text-xs text-muted-foreground">Nueva pagina en PDF</span>
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
