"use client";

import { useState, useEffect, useMemo } from "react";
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

  // Enable infinite scrolling when user starts searching
  useEffect(() => {
    if (search) {
      setShouldUseInfinite(true);
    }
  }, [search]);

  // Determine which data source to use
  // If searching (shouldUseInfinite), show infinite results (may be empty)
  // If NOT searching, show fallback
  // This allows InfiniteCombobox to show proper loading/empty states
  const displayGroups: Group[] = shouldUseInfinite
    ? infiniteGroups  // Can be [] during loading or when no results
    : fallbackGroups;

  const loading: boolean = shouldUseInfinite
    ? isLoading
    : Boolean(fallbackLoading);
  const error: QueryError = shouldUseInfinite && isError ? infiniteError : fallbackError;

  // Convert groups to combobox options
  // IMPORTANT: Memoize to prevent unnecessary re-renders of InfiniteCombobox
  const options: ComboboxOption[] = useMemo(
    () => displayGroups.map((group) => ({
      value: group.id,
      label: group.name,
    })),
    [displayGroups]
  );

  // CRITICAL: Only show skeleton on INITIAL load (fallback loading)
  // Don't unmount the combobox during searches!
  const showInitialLoading = !shouldUseInfinite && Boolean(fallbackLoading);
  const showError = !shouldUseInfinite && Boolean(fallbackError);

  if (showInitialLoading) {
    return (
      <div className="space-y-2">
        <label className="text-sm font-medium">Seleccionar Grupo</label>
        <Skeleton className="w-[300px] h-9" />
      </div>
    );
  }

  if (showError) {
    return (
      <div className="space-y-2">
        <label className="text-sm font-medium">Seleccionar Grupo</label>
        <Alert variant="destructive" className="w-[300px]">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {getErrorMessage(fallbackError)}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium">Seleccionar Grupo</label>
      <InfiniteCombobox
        key="group-selector-combobox" // CRITICAL: Stable key prevents unmount
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
