'use client'

import { useState } from 'react'
import { InfiniteCombobox, type ComboboxOption } from '@/components/ui/infinite-combobox'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { AlertCircle } from 'lucide-react'
import { useInfiniteGroups } from '../services/paginatedQueries'
import type { Group } from '../types'

interface GroupSelectorProps {
  groups: Group[]
  selectedGroupId: string | null
  onGroupChange: (groupId: string | null) => void
  loading?: boolean
  error?: Error | null
}

export function GroupSelector({
  groups: fallbackGroups,
  selectedGroupId,
  onGroupChange,
  loading: fallbackLoading,
  error: fallbackError
}: GroupSelectorProps) {
  const [search, setSearch] = useState('')

  console.log('[GroupSelector] Current search state:', search);

  // Use infinite scroll hook for groups
  const {
    groups,
    hasMore,
    isLoading,
    loadMore,
    error: infiniteError,
    isError
  } = useInfiniteGroups(search)

  // Use fallback groups if infinite query hasn't loaded yet
  const displayGroups = groups.length > 0 ? groups : fallbackGroups
  const loading = isLoading && groups.length === 0
  const error = isError ? infiniteError : fallbackError

  if (loading) {
    return (
      <div className="space-y-2">
        <label className="text-sm font-medium">Seleccionar Grupo</label>
        <Skeleton className="w-[300px] h-9" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-2">
        <label className="text-sm font-medium">Seleccionar Grupo</label>
        <Alert variant="destructive" className="w-[300px]">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {error?.message || 'Error al cargar grupos'}
          </AlertDescription>
        </Alert>
      </div>
    )
  }

  // Convert groups to combobox options
  const options: ComboboxOption[] = displayGroups.map(group => ({
    value: group.id,
    label: group.name
  }))

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium">Seleccionar Grupo</label>
      <InfiniteCombobox
        options={options}
        value={selectedGroupId || undefined}
        onValueChange={(value) => {
          console.log('[GroupSelector] Value changed to:', value);
          onGroupChange(value || null);
        }}
        onSearch={(searchTerm) => {
          console.log('[GroupSelector] Search triggered with:', searchTerm);
          setSearch(searchTerm);
        }}
        onLoadMore={() => {
          console.log('[GroupSelector] Load more triggered');
          loadMore();
        }}
        hasMore={hasMore}
        isLoading={isLoading}
        placeholder="Buscar o seleccionar grupo..."
        searchPlaceholder="Buscar grupo de eventos..."
        emptyMessage="No se encontraron grupos"
        className="w-full"
      />
    </div>
  )
}