"use client";

import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { GripVertical, Trash2, AlignLeft, AlignCenter, AlignRight } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { HeadingBlock } from "./types";

interface HeadingBlockEditorProps {
  block: HeadingBlock;
  onChange: (block: HeadingBlock) => void;
  onDelete: (id: string) => void;
}

export function HeadingBlockEditor({ block, onChange, onDelete }: HeadingBlockEditorProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: block.id,
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const updateField = <K extends keyof HeadingBlock>(field: K, value: HeadingBlock[K]) => {
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
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-muted-foreground">#{block.orden}</span>
            <span className="text-xs font-semibold text-blue-600">HEADING</span>
          </div>

          <div className="grid grid-cols-2 gap-3">
            {/* Level selector */}
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">Nivel</label>
              <Select
                value={block.level.toString()}
                onValueChange={(value) => updateField("level", parseInt(value) as 1 | 2 | 3)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1">Titulo 1 (H1)</SelectItem>
                  <SelectItem value="2">Titulo 2 (H2)</SelectItem>
                  <SelectItem value="3">Titulo 3 (H3)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Alignment */}
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">Alineacion</label>
              <div className="flex gap-1">
                <Button
                  variant={block.align === "left" || !block.align ? "default" : "outline"}
                  size="sm"
                  onClick={() => updateField("align", "left")}
                  className="flex-1"
                >
                  <AlignLeft className="h-4 w-4" />
                </Button>
                <Button
                  variant={block.align === "center" ? "default" : "outline"}
                  size="sm"
                  onClick={() => updateField("align", "center")}
                  className="flex-1"
                >
                  <AlignCenter className="h-4 w-4" />
                </Button>
                <Button
                  variant={block.align === "right" ? "default" : "outline"}
                  size="sm"
                  onClick={() => updateField("align", "right")}
                  className="flex-1"
                >
                  <AlignRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>

          {/* Content input */}
          <Input
            value={block.content}
            onChange={(e) => updateField("content", e.target.value)}
            placeholder="Escribe el titulo..."
            className={`font-semibold ${
              block.level === 1 ? "text-2xl" : block.level === 2 ? "text-xl" : "text-lg"
            }`}
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
