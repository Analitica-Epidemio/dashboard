"use client";

/**
 * Filtros avanzados para personas usando componentes compartidos con eventos
 * Aplica principio DRY compartiendo ProvinciasMultiSelect y EventoSelectorInfinite
 */

import React from "react";
import { MapPin, Activity, User, TrendingUp, Users } from "lucide-react";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { AdvancedFilterPanel, type FilterSection } from "@/components/filters";
import type { PersonaFilters } from "@/features/personas/api";

// Importar componentes compartidos
import { ProvinciasMultiSelect } from "@/components/selectors/provincias-multi-select";
import { GrupoEventoSelector } from "@/components/selectors/grupo-evento-selector";

interface PersonaFiltersAdvancedProps {
  filters?: PersonaFilters;
  onFilterChange: (key: string, value: unknown) => void;
  onClose: () => void;
}

export function PersonaFiltersAdvanced({
  filters,
  onFilterChange,
}: PersonaFiltersAdvancedProps) {

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
      id: "subject-type",
      title: "Tipo de Sujeto",
      icon: <Users className="h-4 w-4" />,
      defaultOpen: true,
      content: (
        <div className="space-y-2">
          <Label htmlFor="tipo_sujeto" className="text-xs text-muted-foreground font-normal">
            Tipo de Sujeto
          </Label>
          <Select
            value={filters?.tipo_sujeto || "todos"}
            onValueChange={(value) =>
              onFilterChange("tipo_sujeto", value === "todos" ? undefined : value)
            }
          >
            <SelectTrigger id="tipo_sujeto">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="todos">Todos</SelectItem>
              <SelectItem value="humano">Humanos</SelectItem>
              <SelectItem value="animal">Animales</SelectItem>
            </SelectContent>
          </Select>
        </div>
      ),
    },
    {
      id: "event-filters",
      title: "Filtros de Eventos",
      icon: <Activity className="h-4 w-4" />,
      description: "Filtra personas según los tipos de eventos que han tenido",
      defaultOpen: true,
      content: (
        <div className="space-y-4">
          <div className="bg-purple-50 dark:bg-purple-950/20 p-3 rounded-lg border border-purple-200 dark:border-purple-900">
            <p className="text-sm font-medium text-purple-900 dark:text-purple-100 mb-2">
              Filtros de Eventos Asociados
            </p>
            <p className="text-xs text-purple-700 dark:text-purple-300">
              Filtra personas según los tipos de eventos que han tenido
            </p>
          </div>

          {/* Selector de Eventos compartido */}
          <GrupoEventoSelector
            selectedGroupIds={filters?.grupo_eno_ids || []}
            selectedEventIds={filters?.tipo_eno_ids || []}
            onSelectionChange={(groups, events) => {
              onFilterChange("grupo_eno_ids", groups.length > 0 ? groups : undefined);
              onFilterChange("tipo_eno_ids", events.length > 0 ? events : undefined);
            }}
          />
        </div>
      ),
    },
    {
      id: "location",
      title: "Ubicación",
      icon: <MapPin className="h-4 w-4" />,
      description: "Filtro por ESTABLECIMIENTO DE NOTIFICACIÓN de eventos",
      defaultOpen: false,
      content: (
        <div className="space-y-2">
          <Label className="text-xs text-muted-foreground font-normal">
            Provincias (por establecimiento de notificación)
          </Label>
          {/* Selector de Provincias compartido con eventos page */}
          <ProvinciasMultiSelect
            selectedProvinciaIds={filters?.provincia_id || []}
            onProvinciasChange={(provinciaIds) => {
              onFilterChange("provincia_id", provinciaIds.length > 0 ? provinciaIds : undefined);
            }}
          />
          <p className="text-xs text-muted-foreground bg-amber-50 dark:bg-amber-950/20 p-2 rounded border border-amber-200 dark:border-amber-900">
            ⚠️ Filtra por provincia del <strong>establecimiento donde se notificaron</strong> los eventos, no por domicilio de la persona
          </p>
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
      id: "special-characteristics",
      title: "Características Especiales",
      icon: <TrendingUp className="h-4 w-4" />,
      defaultOpen: false,
      content: (
        <div className="space-y-4">
          {/* Tiene múltiples eventos */}
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="multiples_eventos">Múltiples Eventos</Label>
              <p className="text-xs text-muted-foreground">
                Personas con más de un evento registrado
              </p>
            </div>
            <Switch
              id="multiples_eventos"
              checked={filters?.tiene_multiples_eventos || false}
              onCheckedChange={(checked) =>
                onFilterChange("tiene_multiples_eventos", checked || undefined)
              }
            />
          </div>
        </div>
      ),
    },
    {
      id: "sorting",
      title: "Ordenamiento",
      icon: <TrendingUp className="h-4 w-4" />,
      defaultOpen: false,
      content: (
        <div className="space-y-2">
          <Label htmlFor="sort_by" className="text-xs text-muted-foreground font-normal">
            Ordenar por
          </Label>
          <Select
            value={filters?.sort_by || "ultimo_evento_desc"}
            onValueChange={(value) => onFilterChange("sort_by", value)}
          >
            <SelectTrigger id="sort_by">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="nombre_asc">Nombre (A-Z)</SelectItem>
              <SelectItem value="nombre_desc">Nombre (Z-A)</SelectItem>
              <SelectItem value="eventos_desc">Más eventos primero</SelectItem>
              <SelectItem value="eventos_asc">Menos eventos primero</SelectItem>
              <SelectItem value="ultimo_evento_desc">Último evento (reciente)</SelectItem>
              <SelectItem value="ultimo_evento_asc">Último evento (antiguo)</SelectItem>
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
