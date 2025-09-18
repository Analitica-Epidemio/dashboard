"use client";

import { useState, useEffect } from "react";
import {
  InfiniteCombobox,
  type ComboboxOption,
} from "@/components/ui/infinite-combobox";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircle } from "lucide-react";
import { useInfiniteGroups } from "../../services/paginatedQueries";
import { Group } from "../../types";

// Tipo más flexible para errores de query - compatible con react-query
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

// Tipo específico para el hook de infinite groups
interface UseInfiniteGroupsResult {
  groups: Group[];
  hasMore: boolean;
  isLoading: boolean;
  loadMore: () => void;
  error: QueryError;
  isError: boolean;
}

interface GroupSelectorProps {
  groups: Group[];
  selectedGroupId: string | null;
  onGroupChange: (groupId: string | null) => void;
  loading?: boolean;
  error?: QueryError;
}

export function GroupSelector({
  groups: fallbackGroups,
  selectedGroupId,
  onGroupChange,
  loading: fallbackLoading,
  error: fallbackError,
}: GroupSelectorProps) {
  const [search, setSearch] = useState("");
  const [shouldUseInfinite, setShouldUseInfinite] = useState(false);

  // Use infinite scroll hook for groups only when searching
  const {
    groups: infiniteGroups,
    hasMore,
    isLoading,
    loadMore,
    error: infiniteError,
    isError,
  }: UseInfiniteGroupsResult = useInfiniteGroups(search);

  // Determine which data source to use
  const displayGroups: Group[] =
    shouldUseInfinite && infiniteGroups.length > 0
      ? infiniteGroups
      : fallbackGroups;

  const loading: boolean = shouldUseInfinite
    ? isLoading && infiniteGroups.length === 0
    : Boolean(fallbackLoading);
  const error: QueryError = shouldUseInfinite && isError ? infiniteError : fallbackError;

  // Enable infinite scrolling when user starts searching
  useEffect(() => {
    if (search) {
      setShouldUseInfinite(true);
    }
  }, [search]);

  if (loading) {
    return (
      <div className="space-y-2">
        <label className="text-sm font-medium">Seleccionar Grupo</label>
        <Skeleton className="w-[300px] h-9" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-2">
        <label className="text-sm font-medium">Seleccionar Grupo</label>
        <Alert variant="destructive" className="w-[300px]">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {getErrorMessage(error)}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  // Convert groups to combobox options
  const options: ComboboxOption[] = displayGroups.map((group) => ({
    value: group.id,
    label: group.name,
  }));

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium">Seleccionar Grupo</label>
      <InfiniteCombobox
        options={options}
        value={selectedGroupId || undefined}
        onValueChange={(value: string | undefined) => {
          onGroupChange(value ?? null);
        }}
        onSearch={(searchTerm: string) => {
          setSearch(searchTerm);
        }}
        onLoadMore={() => {
          if (shouldUseInfinite) {
            loadMore();
          }
        }}
        hasMore={shouldUseInfinite ? hasMore : false}
        isLoading={shouldUseInfinite ? isLoading : false}
        placeholder="Buscar o seleccionar grupo..."
        searchPlaceholder="Buscar grupo de eventos..."
        emptyMessage="No se encontraron grupos"
        className="w-full"
      />
    </div>
  );
}
