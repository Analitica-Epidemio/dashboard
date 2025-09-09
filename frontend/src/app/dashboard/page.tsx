"use client";

import React, { useState } from "react";
import { useDashboardFilters } from "@/features/dashboard/hooks/useDashboardFilters";
import { CollapsibleSidebar } from "@/components/CollapsibleSidebar";
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
    from: null,
    to: null,
  });
  const [appliedCombinations, setAppliedCombinations] = useState<FilterCombination[]>([]);

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
  const handleApplyFilters = (dateRange: DateRange, combinations: FilterCombination[]) => {
    setAppliedDateRange(dateRange);
    setAppliedCombinations(combinations);
    setShowComparison(true);
  };

  // Volver al constructor de filtros
  const handleBackToFilters = () => {
    setShowComparison(false);
  };

  return (
    <>
      {/* Collapsible Navigation Sidebar */}
      <CollapsibleSidebar />

      {/* Main Content with left padding for collapsed sidebar */}
      <div className="h-full lg:pl-14">
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
    </>
  );
}