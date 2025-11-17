"use client";

import { Node, mergeAttributes } from "@tiptap/core";
import { ReactNodeViewRenderer, NodeViewWrapper, type NodeViewProps } from "@tiptap/react";
import type { VariableAttrs } from '../tiptap';
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Hash, Settings } from "lucide-react";

// Variables disponibles para boletines epidemiológicos
export const AVAILABLE_VARIABLES = [
  {
    id: "año",
    nombre: "Año",
    ejemplo: "2025",
    descripcion: "Año del boletín",
  },
  {
    id: "semana",
    nombre: "Semana Epidemiológica",
    ejemplo: "10",
    descripcion: "Número de semana epidemiológica",
  },
  {
    id: "fecha_inicio",
    nombre: "Fecha Inicio Semana",
    ejemplo: "2 de marzo",
    descripcion: "Fecha de inicio de la semana epidemiológica",
  },
  {
    id: "fecha_fin",
    nombre: "Fecha Fin Semana",
    ejemplo: "8 de marzo",
    descripcion: "Fecha de fin de la semana epidemiológica",
  },
  {
    id: "fecha_completa",
    nombre: "Fecha Completa Semana",
    ejemplo: "2 de marzo al 8 de marzo del 2025",
    descripcion: "Rango completo de fechas de la semana",
  },
  {
    id: "semana_anterior",
    nombre: "Semana Anterior",
    ejemplo: "09",
    descripcion: "Número de semana epidemiológica anterior",
  },
  {
    id: "fecha_hasta",
    nombre: "Fecha Hasta",
    ejemplo: "01/03",
    descripcion: "Fecha hasta la cual se procesaron datos",
  },
];

// Componente React para renderizar el nodo
function VariableComponent({ node, updateAttributes }: NodeViewProps) {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const variableId = node.attrs.variableId as string;

  const selectedVariable = AVAILABLE_VARIABLES.find(
    (v) => v.id === variableId
  );

  return (
    <>
      <NodeViewWrapper
        as="span"
        className="inline-block"
        contentEditable={false}
      >
        <span
          onClick={() => setIsDialogOpen(true)}
          className="inline-flex items-center gap-1 px-2 py-0.5 bg-purple-100 hover:bg-purple-200 text-purple-900 rounded text-xs font-medium cursor-pointer transition-colors group border border-purple-200"
          title={selectedVariable?.descripcion}
        >
          <Hash className="h-3 w-3 text-purple-600" />
          <span className="font-semibold">{selectedVariable?.nombre || variableId}:</span>
          <span className="text-purple-700">{selectedVariable?.ejemplo || variableId}</span>
          <Settings className="h-3 w-3 text-purple-600 opacity-0 group-hover:opacity-100 transition-opacity" />
        </span>
      </NodeViewWrapper>

      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Seleccionar Variable</DialogTitle>
            <DialogDescription>
              Elige qué variable dinámica insertar. Se reemplazará
              automáticamente al generar el boletín.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-2">
            <Label>Variable</Label>
            <Select
              value={variableId}
              onValueChange={(value) => {
                updateAttributes({ variableId: value });
                setIsDialogOpen(false);
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="Selecciona variable..." />
              </SelectTrigger>
              <SelectContent>
                {AVAILABLE_VARIABLES.map((v) => (
                  <SelectItem key={v.id} value={v.id}>
                    <div>
                      <div className="font-medium">{v.nombre}</div>
                      <div className="text-xs text-muted-foreground">
                        Ejemplo: {v.ejemplo}
                      </div>
                      <div className="text-[10px] text-muted-foreground">
                        {v.descripcion}
                      </div>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex justify-end gap-2 mt-4">
            <Button
              variant="outline"
              onClick={() => setIsDialogOpen(false)}
            >
              Cancelar
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}

// Definición de la extensión Tiptap
export const VariableExtension = Node.create({
  name: "variable",

  group: "inline",

  inline: true,

  atom: true,

  addAttributes() {
    return {
      variableId: {
        default: "año",
        parseHTML: (element) => element.getAttribute("data-variable-id"),
        renderHTML: (attributes) => {
          return {
            "data-variable-id": attributes.variableId,
          };
        },
      },
    };
  },

  parseHTML() {
    return [
      {
        tag: 'span[data-type="variable"]',
      },
    ];
  },

  renderHTML({ HTMLAttributes }) {
    return [
      "span",
      mergeAttributes(HTMLAttributes, { "data-type": "variable" }),
    ];
  },

  addNodeView() {
    return ReactNodeViewRenderer(VariableComponent);
  },

  addCommands() {
    return {
      insertVariable:
        (variableKey: string, _variableLabel?: string, _variableEmoji?: string, _variableType?: 'basic' | 'stat' | 'chart') =>
        ({ commands }) => {
          return commands.insertContent({
            type: this.name,
            attrs: {
              variableId: variableKey,
            },
          });
        },
    };
  },
});

// Helper para insertar una variable
export const insertVariable = (
  editor: import("@tiptap/react").Editor,
  variableKey: string,
  _variableLabel: string,
  _variableEmoji: string = "📊",
  _variableType: "basic" | "stat" | "chart" = "basic"
) => {
  editor
    .chain()
    .focus()
    .insertContent({
      type: "variable",
      attrs: {
        variableId: variableKey,
      },
    })
    .run();
};
