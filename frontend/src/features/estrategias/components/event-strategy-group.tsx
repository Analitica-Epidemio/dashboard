"use client"

import React, { useState } from 'react'
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import {
  ChevronDown,
  ChevronRight,
  Plus,
  Eye,
  Edit,
  Copy,
  TestTube,
  Trash2,
  AlertTriangle,
  CheckCircle2,
  Clock,
  MoreVertical,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { StrategyTimeline } from "./strategy-timeline"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import type { EventStrategy } from '@/features/estrategias/api'

interface EventStrategyGroupProps {
  tipoEnoId: number
  tipoEnoName: string
  strategies: EventStrategy[]
  onView: (strategy: EventStrategy) => void
  onEdit: (strategy: EventStrategy) => void
  onDuplicate: (strategy: EventStrategy) => void
  onTest: (strategy: EventStrategy) => void
  onDelete: (strategy: EventStrategy) => void
  onCreateNew: (tipoEnoId: number) => void
}

export function EventStrategyGroup({
  tipoEnoId,
  tipoEnoName,
  strategies,
  onView,
  onEdit,
  onDuplicate,
  onTest,
  onDelete,
  onCreateNew,
}: EventStrategyGroupProps) {
  const [isExpanded, setIsExpanded] = useState(true)

  // Ordenar estrategias por fecha
  const sortedStrategies = [...strategies].sort((a, b) => {
    const dateA = new Date(a.valid_from || 0)
    const dateB = new Date(b.valid_from || 0)
    return dateB.getTime() - dateA.getTime()
  })

  // Calcular estadísticas
  const activeCount = strategies.filter(s => s.active).length
  const totalRules = strategies.reduce((sum, s) => sum + (s.classification_rules_count || 0), 0)

  const now = new Date()
  const activeStrategy = strategies.find(s => {
    const from = new Date(s.valid_from || 0)
    const until = s.valid_until ? new Date(s.valid_until) : null
    return from <= now && (!until || until > now) && s.active
  })

  // Detectar problemas
  const hasGaps = checkForGaps(strategies)
  const hasOverlaps = checkForOverlaps(strategies)
  const hasNoActive = activeCount === 0 && strategies.length > 0

  const formatDate = (dateStr: string | undefined) => {
    if (!dateStr) return 'N/A'
    return new Date(dateStr).toLocaleDateString('es-ES', {
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    })
  }

  const formatRelativeTime = (dateStr: string | undefined) => {
    if (!dateStr) return 'N/A'
    const date = new Date(dateStr)
    const now = new Date()
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60))

    if (diffInHours < 1) return "Hace menos de 1 hora"
    if (diffInHours < 24) return `Hace ${diffInHours} horas`
    if (diffInHours < 48) return "Ayer"
    if (diffInHours < 168) return `Hace ${Math.floor(diffInHours / 24)} días`
    return formatDate(dateStr)
  }

  return (
    <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
      <Card className="overflow-hidden">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CollapsibleTrigger asChild>
              <Button variant="ghost" className="-ml-2 flex items-center gap-2 hover:bg-transparent p-0">
                {isExpanded ? (
                  <ChevronDown className="h-5 w-5 text-muted-foreground" />
                ) : (
                  <ChevronRight className="h-5 w-5 text-muted-foreground" />
                )}
                <div className="flex items-center gap-3">
                  <h3 className="text-lg font-semibold">{tipoEnoName}</h3>
                  <Badge variant="outline" className="font-normal">
                    ID: {tipoEnoId}
                  </Badge>
                  {activeStrategy && (
                    <Badge className="bg-green-500/10 text-green-700 border-green-500/20 hover:bg-green-500/20">
                      <CheckCircle2 className="mr-1 h-3 w-3" />
                      Activa
                    </Badge>
                  )}
                  {hasNoActive && (
                    <Badge variant="outline" className="text-amber-600 border-amber-600/50 bg-amber-50/50 dark:bg-amber-950/20">
                      <AlertTriangle className="mr-1 h-3 w-3" />
                      Sin activa
                    </Badge>
                  )}
                </div>
              </Button>
            </CollapsibleTrigger>

            <div className="flex items-center gap-2">
              <div className="text-sm text-muted-foreground">
                {strategies.length} {strategies.length === 1 ? 'estrategia' : 'estrategias'}
              </div>
              <Separator orientation="vertical" className="h-6" />
              <Button
                size="sm"
                onClick={() => onCreateNew(tipoEnoId)}
                className="gap-2"
              >
                <Plus className="h-4 w-4" />
                Nueva
              </Button>
            </div>
          </div>

          {/* Quick stats cuando está colapsado */}
          {!isExpanded && (
            <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
              <div className="flex items-center gap-1">
                <span>{totalRules} reglas totales</span>
              </div>
              {hasGaps && (
                <Badge variant="outline" className="text-amber-600 border-amber-600/50">
                  <AlertTriangle className="mr-1 h-3 w-3" />
                  Gaps
                </Badge>
              )}
              {hasOverlaps && (
                <Badge variant="outline" className="text-destructive border-destructive/50">
                  <AlertTriangle className="mr-1 h-3 w-3" />
                  Solapamientos
                </Badge>
              )}
            </div>
          )}
        </CardHeader>

        <CollapsibleContent>
          <CardContent className="space-y-4 pb-6">
            {/* Timeline */}
            {strategies.length > 0 && (
              <>
                <div>
                  <div className="mb-2 flex items-center gap-2">
                    <Clock className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm font-medium">Timeline de Vigencia</span>
                  </div>
                  <StrategyTimeline
                    strategies={strategies.map(s => ({
                      id: s.id,
                      name: s.name,
                      valid_from: s.valid_from || new Date().toISOString(),
                      valid_until: s.valid_until || null,
                      active: s.active || false,
                      created_by: s.created_by,
                      classification_rules_count: s.classification_rules_count,
                    }))}
                  />
                </div>

                <Separator />
              </>
            )}

            {/* Lista de estrategias */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-medium">
                  Estrategias ({strategies.length})
                </h4>
              </div>

              {strategies.length === 0 ? (
                <div className="rounded-lg border border-dashed border-muted-foreground/25 p-8 text-center">
                  <div className="space-y-3">
                    <div className="mx-auto w-12 h-12 rounded-full bg-muted flex items-center justify-center">
                      <AlertTriangle className="h-6 w-6 text-muted-foreground" />
                    </div>
                    <div className="space-y-1">
                      <p className="font-medium">No hay estrategias configuradas</p>
                      <p className="text-sm text-muted-foreground">
                        Los eventos de este tipo no se clasificarán automáticamente
                      </p>
                    </div>
                    <Button onClick={() => onCreateNew(tipoEnoId)} size="sm">
                      <Plus className="mr-2 h-4 w-4" />
                      Crear primera estrategia
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="space-y-2">
                  {sortedStrategies.map((strategy) => {
                    const isCurrentlyActive = strategy.id === activeStrategy?.id
                    const from = new Date(strategy.valid_from || 0)
                    const until = strategy.valid_until ? new Date(strategy.valid_until) : null
                    const isPast = until && until < now
                    const isFuture = from > now

                    return (
                      <div
                        key={strategy.id}
                        className={cn(
                          "group rounded-lg border p-4 transition-all hover:shadow-md",
                          isCurrentlyActive && "border-green-500/50 bg-green-50/30 dark:bg-green-950/10"
                        )}
                      >
                        <div className="flex items-start justify-between gap-4">
                          {/* Info principal */}
                          <div className="flex-1 space-y-2">
                            <div className="flex items-center gap-2">
                              <h5 className="font-medium">{strategy.name}</h5>
                              {isCurrentlyActive && (
                                <Badge className="bg-green-500 text-white">
                                  ● Activa Ahora
                                </Badge>
                              )}
                              {isPast && (
                                <Badge variant="secondary">
                                  Finalizada
                                </Badge>
                              )}
                              {isFuture && (
                                <Badge variant="outline" className="border-blue-500/50 bg-blue-50/50 text-blue-700">
                                  <Clock className="mr-1 h-3 w-3" />
                                  Programada
                                </Badge>
                              )}
                            </div>

                            {/* Detalles */}
                            <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-sm">
                              <div className="flex items-center gap-2 text-muted-foreground">
                                <span className="font-medium">Vigencia:</span>
                                <span>
                                  {formatDate(strategy.valid_from)} - {strategy.valid_until ? formatDate(strategy.valid_until) : "∞"}
                                </span>
                              </div>
                              <div className="flex items-center gap-2 text-muted-foreground">
                                <span className="font-medium">Reglas:</span>
                                <span>{strategy.classification_rules_count || 0}</span>
                              </div>
                              <div className="flex items-center gap-2 text-muted-foreground">
                                <span className="font-medium">Actualizada:</span>
                                <span>{formatRelativeTime(strategy.updated_at)}</span>
                              </div>
                              <div className="flex items-center gap-2 text-muted-foreground">
                                <span className="font-medium">Por:</span>
                                <span>{strategy.created_by || 'Sistema'}</span>
                              </div>
                            </div>
                          </div>

                          {/* Acciones */}
                          <div className="flex items-center gap-1">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => onView(strategy)}
                              className="opacity-0 group-hover:opacity-100 transition-opacity"
                            >
                              <Eye className="h-4 w-4 mr-2" />
                              Ver
                            </Button>
                            <Button
                              variant="default"
                              size="sm"
                              onClick={() => onEdit(strategy)}
                            >
                              <Edit className="h-4 w-4 mr-2" />
                              Editar
                            </Button>
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="opacity-0 group-hover:opacity-100 transition-opacity"
                                >
                                  <MoreVertical className="h-4 w-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end" className="w-48">
                                <DropdownMenuItem onClick={() => onDuplicate(strategy)}>
                                  <Copy className="mr-2 h-4 w-4" />
                                  Duplicar
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => onTest(strategy)}>
                                  <TestTube className="mr-2 h-4 w-4" />
                                  Probar con datos
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem
                                  className="text-destructive focus:text-destructive"
                                  onClick={() => onDelete(strategy)}
                                >
                                  <Trash2 className="mr-2 h-4 w-4" />
                                  Eliminar
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          </CardContent>
        </CollapsibleContent>
      </Card>
    </Collapsible>
  )
}

// Funciones auxiliares
function checkForGaps(strategies: EventStrategy[]): boolean {
  if (strategies.length < 2) return false

  const sorted = [...strategies].sort((a, b) =>
    new Date(a.valid_from || 0).getTime() - new Date(b.valid_from || 0).getTime()
  )

  for (let i = 0; i < sorted.length - 1; i++) {
    const current = sorted[i]
    const next = sorted[i + 1]

    const currentEnd = current.valid_until ? new Date(current.valid_until) : null
    const nextStart = new Date(next.valid_from || 0)

    if (currentEnd) {
      const gap = nextStart.getTime() - currentEnd.getTime()
      if (gap > 24 * 60 * 60 * 1000) {
        return true
      }
    }
  }

  return false
}

function checkForOverlaps(strategies: EventStrategy[]): boolean {
  if (strategies.length < 2) return false

  const sorted = [...strategies].sort((a, b) =>
    new Date(a.valid_from || 0).getTime() - new Date(b.valid_from || 0).getTime()
  )

  for (let i = 0; i < sorted.length - 1; i++) {
    const current = sorted[i]
    const next = sorted[i + 1]

    const currentEnd = current.valid_until ? new Date(current.valid_until) : null
    const nextStart = new Date(next.valid_from || 0)

    if (currentEnd) {
      const gap = nextStart.getTime() - currentEnd.getTime()
      if (gap < 0) {
        return true
      }
    }
  }

  return false
}
