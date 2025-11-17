"use client";

/**
 * Filtros modernos para eventos usando componentes compartidos
 */

import React, { useState, useCallback } from "react";
import { MapPin, Activity, Calendar, User, TrendingUp, Search, X, Loader2, ChevronDown, ChevronRight, Folder, FileText } from "lucide-react";
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
import { ClassificationSelector } from "@/features/reports/components/selectors/classification-selector";
import type { EventoFilters, TipoClasificacion } from "@/features/eventos/api";
import { useInfiniteGroups } from "@/features/eventos/infinite-queries";
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
import { Check } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Collapsible, CollapsibleContent } from "@/components/ui/collapsible";
import { useDebounce } from "use-debounce";
import { cn } from "@/lib/utils";

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

// Componente Multi-Select para Provincias con códigos INDEC (exportado para compartir con personas)
export const ProvinciasMultiSelect = ({
  selectedProvinciaIds,
  onProvinciasChange,
}: {
  selectedProvinciaIds: number[];
  onProvinciasChange: (provinciaIds: number[]) => void;
}) => {
  const [open, setOpen] = React.useState(false);

  const handleToggle = (provinciaId: number) => {
    const isSelected = selectedProvinciaIds.includes(provinciaId);
    if (isSelected) {
      onProvinciasChange(selectedProvinciaIds.filter((p) => p !== provinciaId));
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
      const provincia = PROVINCIAS_ARGENTINA.find((p) => p.id === selectedProvinciaIds[0]);
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
};

interface EventoFiltersModernProps {
  filters?: EventoFilters;
  onFilterChange: (key: string, value: unknown) => void;
  onClose: () => void;
}

// Componente selector de eventos con infinite scroll (exportado para compartir con personas)
export const EventoSelectorInfinite = ({
  selectedGroupIds,
  selectedEventIds,
  onSelectionChange,
}: {
  selectedGroupIds: number[];
  selectedEventIds: number[];
  onSelectionChange: (groups: number[], events: number[]) => void;
}) => {
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedSearch] = useDebounce(searchQuery, 300);
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());

  // Fetch groups with infinite scroll
  const {
    groups: serverGroups,
    hasMore: hasMoreGroups,
    isLoading: isLoadingGroups,
    loadMore: loadMoreGroups,
  } = useInfiniteGroups(debouncedSearch);

  // Expandir todos los grupos por defecto
  const groupIds = React.useMemo(() => {
    return serverGroups.map((g) => String(g.id));
  }, [serverGroups]);

  React.useEffect(() => {
    if (groupIds.length > 0) {
      setExpandedGroups((prev) => {
        const hasNewGroups = groupIds.some((id) => !prev.has(id));
        if (!hasNewGroups && prev.size > 0) return prev;

        const newExpanded = new Set(prev);
        groupIds.forEach((id) => newExpanded.add(id));
        return newExpanded;
      });
    }
  }, [groupIds]);

  // Intersection Observer para cargar más grupos
  const handleGroupsScroll = useCallback(
    (e: React.UIEvent<HTMLDivElement>) => {
      const target = e.currentTarget;
      const isNearBottom =
        target.scrollHeight - target.scrollTop - target.clientHeight < 100;

      if (isNearBottom && hasMoreGroups && !isLoadingGroups) {
        loadMoreGroups();
      }
    },
    [hasMoreGroups, isLoadingGroups, loadMoreGroups]
  );

  const toggleGroup = (groupId: string) => {
    const newSelectedGroups = new Set(selectedGroupIds.map(String));
    const group = serverGroups.find((g) => String(g.id) === groupId);
    const groupEvents = group?.eventos || [];
    const newSelectedEvents = new Set(selectedEventIds.map(String));

    if (newSelectedGroups.has(groupId)) {
      newSelectedGroups.delete(groupId);
      groupEvents.forEach((e) => newSelectedEvents.delete(String(e.id)));
    } else {
      newSelectedGroups.add(groupId);
      groupEvents.forEach((e) => newSelectedEvents.add(String(e.id)));
    }

    const resultGroups = Array.from(newSelectedGroups).map(id => parseInt(id));
    const resultEvents = Array.from(newSelectedEvents).map(id => parseInt(id));

    console.log('Toggle group:', { groupId, resultGroups, resultEvents });
    onSelectionChange(resultGroups, resultEvents);
  };

  const toggleEvent = (eventId: string, groupId: string) => {
    const newSelectedEvents = new Set(selectedEventIds.map(String));
    const newSelectedGroups = new Set(selectedGroupIds.map(String));

    if (newSelectedEvents.has(eventId)) {
      newSelectedEvents.delete(eventId);
      const group = serverGroups.find((g) => String(g.id) === groupId);
      const groupEvents = group?.eventos || [];
      const hasAnyFromGroup = groupEvents.some((e) =>
        newSelectedEvents.has(String(e.id))
      );
      if (!hasAnyFromGroup) {
        newSelectedGroups.delete(groupId);
      }
    } else {
      newSelectedEvents.add(eventId);
      newSelectedGroups.add(groupId);
    }

    const resultGroups = Array.from(newSelectedGroups).map(id => parseInt(id));
    const resultEvents = Array.from(newSelectedEvents).map(id => parseInt(id));

    console.log('Toggle event:', { eventId, groupId, resultGroups, resultEvents });
    onSelectionChange(resultGroups, resultEvents);
  };

  const toggleGroupExpanded = (groupId: string) => {
    const newExpanded = new Set(expandedGroups);
    if (newExpanded.has(groupId)) {
      newExpanded.delete(groupId);
    } else {
      newExpanded.add(groupId);
    }
    setExpandedGroups(newExpanded);
  };

  const groupMatchesSearch = (groupId: string) => {
    if (!debouncedSearch.trim()) return false;
    const group = serverGroups.find((g) => String(g.id) === groupId);
    return group?.name.toLowerCase().includes(debouncedSearch.toLowerCase());
  };

  const eventMatchesSearch = (eventName: string) => {
    if (!debouncedSearch.trim()) return false;
    return eventName.toLowerCase().includes(debouncedSearch.toLowerCase());
  };

  return (
    <div className="space-y-3">
      {/* Selección actual */}
      {selectedEventIds.length > 0 && (
        <div className="flex items-center justify-between p-3 bg-blue-50 dark:bg-blue-950/20 rounded-lg border border-blue-200 dark:border-blue-900">
          <div className="text-sm">
            <span className="font-medium text-blue-900 dark:text-blue-100">
              {selectedEventIds.length}
            </span>
            <span className="text-blue-700 dark:text-blue-300 ml-1">
              evento(s) seleccionado(s)
            </span>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onSelectionChange([], [])}
            className="h-7 text-xs text-blue-700 hover:text-blue-900 hover:bg-blue-100"
          >
            Limpiar
          </Button>
        </div>
      )}

      {/* Búsqueda */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Buscar grupos o eventos..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-9"
        />
        {searchQuery && (
          <button
            onClick={() => setSearchQuery("")}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Lista de grupos con infinite scroll */}
      <div
        className="space-y-2 max-h-[400px] overflow-y-auto pr-2"
        onScroll={handleGroupsScroll}
      >
        {isLoadingGroups && serverGroups.length === 0 ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : serverGroups.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <Search className="h-12 w-12 mx-auto mb-3 opacity-20" />
            <p className="text-sm">No se encontraron grupos o eventos</p>
          </div>
        ) : (
          <>
            {serverGroups.map((group) => {
              const groupId = String(group.id);
              const groupEvents = group.eventos || [];
              // Asegurar comparación correcta de tipos
              const groupIdNum = typeof group.id === 'string' ? parseInt(group.id) : group.id;
              const isGroupSelected = selectedGroupIds.includes(groupIdNum);
              const isExpanded = expandedGroups.has(groupId);
              const selectedEventsInGroup = groupEvents.filter((e) => {
                const eventIdNum = typeof e.id === 'string' ? parseInt(e.id as string) : e.id;
                return selectedEventIds.includes(eventIdNum as number);
              }).length;
              const groupMatchesBusqueda = groupMatchesSearch(groupId);

              return (
                <div
                  key={groupId}
                  className={cn(
                    "border rounded-lg overflow-hidden bg-white",
                    groupMatchesBusqueda && "ring-2 ring-blue-400"
                  )}
                >
                  <div className="flex items-center gap-2 p-3 bg-slate-50 hover:bg-slate-100 transition-colors">
                    <input
                      type="checkbox"
                      checked={isGroupSelected}
                      onChange={() => toggleGroup(groupId)}
                      className="h-4 w-4 rounded border-gray-300"
                    />
                    <button
                      onClick={() => toggleGroupExpanded(groupId)}
                      className="flex items-center gap-2 flex-1 text-left"
                    >
                      {isExpanded ? (
                        <ChevronDown className="h-4 w-4 text-muted-foreground" />
                      ) : (
                        <ChevronRight className="h-4 w-4 text-muted-foreground" />
                      )}
                      <Folder className={cn("h-4 w-4", groupMatchesBusqueda ? "text-blue-600" : "text-blue-500")} />
                      <span className={cn("font-medium text-sm", groupMatchesBusqueda && "text-blue-700")}>
                        {group.name}
                      </span>
                    </button>
                    <Badge variant="outline" className="text-xs">
                      {selectedEventsInGroup > 0 && `${selectedEventsInGroup}/`}
                      {groupEvents.length}
                    </Badge>
                  </div>

                  <Collapsible open={isExpanded}>
                    <CollapsibleContent>
                      <div className="p-2 bg-white space-y-1">
                        {groupEvents.map((event) => {
                          const eventId = String(event.id);
                          // Asegurar comparación correcta de tipos
                          const eventIdNum = typeof event.id === 'string' ? parseInt(event.id as string) : event.id;
                          const isSelected = selectedEventIds.includes(eventIdNum as number);
                          const eventMatchesBusqueda = eventMatchesSearch(event.name);

                          return (
                            <label
                              key={eventId}
                              className={cn(
                                "flex items-center gap-2 p-2 rounded cursor-pointer hover:bg-slate-50 transition-colors",
                                isSelected && "bg-blue-50",
                                eventMatchesBusqueda && !isSelected && "bg-yellow-50"
                              )}
                            >
                              <input
                                type="checkbox"
                                checked={isSelected}
                                onChange={() => toggleEvent(eventId, groupId)}
                                className="h-4 w-4 rounded border-gray-300 ml-6"
                              />
                              <FileText className={cn("h-4 w-4", eventMatchesBusqueda ? "text-yellow-600" : "text-green-600")} />
                              <span className={cn("text-sm flex-1", eventMatchesBusqueda && "font-medium text-yellow-900")}>
                                {event.name}
                              </span>
                            </label>
                          );
                        })}
                      </div>
                    </CollapsibleContent>
                  </Collapsible>
                </div>
              );
            })}

            {hasMoreGroups && isLoadingGroups && (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

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
        <EventoSelectorInfinite
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
