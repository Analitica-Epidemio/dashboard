'use client'

import React from 'react'
import { EpiWeekRangeSelector } from './EpiWeekRangeSelector'
import { FilterCombinationBuilder } from './FilterCombinationBuilder'
import { SplitPanelRight } from './SplitPanelRight'

export function FilterBuilderView() {
  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <div className="border-b bg-white px-8 py-5 flex-shrink-0">
        <h1 className="text-2xl font-bold text-gray-900">
          Análisis Comparativo
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          Configura período y combinaciones de filtros
        </p>
      </div>

      {/* Split Panel Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Constructor (scroll independiente) */}
        <div className="flex-1 overflow-y-auto px-8 py-6 flex justify-center">
          <div className="w-full max-w-4xl space-y-6">
            <EpiWeekRangeSelector />
            <FilterCombinationBuilder />
          </div>
        </div>

        {/* Right Panel - Preview & Combinations (sticky, scroll independiente) */}
        <div className="w-[420px] border-l bg-white overflow-y-auto flex-shrink-0">
          <SplitPanelRight />
        </div>
      </div>
    </div>
  )
}