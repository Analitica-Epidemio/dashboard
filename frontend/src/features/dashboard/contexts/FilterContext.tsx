'use client'

import React, { createContext, useContext, useState, ReactNode } from 'react'
import { useDashboardFilters } from '../hooks/useDashboardFilters'
import type { Group, Event } from '../types'

export interface FilterCombination {
  id: string
  groupId: string | null
  groupName?: string
  eventIds: number[]
  eventNames?: string[]
  clasificaciones?: Array<string | { value: string; label: string }>
  label?: string
  color?: string
}

export interface DateRange {
  from: Date | null
  to: Date | null
}

interface FilterContextType {
  // Date Range
  dateRange: DateRange
  setDateRange: (range: DateRange) => void

  // Filter Combinations
  filterCombinations: FilterCombination[]
  addFilterCombination: (combination: Omit<FilterCombination, 'id'>) => void
  removeFilterCombination: (id: string) => void
  duplicateFilterCombination: (id: string) => void
  clearFilterCombinations: () => void

  // Data from hooks
  groups: Array<{ id: string; name: string; [key: string]: unknown }>
  groupsLoading: boolean
  groupsError: unknown
  allEvents: Array<{ id: string | number; groupId: string; name: string; [key: string]: unknown }>
  allEventsLoading: boolean
  allEventsError: unknown

  // View state
  isComparisonView: boolean
  setIsComparisonView: (value: boolean) => void
}

const FilterContext = createContext<FilterContextType | undefined>(undefined)

const COMBINATION_COLORS = [
  'bg-blue-100 border-blue-300',
  'bg-green-100 border-green-300',
  'bg-purple-100 border-purple-300',
  'bg-yellow-100 border-yellow-300',
  'bg-pink-100 border-pink-300',
  'bg-indigo-100 border-indigo-300',
]

export function FilterProvider({ children }: { children: ReactNode }) {
  const dashboardFilters = useDashboardFilters()

  const [dateRange, setDateRange] = useState<DateRange>({
    from: new Date(2020, 0, 1),
    to: new Date(2025, 11, 31),
  })

  const [filterCombinations, setFilterCombinations] = useState<FilterCombination[]>([])
  const [isComparisonView, setIsComparisonView] = useState(false)

  const addFilterCombination = (combination: Omit<FilterCombination, 'id'>) => {
    const newCombination: FilterCombination = {
      ...combination,
      id: `filter-${Date.now()}`,
      color: COMBINATION_COLORS[filterCombinations.length % COMBINATION_COLORS.length],
    }
    setFilterCombinations(prev => [...prev, newCombination])
  }

  const removeFilterCombination = (id: string) => {
    setFilterCombinations(prev => prev.filter(f => f.id !== id))
  }

  const duplicateFilterCombination = (id: string) => {
    const original = filterCombinations.find(f => f.id === id)
    if (!original) return

    addFilterCombination({
      ...original,
      label: `${original.label || original.groupName} (copia)`,
    })
  }

  const clearFilterCombinations = () => {
    setFilterCombinations([])
  }

  return (
    <FilterContext.Provider
      value={{
        dateRange,
        setDateRange,
        filterCombinations,
        addFilterCombination,
        removeFilterCombination,
        duplicateFilterCombination,
        clearFilterCombinations,
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
  )
}

export function useFilterContext() {
  const context = useContext(FilterContext)
  if (!context) {
    throw new Error('useFilterContext must be used within FilterProvider')
  }
  return context
}