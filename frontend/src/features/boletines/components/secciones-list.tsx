"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";
import { SeccionItem } from "./seccion-item";
import { SeccionConfigDialog } from "./seccion-config-dialog";
import type { SeccionConfig, TipoSeccion } from "./types";
import { DEFAULT_SECCION_PARAMS, SECCIONES_METADATA } from "./types";
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from "@dnd-kit/core";
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";

interface SeccionesListProps {
  secciones: SeccionConfig[];
  onChange: (secciones: SeccionConfig[]) => void;
}

export function SeccionesList({ secciones, onChange }: SeccionesListProps) {
  const [editingSeccion, setEditingSeccion] = useState<SeccionConfig | null>(null);
  const [showAddDialog, setShowAddDialog] = useState(false);

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      const oldIndex = secciones.findIndex((s) => s.id === active.id);
      const newIndex = secciones.findIndex((s) => s.id === over.id);

      const reordered = arrayMove(secciones, oldIndex, newIndex).map((s, idx) => ({
        ...s,
        orden: idx + 1,
      }));

      onChange(reordered);
    }
  };

  const handleToggleEnabled = (id: string) => {
    onChange(
      secciones.map((s) =>
        s.id === id ? { ...s, enabled: !s.enabled } : s
      )
    );
  };

  const handleConfigureSeccion = (seccion: SeccionConfig) => {
    setEditingSeccion(seccion);
  };

  const handleSaveSeccionConfig = (updated: SeccionConfig) => {
    onChange(secciones.map((s) => (s.id === updated.id ? updated : s)));
    setEditingSeccion(null);
  };

  const handleDeleteSeccion = (id: string) => {
    onChange(secciones.filter((s) => s.id !== id));
  };

  const handleAddSeccion = (tipo: TipoSeccion) => {
    const metadata = SECCIONES_METADATA.find((m) => m.tipo === tipo);
    if (!metadata) return;

    const newSeccion: SeccionConfig = {
      id: `${tipo}-${Date.now()}`,
      tipo,
      orden: secciones.length + 1,
      titulo: metadata.nombre,
      contenido_html: "",
      enabled: true,
      params: DEFAULT_SECCION_PARAMS[tipo] || {},
    };

    onChange([...secciones, newSeccion]);
    setShowAddDialog(false);
  };

  const seccionesFijas = secciones.filter((s) => {
    const meta = SECCIONES_METADATA.find((m) => m.tipo === s.tipo);
    return meta?.categoria === "fija";
  });

  const seccionesConDatos = secciones.filter((s) => {
    const meta = SECCIONES_METADATA.find((m) => m.tipo === s.tipo);
    return meta?.categoria === "datos";
  });

  const seccionesCustom = secciones.filter((s) => {
    const meta = SECCIONES_METADATA.find((m) => m.tipo === s.tipo);
    return meta?.categoria === "custom";
  });

  // Secciones disponibles para agregar (que no están ya en la lista)
  const tiposExistentes = new Set(secciones.map((s) => s.tipo));
  const seccionesDisponibles = SECCIONES_METADATA.filter(
    (m) =>
      !tiposExistentes.has(m.tipo) ||
      m.tipo === "enfermedad_especifica" ||
      m.tipo === "texto_libre"
  );

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <span className="text-2xl">📋</span>
            <span>Secciones del Boletín</span>
          </CardTitle>

          <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
            <DialogTrigger asChild>
              <Button size="sm" variant="outline">
                <Plus className="h-4 w-4 mr-2" />
                Agregar Sección
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Agregar Nueva Sección</DialogTitle>
              </DialogHeader>
              <ScrollArea className="h-[400px] pr-4">
                <div className="space-y-4">
                  {seccionesDisponibles.length === 0 ? (
                    <p className="text-sm text-muted-foreground text-center py-8">
                      Todas las secciones disponibles ya están agregadas.
                    </p>
                  ) : (
                    seccionesDisponibles.map((meta) => (
                      <button
                        key={meta.tipo}
                        onClick={() => handleAddSeccion(meta.tipo)}
                        className="w-full text-left p-4 border rounded-lg hover:bg-accent hover:border-accent-foreground transition-colors"
                      >
                        <div className="flex items-start gap-3">
                          <span className="text-2xl">{meta.icono}</span>
                          <div className="flex-1">
                            <h4 className="font-semibold">{meta.nombre}</h4>
                            <p className="text-sm text-muted-foreground mt-1">
                              {meta.descripcion}
                            </p>
                            <div className="flex gap-2 mt-2">
                              <span className="text-xs px-2 py-0.5 bg-secondary rounded">
                                {meta.categoria}
                              </span>
                              {meta.requiere_backend && (
                                <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded">
                                  Genera datos
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      </button>
                    ))
                  )}
                </div>
              </ScrollArea>
            </DialogContent>
          </Dialog>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        <p className="text-sm text-muted-foreground">
          Arrastra para reordenar. Activa/desactiva con el switch. Click en el ícono de
          configuración para ajustar parámetros.
        </p>

        <DndContext
          sensors={sensors}
          collisionDetection={closestCenter}
          onDragEnd={handleDragEnd}
        >
          <SortableContext items={secciones} strategy={verticalListSortingStrategy}>
            {/* Secciones Fijas */}
            {seccionesFijas.length > 0 && (
              <div className="space-y-2">
                <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
                  Secciones Fijas
                </h3>
                {seccionesFijas.map((seccion) => (
                  <SeccionItem
                    key={seccion.id}
                    seccion={seccion}
                    onToggleEnabled={handleToggleEnabled}
                    onConfigure={handleConfigureSeccion}
                    onDelete={handleDeleteSeccion}
                  />
                ))}
              </div>
            )}

            {/* Secciones con Datos */}
            {seccionesConDatos.length > 0 && (
              <div className="space-y-2">
                <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
                  Secciones con Datos
                </h3>
                {seccionesConDatos.map((seccion) => (
                  <SeccionItem
                    key={seccion.id}
                    seccion={seccion}
                    onToggleEnabled={handleToggleEnabled}
                    onConfigure={handleConfigureSeccion}
                    onDelete={handleDeleteSeccion}
                  />
                ))}
              </div>
            )}

            {/* Secciones Custom */}
            {seccionesCustom.length > 0 && (
              <div className="space-y-2">
                <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
                  Secciones Personalizadas
                </h3>
                {seccionesCustom.map((seccion) => (
                  <SeccionItem
                    key={seccion.id}
                    seccion={seccion}
                    onToggleEnabled={handleToggleEnabled}
                    onConfigure={handleConfigureSeccion}
                    onDelete={handleDeleteSeccion}
                  />
                ))}
              </div>
            )}
          </SortableContext>
        </DndContext>
      </CardContent>

      {/* Dialog de configuración */}
      {editingSeccion && (
        <SeccionConfigDialog
          seccion={editingSeccion}
          onSave={handleSaveSeccionConfig}
          onCancel={() => setEditingSeccion(null)}
        />
      )}
    </Card>
  );
}
