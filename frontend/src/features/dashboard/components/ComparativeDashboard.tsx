/**
 * Comparative Dashboard Component
 * Displays charts in columns for each filter combination
 */

import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CompactFilterBar } from "./CompactFilterBar";
import { Activity, AlertTriangle, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";

// Import dynamic chart components
import { DynamicChart } from "./DynamicChart";
import { useDashboardCharts } from "../hooks/useDashboardCharts";
import { useIndicadores } from "@/features/charts/hooks";
import { useGenerateZipReport, useGenerateSignedUrl } from "@/features/reports/hooks";

interface FilterCombination {
  id: string;
  groupId: string | null;
  groupName?: string;
  eventIds: number[];
  eventNames?: string[];
  clasificaciones?: string[];
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

// Component to render charts for a single column
const DynamicChartsColumn: React.FC<{
  combination: FilterCombination;
  dateRange: DateRange;
}> = ({ combination, dateRange }) => {
  // Format dates for API
  const formatDateForApi = (date: Date | null) => {
    if (!date) return null;
    return date.toISOString().split("T")[0];
  };

  // Fetch charts data
  const { data, isLoading, error } = useDashboardCharts({
    grupoId: combination.groupId ? parseInt(combination.groupId) : null,
    eventoId: combination.eventIds?.[0] || null,
    fechaDesde: formatDateForApi(dateRange.from),
    fechaHasta: formatDateForApi(dateRange.to),
    clasificaciones: combination.clasificaciones || [],
  });

  // Fetch indicadores data
  const { data: indicadores, isLoading: indicadoresLoading } = useIndicadores({
    grupo_id: combination.groupId ? parseInt(combination.groupId) : undefined,
    evento_id: combination.eventIds?.[0] || undefined,
    fecha_desde: formatDateForApi(dateRange.from) || undefined,
    fecha_hasta: formatDateForApi(dateRange.to) || undefined,
    clasificaciones: combination.clasificaciones || undefined,
  });

  if (isLoading) {
    return (
      <div className="flex-1 overflow-y-auto p-4">
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">Cargando charts...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 overflow-y-auto p-4">
        <div className="flex items-center justify-center h-64">
          <div className="text-red-500">Error cargando charts</div>
        </div>
      </div>
    );
  }

  console.log({ data });

  return (
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
                <p className="text-lg font-semibold">
                  {indicadoresLoading
                    ? "..."
                    : (indicadores?.data?.total_casos || 0).toLocaleString()}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-600">Tasa Incidencia</p>
                <p className="text-lg font-semibold">
                  {indicadoresLoading
                    ? "..."
                    : `${indicadores?.data?.tasa_incidencia || 0}/100k`}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-600">Áreas Afectadas</p>
                <p className="text-lg font-semibold">
                  {indicadoresLoading
                    ? "..."
                    : indicadores?.data?.areas_afectadas || 0}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-600">Letalidad</p>
                <p className="text-lg font-semibold">
                  {indicadoresLoading
                    ? "..."
                    : `${indicadores?.data?.letalidad || 0}%`}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Dynamic Charts */}
        {data?.data?.charts?.map((chart) => (
          <DynamicChart
            key={chart.codigo}
            codigo={chart.codigo}
            nombre={chart.nombre}
            descripcion={chart.descripcion}
            tipo={chart.tipo}
            data={chart.data}
            config={chart.config}
          />
        ))}

        {/* If no charts available */}
        {(!data?.data?.charts || data.data.charts.length === 0) && (
          <Card>
            <CardContent className="p-8 text-center text-gray-500">
              No hay charts disponibles para esta selección
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

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
        minWidth: "100%",
        maxWidth: "100%",
      };
    }

    // Two columns: 50% each
    if (count === 2) {
      return {
        minWidth: "50%",
        maxWidth: "50%",
      };
    }

    // Three or more: min 400px, max based on available space
    return {
      minWidth: "400px",
      maxWidth: `${100 / Math.min(count, 3)}%`,
      flex: "1 1 400px",
    };
  };

  const columnStyle = calculateColumnStyle();

  // Generate ZIP report mutation using the new hook
  const generateZipReportMutation = useGenerateZipReport();

  // Generate signed URL mutation
  const generateSignedUrlMutation = useGenerateSignedUrl();

  const handleGenerateZipReport = () => {
    const reportRequest = {
      date_range: {
        from: dateRange.from?.toISOString().split("T")[0] || "",
        to: dateRange.to?.toISOString().split("T")[0] || "",
      },
      combinations: filterCombinations.map((combo) => ({
        id: combo.id,
        group_id: combo.groupId ? parseInt(combo.groupId) : null,
        group_name: combo.groupName || "",
        event_ids: combo.eventIds || [],
        event_names: combo.eventNames || [],
        clasificaciones: combo.clasificaciones || [],
      })),
      format: "pdf",
    };

    generateZipReportMutation.mutate({
      body: reportRequest
    });
  };

  const handleGenerateSignedUrl = () => {
    const reportRequest = {
      filters: filterCombinations.map((combo) => ({
        id: combo.id,
        groupId: combo.groupId ? parseInt(combo.groupId) : null,
        groupName: combo.groupName || "",
        eventIds: combo.eventIds || [],
        eventNames: combo.eventNames || [],
        clasificaciones: combo.clasificaciones || [],
      })),
      date_from: dateRange.from?.toISOString().split("T")[0] || null,
      date_to: dateRange.to?.toISOString().split("T")[0] || null,
      expires_in: 3600, // 1 hour expiration
    };

    generateSignedUrlMutation.mutate(
      { body: reportRequest },
      {
        onSuccess: (data) => {
          // Open the signed URL in a new tab
          const baseUrl = window.location.origin;
          const fullUrl = `${baseUrl}${data.data.signed_url}`;
          window.open(fullUrl, '_blank');
          console.log('✅ Generated signed URL for SSR report');
        },
        onError: (error) => {
          console.error('Error generating signed URL:', error);
          alert('Error al generar la URL del reporte. Por favor intente nuevamente.');
        },
      }
    );
  };

  if (filterCombinations.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <Card className="max-w-md">
          <CardContent className="p-8 text-center">
            <AlertTriangle className="h-12 w-12 text-yellow-500 mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">
              No hay filtros aplicados
            </h3>
            <p className="text-gray-600 mb-4">
              Configura al menos una combinación de filtros para comenzar el
              análisis comparativo
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="h-full bg-gray-50 flex flex-col dashboard-comparative-container">
      {/* Compact Filter Bar */}
      <CompactFilterBar
        dateRange={dateRange}
        filterCombinations={filterCombinations}
        onEditFilters={onBack || (() => {})}
        onGenerateZipReport={handleGenerateZipReport}
        onGenerateSignedUrl={handleGenerateSignedUrl}
        expanded={expandedFilters}
        onToggleExpand={() => setExpandedFilters(!expandedFilters)}
        isGeneratingReport={generateZipReportMutation.isPending}
        isGeneratingSignedUrl={generateSignedUrlMutation.isPending}
      />

      {/* Scrollable columns container */}
      <div className="flex-1 overflow-x-auto overflow-y-hidden bg-gray-50">
        <div
          className="flex h-full"
          style={{ minWidth: `${filterCombinations.length * 400}px` }}
        >
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
                      {combination.eventNames &&
                        combination.eventNames.length > 2 && (
                          <Badge variant="secondary" className="text-xs">
                            +{combination.eventNames.length - 2} más
                          </Badge>
                        )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Charts Container with proper scroll */}
              <DynamicChartsColumn
                combination={combination}
                dateRange={dateRange}
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
