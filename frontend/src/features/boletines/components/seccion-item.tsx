"use client";

import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { GripVertical, Settings, Trash2 } from "lucide-react";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import type { SeccionConfig } from "./types";
import { SECCIONES_METADATA } from "./types";
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

interface SeccionItemProps {
  seccion: SeccionConfig;
  onToggleEnabled: (id: string) => void;
  onConfigure: (seccion: SeccionConfig) => void;
  onDelete: (id: string) => void;
}

export function SeccionItem({
  seccion,
  onToggleEnabled,
  onConfigure,
  onDelete,
}: SeccionItemProps) {
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

  const metadata = SECCIONES_METADATA.find((m) => m.tipo === seccion.tipo);
  const canDelete = metadata?.categoria !== "fija";
  const canConfigure = metadata?.configurable;

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`flex items-center gap-3 p-3 border rounded-lg bg-card ${
        seccion.enabled ? "bg-card" : "bg-muted/30"
      } ${isDragging ? "shadow-lg" : ""}`}
    >
      {/* Drag Handle */}
      <button
        className="cursor-grab active:cursor-grabbing p-1 hover:bg-accent rounded"
        {...attributes}
        {...listeners}
      >
        <GripVertical className="h-4 w-4 text-muted-foreground" />
      </button>

      {/* Icono y número de orden */}
      <div className="flex items-center gap-2">
        <span className="text-xl">{metadata?.icono || "📄"}</span>
        <Badge variant="outline" className="text-xs font-mono">
          {seccion.orden}
        </Badge>
      </div>

      {/* Información de la sección */}
      <div className="flex-1 min-w-0">
        <h4 className={`font-medium ${!seccion.enabled && "text-muted-foreground"}`}>
          {seccion.titulo}
        </h4>
        <div className="flex items-center gap-2 mt-1">
          <span className="text-xs text-muted-foreground capitalize">
            {metadata?.categoria}
          </span>
          {metadata?.requiere_backend && (
            <Badge variant="secondary" className="text-xs">
              Genera datos
            </Badge>
          )}
        </div>
      </div>

      {/* Acciones */}
      <div className="flex items-center gap-2">
        {/* Botón de configuración */}
        {canConfigure && (
          <Button
            size="sm"
            variant="ghost"
            onClick={() => onConfigure(seccion)}
            disabled={!seccion.enabled}
            title="Configurar sección"
          >
            <Settings className="h-4 w-4" />
          </Button>
        )}

        {/* Botón de eliminar (solo para secciones custom/opcionales) */}
        {canDelete && (
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button
                size="sm"
                variant="ghost"
                className="text-destructive hover:text-destructive hover:bg-destructive/10"
                title="Eliminar sección"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>¿Eliminar sección?</AlertDialogTitle>
                <AlertDialogDescription>
                  Se eliminará la sección &quot;{seccion.titulo}&quot; del template. Esta acción no se
                  puede deshacer.
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
        )}

        {/* Switch para activar/desactivar */}
        <Switch
          checked={seccion.enabled}
          onCheckedChange={() => onToggleEnabled(seccion.id)}
        />
      </div>
    </div>
  );
}
