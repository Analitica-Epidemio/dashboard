'use client'

import React, { useState } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { ChevronLeft, ChevronRight, Check, Sparkles, BarChart3, Filter, Layers } from 'lucide-react'
import { UnifiedFilterSelector } from "./unified-filter-selector"
import { ClassificationSelector, TipoClasificacion } from "@/components/selectors/classification-selector"
import type { Group, Event } from '@/lib/types/eventos'

interface FilterWizardProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  groups: Group[]
  allEvents: Event[]
  onComplete: (config: WizardResult) => void
}

export interface WizardResult {
  selectedGroups: string[]
  selectedEvents: string[]
  selectedClassifications: TipoClasificacion[]
  label?: string
}

const STEPS = [
  {
    id: 'welcome',
    title: 'Bienvenido al Dashboard de Reportes',
    description: 'Configura tus filtros en 3 simples pasos'
  },
  {
    id: 'selection',
    title: 'Selecciona Eventos o Grupos',
    description: 'Puedes elegir múltiples grupos y/o eventos individuales'
  },
  {
    id: 'classification',
    title: 'Filtra por Clasificación',
    description: 'Opcional: filtra por estado epidemiológico'
  },
  {
    id: 'summary',
    title: '¡Listo!',
    description: 'Revisa tu configuración'
  }
]

export function FilterWizard({ open, onOpenChange, groups, allEvents, onComplete }: FilterWizardProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const [config, setConfig] = useState<WizardResult>({
    selectedGroups: [],
    selectedEvents: [],
    selectedClassifications: [],
    label: ''
  })

  const progress = ((currentStep + 1) / STEPS.length) * 100

  const handleNext = () => {
    if (currentStep < STEPS.length - 1) {
      setCurrentStep(currentStep + 1)
    } else {
      onComplete(config)
      onOpenChange(false)
      resetWizard()
    }
  }

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
    }
  }

  const resetWizard = () => {
    setCurrentStep(0)
    setConfig({
      selectedGroups: [],
      selectedEvents: [],
      selectedClassifications: [],
      label: ''
    })
  }

  const canProceed = () => {
    switch (currentStep) {
      case 0: // Welcome
        return true
      case 1: // Selection
        return config.selectedGroups.length > 0 || config.selectedEvents.length > 0
      case 2: // Classification
        return true // Optional
      case 3: // Summary
        return true
      default:
        return false
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-2 mb-2">
            <Sparkles className="h-5 w-5 text-primary" />
            <DialogTitle>{STEPS[currentStep].title}</DialogTitle>
          </div>
          <DialogDescription>{STEPS[currentStep].description}</DialogDescription>
        </DialogHeader>

        {/* Progress bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>Paso {currentStep + 1} de {STEPS.length}</span>
            <span>{Math.round(progress)}%</span>
          </div>
          <Progress value={progress} className="h-2" />
        </div>

        {/* Step content */}
        <div className="min-h-[300px] py-6">
          {currentStep === 0 && (
            <div className="space-y-6">
              <div className="text-center space-y-4">
                <div className="inline-flex p-4 rounded-full bg-primary/10">
                  <BarChart3 className="h-12 w-12 text-primary" />
                </div>
                <h3 className="text-lg font-semibold">
                  Compara eventos epidemiológicos fácilmente
                </h3>
                <p className="text-muted-foreground max-w-lg mx-auto">
                  Este asistente te ayudará a configurar filtros personalizados para visualizar
                  y comparar datos epidemiológicos de manera clara y efectiva.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
                <div className="p-4 border rounded-lg space-y-2">
                  <div className="flex items-center gap-2">
                    <div className="p-2 rounded bg-blue-100 dark:bg-blue-900">
                      <Filter className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                    </div>
                    <h4 className="font-medium">Flexible</h4>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Selecciona múltiples grupos o eventos individuales
                  </p>
                </div>

                <div className="p-4 border rounded-lg space-y-2">
                  <div className="flex items-center gap-2">
                    <div className="p-2 rounded bg-green-100 dark:bg-green-900">
                      <Layers className="h-4 w-4 text-green-600 dark:text-green-400" />
                    </div>
                    <h4 className="font-medium">Comparativo</h4>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Compara hasta 6 filtros diferentes en un solo gráfico
                  </p>
                </div>

                <div className="p-4 border rounded-lg space-y-2">
                  <div className="flex items-center gap-2">
                    <div className="p-2 rounded bg-purple-100 dark:bg-purple-900">
                      <BarChart3 className="h-4 w-4 text-purple-600 dark:text-purple-400" />
                    </div>
                    <h4 className="font-medium">Visual</h4>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Gráficos interactivos con datos en tiempo real
                  </p>
                </div>
              </div>
            </div>
          )}

          {currentStep === 1 && (
            <div className="space-y-4">
              <div className="bg-blue-50 dark:bg-blue-950/20 p-4 rounded-lg border border-blue-200 dark:border-blue-900">
                <p className="text-sm text-blue-900 dark:text-blue-100">
                  💡 <strong>Tip:</strong> Puedes seleccionar múltiples grupos para comparar,
                  o eventos individuales si quieres un control más específico.
                  Por ejemplo, si quieres ver Dengue de todos los grupos a los que pertenece.
                </p>
              </div>

              <UnifiedFilterSelector
                groups={groups}
                allEvents={allEvents}
                onSelectionChange={(selection) => {
                  setConfig({
                    ...config,
                    selectedGroups: selection.groups,
                    selectedEvents: selection.events
                  })
                }}
                placeholder="Buscar y seleccionar grupos o eventos..."
              />

              {(config.selectedGroups.length > 0 || config.selectedEvents.length > 0) && (
                <div className="bg-green-50 dark:bg-green-950/20 p-4 rounded-lg border border-green-200 dark:border-green-900">
                  <p className="text-sm text-green-900 dark:text-green-100">
                    ✓ Seleccionaste {config.selectedGroups.length} grupo(s) y {config.selectedEvents.length} evento(s)
                  </p>
                </div>
              )}
            </div>
          )}

          {currentStep === 2 && (
            <div className="space-y-4">
              <div className="bg-amber-50 dark:bg-amber-950/20 p-4 rounded-lg border border-amber-200 dark:border-amber-900">
                <p className="text-sm text-amber-900 dark:text-amber-100">
                  ℹ️ <strong>Opcional:</strong> Si no seleccionas ninguna clasificación,
                  se incluirán todos los estados epidemiológicos.
                </p>
              </div>

              <ClassificationSelector
                selectedClassifications={config.selectedClassifications}
                onClassificationChange={(classifications) => {
                  setConfig({
                    ...config,
                    selectedClassifications: classifications
                  })
                }}
                placeholder="Todas las clasificaciones"
              />

              <div className="text-sm text-muted-foreground">
                Puedes filtrar por: confirmados, sospechosos, probables, en estudio, etc.
              </div>
            </div>
          )}

          {currentStep === 3 && (
            <div className="space-y-6">
              <div className="text-center space-y-2">
                <div className="inline-flex p-3 rounded-full bg-green-100 dark:bg-green-900">
                  <Check className="h-8 w-8 text-green-600 dark:text-green-400" />
                </div>
                <h3 className="text-lg font-semibold">Configuración completa</h3>
                <p className="text-muted-foreground">
                  Revisa tu selección antes de continuar
                </p>
              </div>

              <div className="border rounded-lg p-4 space-y-4">
                <div>
                  <h4 className="font-medium mb-2">Grupos seleccionados</h4>
                  {config.selectedGroups.length === 0 ? (
                    <p className="text-sm text-muted-foreground">Ninguno</p>
                  ) : (
                    <div className="flex flex-wrap gap-2">
                      {config.selectedGroups.map(groupId => {
                        const group = groups.find(g => String(g.id) === groupId)
                        return group ? (
                          <span key={groupId} className="text-sm bg-blue-100 dark:bg-blue-900 px-2 py-1 rounded">
                            {group.name}
                          </span>
                        ) : null
                      })}
                    </div>
                  )}
                </div>

                <div>
                  <h4 className="font-medium mb-2">Eventos individuales</h4>
                  {config.selectedEvents.length === 0 ? (
                    <p className="text-sm text-muted-foreground">Ninguno</p>
                  ) : (
                    <div className="flex flex-wrap gap-2">
                      {config.selectedEvents.map(eventId => {
                        const event = allEvents.find(e => String(e.id) === eventId)
                        return event ? (
                          <span key={eventId} className="text-sm bg-green-100 dark:bg-green-900 px-2 py-1 rounded">
                            {event.name}
                          </span>
                        ) : null
                      })}
                    </div>
                  )}
                </div>

                <div>
                  <h4 className="font-medium mb-2">Clasificaciones</h4>
                  {config.selectedClassifications.length === 0 ? (
                    <p className="text-sm text-muted-foreground">Todas</p>
                  ) : (
                    <div className="flex flex-wrap gap-2">
                      {config.selectedClassifications.map(classification => (
                        <span key={classification} className="text-sm bg-purple-100 dark:bg-purple-900 px-2 py-1 rounded capitalize">
                          {classification}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>

        <DialogFooter className="flex justify-between items-center">
          <div className="flex gap-2">
            {currentStep > 0 && (
              <Button
                variant="outline"
                onClick={handleBack}
              >
                <ChevronLeft className="h-4 w-4 mr-2" />
                Atrás
              </Button>
            )}
          </div>

          <div className="flex gap-2">
            {currentStep < STEPS.length - 1 ? (
              <Button
                onClick={handleNext}
                disabled={!canProceed()}
              >
                Siguiente
                <ChevronRight className="h-4 w-4 ml-2" />
              </Button>
            ) : (
              <Button
                onClick={handleNext}
                className="bg-green-600 hover:bg-green-700"
              >
                <Check className="h-4 w-4 mr-2" />
                Finalizar
              </Button>
            )}
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
