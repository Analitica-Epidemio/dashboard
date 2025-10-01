"use client";

import React, { createContext, useContext, useState, ReactNode } from "react";
import { useDashboardFilters } from "../hooks/useDashboardFilters";
import type { Group, Event } from "../types";
import { TipoClasificacion } from "@/lib/types/clasificacion";

// Tipo más flexible para errores de query - compatible con los tipos de react-query
type QueryError = unknown;

export interface FilterCombination {
  id: string;
  groupId: string | null;
  groupName?: string;
  eventIds: number[];
  eventNames?: string[];
  clasificaciones?: TipoClasificacion[];
  label?: string;
  color?: string;
}

export interface DraftFilter {
  groupId: string | null;
  groupName?: string;
  eventIds: number[];
  eventNames?: string[];
  clasificaciones?: TipoClasificacion[];
  label?: string;
}

export interface DateRange {
  from: Date | null;
  to: Date | null;
}

interface FilterContextType {
  // Date Range
  dateRange: DateRange;
  setDateRange: (range: DateRange) => void;

  // Filter Combinations
  filterCombinations: FilterCombination[];
  addFilterCombination: (combination: Omit<FilterCombination, "id">) => void;
  updateFilterCombination: (id: string, combination: Omit<FilterCombination, "id">) => void;
  removeFilterCombination: (id: string) => void;
  duplicateFilterCombination: (id: string) => void;
  clearFilterCombinations: () => void;

  // Editing state
  editingCombinationId: string | null;
  startEditingCombination: (id: string) => void;
  cancelEditing: () => void;
  getEditingCombination: () => FilterCombination | null;

  // Draft filter (preview en vivo)
  draftFilter: DraftFilter | null;
  setDraftFilter: (filter: DraftFilter | null) => void;

  // Data from hooks
  groups: Group[];
  groupsLoading: boolean;
  groupsError: QueryError;
  allEvents: Event[];
  allEventsLoading: boolean;
  allEventsError: QueryError;

  // View state
  isComparisonView: boolean;
  setIsComparisonView: (value: boolean) => void;
}

const FilterContext = createContext<FilterContextType | undefined>(undefined);

const COMBINATION_COLORS: readonly string[] = [
  "bg-blue-100 border-blue-300",
  "bg-green-100 border-green-300",
  "bg-purple-100 border-purple-300",
  "bg-yellow-100 border-yellow-300",
  "bg-pink-100 border-pink-300",
  "bg-indigo-100 border-indigo-300",
] as const;

interface FilterProviderProps {
  children: ReactNode;
}

export function FilterProvider({ children }: FilterProviderProps) {
  const dashboardFilters = useDashboardFilters();

  const [dateRange, setDateRange] = useState<DateRange>({
    from: new Date(2020, 0, 1),
    to: new Date(2025, 11, 31),
  });

  const [filterCombinations, setFilterCombinations] = useState<
    FilterCombination[]
  >([]);
  const [isComparisonView, setIsComparisonView] = useState(false);
  const [editingCombinationId, setEditingCombinationId] = useState<string | null>(null);
  const [draftFilter, setDraftFilter] = useState<DraftFilter | null>(null);

  const addFilterCombination = (combination: Omit<FilterCombination, "id">) => {
    const newCombination: FilterCombination = {
      ...combination,
      id: `filter-${Date.now()}`,
      color:
        COMBINATION_COLORS[
          filterCombinations.length % COMBINATION_COLORS.length
        ],
    };
    setFilterCombinations((prev: FilterCombination[]) => [...prev, newCombination]);
  };

  const updateFilterCombination = (id: string, combination: Omit<FilterCombination, "id">) => {
    setFilterCombinations((prev: FilterCombination[]) =>
      prev.map((f) => (f.id === id ? { ...combination, id, color: f.color } : f))
    );
    setEditingCombinationId(null);
  };

  const removeFilterCombination = (id: string) => {
    setFilterCombinations((prev: FilterCombination[]) => prev.filter((f) => f.id !== id));
    // Si estamos editando esta combinación, cancelar la edición
    if (editingCombinationId === id) {
      setEditingCombinationId(null);
    }
  };

  const duplicateFilterCombination = (id: string) => {
    const original = filterCombinations.find((f) => f.id === id);
    if (!original) return;

    addFilterCombination({
      ...original,
      label: `${original.label ?? original.groupName} (copia)`,
    });
  };

  const clearFilterCombinations = () => {
    setFilterCombinations([]);
    setEditingCombinationId(null);
  };

  const startEditingCombination = (id: string) => {
    setEditingCombinationId(id);
  };

  const cancelEditing = () => {
    setEditingCombinationId(null);
  };

  const getEditingCombination = (): FilterCombination | null => {
    if (!editingCombinationId) return null;
    return filterCombinations.find((f) => f.id === editingCombinationId) ?? null;
  };

  return (
    <FilterContext.Provider
      value={{
        dateRange,
        setDateRange,
        filterCombinations,
        addFilterCombination,
        updateFilterCombination,
        removeFilterCombination,
        duplicateFilterCombination,
        clearFilterCombinations,
        editingCombinationId,
        startEditingCombination,
        cancelEditing,
        getEditingCombination,
        draftFilter,
        setDraftFilter,
        groups: dashboardFilters.groups,
        groupsLoading: dashboardFilters.groupsLoading,
        groupsError: dashboardFilters.groupsError,
        allEvents: dashboardFilters.allEvents,
        allEventsLoading: dashboardFilters.allEventsLoading,
        allEventsError: dashboardFilters.allEventsError,
        isComparisonView,
        setIsComparisonView,
      }}
    >
      {children}
    </FilterContext.Provider>
  );
}

export function useFilterContext(): FilterContextType {
  const context = useContext(FilterContext);
  if (!context) {
    throw new Error("useFilterContext must be used within FilterProvider");
  }
  return context;
}
