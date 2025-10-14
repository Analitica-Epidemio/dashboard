'use client'

import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Filter, Trash2, Copy, X, Play, Pencil } from 'lucide-react'
import { ClassificationBadges, TipoClasificacion } from '../selectors/ClassificationSelector'
import { useFilterContext } from '../../contexts/FilterContext'

interface FilterCombinationsListProps {
  onApplyFilters?: () => void
}

export function FilterCombinationsList({ onApplyFilters }: FilterCombinationsListProps) {
  const {
    filterCombinations,
    clearFilterCombinations,
    setIsComparisonView,
  } = useFilterContext()

  const handleApply = () => {
    setIsComparisonView(true)
    onApplyFilters?.()
  }

  return (
    <Card className="sticky top-8">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Combinaciones ({filterCombinations.length})
          </CardTitle>
          {filterCombinations.length > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={clearFilterCombinations}
              className="text-red-600 hover:text-red-700"
            >
              <Trash2 className="h-3 w-3 mr-1" />
              Limpiar
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="max-h-[500px] overflow-y-auto">
        {filterCombinations.length === 0 ? (
          <EmptyState />
        ) : (
          <>
            <CombinationsList />
            <ApplyButton onClick={handleApply} />
          </>
        )}
      </CardContent>
    </Card>
  )
}

function EmptyState() {
  return (
    <div className="text-center py-12">
      <Filter className="h-12 w-12 text-gray-400 mx-auto mb-3" />
      <p className="text-gray-500">No hay combinaciones agregadas</p>
      <p className="text-sm text-gray-400 mt-1">
        Agrega al menos una para continuar
      </p>
    </div>
  )
}

function CombinationsList() {
  const {
    filterCombinations,
    removeFilterCombination,
    duplicateFilterCombination,
    startEditingCombination,
  } = useFilterContext()

  return (
    <div className="space-y-2">
      {filterCombinations.map((combination, index) => (
        <CombinationItem
          key={combination.id}
          combination={combination}
          index={index}
          onEdit={() => startEditingCombination(combination.id)}
          onDuplicate={() => duplicateFilterCombination(combination.id)}
          onRemove={() => removeFilterCombination(combination.id)}
        />
      ))}
    </div>
  )
}

interface CombinationItemProps {
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
  onEdit: () => void
  onDuplicate: () => void
  onRemove: () => void
}

function CombinationItem({ combination, index, onEdit, onDuplicate, onRemove }: CombinationItemProps) {
  return (
    <div className="border rounded-lg p-3 bg-white hover:shadow-sm transition-shadow">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 flex-1">
          <Badge variant="outline" className="text-xs font-semibold">
            {index + 1}
          </Badge>
          <div className="flex-1">
            {combination.label && (
              <div className="text-xs font-semibold text-blue-700 mb-0.5">
                {combination.label}
              </div>
            )}
            <span className="text-sm font-medium text-gray-900">
              {combination.groupName}
            </span>
            <span className="text-xs text-gray-500 ml-2">
              {combination.eventIds.length === 0
                ? 'Todos los eventos'
                : combination.eventIds.length === 1
                ? '1 evento'
                : `${combination.eventIds.length} eventos`}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <Button
            size="icon"
            variant="ghost"
            className="h-6 w-6 hover:text-blue-600"
            onClick={onEdit}
            title="Editar"
          >
            <Pencil className="h-3 w-3" />
          </Button>
          <Button
            size="icon"
            variant="ghost"
            className="h-6 w-6"
            onClick={onDuplicate}
            title="Duplicar"
          >
            <Copy className="h-3 w-3" />
          </Button>
          <Button
            size="icon"
            variant="ghost"
            className="h-6 w-6 hover:text-red-600"
            onClick={onRemove}
            title="Eliminar"
          >
            <X className="h-3 w-3" />
          </Button>
        </div>
      </div>

      {/* Event names preview */}
      {combination.eventNames &&
        combination.eventNames.length > 0 &&
        combination.eventNames[0] !== 'Todos los eventos' && (
          <div className="mt-2 flex flex-wrap gap-1">
            {combination.eventNames.slice(0, 3).map((name: string, i: number) => (
              <span key={i} className="text-xs text-gray-600">
                {name}
                {i < Math.min(2, combination.eventNames!.length - 1) && ','}
              </span>
            ))}
            {combination.eventNames.length > 3 && (
              <span className="text-xs text-gray-500">
                +{combination.eventNames.length - 3} más
              </span>
            )}
          </div>
        )}

      {/* Classifications */}
      {combination.clasificaciones && combination.clasificaciones.length > 0 && (
        <div className="mt-2">
          <ClassificationBadges classifications={combination.clasificaciones} />
        </div>
      )}
    </div>
  )
}

function ApplyButton({ onClick }: { onClick: () => void }) {
  const { filterCombinations } = useFilterContext()

  return (
    <div className="mt-6">
      <Button className="w-full bg-green-600 hover:bg-green-700" size="lg" onClick={onClick}>
        <Play className="h-4 w-4 mr-2" />
        Aplicar y Analizar ({filterCombinations.length}{' '}
        {filterCombinations.length === 1 ? 'combinación' : 'combinaciones'})
      </Button>
    </div>
  )
}