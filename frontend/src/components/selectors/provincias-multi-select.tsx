"use client";

/**
 * Selector múltiple de provincias argentinas
 * Componente compartido usado por personas y eventos
 */

import React from "react";
import { Check, ChevronDown } from "lucide-react";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
} from "@/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Button } from "@/components/ui/button";

// Provincias de Argentina con códigos INDEC
const PROVINCIAS_ARGENTINA = [
  { id: 2, nombre: "CABA" },
  { id: 6, nombre: "Buenos Aires" },
  { id: 10, nombre: "Catamarca" },
  { id: 14, nombre: "Córdoba" },
  { id: 18, nombre: "Corrientes" },
  { id: 22, nombre: "Chaco" },
  { id: 26, nombre: "Chubut" },
  { id: 30, nombre: "Entre Ríos" },
  { id: 34, nombre: "Formosa" },
  { id: 38, nombre: "Jujuy" },
  { id: 42, nombre: "La Pampa" },
  { id: 46, nombre: "La Rioja" },
  { id: 50, nombre: "Mendoza" },
  { id: 54, nombre: "Misiones" },
  { id: 58, nombre: "Neuquén" },
  { id: 62, nombre: "Río Negro" },
  { id: 66, nombre: "Salta" },
  { id: 70, nombre: "San Juan" },
  { id: 74, nombre: "San Luis" },
  { id: 78, nombre: "Santa Cruz" },
  { id: 82, nombre: "Santa Fe" },
  { id: 86, nombre: "Santiago del Estero" },
  { id: 90, nombre: "Tucumán" },
  { id: 94, nombre: "Tierra del Fuego" },
];

interface ProvinciasMultiSelectProps {
  selectedProvinciaIds: number[];
  onProvinciasChange: (provinciaIds: number[]) => void;
}

export function ProvinciasMultiSelect({
  selectedProvinciaIds,
  onProvinciasChange,
}: ProvinciasMultiSelectProps) {
  const [open, setOpen] = React.useState(false);

  const handleToggle = (provinciaId: number) => {
    const isSelected = selectedProvinciaIds.includes(provinciaId);
    if (isSelected) {
      onProvinciasChange(
        selectedProvinciaIds.filter((p) => p !== provinciaId)
      );
    } else {
      onProvinciasChange([...selectedProvinciaIds, provinciaId]);
    }
  };

  const handleClearAll = () => {
    onProvinciasChange([]);
  };

  const getButtonLabel = () => {
    if (selectedProvinciaIds.length === 0) return "Todas las provincias";
    if (selectedProvinciaIds.length === 1) {
      const provincia = PROVINCIAS_ARGENTINA.find(
        (p) => p.id === selectedProvinciaIds[0]
      );
      return provincia?.nombre || "Provincia seleccionada";
    }
    return `${selectedProvinciaIds.length} provincias seleccionadas`;
  };

  return (
    <Popover open={open} onOpenChange={setOpen} modal={true}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          className="w-full justify-between"
        >
          <span className="truncate">{getButtonLabel()}</span>
          <ChevronDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-full p-0 z-[100]" align="start">
        <Command>
          <CommandInput placeholder="Buscar provincia..." />
          <CommandEmpty>No se encontraron provincias.</CommandEmpty>
          <CommandGroup className="max-h-[300px] overflow-auto">
            {selectedProvinciaIds.length > 0 && (
              <CommandItem
                onSelect={handleClearAll}
                className="justify-center text-sm text-muted-foreground"
              >
                Limpiar selección
              </CommandItem>
            )}
            {PROVINCIAS_ARGENTINA.map((provincia) => {
              const isSelected = selectedProvinciaIds.includes(provincia.id);
              return (
                <CommandItem
                  key={provincia.id}
                  value={provincia.nombre}
                  onSelect={() => handleToggle(provincia.id)}
                >
                  <Check
                    className={`mr-2 h-4 w-4 ${
                      isSelected ? "opacity-100" : "opacity-0"
                    }`}
                  />
                  {provincia.nombre}
                </CommandItem>
              );
            })}
          </CommandGroup>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
