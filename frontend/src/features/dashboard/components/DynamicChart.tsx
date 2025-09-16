"use client";

/**
 * Componente genérico para renderizar charts dinámicos con Recharts y D3
 */
import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import AgePyramidChart from "./charts/AgePyramidChart";
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
} from "recharts";

interface DynamicChartProps {
  codigo: string;
  nombre: string;
  descripcion?: string;
  tipo: string;
  data: any;
  config?: any;
}

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

export const DynamicChart: React.FC<DynamicChartProps> = ({
  codigo,
  nombre,
  descripcion,
  tipo,
  data,
  config = {},
}) => {
  console.log({ data, tipo, nombre, descripcion });
  // Renderizar el tipo de chart apropiado
  const renderChart = () => {
    if (!data || !data.data) {
      return (
        <div className="flex items-center justify-center h-48 text-gray-500">
          Sin datos disponibles
        </div>
      );
    }

    const height = config.height || 300;

    // Convertir datos de Chart.js a formato Recharts
    const convertChartJsToRecharts = (chartJsData: any) => {
      if (!chartJsData.labels || !chartJsData.datasets) return [];

      // Para line, bar, area charts
      const labels = chartJsData.labels;
      const datasets = chartJsData.datasets;

      return labels.map((label: any, index: number) => {
        const point: any = { name: label };
        datasets.forEach((dataset: any) => {
          point[dataset.label || "value"] = dataset.data[index];
        });
        return point;
      });
    };

    // Convertir datos para pie chart
    const convertPieData = (chartJsData: any) => {
      if (!chartJsData.labels || !chartJsData.datasets?.[0]) return [];

      return chartJsData.labels.map((label: any, index: number) => ({
        name: label,
        value: chartJsData.datasets[0].data[index],
      }));
    };

    switch (tipo) {
      case "line":
        const lineData = convertChartJsToRecharts(data.data);
        const lineKeys = data.data.datasets?.map(
          (d: any) => d.label || "value"
        ) || ["value"];

        return (
          <ResponsiveContainer width="100%" height={height}>
            <LineChart data={lineData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              {lineKeys.map((key: string, index: number) => (
                <Line
                  key={key}
                  type="monotone"
                  dataKey={key}
                  stroke={COLORS[index % COLORS.length]}
                  strokeWidth={2}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        );

      case "bar":
        const barData = convertChartJsToRecharts(data.data);
        const barKeys = data.data.datasets?.map(
          (d: any) => d.label || "value"
        ) || ["value"];

        return (
          <ResponsiveContainer width="100%" height={height}>
            <BarChart data={barData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
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

      case "pie":
        const pieData = convertPieData(data.data);

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
                {pieData.map((entry: any, index: number) => (
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
                formatter={(value: string, entry: any) =>
                  `${value} (${entry.payload.value})`
                }
              />
            </PieChart>
          </ResponsiveContainer>
        );

      case "area":
        const areaData = convertChartJsToRecharts(data.data);
        const areaKeys = data.data.datasets?.map(
          (d: any) => d.label || "value"
        ) || ["value"];

        return (
          <ResponsiveContainer width="100%" height={height}>
            <AreaChart data={areaData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
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

      case "d3_pyramid":
        // Renderizar pirámide poblacional con D3
        const pyramidHeight = config.height || 300;

        if (!data.data || !Array.isArray(data.data)) {
          return (
            <div className="flex items-center justify-center h-48 text-gray-500">
              No hay datos para la pirámide poblacional
            </div>
          );
        }

        return (
          <div className="w-full flex justify-center" style={{ height: pyramidHeight }}>
            <AgePyramidChart data={data.data} width={600} height={pyramidHeight} />
          </div>
        );

      case "mapa":
        // Renderizar mapa geográfico de Chubut
        if (!data.data || !data.data.departamentos) {
          return (
            <div className="flex items-center justify-center h-48 text-gray-500">
              No hay datos geográficos disponibles
            </div>
          );
        }

        // Import dinámico del componente de mapa
        const ChubutMapChart = React.lazy(() => import("./charts/ChubutMapChart"));

        return (
          <React.Suspense fallback={<div>Cargando mapa...</div>}>
            <ChubutMapChart data={data.data} />
          </React.Suspense>
        );

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
