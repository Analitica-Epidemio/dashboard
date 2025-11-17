"use client";

/**
 * Filtros modernos para eventos usando componentes compartidos
 */

import React from "react";
import { MapPin, Activity, Calendar, User, TrendingUp } from "lucide-react";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { AdvancedFilterPanel, type FilterSection } from "@/components/filters";
import { ClassificationSelector } from "@/components/selectors/classification-selector";
import type { EventoFilters, TipoClasificacion } from "@/features/eventos/api";
import { GrupoEventoSelector } from "@/components/selectors/grupo-evento-selector";
import { ProvinciasMultiSelect } from "@/components/selectors/provincias-multi-select";

interface EventoFiltersModernProps {
  filters?: EventoFilters;
  onFilterChange: (key: string, value: unknown) => void;
  onClose: () => void;
}

export function EventoFiltersModern({
  filters,
  onFilterChange,
}: EventoFiltersModernProps) {

  // Contador de filtros activos
  const activeFiltersCount = Object.entries(filters ?? {}).filter(
    ([key, value]) => value && !["page", "page_size", "sort_by"].includes(key)
  ).length;

  const handleClearFilters = () => {
    const keysToReset = Object.keys(filters ?? {}).filter(
      (key) => !["page", "page_size", "sort_by"].includes(key)
    );
    keysToReset.forEach((key) => {
      onFilterChange(key, undefined);
    });
  };

  // Definir secciones del panel de filtros
  const filterSections: FilterSection[] = [
    {
      id: "event-type",
      title: "Tipo de Evento",
      icon: <Activity className="h-4 w-4" />,
      description: "Seleccione grupos o eventos específicos (con infinite scroll)",
      defaultOpen: true,
      content: (
        <GrupoEventoSelector
          selectedGroupIds={filters?.grupo_eno_ids || []}
          selectedEventIds={filters?.tipo_eno_ids || []}
          onSelectionChange={(groups, events) => {
            onFilterChange("grupo_eno_ids", groups.length > 0 ? groups : undefined);
            onFilterChange("tipo_eno_ids", events.length > 0 ? events : undefined);
          }}
        />
      ),
    },
    {
      id: "classification",
      title: "Clasificación y Sujeto",
      icon: <TrendingUp className="h-4 w-4" />,
      defaultOpen: true,
      content: (
        <div className="grid gap-4 md:grid-cols-2">
          {/* Clasificación */}
          <div className="space-y-2">
            <Label className="text-xs text-muted-foreground font-normal">
              Clasificación Estratégica
            </Label>
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
      ),
    },
    {
      id: "location-dates",
      title: "Ubicación y Fechas",
      icon: <MapPin className="h-4 w-4" />,
      defaultOpen: false,
      content: (
        <div className="space-y-4">
          {/* Provincias */}
          <div className="space-y-2">
            <Label className="text-xs text-muted-foreground font-normal">
              Provincias
            </Label>
            <ProvinciasMultiSelect
              selectedProvinciaIds={filters?.provincia_id || []}
              onProvinciasChange={(provinciaIds) => {
                onFilterChange("provincia_id", provinciaIds.length > 0 ? provinciaIds : undefined);
              }}
            />
          </div>

          {/* Fechas */}
          <div className="grid gap-4 md:grid-cols-2">
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
      ),
    },
    {
      id: "age-range",
      title: "Rango de Edad",
      icon: <User className="h-4 w-4" />,
      defaultOpen: false,
      content: (
        <div className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="edad_min" className="text-xs text-muted-foreground font-normal">
                Edad Mínima
              </Label>
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
              <Label htmlFor="edad_max" className="text-xs text-muted-foreground font-normal">
                Edad Máxima
              </Label>
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
            <p className="text-xs text-muted-foreground bg-muted p-2 rounded-md">
              Filtrando: {filters?.edad_min || 0} - {filters?.edad_max || 120} años
            </p>
          )}
        </div>
      ),
    },
    {
      id: "sorting",
      title: "Ordenamiento",
      icon: <Calendar className="h-4 w-4" />,
      defaultOpen: false,
      content: (
        <div className="space-y-2">
          <Label htmlFor="sort_by" className="text-xs text-muted-foreground font-normal">
            Ordenar por
          </Label>
          <Select
            value={filters?.sort_by || "fecha_desc"}
            onValueChange={(value) => onFilterChange("sort_by", value)}
          >
            <SelectTrigger id="sort_by">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="fecha_desc">Fecha (más reciente primero)</SelectItem>
              <SelectItem value="fecha_asc">Fecha (más antiguo primero)</SelectItem>
              <SelectItem value="id_desc">ID (mayor a menor)</SelectItem>
              <SelectItem value="id_asc">ID (menor a mayor)</SelectItem>
              <SelectItem value="tipo_eno">Tipo de Evento (A-Z)</SelectItem>
            </SelectContent>
          </Select>
        </div>
      ),
    },
  ];

  return (
    <AdvancedFilterPanel
      sections={filterSections}
      activeFiltersCount={activeFiltersCount}
      onClearAll={handleClearFilters}
    />
  );
}
