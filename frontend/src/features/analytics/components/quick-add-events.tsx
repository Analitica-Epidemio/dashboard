"use client";

import { useState, useMemo } from "react";
import { Plus, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Command,
  CommandInput,
  CommandList,
  CommandEmpty,
  CommandGroup,
  CommandItem,
} from "@/components/ui/command";
import { useEventosDisponibles } from "@/features/boletines/api";
import type { EventoSeleccionado } from "@/features/boletines/types";

interface QuickAddEventsProps {
  eventosSeleccionados: EventoSeleccionado[];
  onAdd: (evento: EventoSeleccionado) => void;
}

export function QuickAddEvents({ eventosSeleccionados, onAdd }: QuickAddEventsProps) {
  const [open, setOpen] = useState(false);
  const { data, isLoading } = useEventosDisponibles();

  const selectedCodigos = useMemo(
    () => new Set(eventosSeleccionados.map((e) => e.codigo)),
    [eventosSeleccionados]
  );

  const eventos = data?.data || [];
  const grupoEnos = eventos.filter((e) => e.tipo === "grupo_de_enfermedades");
  const tipoEnos = eventos.filter((e) => e.tipo === "tipo_eno");

  const handleSelect = (evento: { id: number; codigo: string; nombre: string; tipo: string }) => {
    if (selectedCodigos.has(evento.codigo)) return;
    onAdd({
      id: evento.id,
      codigo: evento.codigo,
      nombre: evento.nombre,
      tipo: evento.tipo as EventoSeleccionado["tipo"],
      order: eventosSeleccionados.length,
    });
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button variant="outline" size="sm" className="w-full gap-1.5 text-xs">
          <Plus className="h-3.5 w-3.5" />
          Agregar evento
        </Button>
      </PopoverTrigger>
      <PopoverContent className="p-0 w-[300px]" align="start">
        <Command>
          <CommandInput placeholder="Buscar evento..." />
          <CommandList>
            <CommandEmpty>
              {isLoading ? "Cargando..." : "No se encontraron eventos"}
            </CommandEmpty>
            {grupoEnos.length > 0 && (
              <CommandGroup heading="Grupos">
                {grupoEnos.map((evento) => {
                  const isSelected = selectedCodigos.has(evento.codigo);
                  return (
                    <CommandItem
                      key={evento.codigo}
                      value={`${evento.nombre} ${evento.codigo}`}
                      onSelect={() => handleSelect(evento)}
                      disabled={isSelected}
                      className="gap-2"
                    >
                      {isSelected ? (
                        <Check className="h-3.5 w-3.5 text-green-600" />
                      ) : (
                        <Plus className="h-3.5 w-3.5 text-muted-foreground" />
                      )}
                      <span className="truncate">{evento.nombre}</span>
                    </CommandItem>
                  );
                })}
              </CommandGroup>
            )}
            {tipoEnos.length > 0 && (
              <CommandGroup heading="Eventos">
                {tipoEnos.map((evento) => {
                  const isSelected = selectedCodigos.has(evento.codigo);
                  return (
                    <CommandItem
                      key={evento.codigo}
                      value={`${evento.nombre} ${evento.codigo}`}
                      onSelect={() => handleSelect(evento)}
                      disabled={isSelected}
                      className="gap-2"
                    >
                      {isSelected ? (
                        <Check className="h-3.5 w-3.5 text-green-600" />
                      ) : (
                        <Plus className="h-3.5 w-3.5 text-muted-foreground" />
                      )}
                      <span className="truncate">{evento.nombre}</span>
                    </CommandItem>
                  );
                })}
              </CommandGroup>
            )}
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
