/**
 * Componente de Análisis de Rabia Animal
 * Gráficos múltiples: temporal, por especies, ubicación y positividad
 */

import React, { useMemo, useState } from "react";
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
  Line,
} from "recharts";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  AlertTriangle,
  Activity,
  MapPin,
  Stethoscope,
  Calendar,
  PieChart as PieChartIcon,
} from "lucide-react";
import { EpidemiologicalFilters, ChartConfig } from "../../types";
import { useAnimalRabiesData } from "../../hooks/useEpidemiologicalData";
import type { TooltipProps, AnimalRabiesPayload } from "../../types/recharts";

// Configuración de colores (replicando el original)
const COLORS = {
  cases: "rgb(255, 99, 132)", // Rosa para casos
  tested: "rgb(54, 162, 235)", // Azul para muestras
  positive: "rgb(214, 39, 40)", // Rojo para positivos
  positivityRate: "rgb(255, 159, 64)", // Naranja para tasa
  species: [
    "rgb(255, 99, 132)", // Rosa
    "rgb(54, 162, 235)", // Azul
    "rgb(255, 205, 86)", // Amarillo
    "rgb(75, 192, 192)", // Verde agua
    "rgb(153, 102, 255)", // Púrpura
    "rgb(255, 159, 64)", // Naranja
    "rgb(199, 199, 199)", // Gris
    "rgb(83, 102, 255)", // Azul índigo
  ],
  locations: [
    "rgb(75, 192, 192)", // Verde agua
    "rgb(255, 205, 86)", // Amarillo
    "rgb(255, 99, 132)", // Rosa
    "rgb(54, 162, 235)", // Azul
    "rgb(153, 102, 255)", // Púrpura
    "rgb(255, 159, 64)", // Naranja
  ],
} as const;

interface AnimalRabiesChartProps {
  filters?: EpidemiologicalFilters;
  chartConfig?: ChartConfig;
  onDateRangeSelect?: (startDate: string, endDate: string) => void;
  onSpeciesSelect?: (species: string) => void;
  defaultView?: "temporal" | "species" | "location" | "analysis";
  showPositivityRate?: boolean;
}

// Tooltip personalizado para serie temporal
const TimeSeriesTooltip: React.FC<TooltipProps<AnimalRabiesPayload>> = ({ active, payload, label }) => {
  if (!active || !payload || !payload.length) return null;

  const date = label;
  const data = payload[0]?.payload;

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-4 max-w-sm">
      <div className="border-b border-gray-200 pb-2 mb-2">
        <p className="font-semibold text-gray-800">
          {date ? new Date(date).toLocaleDateString("es-ES", {
            year: "numeric",
            month: "long",
            day: "numeric",
          }) : 'Fecha no disponible'}
        </p>
        <p className="text-sm text-gray-600">
          {data?.species} - {data?.location}
        </p>
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div
              className="w-3 h-3 rounded"
              style={{ backgroundColor: COLORS.cases }}
            />
            <span className="text-sm text-gray-700">Casos:</span>
          </div>
          <span className="text-sm font-medium text-gray-900">
            {data?.cases || 0}
          </span>
        </div>

        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div
              className="w-3 h-3 rounded"
              style={{ backgroundColor: COLORS.tested }}
            />
            <span className="text-sm text-gray-700">Muestras:</span>
          </div>
          <span className="text-sm font-medium text-blue-700">
            {data?.tested || 0}
          </span>
        </div>

        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div
              className="w-3 h-3 rounded"
              style={{ backgroundColor: COLORS.positive }}
            />
            <span className="text-sm text-gray-700">Positivos:</span>
          </div>
          <span className="text-sm font-medium text-red-700">
            {data?.positive || 0}
          </span>
        </div>

        {data?.positivityRate !== undefined && (
          <div className="border-t border-gray-200 pt-2">
            <div className="flex items-center justify-between gap-4">
              <span className="text-sm text-orange-600">Positividad:</span>
              <span className="text-sm font-medium text-orange-700">
                {data.positivityRate.toFixed(1)}%
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Tooltip para gráficos demográficos
const DemographicTooltip: React.FC<TooltipProps<AnimalRabiesPayload>> = ({ active, payload, label }) => {
  if (!active || !payload || !payload.length) return null;

  const data = payload[0]?.payload;

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3">
      <p className="font-semibold text-gray-800 mb-2">{label || data?.name}</p>
      <div className="flex items-center justify-between gap-4">
        <span className="text-sm text-gray-700">Casos:</span>
        <span className="text-sm font-medium text-gray-900">
          {data?.value || payload?.[0]?.value || 0}
        </span>
      </div>
    </div>
  );
};

// Componente de estadísticas clave
interface RabiesStatsProps {
  statistics: {
    speciesDistribution: Record<string, number>;
    locationDistribution: Record<string, number>;
    positivityRate: number;
  } | null;
  totalCases: number;
  totalTested: number;
  totalPositive: number;
  overallPositivityRate: number;
}

const RabiesStats: React.FC<RabiesStatsProps> = ({
  statistics,
  totalCases,
  totalTested,
  totalPositive,
  overallPositivityRate,
}) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
      <div className="p-3 bg-red-50 rounded-lg border border-red-200">
        <div className="flex items-center gap-2 mb-1">
          <Activity className="h-4 w-4 text-red-500" />
          <span className="text-sm font-medium text-red-800">Casos</span>
        </div>
        <div className="text-lg font-bold text-red-900">
          {totalCases.toLocaleString()}
        </div>
        <div className="text-sm text-red-700">Total registrados</div>
      </div>

      <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
        <div className="flex items-center gap-2 mb-1">
          <Stethoscope className="h-4 w-4 text-blue-500" />
          <span className="text-sm font-medium text-blue-800">Muestras</span>
        </div>
        <div className="text-lg font-bold text-blue-900">
          {totalTested.toLocaleString()}
        </div>
        <div className="text-sm text-blue-700">Procesadas</div>
      </div>

      <div className="p-3 bg-orange-50 rounded-lg border border-orange-200">
        <div className="flex items-center gap-2 mb-1">
          <AlertTriangle className="h-4 w-4 text-orange-500" />
          <span className="text-sm font-medium text-orange-800">Positivos</span>
        </div>
        <div className="text-lg font-bold text-orange-900">
          {totalPositive.toLocaleString()}
        </div>
        <div className="text-sm text-orange-700">Confirmados</div>
      </div>

      <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
        <div className="flex items-center gap-2 mb-1">
          <PieChartIcon className="h-4 w-4 text-gray-500" />
          <span className="text-sm font-medium text-gray-800">Positividad</span>
        </div>
        <div className="text-lg font-bold text-gray-900">
          {overallPositivityRate.toFixed(1)}%
        </div>
        <div className="text-sm text-gray-700">Tasa general</div>
      </div>
    </div>
  );
};

export const AnimalRabiesChart: React.FC<AnimalRabiesChartProps> = ({
  filters,
  chartConfig = {},
  onDateRangeSelect,
  onSpeciesSelect,
  defaultView = "temporal",
  showPositivityRate = true,
}) => {
  const [activeTab, setActiveTab] = useState(defaultView);
  const [selectedSpecies, setSelectedSpecies] = useState<string | null>(null);

  const { processedData, loading, error, refetch } =
    useAnimalRabiesData(filters);

  // Procesar datos para visualización
  const {
    timeSeriesData,
    speciesData,
    locationData,
    statistics,
    title,
    aggregatedData,
  } = useMemo(() => {
    if (!processedData) {
      return {
        timeSeriesData: [],
        speciesData: [],
        locationData: [],
        statistics: null,
        title: "",
        aggregatedData: null,
      };
    }

    const { timeSeriesData, speciesData, locationData, statistics } =
      processedData;

    // Calcular estadísticas agregadas
    const totalCases = timeSeriesData.reduce(
      (sum, point) => sum + point.cases,
      0
    );
    const totalTested = timeSeriesData.reduce(
      (sum, point) => sum + point.tested,
      0
    );
    const totalPositive = timeSeriesData.reduce(
      (sum, point) => sum + point.positive,
      0
    );
    const overallPositivityRate =
      totalTested > 0 ? (totalPositive / totalTested) * 100 : 0;

    // Agregar colores a datos de especies
    const coloredSpeciesData = speciesData.map((item, index) => ({
      ...item,
      color: COLORS.species[index % COLORS.species.length],
    }));

    // Agregar colores a datos de ubicación
    const coloredLocationData = locationData.map((item, index) => ({
      ...item,
      color: COLORS.locations[index % COLORS.locations.length],
    }));

    const chartTitle = `Análisis de Rabia Animal - ${totalCases} casos, ${totalPositive} positivos`;

    return {
      timeSeriesData,
      speciesData: coloredSpeciesData,
      locationData: coloredLocationData,
      statistics,
      title: chartTitle,
      aggregatedData: {
        totalCases,
        totalTested,
        totalPositive,
        overallPositivityRate,
      },
    };
  }, [processedData]);

  const handleSpeciesClick = (data: { name?: string }) => {
    const species = data.name;
    setSelectedSpecies(selectedSpecies === species ? null : species || null);
    if (onSpeciesSelect) {
      onSpeciesSelect(species || '');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="flex items-center gap-2">
          <div className="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full" />
          <span>Cargando análisis de rabia animal...</span>
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

  return (
    <div className="w-full">
      <div className="mb-4">
        {aggregatedData && statistics && (
          <RabiesStats
            statistics={statistics}
            totalCases={aggregatedData.totalCases}
            totalTested={aggregatedData.totalTested}
            totalPositive={aggregatedData.totalPositive}
            overallPositivityRate={aggregatedData.overallPositivityRate}
          />
        )}
      </div>

      <div>
        <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as "temporal" | "species" | "location" | "analysis")} className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="temporal">
              <Calendar className="h-4 w-4 mr-2" />
              Temporal
            </TabsTrigger>
            <TabsTrigger value="species">
              <Activity className="h-4 w-4 mr-2" />
              Especies
            </TabsTrigger>
            <TabsTrigger value="location">
              <MapPin className="h-4 w-4 mr-2" />
              Ubicación
            </TabsTrigger>
            <TabsTrigger value="analysis">
              <Stethoscope className="h-4 w-4 mr-2" />
              Análisis
            </TabsTrigger>
          </TabsList>

          <TabsContent value="temporal" className="mt-4">
            <div
              className="w-full"
              style={{ height: chartConfig.height || 400 }}
            >
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart
                  data={timeSeriesData}
                  margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
                  onClick={(data) => {
                    if (
                      data?.activePayload?.[0]?.payload &&
                      onDateRangeSelect
                    ) {
                      const point = data.activePayload[0].payload;
                      const date = new Date(point.date);
                      const startDate = new Date(date);
                      startDate.setDate(date.getDate() - 7);
                      const endDate = new Date(date);
                      endDate.setDate(date.getDate() + 7);
                      onDateRangeSelect(
                        startDate.toISOString(),
                        endDate.toISOString()
                      );
                    }
                  }}
                >
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="rgba(128, 128, 128, 0.2)"
                  />

                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 11 }}
                    tickLine={{ stroke: "#666" }}
                    axisLine={{ stroke: "#666" }}
                    tickFormatter={(value) =>
                      new Date(value).toLocaleDateString("es-ES", {
                        month: "short",
                        day: "numeric",
                      })
                    }
                    angle={-45}
                    textAnchor="end"
                    height={80}
                  />

                  <YAxis
                    yAxisId="left"
                    tick={{ fontSize: 12 }}
                    tickLine={{ stroke: "#666" }}
                    axisLine={{ stroke: "#666" }}
                    label={{
                      value: "Casos/Muestras",
                      angle: -90,
                      position: "insideLeft",
                    }}
                  />

                  {showPositivityRate && (
                    <YAxis
                      yAxisId="right"
                      orientation="right"
                      tick={{ fontSize: 12 }}
                      tickLine={{ stroke: "#666" }}
                      axisLine={{ stroke: "#666" }}
                      label={{
                        value: "Positividad (%)",
                        angle: 90,
                        position: "insideRight",
                      }}
                    />
                  )}

                  <Bar
                    yAxisId="left"
                    dataKey="tested"
                    fill={COLORS.tested}
                    fillOpacity={0.6}
                    name="Muestras procesadas"
                  />

                  <Bar
                    yAxisId="left"
                    dataKey="positive"
                    fill={COLORS.positive}
                    name="Casos positivos"
                  />

                  {showPositivityRate && (
                    <Line
                      yAxisId="right"
                      type="monotone"
                      dataKey="positivityRate"
                      stroke={COLORS.positivityRate}
                      strokeWidth={3}
                      dot={{
                        fill: COLORS.positivityRate,
                        strokeWidth: 2,
                        r: 4,
                      }}
                      name="Tasa de positividad"
                    />
                  )}

                  <Tooltip content={<TimeSeriesTooltip />} />
                  <Legend />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </TabsContent>

          <TabsContent value="species" className="mt-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Distribución por especies */}
              <div>
                <h4 className="text-sm font-semibold text-gray-800 mb-3">
                  Distribución por Especies
                </h4>
                <div style={{ height: 350 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={speciesData}
                        cx="50%"
                        cy="50%"
                        innerRadius={50}
                        outerRadius={120}
                        paddingAngle={5}
                        dataKey="value"
                        onClick={(data: any) => {
                        if (data?.activePayload?.[0]?.payload) {
                          handleSpeciesClick({ name: data.activePayload[0].payload.name });
                        }
                      }}
                      >
                        {speciesData.map((entry, index) => (
                          <Cell
                            key={`cell-${index}`}
                            fill={entry.color}
                            stroke={
                              selectedSpecies === entry.name ? "#333" : "none"
                            }
                            strokeWidth={selectedSpecies === entry.name ? 2 : 0}
                          />
                        ))}
                      </Pie>
                      <Tooltip content={<DemographicTooltip />} />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Ranking de especies */}
              <div>
                <h4 className="text-sm font-semibold text-gray-800 mb-3">
                  Ranking por Casos
                </h4>
                <div style={{ height: 350 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={speciesData}
                      margin={{ top: 20, right: 30, left: 20, bottom: 80 }}
                      onClick={(data: any) => {
                        if (data?.activePayload?.[0]?.payload) {
                          handleSpeciesClick({ name: data.activePayload[0].payload.name });
                        }
                      }}
                    >
                      <CartesianGrid
                        strokeDasharray="3 3"
                        stroke="rgba(128, 128, 128, 0.2)"
                      />
                      <XAxis
                        dataKey="name"
                        tick={{ fontSize: 11 }}
                        tickLine={{ stroke: "#666" }}
                        axisLine={{ stroke: "#666" }}
                        height={100}
                        textAnchor="end"
                      />
                      <YAxis />
                      <Tooltip content={<DemographicTooltip />} />
                      <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                        {speciesData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>

            {/* Detalles por especie */}
            <div className="mt-6 p-3 bg-gray-50 rounded-lg">
              <h4 className="text-sm font-semibold text-gray-800 mb-2">
                Detalles por Especies
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {speciesData.map((species) => {
                  const percentage =
                    aggregatedData?.totalCases && aggregatedData.totalCases > 0
                      ? (species.value / aggregatedData.totalCases) * 100
                      : 0;

                  return (
                    <div
                      key={species.name}
                      className={`p-3 rounded border cursor-pointer transition-colors ${
                        selectedSpecies === species.name
                          ? "bg-blue-100 border-blue-300"
                          : "bg-white border-gray-200 hover:bg-gray-50"
                      }`}
                      onClick={() => handleSpeciesClick(species)}
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <div
                          className="w-4 h-4 rounded"
                          style={{ backgroundColor: species.color }}
                        />
                        <span className="text-sm font-medium text-gray-800">
                          {species.name}
                        </span>
                      </div>
                      <div className="text-lg font-bold text-gray-900">
                        {species.value.toLocaleString()}
                      </div>
                      <div className="text-sm text-gray-600">
                        {percentage.toFixed(1)}% del total
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </TabsContent>

          <TabsContent value="location" className="mt-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Distribución por ubicación */}
              <div>
                <h4 className="text-sm font-semibold text-gray-800 mb-3">
                  Distribución por Ubicación
                </h4>
                <div style={{ height: 350 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={locationData}
                      margin={{ top: 20, right: 30, left: 20, bottom: 100 }}
                    >
                      <CartesianGrid
                        strokeDasharray="3 3"
                        stroke="rgba(128, 128, 128, 0.2)"
                      />
                      <XAxis
                        dataKey="name"
                        tick={{ fontSize: 11 }}
                        tickLine={{ stroke: "#666" }}
                        axisLine={{ stroke: "#666" }}
                        height={120}
                        textAnchor="end"
                      />
                      <YAxis />
                      <Tooltip content={<DemographicTooltip />} />
                      <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                        {locationData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Mapa de calor simulado */}
              <div>
                <h4 className="text-sm font-semibold text-gray-800 mb-3">
                  Intensidad por Región
                </h4>
                <div className="grid grid-cols-2 gap-2 h-80 overflow-y-auto">
                  {locationData
                    .sort((a, b) => b.value - a.value)
                    .map((location, index) => {
                      const intensity =
                        aggregatedData?.totalCases && aggregatedData.totalCases > 0
                          ? location.value /
                            Math.max(...locationData.map((l) => l.value))
                          : 0;

                      return (
                        <div
                          key={location.name}
                          className="p-3 rounded border"
                          style={{
                            backgroundColor: `rgba(${location.color
                              .match(/\d+/g)
                              ?.join(",")}, ${intensity})`,
                          }}
                        >
                          <div className="text-sm font-medium text-gray-800 mb-1">
                            {location.name}
                          </div>
                          <div className="text-lg font-bold text-gray-900">
                            {location.value}
                          </div>
                          <div className="text-xs text-gray-600">
                            Ranking #{index + 1}
                          </div>
                        </div>
                      );
                    })}
                </div>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="analysis" className="mt-4">
            <div className="space-y-6">
              {/* Análisis de positividad por especie */}
              <div>
                <h4 className="text-sm font-semibold text-gray-800 mb-3">
                  Tasa de Positividad por Especie
                </h4>
                <div style={{ height: 300 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={speciesData.map((s) => ({
                        ...s,
                        positivityRate:
                          statistics?.speciesDistribution?.[s.name] && statistics.speciesDistribution[s.name] > 0
                            ? (s.value /
                                statistics.speciesDistribution[s.name]) *
                              100
                            : 0,
                      }))}
                      margin={{ top: 20, right: 30, left: 20, bottom: 80 }}
                    >
                      <CartesianGrid
                        strokeDasharray="3 3"
                        stroke="rgba(128, 128, 128, 0.2)"
                      />
                      <XAxis
                        dataKey="name"
                        tick={{ fontSize: 11 }}
                        tickLine={{ stroke: "#666" }}
                        axisLine={{ stroke: "#666" }}
                        height={100}
                        textAnchor="end"
                      />
                      <YAxis
                        label={{
                          value: "Tasa de Positividad (%)",
                          angle: -90,
                          position: "insideLeft",
                        }}
                      />
                      <Tooltip />
                      <Bar dataKey="positivityRate" radius={[4, 4, 0, 0]}>
                        {speciesData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Análisis estadístico final */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 bg-red-50 rounded-lg border border-red-200">
                  <h5 className="text-sm font-semibold text-red-800 mb-2">
                    Especie de Mayor Riesgo
                  </h5>
                  <div className="text-2xl font-bold text-red-900 mb-1">
                    {speciesData[0]?.name || "N/A"}
                  </div>
                  <p className="text-sm text-red-700">
                    {speciesData[0]?.value || 0} casos registrados
                  </p>
                </div>

                <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                  <h5 className="text-sm font-semibold text-blue-800 mb-2">
                    Región Crítica
                  </h5>
                  <div className="text-2xl font-bold text-blue-900 mb-1 truncate">
                    {locationData[0]?.name || "N/A"}
                  </div>
                  <p className="text-sm text-blue-700">
                    Mayor concentración de casos
                  </p>
                </div>

                <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                  <h5 className="text-sm font-semibold text-green-800 mb-2">
                    Cobertura de Muestreo
                  </h5>
                  <div className="text-2xl font-bold text-green-900 mb-1">
                    {aggregatedData?.totalTested && aggregatedData.totalTested > 0 &&
                    aggregatedData?.totalCases && aggregatedData.totalCases > 0
                      ? (
                          (aggregatedData.totalTested /
                            aggregatedData.totalCases) *
                          100
                        ).toFixed(0)
                      : "0"}
                    %
                  </div>
                  <p className="text-sm text-green-700">
                    Casos con muestra procesada
                  </p>
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default AnimalRabiesChart;
