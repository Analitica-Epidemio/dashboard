"use client";

import { useState } from "react";
import { DndContext, closestCenter, DragEndEvent } from "@dnd-kit/core";
import { SortableContext, verticalListSortingStrategy, arrayMove } from "@dnd-kit/sortable";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Plus, Save, FileText, Eye, EyeOff } from "lucide-react";
import { SeccionEditor } from "./seccion-editor";
import { PreviewBoletinPanel } from "./preview-boletin-panel";
import type { BoletinSemanalTemplate, SeccionConfig } from "./types";

interface BoletinSemanalEditorProps {
  initialTemplate: BoletinSemanalTemplate;
  onSave: (template: BoletinSemanalTemplate) => void;
  onCancel: () => void;
}

export function BoletinSemanalEditor({
  initialTemplate,
  onSave,
  onCancel,
}: BoletinSemanalEditorProps) {
  const [template, setTemplate] = useState<BoletinSemanalTemplate>(initialTemplate);
  const [hasChanges, setHasChanges] = useState(false);
  const [showPreview, setShowPreview] = useState(true);

  const updatePortada = <K extends keyof typeof template.portada>(
    field: K,
    value: (typeof template.portada)[K]
  ) => {
    setTemplate((prev) => ({
      ...prev,
      portada: { ...prev.portada, [field]: value },
    }));
    setHasChanges(true);
  };

  const updateSeccion = (updatedSeccion: SeccionConfig) => {
    setTemplate((prev) => ({
      ...prev,
      secciones: prev.secciones.map((s) =>
        s.id === updatedSeccion.id ? updatedSeccion : s
      ),
    }));
    setHasChanges(true);
  };

  const deleteSeccion = (id: string) => {
    setTemplate((prev) => ({
      ...prev,
      secciones: prev.secciones.filter((s) => s.id !== id),
    }));
    setHasChanges(true);
  };

  const addSeccion = () => {
    const newSeccion: SeccionConfig = {
      id: `seccion-${Date.now()}`,
      orden: template.secciones.length + 1,
      titulo: "Nueva Sección",
      contenido_html: "<p>Escribe el contenido aquí...</p>",
    };

    setTemplate((prev) => ({
      ...prev,
      secciones: [...prev.secciones, newSeccion],
    }));
    setHasChanges(true);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      setTemplate((prev) => {
        const oldIndex = prev.secciones.findIndex((s) => s.id === active.id);
        const newIndex = prev.secciones.findIndex((s) => s.id === over.id);

        const reordered = arrayMove(prev.secciones, oldIndex, newIndex);

        // Actualizar el orden de cada sección
        const withUpdatedOrder = reordered.map((s, idx) => ({
          ...s,
          orden: idx + 1,
        }));

        return { ...prev, secciones: withUpdatedOrder };
      });
      setHasChanges(true);
    }
  };

  const handleSave = () => {
    onSave(template);
    setHasChanges(false);
  };

  return (
    <div className="grid grid-cols-12 gap-6">
      {/* Panel Principal */}
      <div className={showPreview ? "col-span-8" : "col-span-12"}>
        <div className="space-y-6">
          {/* Header con acciones */}
          <Card>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <FileText className="h-5 w-5" />
                    {template.nombre}
                  </CardTitle>
                  <p className="text-sm text-muted-foreground mt-1">
                    Template de Boletín Semanal - {template.secciones.length} secciones
                  </p>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowPreview(!showPreview)}
                  >
                    {showPreview ? (
                      <>
                        <EyeOff className="h-4 w-4 mr-2" />
                        Ocultar Preview
                      </>
                    ) : (
                      <>
                        <Eye className="h-4 w-4 mr-2" />
                        Mostrar Preview
                      </>
                    )}
                  </Button>
                  {hasChanges && (
                    <span className="text-xs text-orange-600 flex items-center gap-1">
                      ● Sin guardar
                    </span>
                  )}
                  <Button onClick={handleSave} disabled={!hasChanges}>
                    <Save className="h-4 w-4 mr-2" />
                    Guardar
                  </Button>
                </div>
              </div>
            </CardHeader>
          </Card>

      {/* Configuración de Portada */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Portada</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label>Título</Label>
            <Input
              value={template.portada.titulo}
              onChange={(e) => updatePortada("titulo", e.target.value)}
              placeholder="Ej: Boletín Epidemiológico Provincial"
              className="mt-2"
            />
          </div>

          <div>
            <Label>Subtítulo</Label>
            <Input
              value={template.portada.subtitulo || ""}
              onChange={(e) => updatePortada("subtitulo", e.target.value)}
              placeholder="Ej: Departamento de Epidemiología"
              className="mt-2"
            />
          </div>

          <div className="flex items-center justify-between py-2">
            <div>
              <Label>Incluir logo</Label>
              <p className="text-xs text-muted-foreground">
                Logo institucional en la portada
              </p>
            </div>
            <Switch
              checked={template.portada.incluir_logo}
              onCheckedChange={(checked) => updatePortada("incluir_logo", checked)}
            />
          </div>
        </CardContent>
      </Card>

          {/* Secciones */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">Secciones del Boletín</CardTitle>
                <Button onClick={addSeccion} variant="outline" size="sm">
                  <Plus className="h-4 w-4 mr-2" />
                  Agregar Sección
                </Button>
              </div>
              <p className="text-sm text-muted-foreground">
                Arrastra para reordenar. Usa variables como {"{"}
                {"{"}semana_epidemiologica{"}"}{"}"}  para contenido dinámico.
              </p>
            </CardHeader>
            <CardContent>
              <DndContext
                collisionDetection={closestCenter}
                onDragEnd={handleDragEnd}
              >
                <SortableContext
                  items={template.secciones.map((s) => s.id)}
                  strategy={verticalListSortingStrategy}
                >
                  <div className="space-y-3">
                    {template.secciones.map((seccion) => (
                      <SeccionEditor
                        key={seccion.id}
                        seccion={seccion}
                        onChange={updateSeccion}
                        onDelete={deleteSeccion}
                      />
                    ))}

                    {template.secciones.length === 0 && (
                      <div className="text-center py-12 text-muted-foreground border-2 border-dashed rounded-lg">
                        <FileText className="h-12 w-12 mx-auto mb-3 opacity-20" />
                        <p className="font-medium">No hay secciones</p>
                        <p className="text-sm mt-1">
                          Agrega una sección para comenzar
                        </p>
                      </div>
                    )}
                  </div>
                </SortableContext>
              </DndContext>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Panel de Preview */}
      {showPreview && (
        <div className="col-span-4">
          <div className="sticky top-6">
            <PreviewBoletinPanel template={template} />
          </div>
        </div>
      )}
    </div>
  );
}
