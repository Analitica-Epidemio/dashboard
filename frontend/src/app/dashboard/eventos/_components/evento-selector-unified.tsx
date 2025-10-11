"use client";

import React, { useState, useMemo, useEffect } from "react";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Search,
  X,
  ChevronDown,
  ChevronRight,
  Folder,
  FileText,
} from "lucide-react";
import { Collapsible, CollapsibleContent } from "@/components/ui/collapsible";
import { cn } from "@/lib/utils";

interface Event {
  id: number | string;
  name: string;
  groupId?: string;
}

interface Group {
  id: number | string;
  name: string;
  eventos?: Event[]; // Eventos incluidos en este grupo (del backend)
}

interface Selection {
  groups: string[]; // IDs de grupos seleccionados
  events: string[]; // IDs de eventos individuales seleccionados
}

interface EventoSelectorUnifiedProps {
  groups: Group[];
  allEvents: Event[]; // Para backward compatibility, se ignora si grupos tienen eventos
  loading?: boolean;
  onSelectionChange: (selection: Selection) => void;
  initialSelection?: Selection;
}

export function EventoSelectorUnified({
  groups,
  allEvents,
  loading = false,
  onSelectionChange,
  initialSelection,
}: EventoSelectorUnifiedProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [selection, setSelection] = useState<Selection>(
    initialSelection || {
      groups: [],
      events: [],
    }
  );
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());

  // Memorizar IDs de grupos para evitar loops infinitos
  const groupIds = useMemo(() => {
    return groups.map((g) => String(g.id));
  }, [groups]);

  // Expandir todos los grupos cuando se carguen o cambien
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

  // Agrupar eventos por grupo
  // Si los grupos ya tienen eventos, usarlos; si no, construir desde allEvents
  const eventsByGroup = useMemo(() => {
    const grouped = new Map<string, Event[]>();

    // Primero intentar usar eventos que vienen en los grupos
    const hasGroupEvents = groups.some((g) => g.eventos && g.eventos.length > 0);

    if (hasGroupEvents) {
      // Usar eventos que vienen dentro de cada grupo
      groups.forEach((group) => {
        if (group.eventos) {
          grouped.set(String(group.id), group.eventos);
        }
      });
    } else {
      // Fallback: construir desde allEvents (backward compatibility)
      allEvents.forEach((event) => {
        const groupId = event.groupId || "sin_grupo";
        if (!grouped.has(groupId)) {
          grouped.set(groupId, []);
        }
        grouped.get(groupId)!.push(event);
      });
    }

    return grouped;
  }, [groups, allEvents]);

  // Filtrar grupos según búsqueda (pero siempre mostrar todos sus eventos)
  const filteredGroups = useMemo(() => {
    if (!searchQuery.trim()) return groups;

    const query = searchQuery.toLowerCase();
    return groups.filter((group) => {
      const groupMatches = group.name.toLowerCase().includes(query);
      const groupEvents = eventsByGroup.get(String(group.id)) || [];
      const hasMatchingEvents = groupEvents.some((event) =>
        event.name.toLowerCase().includes(query)
      );
      return groupMatches || hasMatchingEvents;
    });
  }, [groups, searchQuery, eventsByGroup]);

  // Verificar si un grupo coincide con la búsqueda
  const groupMatchesSearch = (groupId: string) => {
    if (!searchQuery.trim()) return false;
    const group = groups.find((g) => String(g.id) === groupId);
    return group?.name.toLowerCase().includes(searchQuery.toLowerCase());
  };

  // Verificar si un evento coincide con la búsqueda
  const eventMatchesSearch = (eventName: string) => {
    if (!searchQuery.trim()) return false;
    return eventName.toLowerCase().includes(searchQuery.toLowerCase());
  };

  const toggleGroup = (groupId: string) => {
    const newSelected = new Set(selection.groups);
    const groupEvents = eventsByGroup.get(groupId) || [];
    const newSelectedEvents = new Set(selection.events);

    if (newSelected.has(groupId)) {
      // Deseleccionar grupo y sus eventos
      newSelected.delete(groupId);
      groupEvents.forEach((e) => newSelectedEvents.delete(String(e.id)));
    } else {
      // Seleccionar grupo y todos sus eventos
      newSelected.add(groupId);
      groupEvents.forEach((e) => newSelectedEvents.add(String(e.id)));
    }

    const newSelection = {
      groups: Array.from(newSelected),
      events: Array.from(newSelectedEvents),
    };
    setSelection(newSelection);
    onSelectionChange(newSelection);
  };

  const toggleEvent = (eventId: string, groupId: string) => {
    const newSelectedEvents = new Set(selection.events);
    const newSelectedGroups = new Set(selection.groups);

    if (newSelectedEvents.has(eventId)) {
      newSelectedEvents.delete(eventId);
      // Si ya no hay eventos de este grupo, quitar el grupo
      const groupEvents = eventsByGroup.get(groupId) || [];
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

    const newSelection = {
      groups: Array.from(newSelectedGroups),
      events: Array.from(newSelectedEvents),
    };
    setSelection(newSelection);
    onSelectionChange(newSelection);
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

  const clearAll = () => {
    const newSelection = { groups: [], events: [] };
    setSelection(newSelection);
    onSelectionChange(newSelection);
  };

  const hasSelection = selection.events.length > 0;

  return (
    <div className="space-y-4">
      {/* Búsqueda */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Buscar grupos o eventos..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-9"
          disabled={loading}
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

      {/* Selección actual */}
      {hasSelection && (
        <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg border">
          <div className="text-sm">
            <span className="font-medium">{selection.events.length}</span> evento(s) seleccionado(s)
          </div>
          <Button variant="ghost" size="sm" onClick={clearAll}>
            Limpiar
          </Button>
        </div>
      )}

      {/* Lista de Grupos con Eventos */}
      <div className="space-y-2 max-h-[500px] overflow-y-auto pr-2 border rounded-lg p-3 bg-slate-50/50">
        {filteredGroups.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <Search className="h-12 w-12 mx-auto mb-3 opacity-20" />
            <p className="text-sm">No se encontraron grupos o eventos</p>
            <p className="text-xs mt-1">Intenta con otra búsqueda</p>
          </div>
        ) : (
          filteredGroups.map((group) => {
            const groupId = String(group.id);
            const groupEvents = eventsByGroup.get(groupId) || [];
            const isGroupSelected = selection.groups.includes(groupId);
            const isExpanded = expandedGroups.has(groupId);
            const selectedEventsInGroup = groupEvents.filter((e) =>
              selection.events.includes(String(e.id))
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
                    <Folder
                      className={cn(
                        "h-4 w-4",
                        groupMatchesBusqueda ? "text-blue-600" : "text-blue-500"
                      )}
                    />
                    <span
                      className={cn(
                        "font-medium",
                        groupMatchesBusqueda && "text-blue-700"
                      )}
                    >
                      {group.name}
                    </span>
                  </button>

                  <Badge variant="outline" className="text-xs">
                    {selectedEventsInGroup > 0 && `${selectedEventsInGroup}/`}
                    {groupEvents.length}
                  </Badge>
                </div>

                {/* Events List */}
                <Collapsible open={isExpanded}>
                  <CollapsibleContent>
                    <div className="p-2 bg-white space-y-1">
                      {groupEvents.map((event) => {
                        const eventId = String(event.id);
                        const isSelected = selection.events.includes(eventId);
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
                            <input
                              type="checkbox"
                              checked={isSelected}
                              onChange={() => toggleEvent(eventId, groupId)}
                              className="h-4 w-4 rounded border-gray-300 ml-6"
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
                      })}
                    </div>
                  </CollapsibleContent>
                </Collapsible>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
