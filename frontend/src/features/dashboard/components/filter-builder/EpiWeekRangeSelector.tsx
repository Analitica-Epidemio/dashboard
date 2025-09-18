'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Calendar, CalendarRange } from 'lucide-react'
import { format } from 'date-fns'
import { es } from 'date-fns/locale'
import EpiCalendar from './epiweek-selector'
import { getEpiWeek, epiWeekToDates } from './epiweek-utils'
import { useFilterContext } from '../../contexts/FilterContext'

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
  const [selectingEnd, setSelectingEnd] = useState(false)

  // Initialize with current values if they exist
  useEffect(() => {
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
  }, [])

  // Update date range when epi weeks change
  useEffect(() => {
    if (epiStart && epiEnd) {
      setDateRange({
        from: epiStart.startDate,
        to: epiEnd.endDate
      })
    }
  }, [epiStart, epiEnd, setDateRange])

  const handleWeekSelect = (date: Date) => {
    const weekInfo = getEpiWeek(date)
    const weekDates = epiWeekToDates(weekInfo.year, weekInfo.week)
    const newWeek: EpiWeekRange = {
      year: weekInfo.year,
      week: weekInfo.week,
      startDate: weekDates.start,
      endDate: weekDates.end
    }

    if (!selectingEnd) {
      // Selecting start week
      setEpiStart(newWeek)
      setEpiEnd(null)
      setSelectingEnd(true)
    } else {
      // Selecting end week
      if (epiStart && newWeek.startDate < epiStart.startDate) {
        // If end is before start, swap them
        setEpiEnd(epiStart)
        setEpiStart(newWeek)
      } else {
        setEpiEnd(newWeek)
      }
      setSelectingEnd(false)
    }
  }

  const clearSelection = () => {
    setEpiStart(null)
    setEpiEnd(null)
    setSelectingEnd(false)
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
        <CardTitle className="flex items-center gap-2">
          <Calendar className="h-5 w-5" />
          Período de Análisis (Semanas Epidemiológicas)
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Selected Range Display */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Período Seleccionado:</span>
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

          <div className="flex items-center gap-2">
            {!epiStart && !epiEnd ? (
              <span className="text-gray-500 text-sm">Selecciona un rango de semanas</span>
            ) : (
              <>
                {epiStart && (
                  <Badge variant="secondary" className="px-3 py-1">
                    <CalendarRange className="h-3 w-3 mr-1" />
                    Desde: {formatEpiWeek(epiStart)}
                  </Badge>
                )}
                {epiStart && !epiEnd && selectingEnd && (
                  <span className="text-gray-500 text-sm">→ Selecciona semana final</span>
                )}
                {epiEnd && (
                  <Badge variant="secondary" className="px-3 py-1">
                    <CalendarRange className="h-3 w-3 mr-1" />
                    Hasta: {formatEpiWeek(epiEnd)}
                  </Badge>
                )}
              </>
            )}
          </div>

          {epiStart && epiEnd && (
            <div className="mt-2 text-xs text-gray-600">
              {formatDateRange(epiStart.startDate, epiEnd.endDate)}
            </div>
          )}
        </div>

        {/* Instructions */}
        <div className="text-sm text-gray-600 bg-gray-50 rounded-lg p-3">
          <p className="font-medium mb-1">Instrucciones:</p>
          <ul className="list-disc list-inside space-y-1 text-xs">
            <li>Haz clic en cualquier día para seleccionar su semana epidemiológica</li>
            <li>Primero selecciona la semana inicial, luego la semana final</li>
            <li>Las semanas epidemiológicas van de domingo a sábado</li>
            <li>El calendario mostrará la semana completa resaltada</li>
          </ul>
        </div>

        {/* Calendar Component */}
        <div className="border rounded-lg p-4">
          <EpiCalendar
            onWeekSelect={handleWeekSelect}
            selectedStart={epiStart}
            selectedEnd={epiEnd}
            selectingEnd={selectingEnd}
          />
        </div>
      </CardContent>
    </Card>
  )
}