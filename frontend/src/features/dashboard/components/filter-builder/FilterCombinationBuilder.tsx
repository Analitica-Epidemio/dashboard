'use client'

import React, { useState, useEffect, useMemo, useRef } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Plus, Layers, Check, X, Save, XCircle } from 'lucide-react'
import { GroupSelector } from '../selectors/GroupSelector'
import { ClassificationSelector, TipoClasificacion } from '../selectors/ClassificationSelector'
import { useFilterContext } from '../../contexts/FilterContext'
import type { Event } from '../../types'

interface CurrentFilter {
  groupId: string | null
  eventIds: number[]
  clasificaciones?: TipoClasificacion[]
  label?: string
}

export function FilterCombinationBuilder() {
  const {
    groups,
    groupsLoading,
    groupsError,
    allEvents,
    addFilterCombination,
    editingCombinationId,
    getEditingCombination,
    updateFilterCombination,
    cancelEditing,
    setDraftFilter,
  } = useFilterContext()

  const [currentFilter, setCurrentFilter] = useState<CurrentFilter>({
    groupId: null,
    eventIds: [],
    label: '',
  })

  const [availableEvents, setAvailableEvents] = useState<Event[]>([])
  const prevDraftRef = useRef<string | null>(null)

  // Cargar datos cuando entramos en modo de edición
  useEffect(() => {
    const editingCombination = getEditingCombination()
    if (editingCombination) {
      const filterToEdit = {
        groupId: editingCombination.groupId,
        eventIds: editingCombination.eventIds,
        clasificaciones: editingCombination.clasificaciones,
        label: editingCombination.label || '',
      }
      setCurrentFilter(filterToEdit)
      setDraftFilter({
        groupId: editingCombination.groupId,
        groupName: editingCombination.groupName,
        eventIds: editingCombination.eventIds,
        eventNames: editingCombination.eventNames,
        clasificaciones: editingCombination.clasificaciones,
        label: editingCombination.label,
      })
    } else {
      // Si no estamos editando, limpiar el draft
      setDraftFilter(null)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [editingCombinationId])

  useEffect(() => {
    if (currentFilter.groupId) {
      const groupEvents = allEvents.filter(e => e.groupId === currentFilter.groupId)
      setAvailableEvents(groupEvents)
    } else {
      setAvailableEvents([])
    }
  }, [currentFilter.groupId, allEvents])

  // Calcular draft filter con useMemo (no causa re-renders)
  const computedDraftFilter = useMemo(() => {
    if (!currentFilter.groupId) return null

    const group = groups.find(g => String(g.id) === currentFilter.groupId)
    const selectedEvents = availableEvents.filter(e => {
      const eventId = typeof e.id === 'string' ? parseInt(e.id) : e.id
      return currentFilter.eventIds.includes(eventId)
    })

    return {
      groupId: currentFilter.groupId,
      groupName: group?.name,
      eventIds: currentFilter.eventIds,
      eventNames:
        currentFilter.eventIds.length > 0
          ? selectedEvents.map(e => e.name)
          : undefined,
      clasificaciones: currentFilter.clasificaciones,
      label: currentFilter.label,
    }
  }, [currentFilter, groups, availableEvents])

  // Sincronizar el draft computado con el estado (solo cuando realmente cambia)
  useEffect(() => {
    const draftString = JSON.stringify(computedDraftFilter)

    // Solo actualizar si realmente cambió
    if (prevDraftRef.current !== draftString) {
      prevDraftRef.current = draftString
      setDraftFilter(computedDraftFilter)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [computedDraftFilter])

  const handleGroupChange = (groupId: string | null) => {
    setCurrentFilter({
      groupId,
      eventIds: [],
      clasificaciones: undefined,
      label: '',
    })
  }

  const handleEventToggle = (eventId: string | number) => {
    const numericId = typeof eventId === 'string' ? parseInt(eventId) : eventId
    setCurrentFilter({
      ...currentFilter,
      eventIds: currentFilter.eventIds.includes(numericId)
        ? currentFilter.eventIds.filter(id => id !== numericId)
        : [...currentFilter.eventIds, numericId],
    })
  }

  const toggleAllEvents = () => {
    setCurrentFilter(currentFilter.eventIds.length === availableEvents.length
      ? { ...currentFilter, eventIds: [] }
      : {
          ...currentFilter,
          eventIds: availableEvents.map(e => typeof e.id === 'string' ? parseInt(e.id) : e.id)
        }
    )
  }

  const handleSaveCombination = () => {
    if (!currentFilter.groupId) return

    const group = groups.find(g => String(g.id) === currentFilter.groupId)
    const selectedEvents = availableEvents.filter(e => {
      const eventId = typeof e.id === 'string' ? parseInt(e.id) : e.id
      return currentFilter.eventIds.includes(eventId)
    })

    const combinationData = {
      groupId: currentFilter.groupId,
      groupName: group?.name,
      eventIds: currentFilter.eventIds.length > 0
        ? currentFilter.eventIds
        : availableEvents.map(e => typeof e.id === 'string' ? parseInt(e.id) : e.id),
      eventNames: currentFilter.eventIds.length > 0
        ? selectedEvents.map(e => e.name)
        : ['Todos los eventos'],
      clasificaciones: currentFilter.clasificaciones,
      label: currentFilter.label,
    }

    // Modo edición o creación
    if (editingCombinationId) {
      updateFilterCombination(editingCombinationId, combinationData)
    } else {
      addFilterCombination(combinationData)
    }

    // Reset form
    resetForm()
  }

  const handleCancel = () => {
    cancelEditing()
    resetForm()
  }

  const resetForm = () => {
    const emptyFilter = {
      groupId: null,
      eventIds: [],
      clasificaciones: undefined,
      label: '',
    }
    setCurrentFilter(emptyFilter)
    setDraftFilter(null)
  }

  const isEditing = !!editingCombinationId

  return (
      <Card>
        <CardHeader>
          <div>
            <CardTitle className="flex items-center gap-2">
              <Layers className="h-5 w-5" />
              {isEditing ? 'Editar Combinación' : 'Agregar Combinación'}
            </CardTitle>
            <p className="text-sm text-gray-500 mt-1">
              {isEditing ? 'Modifica los filtros de la combinación seleccionada' : 'Define grupos, eventos y clasificaciones para comparar'}
            </p>
          </div>
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
                onClassificationChange={(classifications) => {
                  setCurrentFilter({
                    ...currentFilter,
                    clasificaciones: classifications,
                  })
                }}
                placeholder="Todas las clasificaciones"
              />
              <p className="text-xs text-gray-500 mt-1">
                Filtrar por estado epidemiológico
              </p>
            </div>
          )}

          {/* Label personalizable */}
          {currentFilter.groupId && (
            <div>
              <label className="text-sm font-medium text-gray-700 block mb-2">
                4. Etiqueta Personalizada (opcional)
              </label>
              <Input
                type="text"
                placeholder="Ej: Casos Graves, Seguimiento Especial, etc."
                value={currentFilter.label || ''}
                onChange={(e) => {
                  setCurrentFilter({
                    ...currentFilter,
                    label: e.target.value,
                  })
                }}
                className="w-full"
              />
              <p className="text-xs text-gray-500 mt-1">
                Dale un nombre descriptivo a esta combinación
              </p>
            </div>
          )}

          {/* Buttons */}
          {currentFilter.groupId && (
            <div className="flex gap-2 justify-end">
              {isEditing && (
                <Button
                  onClick={handleCancel}
                  variant="outline"
                  className="border-gray-300"
                >
                  <XCircle className="h-4 w-4 mr-2" />
                  Cancelar
                </Button>
              )}
              <Button
                onClick={handleSaveCombination}
                className={isEditing ? 'bg-green-600 hover:bg-green-700' : 'bg-blue-600 hover:bg-blue-700'}
              >
                {isEditing ? (
                  <>
                    <Save className="h-4 w-4 mr-2" />
                    Actualizar
                  </>
                ) : (
                  <>
                    <Plus className="h-4 w-4 mr-2" />
                    Agregar
                  </>
                )}
              </Button>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}