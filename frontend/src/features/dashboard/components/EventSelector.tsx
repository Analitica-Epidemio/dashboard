'use client'

import { useState, useEffect } from 'react'
import { InfiniteCombobox, type ComboboxOption } from '@/components/ui/infinite-combobox'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { AlertCircle } from 'lucide-react'
import { useInfiniteEvents } from '../services/paginatedQueries'
import type { Event } from '../types'

interface EventSelectorProps {
  events: Event[]
  selectedEventId: string | null
  onEventChange: (eventId: string | null) => void
  disabled?: boolean
  loading?: boolean
  error?: Error | null
  groupId?: string | null
}

export function EventSelector({
  events: fallbackEvents,
  selectedEventId,
  onEventChange,
  disabled,
  loading: fallbackLoading,
  error: fallbackError,
  groupId
}: EventSelectorProps) {
  const [search, setSearch] = useState('')

  // Use infinite scroll hook for events
  const {
    events,
    hasMore,
    isLoading,
    loadMore,
    error: infiniteError,
    isError
  } = useInfiniteEvents(groupId || undefined, search)

  // Reset search when group changes
  useEffect(() => {
    setSearch('')
  }, [groupId])

  // Use fallback events if infinite query hasn't loaded yet
  const displayEvents = events.length > 0 ? events : fallbackEvents
  const loading = isLoading && events.length === 0
  const error = isError ? infiniteError : fallbackError

  if (loading) {
    return (
      <div className="space-y-2">
        <label className="text-sm font-medium">Seleccionar Evento</label>
        <Skeleton className="w-[300px] h-9" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-2">
        <label className="text-sm font-medium">Seleccionar Evento</label>
        <Alert variant="destructive" className="w-[300px]">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {error?.message || 'Error al cargar eventos'}
          </AlertDescription>
        </Alert>
      </div>
    )
  }

  // Convert events to combobox options
  const options: ComboboxOption[] = displayEvents.map(event => ({
    value: event.id,
    label: event.name
  }))

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium">Seleccionar Evento</label>
      <InfiniteCombobox
        options={options}
        value={selectedEventId || undefined}
        onValueChange={(value) => onEventChange(value || null)}
        onSearch={setSearch}
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
  )
}