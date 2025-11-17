"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Plus,
  X,
  Trash2,
  Eye,
  Calendar,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Folder,
  FileText,
  Copy,
  Search,
  Info,
  Loader2,
} from "lucide-react";
import { Collapsible, CollapsibleContent } from "@/components/ui/collapsible";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useDebounce } from "use-debounce";
import { EpiWeekRangeSelector } from "./epi-week-range-selector";
import {
  ClassificationSelector,
  TipoClasificacion,
} from "@/components/selectors/classification-selector";
import { useFilterContext } from "@/features/reports/contexts/filter-context";
import { useInfiniteGroups } from "@/features/eventos/infinite-queries";
import { cn } from "@/lib/utils";

interface FilterInProgress {
  id: string;
  selectedGroups: Set<string>;
  selectedEvents: Set<string>;
  clasificaciones: TipoClasificacion[];
  label: string;
}

export function FilterBuilderView() {
  const {
    filterCombinations,
    dateRange,
    soloChubutEnabled,
    setSoloChubutEnabled,
    setIsComparisonView,
    addFilterCombination,
    removeFilterCombination,
    duplicateFilterCombination,
  } = useFilterContext();

  const [filterInProgress, setFilterInProgress] =
    useState<FilterInProgress | null>({
      id: "new",
      selectedGroups: new Set(),
      selectedEvents: new Set(),
      clasificaciones: [],
      label: "",
    });

  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedSearch] = useDebounce(searchQuery, 300);

  // Expandir todos los grupos por defecto
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());

  // Fetch groups with infinite scroll and search
  // Los eventos ya vienen incluidos dentro de cada grupo
  const {
    groups: serverGroups,
    hasMore: hasMoreGroups,
    isLoading: isLoadingGroups,
    loadMore: loadMoreGroups,
  } = useInfiniteGroups(debouncedSearch);

  // Memorizar IDs de grupos para evitar loops infinitos
  const groupIds = React.useMemo(() => {
    return serverGroups.map((g) => String(g.id));
  }, [serverGroups]);

  // Expandir todos los grupos cuando se carguen o se agreguen nuevos
  useEffect(() => {
    if (groupIds.length > 0) {
      setExpandedGroups((prev) => {
        // Solo actualizar si hay grupos nuevos
        const hasNewGroups = groupIds.some((id) => !prev.has(id));
        if (!hasNewGroups && prev.size > 0) return prev;

        const newExpanded = new Set(prev);
        groupIds.forEach((id) => newExpanded.add(id));
        return newExpanded;
      });
    }
  }, [groupIds]);

  // Crear un map de todos los eventos para búsquedas rápidas
  const allEvents = React.useMemo(() => {
    return serverGroups.flatMap((group) => group.eventos || []);
  }, [serverGroups]);

  // Verificar si un evento coincide con la búsqueda actual
  const eventMatchesSearch = (eventName: string) => {
    if (!debouncedSearch.trim()) return false;
    return eventName.toLowerCase().includes(debouncedSearch.toLowerCase());
  };

  // Verificar si un grupo coincide con la búsqueda actual
  const groupMatchesSearch = (groupId: string) => {
    if (!debouncedSearch.trim()) return false;
    const group = serverGroups.find((g) => String(g.id) === groupId);
    return group?.name.toLowerCase().includes(debouncedSearch.toLowerCase());
  };

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
    if (!filterInProgress) return;

    const newSelected = new Set(filterInProgress.selectedGroups);
    const group = serverGroups.find((g) => String(g.id) === groupId);
    const groupEvents = group?.eventos || [];
    const newSelectedEvents = new Set(filterInProgress.selectedEvents);

    if (newSelected.has(groupId)) {
      // Deseleccionar grupo y sus eventos
      newSelected.delete(groupId);
      groupEvents.forEach((e) => newSelectedEvents.delete(String(e.id)));
    } else {
      // Seleccionar grupo y todos sus eventos
      newSelected.add(groupId);
      groupEvents.forEach((e) => newSelectedEvents.add(String(e.id)));
    }

    setFilterInProgress({
      ...filterInProgress,
      selectedGroups: newSelected,
      selectedEvents: newSelectedEvents,
    });
  };

  const toggleEvent = (eventId: string, groupId: string) => {
    if (!filterInProgress) return;

    const newSelectedEvents = new Set(filterInProgress.selectedEvents);
    const newSelectedGroups = new Set(filterInProgress.selectedGroups);

    if (newSelectedEvents.has(eventId)) {
      newSelectedEvents.delete(eventId);
      // Si ya no hay eventos de este grupo, quitar el grupo
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

    setFilterInProgress({
      ...filterInProgress,
      selectedGroups: newSelectedGroups,
      selectedEvents: newSelectedEvents,
    });
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

  const saveFilter = () => {
    if (!filterInProgress || filterInProgress.selectedEvents.size === 0) return;

    const combination = {
      groupId: Array.from(filterInProgress.selectedGroups)[0] || null,
      groupName:
        filterInProgress.selectedGroups.size > 1
          ? `${filterInProgress.selectedGroups.size} grupos`
          : serverGroups.find(
              (g) =>
                String(g.id) === Array.from(filterInProgress.selectedGroups)[0]
            )?.name,
      eventIds: Array.from(filterInProgress.selectedEvents).map((id) =>
        parseInt(id)
      ),
      eventNames: Array.from(filterInProgress.selectedEvents).map((id) => {
        const event = allEvents.find((e) => String(e.id) === id);
        return event?.name || "";
      }),
      clasificaciones: filterInProgress.clasificaciones,
      label:
        filterInProgress.label || `Filtro ${filterCombinations.length + 1}`,
    };

    addFilterCombination(combination);

    // Limpiar
    setFilterInProgress({
      id: "new",
      selectedGroups: new Set(),
      selectedEvents: new Set(),
      clasificaciones: [],
      label: "",
    });
  };

  const canVisualize =
    filterCombinations.length > 0 && dateRange.from && dateRange.to;
  const hasSelection =
    filterInProgress && filterInProgress.selectedEvents.size > 0;

  return (
    <TooltipProvider>
      <div className="h-screen flex flex-col bg-gradient-to-br from-slate-50 to-slate-100">
        {/* Header */}
        <div className="border-b bg-white px-6 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Comparador de Eventos</h1>
            <p className="text-sm text-muted-foreground">
              Selecciona eventos y compara su evolución temporal
            </p>
          </div>
          <Button
            size="lg"
            onClick={() => setIsComparisonView(true)}
            disabled={!canVisualize}
            className="gap-2"
          >
            <Eye className="h-4 w-4" />
            Ver Comparación
            <Badge variant="secondary" className="ml-2">
              {filterCombinations.length}
            </Badge>
          </Button>
        </div>

        <div className="flex-1 overflow-hidden flex">
          {/* Left Panel - Constructor */}
          <div className="flex-1 overflow-y-auto p-6">
            <div className="max-w-4xl mx-auto space-y-6">
              {/* 1. Período */}
              <Card className="p-6">
                <div className="flex items-center gap-2 mb-4">
                  <div className="p-2 rounded-lg bg-blue-100">
                    <Calendar className="h-5 w-5 text-blue-600" />
                  </div>
                  <div className="flex-1">
                    <h2 className="font-semibold">
                      Paso 1: Selecciona el Período
                    </h2>
                    <p className="text-xs text-muted-foreground">
                      Aplica a todas las comparaciones
                    </p>
                  </div>
                  {dateRange.from && dateRange.to && (
                    <CheckCircle2 className="h-5 w-5 text-green-600" />
                  )}
                </div>
                <EpiWeekRangeSelector />

                {/* Checkbox Solo Chubut */}
                <div className="flex items-center space-x-2 mt-4 pt-4 border-t">
                  <Checkbox
                    id="solo-chubut"
                    checked={soloChubutEnabled}
                    onCheckedChange={(checked) => setSoloChubutEnabled(!!checked)}
                  />
                  <label
                    htmlFor="solo-chubut"
                    className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
                  >
                    Solo Chubut
                  </label>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Info className="h-4 w-4 text-muted-foreground cursor-help" />
                    </TooltipTrigger>
                    <TooltipContent>
                      <p className="max-w-xs text-xs">
                        Cuando está activado, filtra los datos solo para la provincia de Chubut.
                        Desactívalo para ver datos de todas las provincias.
                      </p>
                    </TooltipContent>
                  </Tooltip>
                </div>
              </Card>

              {/* 2. Agregar Filtros */}
              <Card className="p-0 gap-0">
                <div className="p-6 ">
                  <div className="flex items-center gap-2 mb-4">
                    <div className="p-2 rounded-lg bg-purple-100">
                      <Plus className="h-5 w-5 text-purple-600" />
                    </div>
                    <div className="flex-1">
                      <h2 className="font-semibold">
                        Paso 2: Agrega Eventos a Comparar
                      </h2>
                      <p className="text-xs text-muted-foreground">
                        {filterInProgress &&
                        filterInProgress.selectedEvents.size > 0
                          ? `${filterInProgress.selectedEvents.size} eventos seleccionados`
                          : "Selecciona grupos completos o eventos individuales"}
                      </p>
                    </div>
                  </div>

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
                </div>

                {/* Lista de Grupos con Eventos */}
                <div
                  className="space-y-2 max-h-[500px] overflow-y-auto pr-2 border-t bg-slate-50/50 px-6 py-3"
                  onScroll={handleGroupsScroll}
                >
                  {isLoadingGroups && serverGroups.length === 0 ? (
                    <div className="flex items-center justify-center py-8">
                      <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                    </div>
                  ) : serverGroups.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      <Search className="h-12 w-12 mx-auto mb-3 opacity-20" />
                      <p className="text-sm">
                        No se encontraron grupos o eventos
                      </p>
                      <p className="text-xs mt-1">Intenta con otra búsqueda</p>
                    </div>
                  ) : (
                    <>
                      {serverGroups.map((group) => {
                      const groupId = String(group.id);
                      const groupEvents = group.eventos || [];
                      const isGroupSelected =
                        filterInProgress?.selectedGroups.has(groupId);
                      const isExpanded = expandedGroups.has(groupId);
                      const selectedEventsInGroup = groupEvents.filter((e) =>
                        filterInProgress?.selectedEvents.has(String(e.id))
                      ).length;
                      const groupMatchesBusqueda = groupMatchesSearch(groupId);

                      return (
                        <div
                          key={groupId}
                          className={cn(
                            "border rounded-lg overflow-hidden",
                            groupMatchesBusqueda && "ring-2 ring-blue-400"
                          )}
                        >
                          {/* Group Header */}
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
                              <Folder className={cn(
                                "h-4 w-4",
                                groupMatchesBusqueda ? "text-blue-600" : "text-blue-500"
                              )} />
                              <span className={cn(
                                "font-medium",
                                groupMatchesBusqueda && "text-blue-700"
                              )}>{group.name}</span>
                            </button>

                            <Badge variant="outline" className="text-xs">
                              {selectedEventsInGroup > 0 &&
                                `${selectedEventsInGroup}/`}
                              {groupEvents.length}
                            </Badge>
                          </div>

                          {/* Events List */}
                          <Collapsible open={isExpanded}>
                            <CollapsibleContent>
                              <div className="p-2 bg-white space-y-1">
                                {groupEvents.map((event) => {
                                  const eventId = String(event.id);
                                  const isSelected =
                                    filterInProgress?.selectedEvents.has(
                                      eventId
                                    );
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
                                        onChange={() =>
                                          toggleEvent(eventId, groupId)
                                        }
                                        className="h-4 w-4 rounded border-gray-300 ml-6"
                                      />
                                      <FileText className={cn(
                                        "h-4 w-4",
                                        eventMatchesBusqueda ? "text-yellow-600" : "text-green-600"
                                      )} />
                                      <span className={cn(
                                        "text-sm flex-1",
                                        eventMatchesBusqueda && "font-medium text-yellow-900"
                                      )}>
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

                    {/* Loading indicator cuando hay más para cargar */}
                    {hasMoreGroups && isLoadingGroups && (
                      <div className="flex items-center justify-center py-4">
                        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                      </div>
                    )}
                  </>
                  )}
                </div>

                <div className="px-6 pt-3 pb-6 border-t">
                  {/* Clasificaciones */}
                  <div className="space-y-2">
                    <label className="text-sm font-medium">
                      Filtrar por clasificación (opcional)
                    </label>
                    <ClassificationSelector
                      selectedClassifications={
                        filterInProgress?.clasificaciones || []
                      }
                      onClassificationChange={(cls) => {
                        if (filterInProgress) {
                          setFilterInProgress({
                            ...filterInProgress,
                            clasificaciones: cls,
                          });
                        }
                      }}
                      placeholder="Todas las clasificaciones"
                      disabled={!hasSelection}
                    />
                  </div>

                  {/* Label */}
                  <div className="space-y-2 mt-4">
                    <label className="text-sm font-medium">
                      Etiqueta del filtro (opcional)
                    </label>

                    <Input
                      placeholder="Ej: Casos confirmados 2024"
                      value={filterInProgress?.label || ""}
                      onChange={(e) => {
                        if (filterInProgress) {
                          setFilterInProgress({
                            ...filterInProgress,
                            label: e.target.value,
                          });
                        }
                      }}
                      disabled={!hasSelection}
                    />
                  </div>

                  {/* Save Button */}
                  <Button
                    onClick={saveFilter}
                    className="w-full mt-4 gap-2"
                    size="lg"
                    disabled={!hasSelection}
                  >
                    <Plus className="h-4 w-4" />
                    Agregar Filtro a la Comparación
                  </Button>
                </div>
              </Card>
            </div>
          </div>

          {/* Right Panel - Active Filters */}
          <div className="w-96 border-l bg-white overflow-y-auto flex-shrink-0">
            <div className="p-6 space-y-4">
              <div>
                <h3 className="font-semibold mb-1">Filtros para Comparar</h3>
                <p className="text-xs text-muted-foreground">
                  {filterCombinations.length}/6 filtros agregados
                </p>
              </div>

              {filterCombinations.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                  <Plus className="h-12 w-12 mx-auto mb-3 opacity-20" />
                  <p className="text-sm">Aún no has agregado filtros</p>
                  <p className="text-xs mt-1">
                    Selecciona eventos para comenzar
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {filterCombinations.map((combo, index) => {
                    const colorClasses = [
                      "border-l-blue-500 bg-blue-50",
                      "border-l-green-500 bg-green-50",
                      "border-l-purple-500 bg-purple-50",
                      "border-l-orange-500 bg-orange-50",
                      "border-l-pink-500 bg-pink-50",
                      "border-l-cyan-500 bg-cyan-50",
                    ][index % 6];

                    return (
                      <div
                        key={combo.id}
                        className={cn(
                          "border-l-4 rounded-lg p-3",
                          colorClasses
                        )}
                      >
                        <div className="flex items-start justify-between gap-2 mb-2">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <p className="font-medium text-sm truncate">
                                {combo.label || combo.groupName || "Sin nombre"}
                              </p>
                              {combo.eventNames &&
                                combo.eventNames.length > 0 && (
                                  <Tooltip>
                                    <TooltipTrigger asChild>
                                      <button className="text-muted-foreground hover:text-foreground">
                                        <Info className="h-3 w-3" />
                                      </button>
                                    </TooltipTrigger>
                                    <TooltipContent
                                      side="left"
                                      className="max-w-xs"
                                    >
                                      <div className="space-y-1">
                                        <p className="font-medium text-xs mb-2">
                                          Eventos incluidos:
                                        </p>
                                        <ul className="space-y-1">
                                          {combo.eventNames.map((name, i) => (
                                            <li
                                              key={i}
                                              className="text-xs flex items-start gap-1"
                                            >
                                              <span className="text-muted-foreground">
                                                •
                                              </span>
                                              <span>{name}</span>
                                            </li>
                                          ))}
                                        </ul>
                                      </div>
                                    </TooltipContent>
                                  </Tooltip>
                                )}
                            </div>
                            <p className="text-xs text-muted-foreground">
                              {combo.eventIds.length} evento(s)
                            </p>
                          </div>
                          <div className="flex gap-1">
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-7 w-7 p-0"
                              onClick={() =>
                                duplicateFilterCombination(combo.id)
                              }
                            >
                              <Copy className="h-3 w-3" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-7 w-7 p-0 hover:bg-red-100"
                              onClick={() => removeFilterCombination(combo.id)}
                            >
                              <Trash2 className="h-3 w-3" />
                            </Button>
                          </div>
                        </div>

                        {combo.clasificaciones &&
                          combo.clasificaciones.length > 0 && (
                            <div className="flex flex-wrap gap-1">
                              {combo.clasificaciones.map((cls) => (
                                <Badge
                                  key={cls}
                                  variant="secondary"
                                  className="text-xs"
                                >
                                  {cls}
                                </Badge>
                              ))}
                            </div>
                          )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </TooltipProvider>
  );
}
