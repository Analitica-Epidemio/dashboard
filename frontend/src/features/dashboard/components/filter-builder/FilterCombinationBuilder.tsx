'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Plus, Layers, Check, X } from 'lucide-react'
import { GroupSelector } from '../selectors/GroupSelector'
import { ClassificationSelector, TipoClasificacion } from '../selectors/ClassificationSelector'
import { useFilterContext } from '../../contexts/FilterContext'
import type { Event } from '../../types'

interface CurrentFilter {
  groupId: string | null
  eventIds: number[]
  clasificaciones?: TipoClasificacion[]
}

export function FilterCombinationBuilder() {
  const {
    groups,
    groupsLoading,
    groupsError,
    allEvents,
    addFilterCombination,
  } = useFilterContext()

  const [currentFilter, setCurrentFilter] = useState<CurrentFilter>({
    groupId: null,
    eventIds: [],
  })

  const [availableEvents, setAvailableEvents] = useState<Event[]>([])

  useEffect(() => {
    if (currentFilter.groupId) {
      const groupEvents = allEvents.filter(e => e.groupId === currentFilter.groupId)
      setAvailableEvents(groupEvents)
    } else {
      setAvailableEvents([])
    }
  }, [currentFilter.groupId, allEvents])

  const handleGroupChange = (groupId: string | null) => {
    setCurrentFilter({
      groupId,
      eventIds: [],
      clasificaciones: undefined,
    })
  }

  const handleEventToggle = (eventId: string | number) => {
    const numericId = typeof eventId === 'string' ? parseInt(eventId) : eventId
    setCurrentFilter(prev => ({
      ...prev,
      eventIds: prev.eventIds.includes(numericId)
        ? prev.eventIds.filter(id => id !== numericId)
        : [...prev.eventIds, numericId],
    }))
  }

  const toggleAllEvents = () => {
    if (currentFilter.eventIds.length === availableEvents.length) {
      setCurrentFilter(prev => ({ ...prev, eventIds: [] }))
    } else {
      setCurrentFilter(prev => ({
        ...prev,
        eventIds: availableEvents.map(e => typeof e.id === 'string' ? parseInt(e.id) : e.id)
      }))
    }
  }

  const handleAddCombination = () => {
    if (!currentFilter.groupId) return

    const group = groups.find(g => String(g.id) === currentFilter.groupId)
    const selectedEvents = availableEvents.filter(e => {
      const eventId = typeof e.id === 'string' ? parseInt(e.id) : e.id
      return currentFilter.eventIds.includes(eventId)
    })

    addFilterCombination({
      groupId: currentFilter.groupId,
      groupName: group?.name,
      eventIds: currentFilter.eventIds.length > 0
        ? currentFilter.eventIds
        : availableEvents.map(e => typeof e.id === 'string' ? parseInt(e.id) : e.id),
      eventNames: currentFilter.eventIds.length > 0
        ? selectedEvents.map(e => e.name)
        : ['Todos los eventos'],
      clasificaciones: currentFilter.clasificaciones,
    })

    // Reset form
    setCurrentFilter({
      groupId: null,
      eventIds: [],
      clasificaciones: undefined,
    })
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Layers className="h-5 w-5" />
          Constructor de Combinaciones
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Group selector */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              1. Selecciona un Grupo de Eventos
            </label>
            <GroupSelector
              groups={groups}
              selectedGroupId={currentFilter.groupId}
              onGroupChange={handleGroupChange}
              loading={groupsLoading}
              error={groupsError}
            />
          </div>

          {/* Event selector */}
          {currentFilter.groupId && availableEvents.length > 0 && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-gray-700">
                  2. Selecciona Eventos Específicos (opcional)
                </label>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={toggleAllEvents}
                >
                  {currentFilter.eventIds.length === availableEvents.length ? (
                    <>
                      <X className="h-3 w-3 mr-1" />
                      Deseleccionar todos
                    </>
                  ) : (
                    <>
                      <Check className="h-3 w-3 mr-1" />
                      Seleccionar todos
                    </>
                  )}
                </Button>
              </div>
              <div className="border border-gray-200 rounded-lg p-3 max-h-48 overflow-y-auto bg-white">
                <div className="grid grid-cols-2 gap-2">
                  {availableEvents.map((event) => (
                    <label
                      key={event.id}
                      className="flex items-center gap-2 p-2 hover:bg-gray-50 rounded cursor-pointer"
                    >
                      <input
                        type="checkbox"
                        checked={currentFilter.eventIds.includes(typeof event.id === 'string' ? parseInt(event.id) : event.id)}
                        onChange={() => handleEventToggle(event.id)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="text-sm text-gray-700">{event.name}</span>
                    </label>
                  ))}
                </div>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Si no seleccionas ninguno, se incluirán todos los eventos del grupo
              </p>
            </div>
          )}

          {/* Classification selector */}
          {currentFilter.groupId && (
            <div>
              <label className="text-sm font-medium text-gray-700 block mb-2">
                3. Selecciona Clasificaciones (opcional)
              </label>
              <ClassificationSelector
                selectedClassifications={currentFilter.clasificaciones || []}
                onClassificationChange={(classifications) =>
                  setCurrentFilter({
                    ...currentFilter,
                    clasificaciones: classifications,
                  })
                }
                placeholder="Todas las clasificaciones"
              />
              <p className="text-xs text-gray-500 mt-1">
                Filtrar por estado epidemiológico
              </p>
            </div>
          )}

          {/* Add button */}
          {currentFilter.groupId && (
            <div className="flex justify-end">
              <Button
                onClick={handleAddCombination}
                className="bg-blue-600 hover:bg-blue-700"
              >
                <Plus className="h-4 w-4 mr-2" />
                Agregar Combinación
              </Button>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}