/**
 * Server-Side Rendered Reports Page
 * Fetches data on the server and renders the report
 */

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { DynamicChart } from "@/features/dashboard/components/DynamicChart";
import { env } from "@/env";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";

interface PageProps {
  searchParams: {
    filters?: string;
    dateFrom?: string;
    dateTo?: string;
  };
}

interface FilterCombination {
  id: string;
  groupId: number | null;
  groupName?: string;
  eventIds: number[];
  eventNames?: string[];
  clasificaciones?: string[];
}

async function fetchReportData(
  combinations: FilterCombination[],
  dateRange: { from: string; to: string }
) {
  // Use the same API host for server-side requests
  const apiHost = env.NEXT_PUBLIC_API_HOST;

  // Get session for authentication
  const session = await getServerSession(authOptions);
  const headers: HeadersInit = session?.accessToken
    ? { 'Authorization': `Bearer ${session.accessToken}` }
    : {};

  const processedCombinations = [];

  for (const combo of combinations) {
    try {
      // Build query params
      const params = new URLSearchParams();
      if (combo.groupId) params.append("grupo_id", combo.groupId.toString());
      if (combo.eventIds?.[0])
        params.append("evento_id", combo.eventIds[0].toString());
      params.append("fecha_desde", dateRange.from);
      params.append("fecha_hasta", dateRange.to);
      if (combo.clasificaciones?.length) {
        combo.clasificaciones.forEach((c) =>
          params.append("clasificaciones", c)
        );
      }

      // Fetch indicators with authentication
      const indicadoresRes = await fetch(
        `${apiHost}/api/v1/charts/indicadores?${params.toString()}`,
        { cache: "no-store", headers }
      );
      const indicadores = await indicadoresRes.json();

      // Fetch charts with authentication
      const chartsRes = await fetch(
        `${apiHost}/api/v1/charts/dashboard?${params.toString()}`,
        { cache: "no-store", headers }
      );
      const chartsData = await chartsRes.json();

      processedCombinations.push({
        ...combo,
        indicadores,
        charts: chartsData.charts || [],
      });
    } catch (error) {
      console.error("Error fetching data for combination:", error);
      processedCombinations.push({
        ...combo,
        indicadores: {},
        charts: [],
      });
    }
  }

  return processedCombinations;
}

export default async function ReportsSSRPage({ searchParams }: PageProps) {
  // Parse filters from URL
  let filterCombinations: FilterCombination[] = [];
  let dateRange = {
    from: searchParams.dateFrom || "",
    to: searchParams.dateTo || "",
  };

  if (searchParams.filters) {
    try {
      filterCombinations = JSON.parse(searchParams.filters);
    } catch (e) {
      console.error("Error parsing filters:", e);
    }
  }

  // Fetch data server-side
  const reportData = await fetchReportData(filterCombinations, dateRange);

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
        {reportData.map((combination, index: number) => (
          <div key={combination.id} className="page-break-before">
            {/* Section Header */}
            <Card className="mb-6">
              <CardHeader>
                <CardTitle className="flex items-center gap-3">
                  <Badge className="text-lg px-3 py-1">#{index + 1}</Badge>
                  <span>{combination.groupName || "Sin grupo"}</span>
                </CardTitle>
                <div className="mt-2 space-y-2">
                  {combination.eventNames &&
                    combination.eventNames.length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        <span className="text-sm text-gray-600">Eventos:</span>
                        {combination.eventNames.map(
                          (name: string, i: number) => (
                            <Badge key={i} variant="secondary">
                              {name}
                            </Badge>
                          )
                        )}
                      </div>
                    )}
                  {combination.clasificaciones &&
                    combination.clasificaciones.length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        <span className="text-sm text-gray-600">
                          Clasificaciones:
                        </span>
                        {combination.clasificaciones.map(
                          (c: string, i: number) => (
                            <Badge key={i} variant="outline">
                              {c}
                            </Badge>
                          )
                        )}
                      </div>
                    )}
                </div>
              </CardHeader>
            </Card>

            {/* Indicators */}
            {combination.indicadores && (
              <div className="mb-6 grid grid-cols-2 md:grid-cols-4 gap-4">
                <Card>
                  <CardContent className="p-4">
                    <div className="text-2xl font-bold">
                      {combination.indicadores.total_casos || 0}
                    </div>
                    <div className="text-sm text-gray-600">Total Casos</div>
                  </CardContent>
                </Card>

                {combination.indicadores.tasa_incidencia !== undefined && (
                  <Card>
                    <CardContent className="p-4">
                      <div className="text-2xl font-bold">
                        {combination.indicadores.tasa_incidencia.toFixed(2)}
                      </div>
                      <div className="text-sm text-gray-600">
                        Tasa Incidencia
                      </div>
                    </CardContent>
                  </Card>
                )}

                {combination.indicadores.areas_afectadas !== undefined && (
                  <Card>
                    <CardContent className="p-4">
                      <div className="text-2xl font-bold">
                        {combination.indicadores.areas_afectadas}
                      </div>
                      <div className="text-sm text-gray-600">
                        Áreas Afectadas
                      </div>
                    </CardContent>
                  </Card>
                )}

                {combination.indicadores.letalidad !== undefined && (
                  <Card>
                    <CardContent className="p-4">
                      <div className="text-2xl font-bold">
                        {combination.indicadores.letalidad.toFixed(2)}%
                      </div>
                      <div className="text-sm text-gray-600">Letalidad</div>
                    </CardContent>
                  </Card>
                )}
              </div>
            )}

            {/* Charts Grid */}
            {combination.charts && combination.charts.length > 0 && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
}
