"use client";

import { Plus, Type, AlignLeft, Table, BarChart3, Image, Minus, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import type { BlockType } from "./types";

interface BlockPaletteProps {
  onAddBlock: (type: BlockType) => void;
}

const BLOCK_TYPES = [
  {
    type: "heading" as BlockType,
    icon: Type,
    label: "Titulo",
    description: "H1, H2 o H3",
    color: "text-blue-600",
  },
  {
    type: "paragraph" as BlockType,
    icon: AlignLeft,
    label: "Parrafo",
    description: "Texto con formato",
    color: "text-green-600",
  },
  {
    type: "table" as BlockType,
    icon: Table,
    label: "Tabla",
    description: "Manual o query",
    color: "text-purple-600",
  },
  {
    type: "chart" as BlockType,
    icon: BarChart3,
    label: "Grafico",
    description: "Lineas, barras, corredor",
    color: "text-orange-600",
  },
  {
    type: "image" as BlockType,
    icon: Image,
    label: "Imagen",
    description: "Con pie de foto",
    color: "text-pink-600",
  },
  {
    type: "divider" as BlockType,
    icon: Minus,
    label: "Separador",
    description: "Linea divisoria",
    color: "text-gray-600",
  },
  {
    type: "pagebreak" as BlockType,
    icon: FileText,
    label: "Salto de pagina",
    description: "Para el PDF",
    color: "text-amber-600",
  },
];

export function BlockPalette({ onAddBlock }: BlockPaletteProps) {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="outline" size="sm">
          <Plus className="h-4 w-4 mr-2" />
          Agregar Bloque
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-80" align="start">
        <div className="space-y-1">
          <h4 className="font-semibold text-sm mb-2">Selecciona un tipo de bloque</h4>
          {BLOCK_TYPES.map((blockType) => (
            <button
              key={blockType.type}
              onClick={() => onAddBlock(blockType.type)}
              className="w-full flex items-start gap-3 p-3 rounded-lg hover:bg-gray-100 transition-colors text-left"
            >
              <blockType.icon className={`h-5 w-5 mt-0.5 ${blockType.color}`} />
              <div className="flex-1">
                <div className="font-medium text-sm">{blockType.label}</div>
                <div className="text-xs text-muted-foreground">
                  {blockType.description}
                </div>
              </div>
            </button>
          ))}
        </div>
      </PopoverContent>
    </Popover>
  );
}
