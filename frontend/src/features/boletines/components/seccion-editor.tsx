"use client";

import { useState } from "react";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { GripVertical, Trash2, ChevronDown, ChevronUp, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { TiptapTemplateEditor } from "@/features/boletines/components/editor/tiptap-template-editor";
import { VARIABLES_DISPONIBLES } from "./types";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import type { SeccionConfig } from "./types";

interface SeccionEditorProps {
  seccion: SeccionConfig;
  onChange: (seccion: SeccionConfig) => void;
  onDelete: (id: string) => void;
}

export function SeccionEditor({ seccion, onChange, onDelete }: SeccionEditorProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: seccion.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const insertVariable = (variable: string) => {
    // Add variable to the end of the content
    const newContent = seccion.contenido_html + " " + variable;
    onChange({ ...seccion, contenido_html: newContent });
  };

  return (
    <Card
      ref={setNodeRef}
      style={style}
      className={`border-2 ${isDragging ? "shadow-lg border-primary" : ""}`}
    >
      {/* Header */}
      <div className="flex items-center gap-2 p-3 border-b bg-muted/30">
        {/* Drag Handle */}
        <button
          className="cursor-grab active:cursor-grabbing p-1 hover:bg-accent rounded"
          {...attributes}
          {...listeners}
        >
          <GripVertical className="h-4 w-4 text-muted-foreground" />
        </button>

        {/* Orden */}
        <span className="text-xs font-mono text-muted-foreground w-8">
          #{seccion.orden}
        </span>

        {/* Titulo editable */}
        <Input
          value={seccion.titulo}
          onChange={(e) => onChange({ ...seccion, titulo: e.target.value })}
          className="flex-1 h-8 font-medium"
          placeholder="Título de la sección"
        />

        {/* Botón de variables */}
        <Popover>
          <PopoverTrigger asChild>
            <Button size="sm" variant="outline" className="h-8">
              <Sparkles className="h-3 w-3 mr-1" />
              Variables
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-80" align="end">
            <div className="space-y-2">
              <h4 className="font-medium text-sm">Insertar variable</h4>
              <p className="text-xs text-muted-foreground">
                Haz click para insertar una variable en el contenido
              </p>
              <div className="space-y-1 max-h-60 overflow-y-auto">
                {VARIABLES_DISPONIBLES.map((v) => (
                  <button
                    key={v.variable}
                    onClick={() => insertVariable(v.variable)}
                    className="w-full text-left p-2 rounded hover:bg-accent text-xs border"
                  >
                    <div className="font-mono text-primary">{v.variable}</div>
                    <div className="text-muted-foreground">{v.descripcion}</div>
                  </button>
                ))}
              </div>
            </div>
          </PopoverContent>
        </Popover>

        {/* Botón expandir/colapsar */}
        <Button
          size="sm"
          variant="ghost"
          onClick={() => setIsExpanded(!isExpanded)}
          className="h-8 w-8 p-0"
        >
          {isExpanded ? (
            <ChevronUp className="h-4 w-4" />
          ) : (
            <ChevronDown className="h-4 w-4" />
          )}
        </Button>

        {/* Botón eliminar */}
        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button
              size="sm"
              variant="ghost"
              className="h-8 w-8 p-0 text-destructive hover:bg-destructive/10"
            >
              <Trash2 className="h-3 w-3" />
            </Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Eliminar sección?</AlertDialogTitle>
              <AlertDialogDescription>
                Se eliminará la sección &quot;{seccion.titulo}&quot;. Esta acción no se puede deshacer.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancelar</AlertDialogCancel>
              <AlertDialogAction
                onClick={() => onDelete(seccion.id)}
                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              >
                Eliminar
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>

      {/* Contenido editable */}
      {isExpanded && (
        <div className="p-4">
          <TiptapTemplateEditor
            initialHtml={seccion.contenido_html}
            onChange={(html) => onChange({ ...seccion, contenido_html: html })}
          />
        </div>
      )}

      {/* Preview colapsado */}
      {!isExpanded && seccion.contenido_html && (
        <div className="p-3 text-sm text-muted-foreground line-clamp-2">
          {seccion.contenido_html.replace(/<[^>]*>/g, "").substring(0, 100)}...
        </div>
      )}
    </Card>
  );
}
