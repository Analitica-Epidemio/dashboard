"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import {
  ChevronDown,
  ChevronRight,
  Folder,
  FileText,
  Search,
  Loader2,
} from "lucide-react";
import { Collapsible, CollapsibleContent } from "@/components/ui/collapsible";
import { useDebounce } from "use-debounce";
import { useInfiniteGroups } from "@/features/eventos/infinite-queries";
import { cn } from "@/lib/utils";

interface GrupoEventoSelectorProps {
  selectedGroups: Set<string>;
  selectedEvents: Set<string>;
  onSelectionChange: (grupos: Set<string>, eventos: Set<string>) => void;
  className?: string;
}

export function GrupoEventoSelector({
  selectedGroups,
  selectedEvents,
  onSelectionChange,
  className = "",
}: GrupoEventoSelectorProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedSearch] = useDebounce(searchQuery, 300);

  // Expandir todos los grupos por defecto
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());

  // Fetch groups with infinite scroll and search
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
    const newSelectedGroups = new Set(selectedGroups);
    const group = serverGroups.find((g) => String(g.id) === groupId);
    const groupEvents = group?.eventos || [];
    const newSelectedEvents = new Set(selectedEvents);

    if (newSelectedGroups.has(groupId)) {
      // Deseleccionar grupo y sus eventos
      newSelectedGroups.delete(groupId);
      groupEvents.forEach((e) => newSelectedEvents.delete(String(e.id)));
    } else {
      // Seleccionar grupo y todos sus eventos
      newSelectedGroups.add(groupId);
      groupEvents.forEach((e) => newSelectedEvents.add(String(e.id)));
    }

    onSelectionChange(newSelectedGroups, newSelectedEvents);
  };

  const toggleEvent = (eventId: string, groupId: string) => {
    const newSelectedEvents = new Set(selectedEvents);
    const newSelectedGroups = new Set(selectedGroups);

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

    onSelectionChange(newSelectedGroups, newSelectedEvents);
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

  // Verificar si un grupo está completo o parcialmente seleccionado
  const getGroupSelectionState = (groupId: string) => {
    const group = serverGroups.find((g) => String(g.id) === groupId);
    const groupEvents = group?.eventos || [];

    if (groupEvents.length === 0) {
      return { isSelected: false, isIndeterminate: false };
    }

    const selectedCount = groupEvents.filter((e) =>
      selectedEvents.has(String(e.id))
    ).length;

    return {
      isSelected: selectedCount === groupEvents.length,
      isIndeterminate: selectedCount > 0 && selectedCount < groupEvents.length,
    };
  };

  return (
    <div className={cn("space-y-3", className)}>
      {/* Search input */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
        <Input
          type="text"
          placeholder="Buscar grupos o eventos..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-9 h-9"
        />
      </div>

      {/* Groups list with scroll */}
      <div
        className="border rounded-md max-h-[400px] overflow-y-auto bg-gray-50"
        onScroll={handleGroupsScroll}
      >
        {isLoadingGroups && serverGroups.length === 0 ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-5 h-5 animate-spin text-gray-400" />
            <span className="ml-2 text-sm text-gray-500">Cargando grupos...</span>
          </div>
        ) : serverGroups.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-gray-500">
            <FileText className="w-8 h-8 mb-2 text-gray-400" />
            <p className="text-sm">No se encontraron grupos</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {serverGroups.map((group) => {
              const groupId = String(group.id);
              const isExpanded = expandedGroups.has(groupId);
              const { isSelected, isIndeterminate } = getGroupSelectionState(groupId);
              const matchesSearch = groupMatchesSearch(groupId);

              return (
                <div
                  key={groupId}
                  className={cn(
                    "bg-white hover:bg-gray-50 transition-colors",
                    matchesSearch && "bg-yellow-50 hover:bg-yellow-100"
                  )}
                >
                  {/* Group header */}
                  <div className="flex items-center gap-2 px-3 py-2.5">
                    <button
                      onClick={() => toggleGroupExpanded(groupId)}
                      className="p-0.5 hover:bg-gray-200 rounded transition-colors"
                      type="button"
                    >
                      {isExpanded ? (
                        <ChevronDown className="w-4 h-4 text-gray-600" />
                      ) : (
                        <ChevronRight className="w-4 h-4 text-gray-600" />
                      )}
                    </button>

                    <Checkbox
                      checked={isSelected}
                      onCheckedChange={() => toggleGroup(groupId)}
                      className={cn(
                        isIndeterminate && "data-[state=checked]:bg-blue-400"
                      )}
                    />

                    <Folder className="w-4 h-4 text-blue-500 flex-shrink-0" />

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-gray-900 truncate">
                          {group.name}
                        </span>
                        <Badge variant="secondary" className="text-xs">
                          {group.eventos?.length || 0}
                        </Badge>
                      </div>
                      {group.description && (
                        <p className="text-xs text-gray-500 truncate mt-0.5">
                          {group.description}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Events list - collapsible */}
                  <Collapsible open={isExpanded}>
                    <CollapsibleContent>
                      <div className="pl-11 pr-3 pb-2 space-y-1">
                        {group.eventos && group.eventos.length > 0 ? (
                          group.eventos.map((event) => {
                            const eventId = String(event.id);
                            const isEventSelected = selectedEvents.has(eventId);
                            const eventMatches = eventMatchesSearch(event.name);

                            return (
                              <div
                                key={eventId}
                                className={cn(
                                  "flex items-center gap-2 px-2 py-1.5 rounded hover:bg-gray-100 transition-colors",
                                  eventMatches && "bg-yellow-100 hover:bg-yellow-200"
                                )}
                              >
                                <Checkbox
                                  checked={isEventSelected}
                                  onCheckedChange={() => toggleEvent(eventId, groupId)}
                                />
                                <FileText className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
                                <span className="text-xs text-gray-700 flex-1 min-w-0 truncate">
                                  {event.name}
                                </span>
                              </div>
                            );
                          })
                        ) : (
                          <p className="text-xs text-gray-400 italic px-2">
                            Sin eventos
                          </p>
                        )}
                      </div>
                    </CollapsibleContent>
                  </Collapsible>
                </div>
              );
            })}

            {/* Loading more indicator */}
            {isLoadingGroups && serverGroups.length > 0 && (
              <div className="flex items-center justify-center py-3 bg-gray-50">
                <Loader2 className="w-4 h-4 animate-spin text-gray-400" />
                <span className="ml-2 text-xs text-gray-500">
                  Cargando más...
                </span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Selection summary */}
      {(selectedGroups.size > 0 || selectedEvents.size > 0) && (
        <div className="flex items-center gap-2 text-xs text-gray-600">
          <span>
            Seleccionados: {selectedGroups.size} grupo(s), {selectedEvents.size} evento(s)
          </span>
        </div>
      )}
    </div>
  );
}
