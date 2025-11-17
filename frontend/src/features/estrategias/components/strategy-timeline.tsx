"use client"

import React, { useMemo } from 'react'
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import { AlertTriangle, Check, Clock } from "lucide-react"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"

export interface Strategy {
  id: number
  name: string
  valid_from: string
  valid_until: string | null
  active: boolean
  created_by?: string | null
  classification_rules_count?: number | null
  usa_provincia_carga?: boolean
  provincia_field?: string
}

interface StrategyTimelineProps {
  strategies: Strategy[]
  className?: string
}

interface TimelineSegment {
  strategy: Strategy
  startPercent: number
  widthPercent: number
  isActive: boolean
  isPast: boolean
  isFuture: boolean
}

export function StrategyTimeline({ strategies, className }: StrategyTimelineProps) {
  const { segments, timeRange, hasGaps, hasOverlaps } = useMemo(() => {
    if (!strategies || strategies.length === 0) {
      return { segments: [], timeRange: { start: new Date(), end: new Date() }, hasGaps: false, hasOverlaps: false }
    }

    // Ordenar por fecha de inicio
    const sortedStrategies = [...strategies].sort((a, b) =>
      new Date(a.valid_from).getTime() - new Date(b.valid_from).getTime()
    )

    // Calcular rango de tiempo para el timeline
    const now = new Date()
    const allDates = sortedStrategies.flatMap(s => [
      new Date(s.valid_from),
      s.valid_until ? new Date(s.valid_until) : new Date(now.getTime() + 365 * 24 * 60 * 60 * 1000) // +1 año si no tiene fin
    ])

    const minDate = new Date(Math.min(...allDates.map(d => d.getTime())))
    const maxDate = new Date(Math.max(...allDates.map(d => d.getTime()), now.getTime()))

    // Agregar margen de 10% a cada lado
    const timeSpan = maxDate.getTime() - minDate.getTime()
    const margin = timeSpan * 0.1
    const start = new Date(minDate.getTime() - margin)
    const end = new Date(maxDate.getTime() + margin)
    const totalSpan = end.getTime() - start.getTime()

    // Calcular segmentos
    const segments: TimelineSegment[] = sortedStrategies.map(strategy => {
      const stratStart = new Date(strategy.valid_from).getTime()
      const stratEnd = strategy.valid_until
        ? new Date(strategy.valid_until).getTime()
        : end.getTime() // Si no tiene fin, va hasta el final del timeline

      const startPercent = ((stratStart - start.getTime()) / totalSpan) * 100
      const endPercent = ((stratEnd - start.getTime()) / totalSpan) * 100
      const widthPercent = endPercent - startPercent

      const nowTime = now.getTime()
      const isActive = stratStart <= nowTime && (stratEnd >= nowTime || !strategy.valid_until)
      const isPast = stratEnd < nowTime
      const isFuture = stratStart > nowTime

      return {
        strategy,
        startPercent,
        widthPercent,
        isActive,
        isPast,
        isFuture,
      }
    })

    // Detectar gaps y overlaps
    let hasGaps = false
    let hasOverlaps = false

    for (let i = 0; i < sortedStrategies.length - 1; i++) {
      const current = sortedStrategies[i]
      const next = sortedStrategies[i + 1]

      const currentEnd = current.valid_until ? new Date(current.valid_until) : null
      const nextStart = new Date(next.valid_from)

      if (currentEnd) {
        const gap = nextStart.getTime() - currentEnd.getTime()
        if (gap > 24 * 60 * 60 * 1000) { // Gap > 1 día
          hasGaps = true
        } else if (gap < 0) { // Solapamiento
          hasOverlaps = true
        }
      }
    }

    // Calcular posición de "hoy"
    const nowPercent = ((now.getTime() - start.getTime()) / totalSpan) * 100

    return {
      segments,
      timeRange: { start, end, nowPercent },
      hasGaps,
      hasOverlaps
    }
  }, [strategies])

  if (segments.length === 0) {
    return (
      <div className={cn("rounded-lg border border-dashed border-muted-foreground/25 p-8 text-center", className)}>
        <p className="text-sm text-muted-foreground">
          No hay estrategias para mostrar en el timeline
        </p>
      </div>
    )
  }

  const formatDate = (date: Date) => {
    return date.toLocaleDateString('es-ES', {
      month: 'short',
      year: 'numeric'
    })
  }

  const getYearMarkers = () => {
    const markers = []
    const start = timeRange.start
    const end = timeRange.end
    const currentYear = start.getFullYear()
    const endYear = end.getFullYear()

    for (let year = currentYear; year <= endYear; year++) {
      const yearStart = new Date(year, 0, 1).getTime()
      const percent = ((yearStart - start.getTime()) / (end.getTime() - start.getTime())) * 100

      if (percent >= 0 && percent <= 100) {
        markers.push({ year, percent })
      }
    }

    return markers
  }

  return (
    <TooltipProvider>
      <div className={cn("space-y-3", className)}>
        {/* Warnings */}
        {(hasGaps || hasOverlaps) && (
          <div className="flex items-center gap-2 text-sm">
            {hasGaps && (
              <Badge variant="outline" className="text-amber-600 border-amber-600/50 bg-amber-50/50 dark:bg-amber-950/20">
                <AlertTriangle className="mr-1 h-3 w-3" />
                Gaps detectados
              </Badge>
            )}
            {hasOverlaps && (
              <Badge variant="outline" className="text-destructive border-destructive/50 bg-destructive/5">
                <AlertTriangle className="mr-1 h-3 w-3" />
                Solapamientos
              </Badge>
            )}
          </div>
        )}

        {/* Timeline */}
        <div className="space-y-2">
          {/* Year markers */}
          <div className="relative h-6 text-xs text-muted-foreground">
            {getYearMarkers().map(({ year, percent }) => (
              <div
                key={year}
                className="absolute top-0 flex flex-col items-start"
                style={{ left: `${percent}%` }}
              >
                <div className="h-2 w-px bg-border" />
                <span className="ml-1">{year}</span>
              </div>
            ))}
          </div>

          {/* Timeline bar */}
          <div className="relative h-16 rounded-md border bg-muted/20">
            {/* Segments */}
            {segments.map(({ strategy, startPercent, widthPercent, isActive, isPast, isFuture }) => (
              <Tooltip key={strategy.id}>
                <TooltipTrigger asChild>
                  <div
                    className={cn(
                      "absolute top-2 h-12 rounded cursor-pointer transition-all hover:z-10 hover:scale-105",
                      "border-2 overflow-hidden",
                      isActive && "border-green-500 bg-green-500/80 shadow-lg shadow-green-500/20",
                      isPast && "border-gray-400 bg-gray-400/60",
                      isFuture && "border-blue-400 bg-blue-400/40 border-dashed"
                    )}
                    style={{
                      left: `${startPercent}%`,
                      width: `${widthPercent}%`,
                      minWidth: '60px'
                    }}
                  >
                    <div className="flex h-full items-center justify-center px-2">
                      <div className="truncate text-xs font-medium text-white drop-shadow-sm">
                        {strategy.name}
                      </div>
                    </div>
                  </div>
                </TooltipTrigger>
                <TooltipContent className="max-w-xs">
                  <div className="space-y-2">
                    <div className="font-semibold">{strategy.name}</div>
                    <div className="space-y-1 text-xs">
                      <div className="flex items-center gap-2">
                        <span className="text-muted-foreground">Desde:</span>
                        <span>{formatDate(new Date(strategy.valid_from))}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-muted-foreground">Hasta:</span>
                        <span>
                          {strategy.valid_until
                            ? formatDate(new Date(strategy.valid_until))
                            : "∞ Sin fin"
                          }
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-muted-foreground">Estado:</span>
                        <Badge
                          variant={isActive ? "default" : isPast ? "secondary" : "outline"}
                          className="h-5"
                        >
                          {isActive && <Check className="mr-1 h-3 w-3" />}
                          {isFuture && <Clock className="mr-1 h-3 w-3" />}
                          {isActive ? "Activa" : isPast ? "Finalizada" : "Programada"}
                        </Badge>
                      </div>
                      {strategy.classification_rules_count !== undefined && (
                        <div className="flex items-center gap-2">
                          <span className="text-muted-foreground">Reglas:</span>
                          <span>{strategy.classification_rules_count}</span>
                        </div>
                      )}
                      {strategy.created_by && (
                        <div className="flex items-center gap-2">
                          <span className="text-muted-foreground">Creada por:</span>
                          <span>{strategy.created_by}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </TooltipContent>
              </Tooltip>
            ))}

            {/* Indicador de "hoy" */}
            <div
              className="absolute top-0 bottom-0 w-px bg-primary z-20"
              style={{ left: `${timeRange.nowPercent}%` }}
            >
              <div className="absolute -top-1 -left-1.5 h-3 w-3 rounded-full bg-primary border-2 border-background" />
              <div className="absolute -bottom-6 -left-6 text-xs font-medium text-primary whitespace-nowrap">
                Hoy
              </div>
            </div>
          </div>

          {/* Legend */}
          <div className="flex items-center gap-4 text-xs text-muted-foreground pt-2">
            <div className="flex items-center gap-1.5">
              <div className="h-3 w-6 rounded border-2 border-green-500 bg-green-500/80" />
              <span>Activa</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="h-3 w-6 rounded border-2 border-gray-400 bg-gray-400/60" />
              <span>Finalizada</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="h-3 w-6 rounded border-2 border-dashed border-blue-400 bg-blue-400/40" />
              <span>Programada</span>
            </div>
          </div>
        </div>
      </div>
    </TooltipProvider>
  )
}
