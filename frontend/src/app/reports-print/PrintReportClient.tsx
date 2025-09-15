"use client";

/**
 * Client component for rendering reports with real DynamicChart components
 */

import React from "react";
import { DynamicChart } from "@/features/dashboard/components/DynamicChart";

interface ReportData {
  id: string;
  groupId: number | null;
  groupName?: string;
  eventIds: number[];
  eventNames?: string[];
  clasificaciones?: string[];
  indicadores: any;
  charts: any[];
}

interface PrintReportClientProps {
  reportData: ReportData[];
  dateRange: { from: string; to: string };
}

export const PrintReportClient: React.FC<PrintReportClientProps> = ({
  reportData,
  dateRange,
}) => {
  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "";
    const date = new Date(dateStr);
    return date.toLocaleDateString("es", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  };

  return (
    <div className="min-h-screen bg-white p-8" id="report-content">
      {/* Report Header */}
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Reporte Epidemiológico
        </h1>
        <p className="text-lg text-gray-600">
          {dateRange.from && dateRange.to && (
            <>
              Período: {formatDate(dateRange.from)} - {formatDate(dateRange.to)}
            </>
          )}
        </p>
      </div>

      {/* Report Content */}
      <div className="space-y-8">
        {reportData.map((combination: any, index: number) => (
          <div key={combination.id} className="page-break-before">
            {/* Section Header */}
            <div className="mb-6 p-4 bg-gray-50 rounded-lg">
              <h2 className="text-xl font-bold flex items-center gap-3">
                <span className="bg-blue-600 text-white px-3 py-1 rounded text-sm">
                  #{index + 1}
                </span>
                <span>{combination.groupName || "Sin grupo"}</span>
              </h2>
              {combination.eventNames && combination.eventNames.length > 0 && (
                <div className="mt-2">
                  <span className="text-sm text-gray-600">Eventos: </span>
                  {combination.eventNames.join(", ")}
                </div>
              )}
              {combination.clasificaciones &&
                combination.clasificaciones.length > 0 && (
                  <div className="mt-1">
                    <span className="text-sm text-gray-600">
                      Clasificaciones:{" "}
                    </span>
                    {combination.clasificaciones.join(", ")}
                  </div>
                )}
            </div>

            {/* Indicators */}
            {combination.indicadores && (
              <div className="mb-6 grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-white border border-gray-200 rounded-lg p-4 text-center">
                  <div className="text-2xl font-bold text-gray-900">
                    {combination.indicadores.total_casos || 0}
                  </div>
                  <div className="text-xs text-gray-600 mt-1">Total Casos</div>
                </div>

                {combination.indicadores.tasa_incidencia !== undefined && (
                  <div className="bg-white border border-gray-200 rounded-lg p-4 text-center">
                    <div className="text-2xl font-bold text-gray-900">
                      {combination.indicadores.tasa_incidencia.toFixed(2)}
                    </div>
                    <div className="text-xs text-gray-600 mt-1">Tasa Incidencia</div>
                  </div>
                )}

                {combination.indicadores.areas_afectadas !== undefined && (
                  <div className="bg-white border border-gray-200 rounded-lg p-4 text-center">
                    <div className="text-2xl font-bold text-gray-900">
                      {combination.indicadores.areas_afectadas}
                    </div>
                    <div className="text-xs text-gray-600 mt-1">Áreas Afectadas</div>
                  </div>
                )}

                {combination.indicadores.letalidad !== undefined && (
                  <div className="bg-white border border-gray-200 rounded-lg p-4 text-center">
                    <div className="text-2xl font-bold text-gray-900">
                      {combination.indicadores.letalidad.toFixed(2)}%
                    </div>
                    <div className="text-xs text-gray-600 mt-1">Letalidad</div>
                  </div>
                )}
              </div>
            )}

            {/* Dynamic Charts - Same as Dashboard! */}
            {combination.charts && combination.charts.length > 0 && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 charts-container">
                {combination.charts.map((chart: any) => (
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
              </div>
            )}

            {/* No data message */}
            {(!combination.charts || combination.charts.length === 0) && (
              <div className="text-center py-8 text-gray-500">
                No hay datos disponibles para esta combinación de filtros
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="mt-12 pt-8 border-t border-gray-200 text-center text-sm text-gray-500">
        <p>
          Reporte generado el{" "}
          {new Date().toLocaleDateString("es", {
            day: "2-digit",
            month: "long",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
          })}
        </p>
        <p className="mt-2">
          Sistema de Vigilancia Epidemiológica - Provincia del Chubut
        </p>
      </div>
    </div>
  );
};