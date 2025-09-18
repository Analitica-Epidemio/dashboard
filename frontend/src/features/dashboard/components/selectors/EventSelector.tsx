"use client";

import { useState, useEffect } from "react";
import {
  InfiniteCombobox,
  type ComboboxOption,
} from "@/components/ui/infinite-combobox";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircle } from "lucide-react";
import { useInfiniteEvents } from "../../services/paginatedQueries";
import type { Event } from "../../types";

// Tipo más flexible para errores de query
type QueryError = unknown;

// Helper para extraer mensaje de error
function getErrorMessage(error: QueryError): string {
  if (!error) return 'Error desconocido';
  if (typeof error === 'object' && error !== null) {
    if ('message' in error && typeof error.message === 'string') {
      return error.message;
    }
    if ('error' in error && typeof error.error === 'object' && error.error !== null && 'message' in error.error) {
      return String(error.error.message);
    }
  }
  return 'Error desconocido';
}

interface EventSelectorProps {
  events: Event[];
  selectedEventId: string | null;
  onEventChange: (eventId: string | null) => void;
  disabled?: boolean;
  loading?: boolean;
  error?: QueryError;
  groupId?: string | null;
}

export function EventSelector({
  events: fallbackEvents,
  selectedEventId,
  onEventChange,
  disabled,
  loading: _fallbackLoading,
  error: fallbackError,
  groupId,
}: EventSelectorProps) {
  const [search, setSearch] = useState("");

  // Use infinite scroll hook for events
  const {
    events,
    hasMore,
    isLoading,
    loadMore,
    error: infiniteError,
    isError,
  } = useInfiniteEvents(groupId || undefined, search);

  // Reset search when group changes
  useEffect(() => {
    setSearch("");
  }, [groupId]);

  // Use fallback events if infinite query hasn't loaded yet
  const displayEvents = events.length > 0 ? events : fallbackEvents;
  const loading = isLoading && events.length === 0;
  const error = isError ? infiniteError : fallbackError;

  if (loading) {
    return (
      <div className="space-y-2">
        <label className="text-sm font-medium">Seleccionar Evento</label>
        <Skeleton className="w-[300px] h-9" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-2">
        <label className="text-sm font-medium">Seleccionar Evento</label>
        <Alert variant="destructive" className="w-[300px]">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {getErrorMessage(error)}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  // Convert events to combobox options
  const options: ComboboxOption[] = displayEvents.map((event) => ({
    value: event.id,
    label: event.name,
  }));

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium">Seleccionar Evento</label>
      <InfiniteCombobox
        options={options}
        value={selectedEventId || undefined}
        onValueChange={(value: string | undefined) => onEventChange(value ?? null)}
        onSearch={(searchTerm: string) => setSearch(searchTerm)}
        onLoadMore={loadMore}
        hasMore={hasMore}
        isLoading={isLoading}
        disabled={disabled || !groupId}
        placeholder={
          disabled || !groupId
            ? "Primero selecciona un grupo..."
            : "Buscar o seleccionar evento..."
        }
        searchPlaceholder="Buscar evento..."
        emptyMessage="No se encontraron eventos"
        className="w-full"
      />
    </div>
  );
}
