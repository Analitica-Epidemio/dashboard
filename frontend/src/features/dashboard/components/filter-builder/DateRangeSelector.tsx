'use client'

import React from 'react'
import { format } from 'date-fns'
import { es } from 'date-fns/locale'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { CalendarDays } from 'lucide-react'
import { DateRangePicker } from '@/components/DateRangePicker'
import { useFilterContext } from '../../contexts/FilterContext'

export function DateRangeSelector() {
  const { dateRange, setDateRange } = useFilterContext()

  const formatDateRange = () => {
    if (!dateRange.from || !dateRange.to) return 'Seleccionar rango'
    return `${format(dateRange.from, 'd MMM yyyy', { locale: es })} - ${format(
      dateRange.to,
      'd MMM yyyy',
      { locale: es }
    )}`
  }

  const getDuration = () => {
    if (!dateRange.from || !dateRange.to) return 0
    return Math.ceil((dateRange.to.getTime() - dateRange.from.getTime()) / (1000 * 60 * 60 * 24)) + 1
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CalendarDays className="h-5 w-5" />
          Período de Análisis
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Selecciona el período de análisis
            </label>
            <DateRangePicker
              value={dateRange}
              onChange={setDateRange}
              className="w-full"
            />
          </div>

          {dateRange.from && dateRange.to && (
            <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-blue-700 mb-1">Período seleccionado</p>
                  <p className="text-lg font-semibold text-blue-900">
                    {formatDateRange()}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-blue-700 mb-1">Duración</p>
                  <p className="text-lg font-semibold text-blue-900">
                    {getDuration()} días
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}