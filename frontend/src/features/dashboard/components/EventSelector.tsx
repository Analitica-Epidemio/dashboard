'use client'

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { AlertCircle } from 'lucide-react'
import type { Event } from '../types'

interface EventSelectorProps {
  events: Event[]
  selectedEventId: string | null
  onEventChange: (eventId: string | null) => void
  disabled?: boolean
  loading?: boolean
  error?: Error | null
}

export function EventSelector({ 
  events, 
  selectedEventId, 
  onEventChange, 
  disabled, 
  loading, 
  error 
}: EventSelectorProps) {
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
            {error.message || 'Error al cargar eventos'}
          </AlertDescription>
        </Alert>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium">Seleccionar Evento</label>
      <Select 
        value={selectedEventId || ''} 
        onValueChange={(value) => onEventChange(value || null)}
        disabled={disabled || events.length === 0}
      >
        <SelectTrigger className="w-[300px]">
          <SelectValue 
            placeholder={
              disabled || events.length === 0 
                ? "Primero selecciona un grupo..." 
                : "Selecciona un evento..."
            } 
          />
        </SelectTrigger>
        <SelectContent>
          {events.map((event) => (
            <SelectItem key={event.id} value={event.id}>
              {event.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}