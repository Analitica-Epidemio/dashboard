"use client";

/**
 * Componente genérico para renderizar charts dinámicos con Recharts y D3
 */
import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
  TooltipProps,
} from "recharts";
import type { components } from "@/lib/api/types";
import { format } from "date-fns";
import { es } from "date-fns/locale";

interface WeekMetadata {
  year: number;
  week: number;
  start_date: string;
  end_date: string;
}

// Tipos base para datos de charts
interface BaseChartData {
  labels: string[];
  datasets: Array<{
    label?: string;
    data: number[];
  }>;
  metadata?: WeekMetadata[];
}

interface MapChartData {
  departamentos: Array<{
    nombre: string;
    casos: number;
    [key: string]: unknown;
  }>;
  total_casos: number;
}

type PyramidChartData = Array<{
  age_group: string;
  male: number;
  female: number;
  [key: string]: unknown;
}>;

// Error estructurado del backend
interface ChartError {
  code: string;
  title: string;
  message: string;
  details?: unknown;
  suggestion?: string;
}

// Data wrapper genérico con error
interface ChartDataWithError<T> {
  data?: T;
  error?: string | ChartError;
}

// Union type discriminado por el campo 'tipo'
type DynamicChartProps = Omit<components["schemas"]["ChartDataItem"], 'data' | 'tipo'> & (
  | {
      tipo: "line" | "bar" | "area";
      data: ChartDataWithError<BaseChartData>;
      config?: { height?: number; [key: string]: unknown };
    }
  | {
      tipo: "pie";
      data: ChartDataWithError<BaseChartData>;
      config?: { height?: number; [key: string]: unknown };
    }
  | {
      tipo: "d3_pyramid";
      data: ChartDataWithError<PyramidChartData>;
      config?: { height?: number; [key: string]: unknown };
    }
  | {
      tipo: "mapa";
      data: ChartDataWithError<MapChartData>;
      config?: { height?: number; [key: string]: unknown };
    }
  | {
      tipo: string; // Fallback para tipos desconocidos
      data: ChartDataWithError<unknown>;
      config?: { height?: number; [key: string]: unknown };
    }
);

// Colores predefinidos para los charts
const COLORS = [
  "#0088FE",
  "#00C49F",
  "#FFBB28",
  "#FF8042",
  "#8884D8",
  "#82CA9D",
  "#FFC658",
  "#8DD1E1",
  "#A4DE6C",
  "#FFD93D",
];

/**
 * Custom Tooltip Component
 * Shows week metadata (date range) when available
 */
const CustomTooltip: React.FC<TooltipProps<number, string> & { metadata?: WeekMetadata[] }> = ({
  active,
  payload,
  label,
  metadata,
}) => {
  if (!active || !payload || !payload.length) {
    return null;
  }

  // Try to find metadata for this label
  let weekInfo: WeekMetadata | undefined;
  if (metadata && metadata.length > 0) {
    // Try exact match first
    weekInfo = metadata.find((m) => `SE ${m.week}/${m.year}` === label);

    // If not found, try to extract week number from label
    if (!weekInfo) {
      const weekMatch = label.match(/(\d+)/);
      if (weekMatch) {
        const weekNum = parseInt(weekMatch[1]);
        weekInfo = metadata.find((m) => m.week === weekNum);
      }
    }
  }

  return (
    <div className="bg-white p-3 border rounded-lg shadow-lg">
      <p className="font-semibold text-sm mb-1">{label}</p>

      {/* Show date range if metadata available */}
      {weekInfo && (
        <p className="text-xs text-gray-600 mb-2">
          {format(new Date(weekInfo.start_date), 'dd/MM/yyyy', { locale: es })} -{' '}
          {format(new Date(weekInfo.end_date), 'dd/MM/yyyy', { locale: es })}
        </p>
      )}

      {/* Show data values */}
      {payload.map((entry, index: number) => (
        <p key={index} className="text-sm" style={{ color: entry.color }}>
          <span className="font-medium">{entry.name}:</span> {entry.value?.toLocaleString('es-AR')}
        </p>
      ))}
    </div>
  );
};

export const DynamicChart: React.FC<DynamicChartProps> = ({
  codigo,
  nombre,
  descripcion,
  tipo,
  data,
  config = {},
}) => {
  // Type assertion para config ya que viene como unknown del schema
  const chartConfig = config as { height?: number; [key: string]: unknown };

  // Renderizar el tipo de chart apropiado
  const renderChart = () => {
    if (!data || !data.data) {
      return (
        <div className="flex items-center justify-center h-48 text-gray-500">
          Sin datos disponibles
        </div>
      );
    }

    // Manejar errores del procesador
    if (data.error) {
      // Check if error is structured (new format) or plain string (old format)
      const isStructuredError = typeof data.error === 'object' && 'code' in data.error;

      if (isStructuredError) {
        const error = data.error as ChartError;

        return (
          <div className="flex items-center justify-center h-full min-h-[300px] max-h-[400px] p-6">
            <div className="max-w-md w-full">
              {/* Error card */}
              <div className="border border-gray-200 rounded-lg bg-gray-50 p-6 space-y-4">
                {/* Title */}
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-5 h-5 mt-0.5">
                    <svg className="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div className="flex-1">
                    <h3 className="text-base font-semibold text-gray-900 mb-1">
                      {error.title}
                    </h3>
                    <p className="text-sm text-gray-600 leading-relaxed">
                      {error.message}
                    </p>
                  </div>
                </div>

                {/* Suggestion */}
                {error.suggestion && (
                  <div className="bg-blue-50 border border-blue-100 rounded-md px-4 py-3">
                    <p className="text-sm text-blue-900">
                      {error.suggestion}
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        );
      } else {
        // Fallback for old string errors
        return (
          <div className="flex flex-col items-center justify-center h-48 p-6 text-center">
            <div className="text-yellow-600 font-medium mb-2">
              ⚠️ Advertencia
            </div>
            <div className="text-sm text-gray-600 whitespace-pre-line">
              {data.error as string}
            </div>
          </div>
        );
      }
    }

    const height: number = chartConfig.height || 300;

    // Convertir datos de Chart.js a formato Recharts
    const convertChartJsToRecharts = (chartJsData: { labels: string[]; datasets: Array<{ label?: string; data: number[] }> }) => {
      if (!chartJsData.labels || !chartJsData.datasets) return [];

      // Para line, bar, area charts
      const labels = chartJsData.labels;
      const datasets = chartJsData.datasets;

      return labels.map((label, index: number) => {
        const point: Record<string, string | number> = { name: label };
        datasets.forEach((dataset: { label?: string; data: number[] }) => {
          point[dataset.label || "value"] = dataset.data[index];
        });
        return point;
      });
    };

    // Convertir datos para pie chart
    const convertPieData = (chartJsData: { labels: string[]; datasets: Array<{ data: number[] }> }) => {
      if (!chartJsData.labels || !chartJsData.datasets?.[0]) return [];

      return chartJsData.labels.map((label, index: number) => ({
        name: label,
        value: chartJsData.datasets[0].data[index],
      }));
    };

    switch (tipo) {
      case "line": {
        // Type guard para BaseChartData
        const chartData = data.data as BaseChartData | undefined;
        if (!chartData?.labels || !chartData?.datasets) return null;

        const lineData = convertChartJsToRecharts(chartData);
        const lineKeys = chartData.datasets.map((d) => d.label || "value");
        const lineMetadata = chartData.metadata;

        return (
          <ResponsiveContainer width="100%" height={height}>
            <LineChart data={lineData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="name"
                angle={-45}
                textAnchor="end"
                height={80}
                interval="preserveStartEnd"
                tick={{ fontSize: 11 }}
              />
              <YAxis />
              <Tooltip content={<CustomTooltip metadata={lineMetadata} />} />
              <Legend />
              {lineKeys.map((key: string, index: number) => (
                <Line
                  key={key}
                  type="monotone"
                  dataKey={key}
                  stroke={COLORS[index % COLORS.length]}
                  strokeWidth={2}
                  dot={{ r: 3 }}
                  activeDot={{ r: 5 }}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        );
      }

      case "bar": {
        // Type guard para BaseChartData
        const chartData = data.data as BaseChartData | undefined;
        if (!chartData?.labels || !chartData?.datasets) return null;

        const barData = convertChartJsToRecharts(chartData);
        const barKeys = chartData.datasets.map((d) => d.label || "value");
        const barMetadata = chartData.metadata;

        return (
          <ResponsiveContainer width="100%" height={height}>
            <BarChart data={barData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="name"
                angle={-45}
                textAnchor="end"
                height={80}
                interval="preserveStartEnd"
                tick={{ fontSize: 11 }}
              />
              <YAxis />
              <Tooltip content={<CustomTooltip metadata={barMetadata} />} />
              <Legend />
              {barKeys.map((key: string, index: number) => (
                <Bar
                  key={key}
                  dataKey={key}
                  fill={COLORS[index % COLORS.length]}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        );
      }

      case "pie": {
        // Type guard para BaseChartData
        const chartData = data.data as BaseChartData | undefined;
        if (!chartData?.labels || !chartData?.datasets) return null;

        const pieData = convertPieData(chartData);

        return (
          <ResponsiveContainer width="100%" height={height}>
            <PieChart>
              <Pie
                data={pieData}
                cx="40%"
                cy="50%"
                labelLine={false}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {pieData.map((entry, index: number) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={COLORS[index % COLORS.length]}
                  />
                ))}
              </Pie>
              <Tooltip />
              <Legend
                verticalAlign="middle"
                align="right"
                layout="vertical"
                formatter={(value: string, entry) =>
                  `${value} (${entry.payload?.value || 0})`
                }
              />
            </PieChart>
          </ResponsiveContainer>
        );
      }

      case "area": {
        // Type guard para BaseChartData
        const chartData = data.data as BaseChartData | undefined;
        if (!chartData?.labels || !chartData?.datasets) return null;

        const areaData = convertChartJsToRecharts(chartData);
        const areaKeys = chartData.datasets.map((d) => d.label || "value");
        const areaMetadata = chartData.metadata;

        return (
          <ResponsiveContainer width="100%" height={height}>
            <AreaChart data={areaData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="name"
                angle={-45}
                textAnchor="end"
                height={80}
                interval="preserveStartEnd"
                tick={{ fontSize: 11 }}
              />
              <YAxis />
              <Tooltip content={<CustomTooltip metadata={areaMetadata} />} />
              <Legend />
              {areaKeys.map((key: string, index: number) => (
                <Area
                  key={key}
                  type="monotone"
                  dataKey={key}
                  stroke={COLORS[index % COLORS.length]}
                  fill={COLORS[index % COLORS.length]}
                  fillOpacity={0.6}
                />
              ))}
            </AreaChart>
          </ResponsiveContainer>
        );
      }

      case "d3_pyramid": {
        // Renderizar pirámide poblacional con D3
        // Type guard para PyramidChartData
        const rawChartData = data.data as PyramidChartData | undefined;
        if (!rawChartData || !Array.isArray(rawChartData) || rawChartData.length === 0) {
          return (
            <div className="flex items-center justify-center h-48 text-gray-500">
              No hay datos para la pirámide poblacional
            </div>
          );
        }

        // Transform from wide format to long format for pyramid
        const chartData = rawChartData.flatMap((item) => [
          { age: item.age_group, sex: "M" as const, value: item.male },
          { age: item.age_group, sex: "F" as const, value: item.female },
        ]);

        // Import dinámico del componente de pirámide
        const PopulationPyramid = React.lazy(() =>
          import("./population-pyramid").then(module => ({
            default: module.PopulationPyramid
          }))
        );

        return (
          <React.Suspense fallback={<div>Cargando pirámide...</div>}>
            <PopulationPyramid
              data={chartData}
              height={chartConfig.height || 400}
            />
          </React.Suspense>
        );
      }

      case "mapa": {
        // Renderizar mapa geográfico de Chubut
        // Type guard para MapChartData
        const rawChartData = data.data as MapChartData | undefined;
        if (!rawChartData || !rawChartData.departamentos) {
          return (
            <div className="flex items-center justify-center h-48 text-gray-500">
              No hay datos geográficos disponibles
            </div>
          );
        }

        // Transform to DepartmentData format with default values
        const transformedData = {
          departamentos: rawChartData.departamentos.map((dept) => ({
            codigo_indec: 0,
            nombre: dept.nombre,
            zona_ugd: "",
            poblacion: 0,
            casos: dept.casos,
            tasa_incidencia: 0,
          })),
          total_casos: rawChartData.total_casos,
        };

        // Import dinámico del componente de mapa
        const ChubutMapChart = React.lazy(() => import("./chubut-map-chart"));

        return (
          <React.Suspense fallback={<div>Cargando mapa...</div>}>
            <ChubutMapChart data={transformedData} />
          </React.Suspense>
        );
      }

      default:
        return (
          <div className="flex items-center justify-center h-48 text-gray-500">
            Tipo de gráfico no soportado: {tipo}
          </div>
        );
    }
  };

  return (
    <Card className="dynamic-chart">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm">{nombre}</CardTitle>
        {descripcion && <p className="text-xs text-gray-600">{descripcion}</p>}
      </CardHeader>
      <CardContent>{renderChart()}</CardContent>
    </Card>
  );
};
