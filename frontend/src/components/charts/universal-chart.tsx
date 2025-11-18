"use client";

/**
 * UniversalChart Component
 * Renderiza UniversalChartSpec con datos REALES del backend
 * 100% compatible con el nuevo sistema server-side
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
  ComposedChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from "recharts";
import type { UniversalChartSpec } from "@/lib/types/chart-spec";
import { ChubutMapChart } from "./chubut-map-chart";
import { PopulationPyramid } from "@/features/dashboard/components/charts/population-pyramid";

interface UniversalChartProps {
  spec: UniversalChartSpec;
  className?: string;
}

export function UniversalChart({ spec, className }: UniversalChartProps) {
  // Determinar altura del chart
  const height = spec.config?.config?.height || 400;

  // Verificar si hay datos
  const hasData = React.useMemo(() => {
    if (spec.data.type === "d3_pyramid") {
      // Verificar si hay al menos un grupo con valores > 0
      return spec.data.data.some((item) => item.male > 0 || item.female > 0);
    }
    if (spec.data.type === "mapa") {
      return spec.data.data.departamentos.length > 0;
    }
    // Para line, bar, area, pie
    if ("data" in spec.data) {
      return (
        spec.data.data.labels.length > 0 ||
        spec.data.data.datasets.some((d) => d.data.length > 0)
      );
    }
    return false;
  }, [spec.data]);

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>{spec.title}</CardTitle>
        {spec.description && (
          <p className="text-sm text-muted-foreground">{spec.description}</p>
        )}
      </CardHeader>
      <CardContent>
        {!hasData ? (
          <div
            className="flex items-center justify-center bg-gray-50 rounded-lg border-2 border-dashed border-gray-300"
            style={{ height: height }}
          >
            <div className="text-center p-6">
              <svg
                className="mx-auto h-12 w-12 text-gray-400 mb-3"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                />
              </svg>
              <p className="text-sm font-medium text-gray-900 mb-1">
                No hay datos disponibles
              </p>
              <p className="text-xs text-gray-500">
                No se encontraron datos para los filtros seleccionados
              </p>
            </div>
          </div>
        ) : (
          <>
            {spec.type === "line" && spec.data.type === "line" && (
              <LineChartRenderer spec={spec} height={height} />
            )}
            {spec.type === "bar" && spec.data.type === "bar" && (
              <BarChartRenderer spec={spec} height={height} />
            )}
            {spec.type === "area" && spec.data.type === "area" && (
              <AreaChartRenderer spec={spec} height={height} />
            )}
            {spec.type === "pie" && spec.data.type === "pie" && (
              <PieChartRenderer spec={spec} height={height} />
            )}
            {spec.type === "d3_pyramid" && spec.data.type === "d3_pyramid" && (
              <PyramidChartRenderer spec={spec} height={height} />
            )}
            {spec.type === "mapa" && spec.data.type === "mapa" && (
              <MapChartRenderer spec={spec} height={height} />
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}

// Line Chart Renderer
function LineChartRenderer({
  spec,
  height,
}: {
  spec: UniversalChartSpec;
  height: number;
}) {
  if (spec.data.type !== "line") return null;

  const { data } = spec.data;
  const config = spec.config.type === "line" ? spec.config.config : {};

  // Transformar datos para Recharts
  const chartData = data.labels.map((label, index) => {
    const point: Record<string, string | number> = { name: label };
    data.datasets.forEach((dataset) => {
      if (dataset.label) {
        const rawValue = dataset.data[index];
        point[dataset.label] = rawValue;
      }
    });
    return point;
  });

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={chartData}>
        {config.showGrid !== false && <CartesianGrid strokeDasharray="3 3" />}
        <XAxis dataKey="name" />
        <YAxis />
        <Tooltip />
        {config.showLegend !== false && <Legend />}
        {data.datasets.map((dataset, index) => (
          <Line
            key={index}
            type={config.curved ? "monotone" : "linear"}
            dataKey={dataset.label || `Series ${index + 1}`}
            stroke={dataset.color || `hsl(${index * 60}, 70%, 50%)`}
            strokeWidth={2}
            dot={config.showPoints !== false}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}

// Bar Chart Renderer
function BarChartRenderer({
  spec,
  height,
}: {
  spec: UniversalChartSpec;
  height: number;
}) {
  if (spec.data.type !== "bar") return null;

  const { data } = spec.data;
  const config = spec.config.type === "bar" ? spec.config.config : {};

  const chartData = data.labels.map((label, index) => {
    const point: Record<string, string | number> = { name: label };
    data.datasets.forEach((dataset) => {
      if (dataset.label) {
        const rawValue = dataset.data[index];
        const numericValue = rawValue;
        point[dataset.label] = numericValue || 0;
      }
    });
    return point;
  });

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart
        data={chartData}
        layout={config.horizontal ? "vertical" : "horizontal"}
      >
        {config.showGrid !== false && <CartesianGrid strokeDasharray="3 3" />}
        <XAxis
          type={config.horizontal ? "number" : "category"}
          dataKey={config.horizontal ? undefined : "name"}
        />
        <YAxis
          type={config.horizontal ? "category" : "number"}
          dataKey={config.horizontal ? "name" : undefined}
        />
        <Tooltip />
        {config.showLegend !== false && data.datasets.length > 1 && <Legend />}
        {data.datasets.map((dataset, index) => (
          <Bar
            key={index}
            dataKey={dataset.label || `Series ${index + 1}`}
            fill={dataset.color || `hsl(${index * 60}, 70%, 50%)`}
            stackId={config.stacked ? "stack" : undefined}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}

// Area Chart Renderer
function AreaChartRenderer({
  spec,
  height,
}: {
  spec: UniversalChartSpec;
  height: number;
}) {
  if (spec.data.type !== "area") return null;

  const { data } = spec.data;
  const config = spec.config.type === "area" ? spec.config.config : {};

  const chartData = data.labels.map((label, index) => {
    const point: Record<string, string | number> = { name: label };
    data.datasets.forEach((dataset) => {
      if (dataset.label) {
        const rawValue = dataset.data[index];
        const numericValue = rawValue;
        point[dataset.label] = numericValue || 0;
      }
    });
  });
}

// Pie Chart Renderer
function PieChartRenderer({
  spec,
  height,
}: {
  spec: UniversalChartSpec;
  height: number;
}) {
  if (spec.data.type !== "pie") return null;

  const { data } = spec.data;
  const config = spec.config.type === "pie" ? spec.config.config : {};

  const dataset = data.datasets[0];
  const chartData = data.labels.map((label, index) => ({
    name: label,
    value: dataset.data[index] || 0,
  }));

  const COLORS = [
    "#0088FE",
    "#00C49F",
    "#FFBB28",
    "#FF8042",
    "#8884d8",
    "#82ca9d",
  ];

  return (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          labelLine={config.showPercentages !== false}
          label={config.showPercentages !== false ? renderPieLabel : undefined}
          outerRadius={height / 3}
          innerRadius={config.innerRadius || 0}
          fill="#8884d8"
          dataKey="value"
        >
          {chartData.map((_, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip />
        {config.showLegend !== false && <Legend />}
      </PieChart>
    </ResponsiveContainer>
  );
}

function renderPieLabel(entry: { name: string; percent: number }) {
  return `${entry.name}: ${(entry.percent * 100).toFixed(0)}%`;
}

// Pyramid Chart Renderer (usando D3)
function PyramidChartRenderer({
  spec,
  height,
}: {
  spec: UniversalChartSpec;
  height: number;
}) {
  if (spec.data.type !== "d3_pyramid") return null;

  const { data } = spec.data;

  // Transformar datos al formato que espera PopulationPyramid
  // El backend retorna: [{ age_group: "0-4", male: 10, female: 12 }, ...]
  // PopulationPyramid espera: [{ age: "0-4", sex: "M", value: 10 }, { age: "0-4", sex: "F", value: 12 }, ...]
  const pyramidData: Array<{ age: string; sex: "M" | "F"; value: number }> = [];

  data.forEach((item) => {
    // Agregar masculino
    pyramidData.push({
      age: item.age_group,
      sex: "M",
      value: item.male,
    });
    // Agregar femenino
    pyramidData.push({
      age: item.age_group,
      sex: "F",
      value: item.female,
    });
  });

  return (
    <div className="w-full">
      <PopulationPyramid data={pyramidData} width={800} height={height} />
    </div>
  );
}

// Map Chart Renderer (SVG coroplético de Chubut)
function MapChartRenderer({
  spec,
  height,
}: {
  spec: UniversalChartSpec;
  height: number;
}) {
  if (spec.data.type !== "mapa") return null;

  const { data } = spec.data;

  return (
    <div className="w-full" style={{ height: height }}>
      <ChubutMapChart data={data} />
    </div>
  );
}
