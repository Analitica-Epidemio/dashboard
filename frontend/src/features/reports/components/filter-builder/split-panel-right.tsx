'use client'

import React from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Play, Filter, Pencil, Copy, X } from 'lucide-react'
import { useFilterContext } from "@/features/reports/contexts/filter-context"
import { ClassificationBadges, TipoClasificacion } from "@/components/selectors/classification-selector"

export function SplitPanelRight() {
  const {
    filterCombinations,
    editingCombinationId,
    setIsComparisonView,
    removeFilterCombination,
    duplicateFilterCombination,
    startEditingCombination,
  } = useFilterContext()

  const handleApply = () => {
    setIsComparisonView(true)
  }

  return (
    <div className="h-full flex flex-col">
      {/* Combinations List - scrollable */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-gray-600" />
            <h3 className="font-semibold text-gray-900">
              Combinaciones ({filterCombinations.length})
            </h3>
          </div>
        </div>

        {filterCombinations.length === 0 ? (
          <div className="text-center py-12">
            <Filter className="h-12 w-12 text-gray-400 mx-auto mb-3" />
            <p className="text-sm text-gray-500">No hay combinaciones</p>
            <p className="text-xs text-gray-400 mt-1">
              Agrega al menos una para continuar
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {filterCombinations.map((combination, index) => (
              <CombinationCard
                key={combination.id}
                combination={combination}
                index={index}
                isEditing={editingCombinationId === combination.id}
                onEdit={() => startEditingCombination(combination.id)}
                onDuplicate={() => duplicateFilterCombination(combination.id)}
                onRemove={() => removeFilterCombination(combination.id)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Apply Button - sticky bottom */}
      {filterCombinations.length > 0 && (
        <div className="p-6 border-t bg-white">
          <Button
            className="w-full bg-green-600 hover:bg-green-700"
            size="lg"
            onClick={handleApply}
          >
            <Play className="h-4 w-4 mr-2" />
            Aplicar y Analizar ({filterCombinations.length})
          </Button>
        </div>
      )}
    </div>
  )
}

interface CombinationCardProps {
  combination: {
    id: string
    groupId: string | null
    groupName?: string
    eventIds: number[]
    eventNames?: string[]
    clasificaciones?: TipoClasificacion[]
    label?: string
    color?: string
  }
  index: number
  isEditing: boolean
  onEdit: () => void
  onDuplicate: () => void
  onRemove: () => void
}

function CombinationCard({ combination, index, isEditing, onEdit, onDuplicate, onRemove }: CombinationCardProps) {
  return (
    <div className={`border rounded-lg p-3 transition-all ${
      isEditing
        ? 'bg-blue-50 border-blue-400 shadow-md ring-2 ring-blue-200'
        : 'bg-white hover:shadow-sm border-gray-200'
    }`}>
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-start gap-2 flex-1">
          <Badge
            variant="outline"
            className={`text-xs font-semibold mt-0.5 ${
              isEditing ? 'bg-blue-600 text-white border-blue-600' : ''
            }`}
          >
            #{index + 1}
          </Badge>
          <div className="flex-1 min-w-0">
            {combination.label && (
              <div className="text-xs font-semibold text-blue-700 mb-1 truncate">
                {combination.label}
              </div>
            )}
            <div className="text-sm font-medium text-gray-900 truncate">
              {combination.groupName}
            </div>
            <div className="text-xs text-gray-500 mt-0.5">
              {combination.eventIds.length === 0
                ? 'Todos los eventos'
                : combination.eventIds.length === 1
                ? '1 evento'
                : `${combination.eventIds.length} eventos`}
            </div>
          </div>
        </div>
      </div>

      {/* Classifications */}
      {combination.clasificaciones && combination.clasificaciones.length > 0 && (
        <div className="mb-2">
          <ClassificationBadges classifications={combination.clasificaciones} />
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-1 pt-2 border-t">
        <Button
          size="sm"
          variant="ghost"
          className="h-7 text-xs hover:text-blue-600"
          onClick={onEdit}
        >
          <Pencil className="h-3 w-3 mr-1" />
          Editar
        </Button>
        <Button
          size="sm"
          variant="ghost"
          className="h-7 text-xs"
          onClick={onDuplicate}
        >
          <Copy className="h-3 w-3 mr-1" />
          Duplicar
        </Button>
        <Button
          size="sm"
          variant="ghost"
          className="h-7 text-xs hover:text-red-600"
          onClick={onRemove}
        >
          <X className="h-3 w-3 mr-1" />
          Eliminar
        </Button>
      </div>
    </div>
  )
}
