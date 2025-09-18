/**
 * Componente de Totales Históricos
 * Gráfico de líneas múltiples con comparativa anual por área programática
 */

import React, { useMemo } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
} from "recharts";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, TrendingUp, TrendingDown, Minus } from "lucide-react";
import { EpidemiologicalFilters, ChartConfig } from "../../types";
import { useHistoricalTotals } from "../../hooks/useEpidemiologicalData";
import type {
  TooltipProps,
  LegendPayload,
  HistoricalPayload,
} from "../../types/recharts";

// Colores para áreas programáticas (replicando el original)
const AREA_COLORS = [
  "rgb(31, 119, 180)", // Azul
  "rgb(255, 127, 14)", // Naranja
  "rgb(44, 160, 44)", // Verde
  "rgb(214, 39, 40)", // Rojo
  "rgb(148, 103, 189)", // Púrpura
  "rgb(140, 86, 75)", // Marrón
  "rgb(227, 119, 194)", // Rosa
  "rgb(127, 127, 127)", // Gris
  "rgb(188, 189, 34)", // Verde oliva
  "rgb(23, 190, 207)", // Cyan
] as const;

interface HistoricalTotalsChartProps {
  filters?: EpidemiologicalFilters;
  chartConfig?: ChartConfig;
  onYearSelect?: (year: number) => void;
  chartType?: "line" | "bar";
  showTrendIndicators?: boolean;
}

// Tooltip personalizado
const CustomTooltip: React.FC<TooltipProps<HistoricalPayload>> = ({
  active,
  payload,
  label,
}) => {
  if (!active || !payload || !payload.length) return null;

  const year = label;
  const data = payload[0]?.payload;

  // Calcular total de casos del año
  const totalCases = payload.reduce((sum, entry) => {
    if (entry.dataKey !== "total" && entry.dataKey !== "mortalityRate") {
      return sum + (Number(entry.value) || 0);
    }
    return sum;
  }, 0);

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 max-w-sm">
      <div className="border-b border-gray-200 pb-2 mb-2">
        <p className="font-semibold text-gray-800">Año {year}</p>
        <p className="text-sm text-gray-600">
          Total casos: {totalCases.toLocaleString()}
        </p>
      </div>

      <div className="space-y-1">
        {payload
          .filter(
            (entry) =>
              entry.dataKey !== "total" && entry.dataKey !== "mortalityRate"
          )
          .map((entry, index) => (
            <div
              key={index}
              className="flex items-center justify-between gap-4"
            >
              <div className="flex items-center gap-2 min-w-0">
                <div
                  className="w-3 h-3 rounded flex-shrink-0"
                  style={{ backgroundColor: entry.color }}
                />
                <span className="text-sm text-gray-700 truncate">
                  {entry.name}
                </span>
              </div>
              <span className="text-sm font-medium text-gray-900">
                {entry.value?.toLocaleString()}
              </span>
            </div>
          ))}
      </div>

      {data?.mortalityRate && data.mortalityRate > 0 && (
        <div className="border-t border-gray-200 pt-2 mt-2">
          <div className="flex items-center justify-between">
            <span className="text-sm text-red-600">Tasa letalidad:</span>
            <span className="text-sm font-medium text-red-700">
              {data.mortalityRate.toFixed(2)}%
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

// Componente de indicador de tendencia
const TrendIndicator: React.FC<{
  current: number;
  previous: number;
}> = ({ current, previous }) => {
  if (previous === 0) return null;

  const percentageChange = ((current - previous) / previous) * 100;
  const isIncrease = percentageChange > 0;
  const isDecrease = percentageChange < 0;

  if (Math.abs(percentageChange) < 1) {
    return (
      <div className="flex items-center gap-1">
        <Minus className="h-3 w-3 text-gray-500" />
        <span className="text-xs text-gray-500">Sin cambio</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-1">
      {isIncrease && <TrendingUp className="h-3 w-3 text-red-500" />}
      {isDecrease && <TrendingDown className="h-3 w-3 text-green-500" />}
      <span
        className={`text-xs ${
          isIncrease
            ? "text-red-500"
            : isDecrease
            ? "text-green-500"
            : "text-gray-500"
        }`}
      >
        {isIncrease ? "+" : ""}
        {percentageChange.toFixed(1)}%
      </span>
    </div>
  );
};

export const HistoricalTotalsChart: React.FC<HistoricalTotalsChartProps> = ({
  filters,
  chartConfig = {},
  onYearSelect,
  chartType = "line",
  showTrendIndicators = true,
}) => {
  const { processedData, loading, error, refetch } =
    useHistoricalTotals(filters);

  // Preparar datos y estadísticas
  const { chartData, areas, statistics, title, trends } = useMemo(() => {
    if (!processedData) {
      return {
        chartData: [],
        areas: [],
        statistics: null,
        title: "",
        trends: [],
      };
    }

    const { chartData, areas, statistics } = processedData;

    // Calcular tendencias año a año
    const trendCalculations = chartData
      .map((current, index) => {
        const previous = chartData[index - 1];
        if (!previous) return null;

        return {
          year: current.year,
          totalChange: current.total - previous.total,
          percentageChange:
            previous.total > 0
              ? ((current.total - previous.total) / previous.total) * 100
              : 0,
        };
      })
      .filter(Boolean);

    // Generar título
    const years = chartData.map((d) => d.year);
    const yearRange =
      years.length > 1
        ? `${Math.min(...years)}-${Math.max(...years)}`
        : `${years[0] || ""}`;

    const chartTitle = `Totales Históricos por Área Programática - ${yearRange}`;

    return {
      chartData,
      areas,
      statistics,
      title: chartTitle,
      trends: trendCalculations,
    };
  }, [processedData]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="flex items-center gap-2">
          <div className="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full" />
          <span>Cargando totales históricos...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-4">
        <AlertTriangle className="h-12 w-12 text-red-500" />
        <div className="text-center">
          <p className="text-lg font-semibold text-gray-800">
            Error al cargar datos
          </p>
          <p className="text-sm text-gray-600">{error}</p>
          <button
            onClick={refetch}
            className="mt-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
          >
            Reintentar
          </button>
        </div>
      </div>
    );
  }

  const ChartComponent = chartType === "bar" ? BarChart : LineChart;

  return (
    <div className="w-full">
      <div className="mb-4">
        {statistics && (
          <div className="flex flex-wrap gap-4">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-blue-500" />
              <span className="text-sm font-medium">
                Total casos: {statistics.totalCases.toLocaleString()}
              </span>
            </div>

            {(statistics.averageMortalityRate || 0) > 0 && (
              <>
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 text-red-500" />
                  <span className="text-sm font-medium">
                    Tasa de mortalidad promedio:{" "}
                    {(statistics.averageMortalityRate || 0).toFixed(2)}%
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">
                    Tasa de mortalidad:{" "}
                    {(statistics.averageMortalityRate || 0).toFixed(2)}%
                  </span>
                </div>
              </>
            )}
          </div>
        )}

        {/* Indicadores de tendencia reciente */}
        {showTrendIndicators && trends.length > 0 && (
          <div className="mt-2 p-3 bg-gray-50 rounded-lg">
            <p className="text-sm font-medium text-gray-700 mb-2">
              Tendencia reciente:
            </p>
            <div className="flex items-center gap-4">
              {trends.slice(-2).map((trend) =>
                trend ? (
                  <div key={trend.year} className="flex items-center gap-2">
                    <span className="text-sm text-gray-600">{trend.year}:</span>
                    <TrendIndicator
                      current={
                        chartData.find((d) => d.year === trend.year)?.total || 0
                      }
                      previous={
                        chartData.find((d) => d.year === trend.year - 1)
                          ?.total || 0
                      }
                    />
                  </div>
                ) : null
              )}
            </div>
          </div>
        )}
      </div>

      <div>
        <div className="w-full" style={{ height: chartConfig.height || 400 }}>
          <ResponsiveContainer width="100%" height="100%">
            <ChartComponent
              data={chartData}
              margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
              onClick={(data) => {
                if (data?.activePayload?.[0]?.payload && onYearSelect) {
                  const point = data.activePayload[0].payload;
                  onYearSelect(point.year);
                }
              }}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="rgba(128, 128, 128, 0.2)"
              />

              <XAxis
                dataKey="year"
                tick={{ fontSize: 12 }}
                tickLine={{ stroke: "#666" }}
                axisLine={{ stroke: "#666" }}
                label={{ value: "Año", position: "insideBottom", offset: -40 }}
              />

              <YAxis
                tick={{ fontSize: 12 }}
                tickLine={{ stroke: "#666" }}
                axisLine={{ stroke: "#666" }}
                label={{ value: "Casos", angle: -90, position: "insideLeft" }}
              />

              {/* Líneas/Barras para cada área */}
              {areas.map((area, index) => {
                const color = AREA_COLORS[index % AREA_COLORS.length];

                return chartType === "bar" ? (
                  <Bar
                    key={area.id}
                    dataKey={area.id}
                    fill={color}
                    stroke="rgba(255, 255, 255, 0.8)"
                    strokeWidth={0.5}
                  />
                ) : (
                  <Line
                    key={area.id}
                    type="monotone"
                    dataKey={area.id}
                    stroke={color}
                    strokeWidth={2}
                    dot={{ fill: color, strokeWidth: 2, r: 4 }}
                    connectNulls={false}
                  />
                );
              })}

              {/* Línea de total si es necesario */}
              {chartType === "line" && (
                <Line
                  type="monotone"
                  dataKey="total"
                  stroke="rgb(0, 0, 0)"
                  strokeWidth={3}
                  strokeDasharray="5 5"
                  dot={{ fill: "rgb(0, 0, 0)", strokeWidth: 2, r: 5 }}
                  connectNulls={false}
                />
              )}

              <Tooltip content={<CustomTooltip />} />

              <Legend
                layout="horizontal"
                verticalAlign="bottom"
                align="center"
                wrapperStyle={{ paddingTop: "20px" }}
                payload={[
                  ...areas.map((area, index) => ({
                    value: area.name,
                    type: (chartType === "bar" ? "rect" : "line") as
                      | "rect"
                      | "line",
                    color: AREA_COLORS[index % AREA_COLORS.length],
                  })),
                  ...(chartType === "line"
                    ? [
                        {
                          value: "Total General",
                          type: "line" as const,
                          color: "rgb(0, 0, 0)",
                        },
                      ]
                    : []),
                ]}
              />
            </ChartComponent>
          </ResponsiveContainer>
        </div>

        {/* Ranking de áreas por casos */}
        {statistics && areas.length > 0 && (
          <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-3 bg-gray-50 rounded-lg">
              <h4 className="text-sm font-semibold text-gray-800 mb-2">
                Ranking por casos totales
              </h4>
              <div className="space-y-1">
                {areas
                  .map((area) => ({
                    ...area,
                    totalCases: chartData.reduce(
                      (sum, point) => {
                        const chartPoint = point as Record<string, number>;
                        return sum + (chartPoint[area.id] || 0);
                      },
                      0
                    ),
                  }))
                  .sort((a, b) => b.totalCases - a.totalCases)
                  .slice(0, 5)
                  .map((area, index) => (
                    <div
                      key={area.id}
                      className="flex items-center justify-between"
                    >
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="text-xs">
                          {index + 1}
                        </Badge>
                        <span className="text-sm text-gray-700">
                          {area.name}
                        </span>
                      </div>
                      <span className="text-sm font-medium">
                        {area.totalCases.toLocaleString()}
                      </span>
                    </div>
                  ))}
              </div>
            </div>

            {showTrendIndicators && trends.length > 0 && (
              <div className="p-3 bg-gray-50 rounded-lg">
                <h4 className="text-sm font-semibold text-gray-800 mb-2">
                  Tendencias recientes
                </h4>
                <div className="space-y-2">
                  {trends.slice(-3).map((trend) =>
                    trend ? (
                      <div
                        key={trend.year}
                        className="flex items-center justify-between"
                      >
                        <span className="text-sm text-gray-700">
                          {trend.year}
                        </span>
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-gray-600">
                            {trend.totalChange > 0 ? "+" : ""}
                            {trend.totalChange.toLocaleString()}
                          </span>
                          <TrendIndicator
                            current={
                              chartData.find((d) => d.year === trend.year)
                                ?.total || 0
                            }
                            previous={
                              chartData.find((d) => d.year === trend.year - 1)
                                ?.total || 0
                            }
                          />
                        </div>
                      </div>
                    ) : null
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default HistoricalTotalsChart;
