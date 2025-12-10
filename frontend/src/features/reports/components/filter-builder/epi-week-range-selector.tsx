'use client'

import React, { useState, useEffect, useRef } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Calendar, CalendarRange } from 'lucide-react'
import { format } from 'date-fns'
import { es } from 'date-fns/locale'
import EpiCalendar from './epiweek-selector'
import { getEpiWeek, epiWeekToDates } from './epiweek-utils'
import { useFilterContext } from "@/features/reports/contexts/filter-context"

interface EpiWeekRange {
  year: number;
  week: number;
  startDate: Date;
  endDate: Date;
}

export function EpiWeekRangeSelector() {
  const { dateRange, setDateRange } = useFilterContext()

  const [epiStart, setEpiStart] = useState<EpiWeekRange | null>(null)
  const [epiEnd, setEpiEnd] = useState<EpiWeekRange | null>(null)
  const initializedRef = useRef(false)

  // Initialize with current values if they exist (only once)
  useEffect(() => {
    if (initializedRef.current) return
    initializedRef.current = true

    if (dateRange.from) {
      const startWeek = getEpiWeek(dateRange.from)
      const dates = epiWeekToDates(startWeek.year, startWeek.week)
      setEpiStart({
        year: startWeek.year,
        week: startWeek.week,
        startDate: dates.start,
        endDate: dates.end
      })
    }
    if (dateRange.to) {
      const endWeek = getEpiWeek(dateRange.to)
      const dates = epiWeekToDates(endWeek.year, endWeek.week)
      setEpiEnd({
        year: endWeek.year,
        week: endWeek.week,
        startDate: dates.start,
        endDate: dates.end
      })
    }
  }, [dateRange.from, dateRange.to])

  // Update date range when epi weeks change
  useEffect(() => {
    if (epiStart && epiEnd) {
      setDateRange({
        from: epiStart.startDate,
        to: epiEnd.endDate
      })
    }
  }, [epiStart, epiEnd, setDateRange])

  const handleStartWeekSelect = (date: Date) => {
    const weekInfo = getEpiWeek(date)
    const weekDates = epiWeekToDates(weekInfo.year, weekInfo.week)
    const newWeek: EpiWeekRange = {
      year: weekInfo.year,
      week: weekInfo.week,
      startDate: weekDates.start,
      endDate: weekDates.end
    }

    setEpiStart(newWeek)

    // If end week is before the new start week, clear it
    if (epiEnd && newWeek.startDate > epiEnd.startDate) {
      setEpiEnd(null)
    }
  }

  const handleEndWeekSelect = (date: Date) => {
    const weekInfo = getEpiWeek(date)
    const weekDates = epiWeekToDates(weekInfo.year, weekInfo.week)
    const newWeek: EpiWeekRange = {
      year: weekInfo.year,
      week: weekInfo.week,
      startDate: weekDates.start,
      endDate: weekDates.end
    }

    // Only set if there's a start week selected and the new week is after or equal to it
    if (epiStart && newWeek.startDate >= epiStart.startDate) {
      setEpiEnd(newWeek)
    } else if (!epiStart) {
      // If no start week is selected yet, just set it
      setEpiEnd(newWeek)
    }
  }

  const clearSelection = () => {
    setEpiStart(null)
    setEpiEnd(null)
    setDateRange({ from: null, to: null })
  }

  const formatEpiWeek = (week: EpiWeekRange) => {
    return `SE ${week.week}/${week.year}`
  }

  const formatDateRange = (start: Date, end: Date) => {
    return `${format(start, 'd MMM', { locale: es })} - ${format(end, 'd MMM yyyy', { locale: es })}`
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Período de Análisis
            </CardTitle>
            <p className="text-sm text-gray-500 mt-1">
              Aplica a todas las combinaciones de filtros
            </p>
          </div>
          {(epiStart || epiEnd) && (
            <Button
              variant="ghost"
              size="sm"
              onClick={clearSelection}
              className="text-gray-500 hover:text-gray-700"
            >
              Limpiar
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Selected Range Display */}
        {(epiStart || epiEnd) && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <div className="flex items-center gap-2 flex-wrap">
              {epiStart && (
                <Badge variant="secondary" className="px-3 py-1">
                  <CalendarRange className="h-3 w-3 mr-1" />
                  Desde: {formatEpiWeek(epiStart)}
                </Badge>
              )}
              {epiEnd && (
                <Badge variant="secondary" className="px-3 py-1">
                  <CalendarRange className="h-3 w-3 mr-1" />
                  Hasta: {formatEpiWeek(epiEnd)}
                </Badge>
              )}
            </div>
            {epiStart && epiEnd && (
              <div className="mt-2 text-xs text-gray-600">
                {formatDateRange(epiStart.startDate, epiEnd.endDate)}
              </div>
            )}
          </div>
        )}

        {/* Calendar Components - Side by Side */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Start Week Selector */}
          <div className="border rounded-lg overflow-hidden bg-card">
            <h3 className="text-sm font-semibold text-foreground p-4 text-center border-b bg-muted/30">
              Semana Inicial
            </h3>
            <div className="p-4">
              <EpiCalendar
                onWeekSelect={handleStartWeekSelect}
                selectedStart={epiStart}
                selectedEnd={epiEnd}
                selectingEnd={false}
              />
            </div>
          </div>

          {/* End Week Selector */}
          <div className="border rounded-lg overflow-hidden bg-card">
            <h3 className="text-sm font-semibold text-foreground p-4 text-center border-b bg-muted/30">
              Semana Final
            </h3>
            <div className="p-4">
              <EpiCalendar
                onWeekSelect={handleEndWeekSelect}
                selectedStart={epiStart}
                selectedEnd={epiEnd}
                selectingEnd={true}
              />
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}