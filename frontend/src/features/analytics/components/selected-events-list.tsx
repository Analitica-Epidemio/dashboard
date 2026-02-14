"use client";

import { useCallback } from "react";
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
import { GripVertical, X, TrendingUp, TrendingDown, Minus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import type { EventoSeleccionado } from "@/features/boletines/types";
import { useEventoPreview } from "@/features/boletines/api";
import {
  getColorForEvento,
  type ZonaEpidemica,
} from "@/features/boletines/components/nuevo/section-definitions";

interface SelectedEventsListProps {
  eventos: EventoSeleccionado[];
  semana: number;
  anio: number;
  numSemanas: number;
  onChange: (eventos: EventoSeleccionado[]) => void;
}

export function SelectedEventsList({
  eventos,
  semana,
  anio,
  numSemanas,
  onChange,
}: SelectedEventsListProps) {
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = useCallback(
    (event: DragEndEvent) => {
      const { active, over } = event;
      if (over && active.id !== over.id) {
        const oldIndex = eventos.findIndex((e) => e.codigo === active.id);
        const newIndex = eventos.findIndex((e) => e.codigo === over.id);
        const reordered = arrayMove(eventos, oldIndex, newIndex).map(
          (e, i) => ({ ...e, order: i })
        );
        onChange(reordered);
      }
    },
    [eventos, onChange]
  );

  const handleRemove = useCallback(
    (codigo: string) => {
      onChange(
        eventos
          .filter((e) => e.codigo !== codigo)
          .map((e, i) => ({ ...e, order: i }))
      );
    },
    [eventos, onChange]
  );

  if (eventos.length === 0) return null;

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragEnd={handleDragEnd}
    >
      <SortableContext
        items={eventos.map((e) => e.codigo)}
        strategy={verticalListSortingStrategy}
      >
        <div className="space-y-2">
          {eventos.map((evento) => (
            <SortableEventCard
              key={evento.codigo}
              evento={evento}
              semana={semana}
              anio={anio}
              numSemanas={numSemanas}
              onRemove={() => handleRemove(evento.codigo)}
            />
          ))}
        </div>
      </SortableContext>
    </DndContext>
  );
}

function SortableEventCard({
  evento,
  semana,
  anio,
  numSemanas,
  onRemove,
}: {
  evento: EventoSeleccionado;
  semana: number;
  anio: number;
  numSemanas: number;
  onRemove: () => void;
}) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: evento.codigo });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  const { data, isLoading } = useEventoPreview({
    codigo: evento.codigo,
    semana,
    anio,
    numSemanas,
  });

  const preview = data?.data;
  const color = getColorForEvento(evento.nombre);

  const borderColors: Record<string, string> = {
    blue: "border-l-blue-400",
    purple: "border-l-purple-400",
    orange: "border-l-orange-400",
    cyan: "border-l-cyan-400",
    red: "border-l-red-400",
    amber: "border-l-amber-400",
    rose: "border-l-rose-400",
    slate: "border-l-slate-400",
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={cn(
        "rounded-lg border border-l-4 p-2.5 bg-background text-sm group transition-shadow",
        borderColors[color] || borderColors.slate,
        isDragging && "shadow-lg ring-2 ring-primary/20"
      )}
    >
      {/* Header row: drag + name + remove */}
      <div className="flex items-center gap-1.5">
        <button
          {...attributes}
          {...listeners}
          className="p-0.5 cursor-grab active:cursor-grabbing text-muted-foreground/40 hover:text-muted-foreground shrink-0"
        >
          <GripVertical className="h-3.5 w-3.5" />
        </button>

        <span className="flex-1 truncate text-xs font-semibold">{evento.nombre}</span>

        <Button
          variant="ghost"
          size="sm"
          className="h-5 w-5 p-0 opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-destructive shrink-0"
          onClick={onRemove}
        >
          <X className="h-3 w-3" />
        </Button>
      </div>

      {/* Preview data */}
      {isLoading ? (
        <div className="mt-2 space-y-1">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-3 w-32" />
        </div>
      ) : preview?.corredor ? (
        <div className="mt-1.5 flex items-center gap-2 flex-wrap">
          <ZonaBadge zona={preview.corredor.zona_actual as ZonaEpidemica} />
          <TrendIndicator
            trend={preview.corredor.tendencia}
            value={preview.corredor.porcentaje_cambio ?? undefined}
          />
          {preview.metrics && preview.metrics.length > 0 && (
            <span className="text-[10px] text-muted-foreground">
              {preview.metrics[0].label}: <strong className="text-foreground">{preview.metrics[0].value}</strong>
            </span>
          )}
        </div>
      ) : preview?.metrics && preview.metrics.length > 0 ? (
        <div className="mt-1.5 flex items-center gap-3 text-[10px] text-muted-foreground">
          {preview.metrics.slice(0, 2).map((metric, i) => (
            <span key={i}>
              {metric.label}: <strong className="text-foreground">{metric.value}</strong>
            </span>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function ZonaBadge({ zona }: { zona: ZonaEpidemica }) {
  const config: Record<ZonaEpidemica, { bg: string; text: string; label: string }> = {
    exito: { bg: "bg-green-100", text: "text-green-800", label: "Éxito" },
    seguridad: { bg: "bg-yellow-100", text: "text-yellow-800", label: "Seguridad" },
    alerta: { bg: "bg-orange-100", text: "text-orange-800", label: "Alerta" },
    brote: { bg: "bg-red-100", text: "text-red-800", label: "Brote" },
  };
  const c = config[zona] || config.seguridad;
  return (
    <span className={cn("inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold", c.bg, c.text)}>
      {c.label}
    </span>
  );
}

function TrendIndicator({ trend, value }: { trend?: "up" | "down" | "stable"; value?: number }) {
  if (!trend) return null;
  const config = {
    up: { icon: TrendingUp, color: "text-red-600" },
    down: { icon: TrendingDown, color: "text-green-600" },
    stable: { icon: Minus, color: "text-gray-500" },
  };
  const c = config[trend];
  const Icon = c.icon;
  const displayValue = value !== undefined ? `${value > 0 ? "+" : ""}${value.toFixed(0)}%` : "";
  return (
    <span className={cn("inline-flex items-center gap-0.5 text-[10px] font-medium", c.color)}>
      <Icon className="h-3 w-3" />
      {displayValue}
    </span>
  );
}
