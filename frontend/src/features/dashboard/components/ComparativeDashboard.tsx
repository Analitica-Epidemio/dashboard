/**
 * Comparative Dashboard Component
 * Displays charts in columns for each filter combination
 */

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { CompactFilterBar } from './CompactFilterBar';
import { 
  Activity,
  TrendingUp,
  Users,
  AlertTriangle,
} from 'lucide-react';

// Import all chart components
import { EpidemiologicalCurveChart } from './charts/EpidemiologicalCurveChart';
import { EndemicCorridorChart } from './charts/EndemicCorridorChart';
import { AgePyramidChart } from './charts/AgePyramidChart';
import { HistoricalTotalsChart } from './charts/HistoricalTotalsChart';
import { UGDPieChart } from './charts/UGDPieChart';
import { SuicideAttemptChart } from './charts/SuicideAttemptChart';
import { AnimalRabiesChart } from './charts/AnimalRabiesChart';

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

interface ComparativeDashboardProps {
  dateRange: DateRange;
  filterCombinations: FilterCombination[];
  onBack?: () => void;
}

export const ComparativeDashboard: React.FC<ComparativeDashboardProps> = ({
  dateRange,
  filterCombinations,
  onBack,
}) => {
  const [expandedFilters, setExpandedFilters] = useState(false);
  
  // Calculate column width based on number of combinations
  const calculateColumnStyle = () => {
    const count = filterCombinations.length;
    
    if (count === 0) return {};
    
    // Single column: full width
    if (count === 1) {
      return {
        minWidth: '100%',
        maxWidth: '100%',
      };
    }
    
    // Two columns: 50% each
    if (count === 2) {
      return {
        minWidth: '50%',
        maxWidth: '50%',
      };
    }
    
    // Three or more: min 400px, max based on available space
    return {
      minWidth: '400px',
      maxWidth: `${100 / Math.min(count, 3)}%`,
      flex: '1 1 400px',
    };
  };

  const columnStyle = calculateColumnStyle();

  // Format date range for display
  const formatDateRange = () => {
    if (!dateRange.from || !dateRange.to) return '';
    const options: Intl.DateTimeFormatOptions = { day: '2-digit', month: 'short', year: 'numeric' };
    return `${dateRange.from.toLocaleDateString('es', options)} - ${dateRange.to.toLocaleDateString('es', options)}`;
  };

  // Generate mock data for charts (in production, this would come from API)
  const getMockChartData = (combination: FilterCombination) => {
    // This would be replaced with actual API calls based on combination filters
    return {
      epidemiologicalCurve: {
        // Mock data structure matching the chart component expectations
        data: [],
      },
      endemicCorridor: {
        data: [],
      },
      agePyramid: {
        data: [],
      },
      // ... other chart data
    };
  };

  if (filterCombinations.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <Card className="max-w-md">
          <CardContent className="p-8 text-center">
            <AlertTriangle className="h-12 w-12 text-yellow-500 mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">No hay filtros aplicados</h3>
            <p className="text-gray-600 mb-4">
              Configura al menos una combinación de filtros para comenzar el análisis comparativo
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="h-full bg-gray-50 flex flex-col">
      {/* Compact Filter Bar */}
      <CompactFilterBar
        dateRange={dateRange}
        filterCombinations={filterCombinations}
        onEditFilters={onBack || (() => {})}
        expanded={expandedFilters}
        onToggleExpand={() => setExpandedFilters(!expandedFilters)}
      />

      {/* Scrollable columns container */}
      <div className="flex-1 overflow-x-auto overflow-y-hidden bg-gray-50">
        <div className="flex h-full" style={{ minWidth: `${filterCombinations.length * 400}px` }}>
          {filterCombinations.map((combination, index) => (
            <div
              key={combination.id}
              className="border-r border-gray-200 last:border-r-0 flex flex-col h-full bg-white"
              style={columnStyle}
            >
              {/* Column Header */}
              <div className="flex-shrink-0 bg-white border-b border-gray-200 px-4 py-3">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <Badge className="text-xs">#{index + 1}</Badge>
                      <h3 className="font-semibold text-gray-900">
                        {combination.groupName}
                      </h3>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {combination.eventNames?.slice(0, 2).map((name, i) => (
                        <Badge key={i} variant="secondary" className="text-xs">
                          {name}
                        </Badge>
                      ))}
                      {combination.eventNames && combination.eventNames.length > 2 && (
                        <Badge variant="secondary" className="text-xs">
                          +{combination.eventNames.length - 2} más
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Charts Container with proper scroll */}
              <div className="flex-1 overflow-y-auto p-4">
                <div className="space-y-4">
                {/* KPI Summary Card */}
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm flex items-center gap-2">
                      <Activity className="h-4 w-4" />
                      Resumen de Indicadores
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <p className="text-xs text-gray-600">Total Casos</p>
                        <p className="text-lg font-semibold">2,847</p>
                        <p className="text-xs text-green-600 flex items-center gap-1">
                          <TrendingUp className="h-3 w-3" />
                          +7.4%
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-600">Tasa Incidencia</p>
                        <p className="text-lg font-semibold">45.2</p>
                        <p className="text-xs text-gray-500">/100k hab</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-600">Áreas Afectadas</p>
                        <p className="text-lg font-semibold">12</p>
                        <p className="text-xs text-gray-500">de 24</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-600">Letalidad</p>
                        <p className="text-lg font-semibold">2.3%</p>
                        <p className="text-xs text-red-600 flex items-center gap-1">
                          <TrendingUp className="h-3 w-3" />
                          +0.2%
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Epidemiological Curve */}
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm">Curva Epidemiológica</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="h-64">
                      <EpidemiologicalCurveChart 
                        filters={{
                          selectedGroupId: combination.groupId,
                          selectedEventId: combination.eventIds[0], // For now, use first event
                        }}
                      />
                    </div>
                  </CardContent>
                </Card>

                {/* Endemic Corridor */}
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm">Corredor Endémico</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="h-64">
                      <EndemicCorridorChart 
                        filters={{
                          selectedGroupId: combination.groupId,
                          selectedEventId: combination.eventIds[0],
                        }}
                      />
                    </div>
                  </CardContent>
                </Card>

                {/* Age Pyramid */}
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm">Pirámide Poblacional</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="h-64">
                      <AgePyramidChart 
                        filters={{
                          selectedGroupId: combination.groupId,
                          selectedEventId: combination.eventIds[0],
                        }}
                      />
                    </div>
                  </CardContent>
                </Card>

                {/* Geographic Distribution */}
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm">Distribución Geográfica</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="h-64">
                      <UGDPieChart 
                        filters={{
                          selectedGroupId: combination.groupId,
                          selectedEventId: combination.eventIds[0],
                        }}
                      />
                    </div>
                  </CardContent>
                </Card>

                {/* Historical Totals */}
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm">Totales Históricos</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="h-64">
                      <HistoricalTotalsChart 
                        filters={{
                          selectedGroupId: combination.groupId,
                          selectedEventId: combination.eventIds[0],
                        }}
                      />
                    </div>
                  </CardContent>
                </Card>

                {/* Conditional charts based on group type */}
                {combination.groupName?.toLowerCase().includes('suicid') && (
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm">Análisis de Intentos</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="h-64">
                        <SuicideAttemptChart 
                          filters={{
                            selectedGroupId: combination.groupId,
                            selectedEventId: combination.eventIds[0],
                          }}
                        />
                      </div>
                    </CardContent>
                  </Card>
                )}

                {combination.groupName?.toLowerCase().includes('rabia') && (
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm">Casos de Rabia Animal</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="h-64">
                        <AnimalRabiesChart 
                          filters={{
                            selectedGroupId: combination.groupId,
                            selectedEventId: combination.eventIds[0],
                          }}
                        />
                      </div>
                    </CardContent>
                  </Card>
                )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};