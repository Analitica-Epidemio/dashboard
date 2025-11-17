'use client'

import React, { useState, useMemo } from 'react'
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from '@/components/ui/command'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Check, ChevronsUpDown, Folder, FileText, X } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { Group, Event } from '@/features/dashboard/types'

interface Selection {
  groups: string[]  // IDs de grupos seleccionados
  events: string[]  // IDs de eventos individuales seleccionados
}

interface UnifiedFilterSelectorProps {
  groups: Group[]
  allEvents: Event[]
  loading?: boolean
  onSelectionChange: (selection: Selection) => void
  placeholder?: string
}

export function UnifiedFilterSelector({
  groups,
  allEvents,
  loading = false,
  onSelectionChange,
  placeholder = "Buscar grupos o eventos..."
}: UnifiedFilterSelectorProps) {
  const [open, setOpen] = useState(false)
  const [selection, setSelection] = useState<Selection>({
    groups: [],
    events: []
  })

  // Agrupar eventos por grupo para mostrar en la búsqueda
  const eventsByGroup = useMemo(() => {
    const grouped = new Map<string, Event[]>()

    allEvents.forEach(event => {
      if (event.groupId) {
        if (!grouped.has(event.groupId)) {
          grouped.set(event.groupId, [])
        }
        grouped.get(event.groupId)!.push(event)
      } else {
        // Eventos sin grupo
        if (!grouped.has('sin_grupo')) {
          grouped.set('sin_grupo', [])
        }
        grouped.get('sin_grupo')!.push(event)
      }
    })

    return grouped
  }, [allEvents])

  // Items seleccionados para mostrar como chips
  const selectedItems = useMemo(() => {
    const items: Array<{ id: string, name: string, type: 'group' | 'event' }> = []

    // Agregar grupos seleccionados
    selection.groups.forEach(groupId => {
      const group = groups.find(g => String(g.id) === groupId)
      if (group) {
        items.push({ id: groupId, name: group.name, type: 'group' })
      }
    })

    // Agregar eventos seleccionados
    selection.events.forEach(eventId => {
      const event = allEvents.find(e => String(e.id) === eventId)
      if (event) {
        items.push({ id: eventId, name: event.name, type: 'event' })
      }
    })

    return items
  }, [selection, groups, allEvents])

  const toggleGroup = (groupId: string) => {
    const newSelection = {
      ...selection,
      groups: selection.groups.includes(groupId)
        ? selection.groups.filter(id => id !== groupId)
        : [...selection.groups, groupId]
    }
    setSelection(newSelection)
    onSelectionChange(newSelection)
  }

  const toggleEvent = (eventId: string) => {
    const newSelection = {
      ...selection,
      events: selection.events.includes(eventId)
        ? selection.events.filter(id => id !== eventId)
        : [...selection.events, eventId]
    }
    setSelection(newSelection)
    onSelectionChange(newSelection)
  }

  const removeItem = (id: string, type: 'group' | 'event') => {
    if (type === 'group') {
      toggleGroup(id)
    } else {
      toggleEvent(id)
    }
  }

  const clearAll = () => {
    const newSelection = { groups: [], events: [] }
    setSelection(newSelection)
    onSelectionChange(newSelection)
  }

  return (
    <div className="space-y-3">
      {/* Selector con búsqueda */}
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            role="combobox"
            aria-expanded={open}
            className="w-full justify-between h-auto min-h-[2.5rem] py-2"
            disabled={loading}
          >
            {selectedItems.length === 0 ? (
              <span className="text-muted-foreground">{placeholder}</span>
            ) : (
              <div className="flex flex-wrap gap-1">
                {selectedItems.slice(0, 3).map(item => (
                  <Badge
                    key={`${item.type}-${item.id}`}
                    variant="secondary"
                    className="gap-1"
                  >
                    {item.type === 'group' ? (
                      <Folder className="h-3 w-3" />
                    ) : (
                      <FileText className="h-3 w-3" />
                    )}
                    {item.name}
                  </Badge>
                ))}
                {selectedItems.length > 3 && (
                  <Badge variant="secondary">
                    +{selectedItems.length - 3} más
                  </Badge>
                )}
              </div>
            )}
            <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-[500px] p-0" align="start">
          <Command>
            <CommandInput placeholder="Buscar grupos o eventos..." />
            <CommandEmpty>No se encontraron resultados</CommandEmpty>
            <CommandList className="max-h-[400px]">
              {/* Grupos */}
              <CommandGroup heading="Grupos de Eventos">
                {groups.map(group => {
                  const isSelected = selection.groups.includes(String(group.id))
                  const eventsCount = eventsByGroup.get(String(group.id))?.length || 0

                  return (
                    <CommandItem
                      key={`group-${group.id}`}
                      onSelect={() => toggleGroup(String(group.id))}
                      className="cursor-pointer"
                    >
                      <div className="flex items-center justify-between w-full">
                        <div className="flex items-center gap-2">
                          <Check
                            className={cn(
                              "h-4 w-4",
                              isSelected ? "opacity-100" : "opacity-0"
                            )}
                          />
                          <Folder className="h-4 w-4 text-blue-600" />
                          <span>{group.name}</span>
                        </div>
                        <Badge variant="outline" className="text-xs">
                          {eventsCount} {eventsCount === 1 ? 'evento' : 'eventos'}
                        </Badge>
                      </div>
                    </CommandItem>
                  )
                })}
              </CommandGroup>

              {/* Eventos individuales */}
              <CommandGroup heading="Eventos Individuales">
                {allEvents.slice(0, 50).map(event => {
                  const isSelected = selection.events.includes(String(event.id))
                  const groupName = event.groupName || 'Sin grupo'

                  return (
                    <CommandItem
                      key={`event-${event.id}`}
                      onSelect={() => toggleEvent(String(event.id))}
                      className="cursor-pointer"
                    >
                      <div className="flex items-center justify-between w-full">
                        <div className="flex items-center gap-2">
                          <Check
                            className={cn(
                              "h-4 w-4",
                              isSelected ? "opacity-100" : "opacity-0"
                            )}
                          />
                          <FileText className="h-4 w-4 text-green-600" />
                          <div className="flex flex-col">
                            <span className="text-sm">{event.name}</span>
                            <span className="text-xs text-muted-foreground">{groupName}</span>
                          </div>
                        </div>
                      </div>
                    </CommandItem>
                  )
                })}
              </CommandGroup>
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>

      {/* Chips de selección */}
      {selectedItems.length > 0 && (
        <div className="flex flex-wrap gap-2 p-3 bg-muted/50 rounded-lg border">
          <div className="flex items-center gap-2 w-full">
            <span className="text-xs font-medium text-muted-foreground">
              Seleccionados ({selectedItems.length}):
            </span>
            <Button
              variant="ghost"
              size="sm"
              onClick={clearAll}
              className="h-6 text-xs ml-auto"
            >
              Limpiar todo
            </Button>
          </div>

          <div className="flex flex-wrap gap-2 w-full">
            {selectedItems.map(item => (
              <Badge
                key={`chip-${item.type}-${item.id}`}
                variant={item.type === 'group' ? 'default' : 'secondary'}
                className="gap-2 pr-1"
              >
                {item.type === 'group' ? (
                  <Folder className="h-3 w-3" />
                ) : (
                  <FileText className="h-3 w-3" />
                )}
                <span>{item.name}</span>
                <button
                  onClick={() => removeItem(item.id, item.type)}
                  className="ml-1 ring-offset-background rounded-full outline-none hover:bg-accent hover:text-accent-foreground"
                >
                  <X className="h-3 w-3" />
                </button>
              </Badge>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
