'use client'

import React from 'react'
import { DateRangeSelector } from './DateRangeSelector'
import { FilterCombinationBuilder } from './FilterCombinationBuilder'
import { FilterCombinationsList } from './FilterCombinationsList'

export function FilterBuilderView() {
  return (
    <div className="h-full bg-gray-50 overflow-auto">
      <div className="max-w-7xl mx-auto p-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Configurar Análisis Comparativo
          </h1>
          <p className="text-gray-600">
            Define el período de tiempo y las combinaciones de filtros para tu análisis
          </p>
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Date Range & Filter Builder */}
          <div className="lg:col-span-2 space-y-6">
            <DateRangeSelector />
            <FilterCombinationBuilder />
          </div>

          {/* Right Column - Added Combinations */}
          <div className="lg:col-span-1">
            <FilterCombinationsList />
          </div>
        </div>
      </div>
    </div>
  )
}