"use client";

import React from "react";
import { MapPin, Activity, Filter } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { ClassificationSelector } from "@/features/dashboard/components/selectors/ClassificationSelector";
import type { EventoFilters, TipoClasificacion } from "@/lib/api/eventos";
import { useInfiniteGroups } from "@/features/dashboard/services/paginatedQueries";
import { EventoSelectorUnified } from "./evento-selector-unified";
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
import { Check, ChevronDown } from "lucide-react";

// Provincias de Argentina
const PROVINCIAS_ARGENTINA = [
  "Buenos Aires",
  "CABA",
  "Catamarca",
  "Chaco",
  "Chubut",
  "Córdoba",
  "Corrientes",
  "Entre Ríos",
  "Formosa",
  "Jujuy",
  "La Pampa",
  "La Rioja",
  "Mendoza",
  "Misiones",
  "Neuquén",
  "Río Negro",
  "Salta",
  "San Juan",
  "San Luis",
  "Santa Cruz",
  "Santa Fe",
  "Santiago del Estero",
  "Tierra del Fuego",
  "Tucumán",
];

// Componente Multi-Select para Provincias
const ProvinciasMultiSelect = ({
  selectedProvincias,
  onProvinciasChange,
}: {
  selectedProvincias: string[];
  onProvinciasChange: (provincias: string[]) => void;
}) => {
  const [open, setOpen] = React.useState(false);

  const handleToggle = (provincia: string) => {
    const isSelected = selectedProvincias.includes(provincia);
    if (isSelected) {
      onProvinciasChange(selectedProvincias.filter((p) => p !== provincia));
    } else {
      onProvinciasChange([...selectedProvincias, provincia]);
    }
  };

  const handleClearAll = () => {
    onProvinciasChange([]);
  };

  const getButtonLabel = () => {
    if (selectedProvincias.length === 0) return "Todas las provincias";
    if (selectedProvincias.length === 1) return selectedProvincias[0];
    return `${selectedProvincias.length} provincias`;
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
            {selectedProvincias.length > 0 && (
              <CommandItem
                onSelect={handleClearAll}
                className="justify-center text-sm text-muted-foreground"
              >
                Limpiar selección
              </CommandItem>
            )}
            {PROVINCIAS_ARGENTINA.map((provincia) => {
              const isSelected = selectedProvincias.includes(provincia);
              return (
                <CommandItem
                  key={provincia}
                  value={provincia}
                  onSelect={() => handleToggle(provincia)}
                >
                  <Check
                    className={`mr-2 h-4 w-4 ${
                      isSelected ? "opacity-100" : "opacity-0"
                    }`}
                  />
                  {provincia}
                </CommandItem>
              );
            })}
          </CommandGroup>
        </Command>
      </PopoverContent>
    </Popover>
  );
};

interface EventoFiltersAdvancedProps {
  filters?: EventoFilters;
  onFilterChange: (key: string, value: unknown) => void;
  onClose: () => void;
}

export function EventoFiltersAdvanced({
  filters,
  onFilterChange,
}: EventoFiltersAdvancedProps) {
  // Fetch grupos - los eventos ya vienen incluidos dentro de cada grupo
  const {
    groups: infiniteGrupos,
    isLoading: isLoadingGrupos,
  } = useInfiniteGroups("");

  // Extraer todos los eventos de los grupos
  const displayGrupos = infiniteGrupos;
  const displayTipos = React.useMemo(() => {
    return infiniteGrupos.flatMap((group) => group.eventos || []);
  }, [infiniteGrupos]);

  // Contador de filtros activos
  const activeFiltersCount = filters ? Object.entries(filters).filter(
    ([key, value]) => value && !["page", "page_size", "sort_by"].includes(key)
  ).length : 0;

  const handleClearFilters = () => {
    if (!filters) return;
    const keysToReset = Object.keys(filters).filter(
      (key) => !["page", "page_size", "sort_by"].includes(key)
    );
    keysToReset.forEach((key) => {
      onFilterChange(key, undefined);
    });
  };

  return (
    <div className="space-y-6">
      {/* Filtros activos counter y clear button */}
      {activeFiltersCount > 0 && (
        <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg border">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-medium">{activeFiltersCount} filtros activos</span>
          </div>
          <Button variant="ghost" size="sm" onClick={handleClearFilters}>
            Limpiar filtros
          </Button>
        </div>
      )}

      {/* Grupo de Filtros: Eventos */}
      <div className="space-y-4">
        <h4 className="text-sm font-semibold flex items-center gap-2">
          <Activity className="h-4 w-4" />
          Tipo de Evento
        </h4>
        <EventoSelectorUnified
          groups={displayGrupos}
          allEvents={displayTipos}
          loading={isLoadingGrupos}
          onSelectionChange={(selection) => {
            // Actualizar filtros con la selección
            onFilterChange(
              "grupo_eno_ids",
              selection.groups.length > 0 ? selection.groups.map((id) => parseInt(id)) : undefined
            );
            onFilterChange(
              "tipo_eno_ids",
              selection.events.length > 0 ? selection.events.map((id) => parseInt(id)) : undefined
            );
          }}
          initialSelection={{
            groups: filters?.grupo_eno_ids?.map(String) || [],
            events: filters?.tipo_eno_ids?.map(String) || [],
          }}
        />
      </div>

      <Separator />

      {/* Grupo de Filtros: Clasificación y Sujeto */}
      <div className="space-y-4">
        <h4 className="text-sm font-semibold">Clasificación y Sujeto</h4>
        <div className="grid gap-4 md:grid-cols-2">
          {/* Clasificación - Multi-select */}
          <div className="space-y-2">
            <Label className="text-xs text-muted-foreground font-normal">Clasificación Estratégica</Label>
            <ClassificationSelector
              selectedClassifications={Array.isArray(filters?.clasificacion) ? (filters.clasificacion as TipoClasificacion[]) : []}
              onClassificationChange={(classifications) => {
                onFilterChange("clasificacion", classifications.length > 0 ? classifications : undefined);
              }}
              placeholder="Todas las clasificaciones"
            />
          </div>

          {/* Tipo de Sujeto */}
          <div className="space-y-2">
            <Label htmlFor="tipo_sujeto" className="text-xs text-muted-foreground font-normal">
              Tipo de Sujeto
            </Label>
          <Select
            value={filters?.tipo_sujeto || ""}
            onValueChange={(value) =>
              onFilterChange("tipo_sujeto", value || undefined)
            }
          >
            <SelectTrigger id="tipo_sujeto">
              <SelectValue placeholder="Todos los sujetos" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="humano">Humanos</SelectItem>
              <SelectItem value="animal">Animales</SelectItem>
              <SelectItem value="desconocido">Desconocido</SelectItem>
            </SelectContent>
          </Select>
          </div>
        </div>
      </div>

      <Separator />

      {/* Grupo de Filtros: Ubicación y Fechas */}
      <div className="space-y-4">
        <h4 className="text-sm font-semibold flex items-center gap-2">
          <MapPin className="h-4 w-4" />
          Ubicación y Fechas
        </h4>
        <div className="grid gap-4 md:grid-cols-3">
          {/* Provincia - Multi-select */}
          <div className="space-y-2 md:col-span-2">
            <Label className="text-xs text-muted-foreground font-normal">
              Provincias
            </Label>
            <ProvinciasMultiSelect
              selectedProvincias={Array.isArray(filters?.provincia_id) ? filters.provincia_id.map(String) : []}
              onProvinciasChange={(provincias) => {
                onFilterChange("provincia_id", provincias.length > 0 ? provincias.map(Number) : undefined);
              }}
            />
          </div>

          {/* Fecha Desde */}
          <div className="space-y-2">
            <Label htmlFor="fecha_desde" className="text-xs text-muted-foreground font-normal">
              Fecha Desde
            </Label>
          <Input
            id="fecha_desde"
            type="date"
            value={filters?.fecha_desde || ""}
            onChange={(e) =>
              onFilterChange("fecha_desde", e.target.value || undefined)
            }
          />
        </div>

          {/* Fecha Hasta */}
          <div className="space-y-2">
            <Label htmlFor="fecha_hasta" className="text-xs text-muted-foreground font-normal">
              Fecha Hasta
            </Label>
          <Input
            id="fecha_hasta"
            type="date"
            value={filters?.fecha_hasta || ""}
            onChange={(e) =>
              onFilterChange("fecha_hasta", e.target.value || undefined)
            }
          />
          </div>
        </div>
      </div>

      <Separator />

      {/* Filtros Adicionales */}
      <div className="space-y-4">
        <h4 className="text-sm font-semibold">Rango de Edad</h4>
        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="edad_min" className="text-xs">Edad Mínima</Label>
            <Input
              id="edad_min"
              type="number"
              min="0"
              max="120"
              placeholder="0"
              value={filters?.edad_min || ""}
              onChange={(e) =>
                onFilterChange("edad_min", e.target.value ? parseInt(e.target.value) : undefined)
              }
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="edad_max" className="text-xs">Edad Máxima</Label>
            <Input
              id="edad_max"
              type="number"
              min="0"
              max="120"
              placeholder="120"
              value={filters?.edad_max || ""}
              onChange={(e) =>
                onFilterChange("edad_max", e.target.value ? parseInt(e.target.value) : undefined)
              }
            />
          </div>
        </div>
        {(filters?.edad_min || filters?.edad_max) && (
          <p className="text-xs text-muted-foreground">
            Filtrando: {filters?.edad_min || 0} - {filters?.edad_max || 120} años
          </p>
        )}
      </div>

      <Separator />

      {/* Ordenamiento */}
      <div className="space-y-4">
        <h4 className="text-sm font-semibold">Ordenamiento</h4>
        <div className="space-y-2">
          <Label htmlFor="sort_by" className="text-xs text-muted-foreground font-normal">Ordenar por</Label>
        <Select
          value={filters?.sort_by || "fecha_desc"}
          onValueChange={(value) => onFilterChange("sort_by", value)}
        >
          <SelectTrigger id="sort_by">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="fecha_desc">Fecha (más reciente)</SelectItem>
            <SelectItem value="fecha_asc">Fecha (más antiguo)</SelectItem>
            <SelectItem value="id_desc">ID (mayor a menor)</SelectItem>
            <SelectItem value="id_asc">ID (menor a mayor)</SelectItem>
            <SelectItem value="tipo_eno">Tipo de Evento</SelectItem>
          </SelectContent>
        </Select>
        </div>
      </div>
    </div>
  );
}
