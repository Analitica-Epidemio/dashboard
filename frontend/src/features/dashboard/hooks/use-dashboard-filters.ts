'use client'

import { useState, useMemo } from 'react'
import type { DashboardFilters, Group, Event } from '../types'
import { useGroups, useAllEvents, useEventsByGroup } from '@/features/eventos/api'

// Tipo más flexible para errores de query - compatible con react-query
type QueryError = unknown;

// Tipo para el resultado del hook
interface UseDashboardFiltersResult {
  filters: DashboardFilters;
  // Groups data and state
  groups: Group[];
  groupsLoading: boolean;
  groupsError: QueryError;
  // All events (for filter builder)
  allEvents: Event[];
  allEventsLoading: boolean;
  allEventsError: QueryError;
  // Events data and state (filtered by group)
  availableEvents: Event[];
  eventsLoading: boolean;
  eventsError: QueryError;
  // Selected items
  selectedGroup: Group | null;
  selectedEvent: Event | null;
  // Actions
  setSelectedGroup: (groupId: string | null) => void;
  setSelectedEvent: (eventId: string | null) => void;
}

export const useDashboardFilters = (): UseDashboardFiltersResult => {
  const [filters, setFilters] = useState<DashboardFilters>({
    selectedGroupId: null,
    selectedEventId: null,
  })

  // React Query hooks
  const groupsQuery = useGroups()
  const allEventsQuery = useAllEvents()
  const eventsQuery = useEventsByGroup(filters.selectedGroupId)

  const selectedGroup = useMemo((): Group | null =>
    groupsQuery.data?.find((group: Group) => group.id === filters.selectedGroupId) ?? null,
    [groupsQuery.data, filters.selectedGroupId]
  );

  const selectedEvent = useMemo((): Event | null =>
    eventsQuery.data?.find((event: Event) => event.id === filters.selectedEventId) ?? null,
    [eventsQuery.data, filters.selectedEventId]
  );

  const setSelectedGroup = (groupId: string | null): void => {
    setFilters({
      selectedGroupId: groupId,
      selectedEventId: null, // Reset event when group changes
    });
  };

  const setSelectedEvent = (eventId: string | null): void => {
    setFilters((prev: DashboardFilters) => ({
      ...prev,
      selectedEventId: eventId,
    }));
  };

  // Los errores ya vienen con tipos correctos de react-query

  return {
    filters,

    // Groups data and state
    groups: groupsQuery.data ?? [],
    groupsLoading: groupsQuery.isLoading,
    groupsError: groupsQuery.error,

    // All events (for filter builder)
    allEvents: allEventsQuery.data ?? [],
    allEventsLoading: allEventsQuery.isLoading,
    allEventsError: allEventsQuery.error,

    // Events data and state (filtered by group)
    availableEvents: eventsQuery.data ?? [],
    eventsLoading: eventsQuery.isLoading,
    eventsError: eventsQuery.error,

    selectedGroup,
    selectedEvent,
    setSelectedGroup,
    setSelectedEvent,
  };
}
