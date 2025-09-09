'use client'

import { Combobox, ComboboxOption } from '@/components/ui/combobox'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { AlertCircle } from 'lucide-react'
import type { Group } from '../types'

interface GroupSelectorProps {
  groups: Group[]
  selectedGroupId: string | null
  onGroupChange: (groupId: string | null) => void
  loading?: boolean
  error?: Error | null
}

export function GroupSelector({ 
  groups, 
  selectedGroupId, 
  onGroupChange, 
  loading, 
  error 
}: GroupSelectorProps) {
  if (loading) {
    return (
      <div className="space-y-2">
        <label className="text-sm font-medium">Seleccionar Grupo</label>
        <Skeleton className="w-[300px] h-9" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-2">
        <label className="text-sm font-medium">Seleccionar Grupo</label>
        <Alert variant="destructive" className="w-[300px]">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {error.message || 'Error al cargar grupos'}
          </AlertDescription>
        </Alert>
      </div>
    )
  }

  // Convert groups to combobox options
  const options: ComboboxOption[] = groups.map(group => ({
    value: group.id,
    label: group.name
  }))

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium">Seleccionar Grupo</label>
      <Combobox
        options={options}
        value={selectedGroupId || undefined}
        onValueChange={(value) => onGroupChange(value || null)}
        placeholder="Buscar o seleccionar grupo..."
        searchPlaceholder="Buscar grupo de eventos..."
        emptyMessage="No se encontraron grupos"
        className="w-full"
      />
    </div>
  )
}