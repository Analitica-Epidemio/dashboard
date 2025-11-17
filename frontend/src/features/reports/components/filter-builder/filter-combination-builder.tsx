'use client'

import React, { useState, useEffect, useMemo, useRef } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Plus, Layers, Check, X, Save, XCircle } from 'lucide-react'
import { GroupSelector } from "../selectors/group-selector"
import { ClassificationSelector, TipoClasificacion } from "../selectors/classification-selector"
import { useFilterContext } from "@/features/reports/contexts/filter-context"
import type { Event } from '@/features/dashboard/types'

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
    availableEvents: eventsByGroup,
    eventsLoading,
    addFilterCombination,
    editingCombinationId,
    getEditingCombination,
    updateFilterCombination,
    cancelEditing,
    setDraftFilter,
    setSelectedGroup,
  } = useFilterContext()

  const [currentFilter, setCurrentFilter] = useState<CurrentFilter>({
    groupId: null,
    eventIds: [],
    label: '',
  })

  const prevDraftRef = useRef<string | null>(null)

  // Los eventos disponibles vienen del contexto, filtrados por el hook useEventsByGroup
  const availableEvents = eventsByGroup || []

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
      setSelectedGroup(editingCombination.groupId)
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
      setSelectedGroup(null)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [editingCombinationId])

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
    // Actualizar el grupo seleccionado en el contexto para que filtre los eventos
    setSelectedGroup(groupId)
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
          {currentFilter.groupId && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-gray-700">
                  2. Selecciona Eventos Específicos (opcional)
                </label>
                {availableEvents.length > 0 && (
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
                )}
              </div>

              {eventsLoading ? (
                <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                  <div className="flex items-center justify-center gap-2 text-gray-500">
                    <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <span className="text-sm">Cargando eventos...</span>
                  </div>
                </div>
              ) : availableEvents.length > 0 ? (
                <>
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
                </>
              ) : (
                <div className="border border-amber-200 rounded-lg p-4 bg-amber-50">
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-amber-600" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="flex-1">
                      <h4 className="text-sm font-medium text-amber-800 mb-1">
                        No hay eventos asociados a este grupo
                      </h4>
                      <p className="text-xs text-amber-700">
                        Este grupo no tiene tipos de eventos configurados en la base de datos.
                        Puedes continuar creando el filtro y se incluirá el grupo completo cuando se agreguen eventos.
                      </p>
                    </div>
                  </div>
                </div>
              )}
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