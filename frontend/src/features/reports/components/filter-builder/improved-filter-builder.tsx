'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import {
  Plus,
  Wand2,
  X,
  Edit2,
  Copy,
  Trash2,
  Sparkles,
  Info
} from 'lucide-react'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { FilterWizard, type WizardResult } from "./filter-wizard"
import { UnifiedFilterSelector } from "./unified-filter-selector"
import { ClassificationSelector, TipoClasificacion } from "@/components/selectors/classification-selector"
import { useFilterContext } from "@/features/reports/contexts/filter-context"

const COMBINATION_COLORS = [
  'bg-blue-500',
  'bg-green-500',
  'bg-purple-500',
  'bg-orange-500',
  'bg-pink-500',
  'bg-cyan-500',
]

export function ImprovedFilterBuilder() {
  const {
    groups,
    groupsLoading,
    allEvents,
    filterCombinations,
    addFilterCombination,
    removeFilterCombination,
    duplicateFilterCombination,
    startEditingCombination,
    editingCombinationId,
    getEditingCombination,
    updateFilterCombination,
    cancelEditing,
  } = useFilterContext()

  const [showWizard, setShowWizard] = useState(false)
  const [showQuickAdd, setShowQuickAdd] = useState(false)
  const [quickAddConfig, setQuickAddConfig] = useState({
    groups: [] as string[],
    events: [] as string[],
    classifications: [] as TipoClasificacion[],
    label: ''
  })

  // Mostrar wizard automáticamente si no hay filtros
  useEffect(() => {
    const hasSeenWizard = localStorage.getItem('hasSeenFilterWizard')
    if (!hasSeenWizard && filterCombinations.length === 0) {
      setShowWizard(true)
    }
  }, [filterCombinations.length])

  const handleWizardComplete = (config: WizardResult) => {
    localStorage.setItem('hasSeenWizard', 'true')

    // Convertir a formato de FilterCombination
    const combination = {
      groupId: config.selectedGroups[0] || null, // Por compatibilidad, tomamos el primero
      groupName: config.selectedGroups[0]
        ? groups.find(g => String(g.id) === config.selectedGroups[0])?.name
        : undefined,
      eventIds: config.selectedEvents.map(id => parseInt(id)),
      eventNames: config.selectedEvents.map(id => {
        const event = allEvents.find(e => String(e.id) === id)
        return event?.name || ''
      }),
      clasificaciones: config.selectedClassifications,
      label: config.label || 'Nuevo filtro'
    }

    addFilterCombination(combination)
  }

  const handleQuickAdd = () => {
    if (quickAddConfig.groups.length === 0 && quickAddConfig.events.length === 0) {
      return
    }

    const combination = {
      groupId: quickAddConfig.groups[0] || null,
      groupName: quickAddConfig.groups[0]
        ? groups.find(g => String(g.id) === quickAddConfig.groups[0])?.name
        : undefined,
      eventIds: quickAddConfig.events.map(id => parseInt(id)),
      eventNames: quickAddConfig.events.map(id => {
        const event = allEvents.find(e => String(e.id) === id)
        return event?.name || ''
      }),
      clasificaciones: quickAddConfig.classifications,
      label: quickAddConfig.label || 'Filtro sin nombre'
    }

    addFilterCombination(combination)
    setShowQuickAdd(false)
    setQuickAddConfig({
      groups: [],
      events: [],
      classifications: [],
      label: ''
    })
  }

  const getColorForIndex = (index: number) => {
    return COMBINATION_COLORS[index % COMBINATION_COLORS.length]
  }

  return (
    <TooltipProvider>
      <div className="space-y-4">
        {/* Header con botones principales */}
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <h2 className="text-2xl font-bold tracking-tight">Filtros de Comparación</h2>
            <p className="text-sm text-muted-foreground">
              Configura múltiples filtros para comparar datos epidemiológicos
            </p>
          </div>

          <div className="flex gap-2">
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowWizard(true)}
                >
                  <Wand2 className="h-4 w-4 mr-2" />
                  Asistente
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                Configuración guiada paso a paso
              </TooltipContent>
            </Tooltip>

            <Button
              size="sm"
              onClick={() => setShowQuickAdd(!showQuickAdd)}
              disabled={filterCombinations.length >= 6}
            >
              <Plus className="h-4 w-4 mr-2" />
              Agregar Filtro
            </Button>
          </div>
        </div>

        {/* Info sobre límite de filtros */}
        {filterCombinations.length === 0 && (
          <Alert>
            <Info className="h-4 w-4" />
            <AlertDescription>
              <strong>¿Primera vez aquí?</strong> Usa el <button
                onClick={() => setShowWizard(true)}
                className="underline font-medium hover:text-primary"
              >
                Asistente
              </button> para configurar tus filtros de manera guiada.
              Puedes comparar hasta 6 filtros simultáneamente.
            </AlertDescription>
          </Alert>
        )}

        {filterCombinations.length >= 6 && (
          <Alert variant="destructive">
            <AlertDescription>
              Has alcanzado el límite de 6 filtros. Elimina alguno para agregar más.
            </AlertDescription>
          </Alert>
        )}

        {/* Formulario de agregar rápido */}
        {showQuickAdd && (
          <Card className="border-2 border-primary">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Plus className="h-5 w-5" />
                Agregar Nuevo Filtro
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">
                  Selecciona Grupos o Eventos
                </label>
                <UnifiedFilterSelector
                  groups={groups}
                  allEvents={allEvents}
                  loading={groupsLoading}
                  onSelectionChange={(selection) => {
                    setQuickAddConfig({
                      ...quickAddConfig,
                      groups: selection.groups,
                      events: selection.events
                    })
                  }}
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">
                  Clasificaciones (opcional)
                </label>
                <ClassificationSelector
                  selectedClassifications={quickAddConfig.classifications}
                  onClassificationChange={(classifications) => {
                    setQuickAddConfig({
                      ...quickAddConfig,
                      classifications
                    })
                  }}
                  placeholder="Todas las clasificaciones"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">
                  Etiqueta personalizada
                </label>
                <Input
                  placeholder="Ej: Casos Confirmados Q1 2024"
                  value={quickAddConfig.label}
                  onChange={(e) => setQuickAddConfig({
                    ...quickAddConfig,
                    label: e.target.value
                  })}
                />
              </div>

              <div className="flex gap-2 justify-end">
                <Button
                  variant="outline"
                  onClick={() => setShowQuickAdd(false)}
                >
                  Cancelar
                </Button>
                <Button
                  onClick={handleQuickAdd}
                  disabled={quickAddConfig.groups.length === 0 && quickAddConfig.events.length === 0}
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Agregar
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Lista de filtros activos */}
        {filterCombinations.length > 0 && (
          <div className="space-y-3">
            <h3 className="text-sm font-medium text-muted-foreground">
              Filtros Activos ({filterCombinations.length}/6)
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {filterCombinations.map((combination, index) => {
                const colorClass = getColorForIndex(index)

                return (
                  <Card key={combination.id} className="relative overflow-hidden">
                    <div className={`absolute top-0 left-0 w-1 h-full ${colorClass}`} />

                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1 min-w-0">
                          <CardTitle className="text-sm font-medium truncate">
                            {combination.label || combination.groupName || 'Sin nombre'}
                          </CardTitle>
                          {combination.groupName && combination.label !== combination.groupName && (
                            <p className="text-xs text-muted-foreground truncate mt-1">
                              {combination.groupName}
                            </p>
                          )}
                        </div>

                        <div className="flex gap-1">
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-7 w-7 p-0"
                                onClick={() => duplicateFilterCombination(combination.id)}
                              >
                                <Copy className="h-3 w-3" />
                              </Button>
                            </TooltipTrigger>
                            <TooltipContent>Duplicar</TooltipContent>
                          </Tooltip>

                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-7 w-7 p-0"
                                onClick={() => removeFilterCombination(combination.id)}
                              >
                                <Trash2 className="h-3 w-3" />
                              </Button>
                            </TooltipTrigger>
                            <TooltipContent>Eliminar</TooltipContent>
                          </Tooltip>
                        </div>
                      </div>
                    </CardHeader>

                    <CardContent className="space-y-2">
                      {/* Eventos */}
                      <div>
                        <p className="text-xs font-medium text-muted-foreground mb-1">
                          Eventos:
                        </p>
                        <div className="flex flex-wrap gap-1">
                          {combination.eventNames && combination.eventNames.length > 0 ? (
                            combination.eventNames.slice(0, 2).map((name, i) => (
                              <Badge key={i} variant="secondary" className="text-xs">
                                {name}
                              </Badge>
                            ))
                          ) : (
                            <Badge variant="secondary" className="text-xs">
                              Todos
                            </Badge>
                          )}
                          {combination.eventNames && combination.eventNames.length > 2 && (
                            <Badge variant="secondary" className="text-xs">
                              +{combination.eventNames.length - 2}
                            </Badge>
                          )}
                        </div>
                      </div>

                      {/* Clasificaciones */}
                      {combination.clasificaciones && combination.clasificaciones.length > 0 && (
                        <div>
                          <p className="text-xs font-medium text-muted-foreground mb-1">
                            Clasificaciones:
                          </p>
                          <div className="flex flex-wrap gap-1">
                            {combination.clasificaciones.slice(0, 2).map((cls, i) => (
                              <Badge key={i} variant="outline" className="text-xs capitalize">
                                {cls}
                              </Badge>
                            ))}
                            {combination.clasificaciones.length > 2 && (
                              <Badge variant="outline" className="text-xs">
                                +{combination.clasificaciones.length - 2}
                              </Badge>
                            )}
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          </div>
        )}

        {/* Wizard */}
        <FilterWizard
          open={showWizard}
          onOpenChange={setShowWizard}
          groups={groups}
          allEvents={allEvents}
          onComplete={handleWizardComplete}
        />
      </div>
    </TooltipProvider>
  )
}
