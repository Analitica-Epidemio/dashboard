"use client";

import React from "react";
import {
  FilterProvider,
  useFilterContext,
} from "@/features/dashboard/contexts/FilterContext";
import { ComparativeDashboard } from "@/features/dashboard/components/comparison/ComparativeDashboard";
import { CollapsibleSidebar } from "@/features/layout/components";
import { FilterBuilderView } from "@/features/dashboard/components/filter-builder/FilterBuilderView";

function DashboardContent() {
  const {
    isComparisonView,
    dateRange,
    filterCombinations,
    soloChubutEnabled,
    setIsComparisonView,
  } = useFilterContext();

  const handleBackToFilters = () => {
    setIsComparisonView(false);
  };

  return (
    <div className="flex h-screen overflow-hidden">
      <CollapsibleSidebar />

      <div className="flex-1 overflow-y-scroll">
        {!isComparisonView ? (
          <FilterBuilderView />
        ) : (
          <ComparativeDashboard
            dateRange={dateRange}
            filterCombinations={filterCombinations}
            soloChubutEnabled={soloChubutEnabled}
            onBack={handleBackToFilters}
          />
        )}
      </div>
    </div>
  );
}

export default function EpidemiologyDashboard() {
  return (
    <FilterProvider>
      <DashboardContent />
    </FilterProvider>
  );
}
