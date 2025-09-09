'use client'

import { useState, useMemo } from 'react'
import type { DashboardFilters } from '../types'
import { useGroups, useAllEvents, useEventsByGroup, useChartData } from '../services/queries'

export const useDashboardFilters = () => {
  const [filters, setFilters] = useState<DashboardFilters>({
    selectedGroupId: null,
    selectedEventId: null,
  })

  // React Query hooks
  const groupsQuery = useGroups()
  const allEventsQuery = useAllEvents()
  const eventsQuery = useEventsByGroup(filters.selectedGroupId)
  const chartDataQuery = useChartData(filters.selectedEventId)

  const selectedGroup = useMemo(() => 
    groupsQuery.data?.find(group => group.id === filters.selectedGroupId) || null,
    [groupsQuery.data, filters.selectedGroupId]
  )

  const selectedEvent = useMemo(() => 
    eventsQuery.data?.find(event => event.id === filters.selectedEventId) || null,
    [eventsQuery.data, filters.selectedEventId]
  )

  const setSelectedGroup = (groupId: string | null) => {
    setFilters({
      selectedGroupId: groupId,
      selectedEventId: null, // Reset event when group changes
    })
  }

  const setSelectedEvent = (eventId: string | null) => {
    setFilters(prev => ({
      ...prev,
      selectedEventId: eventId,
    }))
  }

  return {
    filters,
    
    // Groups data and state
    groups: groupsQuery.data || [],
    groupsLoading: groupsQuery.isLoading,
    groupsError: groupsQuery.error,
    
    // All events (for filter builder)
    allEvents: allEventsQuery.data || [],
    allEventsLoading: allEventsQuery.isLoading,
    allEventsError: allEventsQuery.error,
    
    // Events data and state (filtered by group)
    availableEvents: eventsQuery.data || [],
    eventsLoading: eventsQuery.isLoading,
    eventsError: eventsQuery.error,
    
    // Chart data and state
    chartData: chartDataQuery.data || [],
    chartDataLoading: chartDataQuery.isLoading,
    chartDataError: chartDataQuery.error,
    
    selectedGroup,
    selectedEvent,
    setSelectedGroup,
    setSelectedEvent,
  }
}