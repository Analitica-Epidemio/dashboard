"use client";

import { useCallback, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { toast } from "sonner";
import { ChevronDown, GripVertical } from "lucide-react";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  useSeccionesConfig,
  useUpdateSeccionesOrder,
} from "@/features/boletines/api";
import type { components } from "@/lib/api/types";

type SeccionConfig = components["schemas"]["SeccionConfigResponse"];

interface LocalSeccion extends SeccionConfig {
  _localActivo: boolean;
  _localOrden: number;
}

function toLocal(secciones: SeccionConfig[]): LocalSeccion[] {
  return secciones.map((s) => ({
    ...s,
    _localActivo: s.activo,
    _localOrden: s.orden,
  }));
}

export function SectionsStructure() {
  const queryClient = useQueryClient();
  const { data, isLoading } = useSeccionesConfig();
  const updateOrder = useUpdateSeccionesOrder();

  const [localSecciones, setLocalSecciones] = useState<LocalSeccion[] | null>(
    null
  );

  const serverSecciones = data?.data?.secciones ?? [];
  const secciones: LocalSeccion[] =
    localSecciones ?? toLocal(serverSecciones);

  const activasCount = secciones.filter((s) => s._localActivo).length;

  const hasChanges =
    localSecciones !== null &&
    serverSecciones.length > 0 &&
    JSON.stringify(
      localSecciones.map((s) => ({
        id: s.id,
        orden: s._localOrden,
        activo: s._localActivo,
      }))
    ) !==
      JSON.stringify(
        serverSecciones.map((s) => ({
          id: s.id,
          orden: s.orden,
          activo: s.activo,
        }))
      );

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = useCallback(
    (event: DragEndEvent) => {
      const { active, over } = event;
      if (!over || active.id === over.id) return;

      const oldIndex = secciones.findIndex((s) => s.id === active.id);
      const newIndex = secciones.findIndex((s) => s.id === over.id);

      const reordered = arrayMove(secciones, oldIndex, newIndex).map(
        (s, idx) => ({
          ...s,
          _localOrden: idx + 1,
        })
      );
      setLocalSecciones(reordered);
    },
    [secciones]
  );

  const handleToggle = useCallback(
    (id: number) => {
      const updated = secciones.map((s) =>
        s.id === id ? { ...s, _localActivo: !s._localActivo } : s
      );
      setLocalSecciones(updated);
    },
    [secciones]
  );

  const handleSave = async () => {
    try {
      await updateOrder.mutateAsync({
        body: {
          secciones: secciones.map((s) => ({
            id: s.id,
            orden: s._localOrden,
            activo: s._localActivo,
          })),
        },
      });
      queryClient.invalidateQueries({
        queryKey: ["get", "/api/v1/boletines/secciones-config"],
      });
      setLocalSecciones(null);
      toast.success("Estructura guardada");
    } catch {
      toast.error("Error al guardar estructura");
    }
  };

  if (isLoading) {
    return (
      <div className="max-w-2xl space-y-3 py-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-16 w-full rounded-lg" />
        ))}
      </div>
    );
  }

  return (
    <div className="max-w-2xl space-y-4 py-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          Arrastrá para reordenar. Usá el switch para activar/desactivar
          secciones.
        </p>
        <span className="text-sm text-muted-foreground tabular-nums">
          {activasCount}/{secciones.length} activas
        </span>
      </div>

      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={handleDragEnd}
      >
        <SortableContext
          items={secciones.map((s) => s.id)}
          strategy={verticalListSortingStrategy}
        >
          <div className="space-y-2">
            {secciones.map((seccion) => (
              <SortableSeccionCard
                key={seccion.id}
                seccion={seccion}
                onToggle={handleToggle}
              />
            ))}
          </div>
        </SortableContext>
      </DndContext>

      <div className="flex items-center gap-3 pt-2">
        <Button
          onClick={handleSave}
          disabled={!hasChanges || updateOrder.isPending}
        >
          {updateOrder.isPending ? "Guardando..." : "Guardar cambios"}
        </Button>
        {hasChanges && (
          <span className="text-sm text-amber-600">
            Cambios sin guardar
          </span>
        )}
      </div>
    </div>
  );
}

function SortableSeccionCard({
  seccion,
  onToggle,
}: {
  seccion: LocalSeccion;
  onToggle: (id: number) => void;
}) {
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
  };

  const bloques = seccion.bloques ?? [];

  return (
    <Collapsible>
      <div
        ref={setNodeRef}
        style={style}
        className={cn(
          "rounded-lg border bg-card p-3 transition-opacity",
          isDragging && "shadow-lg ring-2 ring-primary/20 z-10",
          !seccion._localActivo && "opacity-50"
        )}
      >
        <div className="flex items-center gap-3">
          <button
            className="cursor-grab active:cursor-grabbing touch-none text-muted-foreground hover:text-foreground"
            {...attributes}
            {...listeners}
          >
            <GripVertical className="h-4 w-4" />
          </button>

          <Switch
            checked={seccion._localActivo}
            onCheckedChange={() => onToggle(seccion.id)}
          />

          <div className="flex-1 min-w-0">
            <span className="text-sm font-medium truncate block">
              {seccion.titulo}
            </span>
            {seccion.descripcion && (
              <span className="text-xs text-muted-foreground truncate block">
                {seccion.descripcion}
              </span>
            )}
          </div>

          {bloques.length > 0 && (
            <CollapsibleTrigger asChild>
              <Button variant="ghost" size="sm" className="h-7 px-2">
                <span className="text-xs text-muted-foreground mr-1">
                  {bloques.length} bloque{bloques.length !== 1 ? "s" : ""}
                </span>
                <ChevronDown className="h-3 w-3 transition-transform [[data-state=open]_&]:rotate-180" />
              </Button>
            </CollapsibleTrigger>
          )}
        </div>

        {bloques.length > 0 && (
          <CollapsibleContent>
            <div className="mt-2 ml-11 space-y-1 border-l pl-3">
              {bloques.map((bloque) => (
                <div
                  key={bloque.id}
                  className="flex items-center gap-2 text-xs text-muted-foreground py-0.5"
                >
                  <Badge
                    variant="outline"
                    className="text-[10px] px-1.5 py-0 shrink-0"
                  >
                    {bloque.tipo_visualizacion}
                  </Badge>
                  <span className="truncate">{bloque.titulo_template}</span>
                </div>
              ))}
            </div>
          </CollapsibleContent>
        )}
      </div>
    </Collapsible>
  );
}
