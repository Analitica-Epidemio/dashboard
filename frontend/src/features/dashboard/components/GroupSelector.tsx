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

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium">Seleccionar Grupo</label>
      <Select 
        value={selectedGroupId || ''} 
        onValueChange={(value) => onGroupChange(value || null)}
      >
        <SelectTrigger className="w-[300px]">
          <SelectValue placeholder="Selecciona un grupo..." />
        </SelectTrigger>
        <SelectContent>
          {groups.map((group) => (
            <SelectItem key={group.id} value={group.id}>
              {group.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}