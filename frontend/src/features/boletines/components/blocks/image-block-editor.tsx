"use client";

import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { GripVertical, Trash2, AlignLeft, AlignCenter, AlignRight, Image as ImageIcon } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import type { ImageBlock } from "./types";

interface ImageBlockEditorProps {
  block: ImageBlock;
  onChange: (block: ImageBlock) => void;
  onDelete: (id: string) => void;
}

export function ImageBlockEditor({ block, onChange, onDelete }: ImageBlockEditorProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: block.id,
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const updateField = <K extends keyof ImageBlock>(field: K, value: ImageBlock[K]) => {
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
            <span className="text-xs font-semibold text-pink-600">IMAGE</span>
          </div>

          {/* URL */}
          <div>
            <Label className="text-xs">URL de la imagen</Label>
            <Input
              value={block.url}
              onChange={(e) => updateField("url", e.target.value)}
              placeholder="https://ejemplo.com/imagen.png o /images/logo.png"
              className="mt-1"
            />
          </div>

          {/* Preview */}
          {block.url && (
            <div className="border rounded-lg p-2 bg-gray-50">
              <div className="flex items-center justify-center min-h-[100px]">
                <img
                  src={block.url}
                  alt={block.alt || "Preview"}
                  className="max-h-40 object-contain"
                  onError={(e) => {
                    (e.target as HTMLImageElement).style.display = "none";
                  }}
                />
              </div>
            </div>
          )}

          {!block.url && (
            <div className="border-2 border-dashed rounded-lg p-8 text-center text-muted-foreground">
              <ImageIcon className="h-12 w-12 mx-auto mb-2 opacity-20" />
              <p className="text-xs">Ingresa una URL para ver la preview</p>
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
            {/* Alt text */}
            <div>
              <Label className="text-xs">Texto alternativo</Label>
              <Input
                value={block.alt || ""}
                onChange={(e) => updateField("alt", e.target.value)}
                placeholder="Descripcion de la imagen"
                className="mt-1"
              />
            </div>

            {/* Width */}
            <div>
              <Label className="text-xs">Ancho (px o %)</Label>
              <Input
                type="number"
                value={block.width || ""}
                onChange={(e) => updateField("width", parseInt(e.target.value))}
                placeholder="Ej: 600"
                className="mt-1"
              />
            </div>
          </div>

          {/* Alignment */}
          <div>
            <Label className="text-xs">Alineacion</Label>
            <div className="flex gap-1 mt-1">
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

          {/* Caption */}
          <div>
            <Label className="text-xs">Pie de imagen (opcional)</Label>
            <Textarea
              value={block.caption || ""}
              onChange={(e) => updateField("caption", e.target.value)}
              placeholder="Ej: Figura 1. Calendario epidemiologico..."
              rows={2}
              className="mt-1 text-xs"
            />
          </div>
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
