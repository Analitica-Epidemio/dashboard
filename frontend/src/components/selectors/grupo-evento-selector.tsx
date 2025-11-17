"use client";

/**
 * Selector unificado de grupos y eventos con infinite scroll
 * Componente compartido usado por personas, eventos y boletines
 */

import React, { useState, useCallback } from "react";
import {
  Search,
  X,
  Loader2,
  ChevronDown,
  ChevronRight,
  Folder,
  FileText,
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Collapsible, CollapsibleContent } from "@/components/ui/collapsible";
import { useDebounce } from "use-debounce";
import { useInfiniteGroups } from "@/features/eventos/infinite-queries";
import { cn } from "@/lib/utils";

interface GrupoEventoSelectorProps {
  selectedGroupIds: number[];
  selectedEventIds: number[];
  onSelectionChange: (groups: number[], events: number[]) => void;
  className?: string;
  showSelectionSummary?: boolean;
  maxHeight?: string;
}

export function GrupoEventoSelector({
  selectedGroupIds,
  selectedEventIds,
  onSelectionChange,
  className = "",
  showSelectionSummary = true,
  maxHeight = "400px",
}: GrupoEventoSelectorProps) {
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

    const resultGroups = Array.from(newSelectedGroups).map((id) =>
      parseInt(id)
    );
    const resultEvents = Array.from(newSelectedEvents).map((id) =>
      parseInt(id)
    );

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

    const resultGroups = Array.from(newSelectedGroups).map((id) =>
      parseInt(id)
    );
    const resultEvents = Array.from(newSelectedEvents).map((id) =>
      parseInt(id)
    );

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

  const clearSelection = () => {
    onSelectionChange([], []);
  };

  // Verificar si un grupo está completo o parcialmente seleccionado
  const getGroupSelectionState = (groupId: string) => {
    const group = serverGroups.find((g) => String(g.id) === groupId);
    const groupEvents = group?.eventos || [];

    if (groupEvents.length === 0) {
      return { isSelected: false, isIndeterminate: false };
    }

    const selectedCount = groupEvents.filter((e) => {
      const eventIdNum =
        typeof e.id === "string" ? parseInt(e.id as string) : e.id;
      return selectedEventIds.includes(eventIdNum as number);
    }).length;

    return {
      isSelected: selectedCount === groupEvents.length,
      isIndeterminate: selectedCount > 0 && selectedCount < groupEvents.length,
    };
  };

  return (
    <div className={cn("space-y-3", className)}>
      {/* Selección actual */}
      {showSelectionSummary && selectedEventIds.length > 0 && (
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
            onClick={clearSelection}
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
        className="space-y-2 overflow-y-auto pr-2 border rounded-lg p-3 bg-slate-50/50"
        style={{ maxHeight }}
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
              const groupIdNum =
                typeof group.id === "string" ? parseInt(group.id) : group.id;
              const isGroupSelected = selectedGroupIds.includes(groupIdNum);
              const isExpanded = expandedGroups.has(groupId);
              const { isIndeterminate } = getGroupSelectionState(groupId);
              const selectedEventsInGroup = groupEvents.filter((e) => {
                const eventIdNum =
                  typeof e.id === "string" ? parseInt(e.id as string) : e.id;
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
                  {/* Group header */}
                  <div className="flex items-center gap-2 p-3 bg-slate-50 hover:bg-slate-100 transition-colors">
                    <Checkbox
                      checked={isGroupSelected}
                      onCheckedChange={() => toggleGroup(groupId)}
                      className={cn(
                        isIndeterminate && "data-[state=checked]:bg-blue-400"
                      )}
                    />
                    <button
                      onClick={() => toggleGroupExpanded(groupId)}
                      className="flex items-center gap-2 flex-1 text-left"
                      type="button"
                    >
                      {isExpanded ? (
                        <ChevronDown className="h-4 w-4 text-muted-foreground" />
                      ) : (
                        <ChevronRight className="h-4 w-4 text-muted-foreground" />
                      )}
                      <Folder
                        className={cn(
                          "h-4 w-4",
                          groupMatchesBusqueda ? "text-blue-600" : "text-blue-500"
                        )}
                      />
                      <span
                        className={cn(
                          "font-medium text-sm",
                          groupMatchesBusqueda && "text-blue-700"
                        )}
                      >
                        {group.name}
                      </span>
                    </button>
                    <Badge variant="outline" className="text-xs">
                      {selectedEventsInGroup > 0 &&
                        `${selectedEventsInGroup}/`}
                      {groupEvents.length}
                    </Badge>
                  </div>

                  {/* Events list */}
                  <Collapsible open={isExpanded}>
                    <CollapsibleContent>
                      <div className="p-2 bg-white space-y-1">
                        {groupEvents.length > 0 ? (
                          groupEvents.map((event) => {
                            const eventId = String(event.id);
                            const eventIdNum =
                              typeof event.id === "string"
                                ? parseInt(event.id as string)
                                : event.id;
                            const isSelected = selectedEventIds.includes(
                              eventIdNum as number
                            );
                            const eventMatchesBusqueda =
                              eventMatchesSearch(event.name);

                            return (
                              <label
                                key={eventId}
                                className={cn(
                                  "flex items-center gap-2 p-2 rounded cursor-pointer hover:bg-slate-50 transition-colors",
                                  isSelected && "bg-blue-50",
                                  eventMatchesBusqueda &&
                                    !isSelected &&
                                    "bg-yellow-50"
                                )}
                              >
                                <Checkbox
                                  checked={isSelected}
                                  onCheckedChange={() =>
                                    toggleEvent(eventId, groupId)
                                  }
                                  className="ml-6"
                                />
                                <FileText
                                  className={cn(
                                    "h-4 w-4",
                                    eventMatchesBusqueda
                                      ? "text-yellow-600"
                                      : "text-green-600"
                                  )}
                                />
                                <span
                                  className={cn(
                                    "text-sm flex-1",
                                    eventMatchesBusqueda &&
                                      "font-medium text-yellow-900"
                                  )}
                                >
                                  {event.name}
                                </span>
                              </label>
                            );
                          })
                        ) : (
                          <p className="text-xs text-gray-400 italic px-2 ml-6">
                            Sin eventos
                          </p>
                        )}
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
}
