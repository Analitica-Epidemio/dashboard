/**
 * Editing Indicator Component
 * Muestra un badge visual cuando estás editando una combinación
 */

import React from 'react'
import { Badge } from '@/components/ui/badge'
import { Pencil } from 'lucide-react'

interface EditingIndicatorProps {
  combinationNumber: number
}

export function EditingIndicator({ combinationNumber }: EditingIndicatorProps) {
  return (
    <Badge className="bg-blue-100 text-blue-800 border-blue-300 text-xs font-semibold px-3 py-1 flex items-center gap-1.5 animate-pulse">
      <Pencil className="h-3 w-3" />
      Editando Combinación #{combinationNumber}
    </Badge>
  )
}
