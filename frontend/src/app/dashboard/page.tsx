"use client";

import React, { useState } from "react";
import { useDashboardFilters } from "@/features/dashboard/hooks/useDashboardFilters";
import { CollapsibleSidebar } from "@/features/layout/components";
import { FullscreenFilterBuilder } from "@/features/dashboard/components/FullscreenFilterBuilder";
import { ComparativeDashboard } from "@/features/dashboard/components/ComparativeDashboard";

interface FilterCombination {
  id: string;
  groupId: string | null;
  groupName?: string;
  eventIds: number[];
  eventNames?: string[];
  label?: string;
  color?: string;
}

interface DateRange {
  from: Date | null;
  to: Date | null;
}

export default function EpidemiologyDashboard() {
  // Estado para controlar qué vista mostrar
  const [showComparison, setShowComparison] = useState(false);
  const [appliedDateRange, setAppliedDateRange] = useState<DateRange>({
    from: new Date(2020, 0, 1), // 1 de enero 2020
    to: new Date(2025, 11, 31), // 31 de diciembre 2025
  });
  const [appliedCombinations, setAppliedCombinations] = useState<
    FilterCombination[]
  >([]);

  // Reutilizamos la lógica existente de filtros
  const {
    groups,
    groupsLoading,
    groupsError,
    allEvents,
    allEventsLoading,
    allEventsError,
  } = useDashboardFilters();

  // Manejar aplicación de filtros
  const handleApplyFilters = (
    dateRange: DateRange,
    combinations: FilterCombination[]
  ) => {
    setAppliedDateRange(dateRange);
    setAppliedCombinations(combinations);
    setShowComparison(true);
  };

  // Volver al constructor de filtros (mantiene las combinaciones)
  const handleBackToFilters = () => {
    setShowComparison(false);
  };

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Collapsible Navigation Sidebar */}
      <CollapsibleSidebar />

      {/* Main Content */}
      <div className="flex-1 overflow-y-scroll">
        {!showComparison ? (
          /* Fullscreen Filter Builder */
          <FullscreenFilterBuilder
            groups={groups}
            availableEvents={allEvents}
            onApplyFilters={handleApplyFilters}
            groupsLoading={groupsLoading}
            eventsLoading={allEventsLoading}
            groupsError={groupsError}
            eventsError={allEventsError}
            initialDateRange={appliedDateRange}
            initialCombinations={appliedCombinations}
          />
        ) : (
          /* Comparative Dashboard with compact filter bar */
          <ComparativeDashboard
            dateRange={appliedDateRange}
            filterCombinations={appliedCombinations}
            onBack={handleBackToFilters}
          />
        )}
      </div>
    </div>
  );
}
