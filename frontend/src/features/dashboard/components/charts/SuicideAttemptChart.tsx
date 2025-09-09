/**
 * Componente de Análisis de Intento de Suicidio
 * Gráficos múltiples: temporal, demográfico y por factores de riesgo
 */

import React, { useMemo, useState } from 'react';
import {
  LineChart,
  Line,
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
  Area,
  AreaChart,
} from 'recharts';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AlertTriangle, TrendingUp, Users, Calendar, Heart, AlertCircle } from 'lucide-react';
import {
  EpidemiologicalFilters,
  ChartConfig,
} from '../../types';
import { useSuicideAttemptData } from '../../hooks/useEpidemiologicalData';

// Configuración de colores (replicando el original)
const COLORS = {
  attempts: 'rgb(255, 99, 132)',      // Rosa para intentos
  deaths: 'rgb(214, 39, 40)',         // Rojo para fallecimientos
  mortalityRate: 'rgb(255, 159, 64)', // Naranja para tasa
  male: 'rgb(54, 162, 235)',          // Azul para masculino
  female: 'rgb(255, 99, 132)',        // Rosa para femenino
  ageGroups: [
    'rgb(255, 99, 132)',
    'rgb(54, 162, 235)', 
    'rgb(255, 205, 86)',
    'rgb(75, 192, 192)',
    'rgb(153, 102, 255)',
    'rgb(255, 159, 64)',
  ],
} as const;

interface SuicideAttemptChartProps {
  filters?: EpidemiologicalFilters;
  chartConfig?: ChartConfig;
  onTimeRangeSelect?: (startWeek: number, endWeek: number, year: number) => void;
  showDemographics?: boolean;
  defaultView?: 'temporal' | 'demographics' | 'risk-factors';
}

// Tooltip personalizado para serie temporal
const TimeSeriesTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload || !payload.length) return null;

  const week = label;
  const data = payload[0]?.payload;

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-4 max-w-sm">
      <div className="border-b border-gray-200 pb-2 mb-2">
        <p className="font-semibold text-gray-800">
          Semana {week} - Año {data?.year}
        </p>
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded" style={{ backgroundColor: COLORS.attempts }} />
            <span className="text-sm text-gray-700">Intentos:</span>
          </div>
          <span className="text-sm font-medium text-gray-900">
            {data?.attempts || 0}
          </span>
        </div>

        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded" style={{ backgroundColor: COLORS.deaths }} />
            <span className="text-sm text-gray-700">Fallecimientos:</span>
          </div>
          <span className="text-sm font-medium text-red-700">
            {data?.deaths || 0}
          </span>
        </div>

        {data?.mortalityRate > 0 && (
          <div className="border-t border-gray-200 pt-2">
            <div className="flex items-center justify-between gap-4">
              <span className="text-sm text-red-600">Tasa letalidad:</span>
              <span className="text-sm font-medium text-red-700">
                {data.mortalityRate.toFixed(2)}%
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Tooltip para gráficos demográficos
const DemographicTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload || !payload.length) return null;

  const data = payload[0]?.payload;

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3">
      <p className="font-semibold text-gray-800 mb-2">{label || data.name}</p>
      <div className="flex items-center justify-between gap-4">
        <span className="text-sm text-gray-700">Casos:</span>
        <span className="text-sm font-medium text-gray-900">
          {data.value || payload[0].value}
        </span>
      </div>
    </div>
  );
};

// Componente de estadísticas clave
const SuicideStats: React.FC<{
  demographics: any;
  totalAttempts: number;
  totalDeaths: number;
  mortalityRate: number;
}> = ({ demographics, totalAttempts, totalDeaths, mortalityRate }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
      <div className="p-3 bg-red-50 rounded-lg border border-red-200">
        <div className="flex items-center gap-2 mb-1">
          <AlertCircle className="h-4 w-4 text-red-500" />
          <span className="text-sm font-medium text-red-800">Intentos</span>
        </div>
        <div className="text-lg font-bold text-red-900">
          {totalAttempts.toLocaleString()}
        </div>
        <div className="text-sm text-red-700">
          Total registrados
        </div>
      </div>

      <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
        <div className="flex items-center gap-2 mb-1">
          <Heart className="h-4 w-4 text-gray-500" />
          <span className="text-sm font-medium text-gray-800">Fallecimientos</span>
        </div>
        <div className="text-lg font-bold text-gray-900">
          {totalDeaths.toLocaleString()}
        </div>
        <div className="text-sm text-gray-700">
          Casos fatales
        </div>
      </div>

      <div className="p-3 bg-orange-50 rounded-lg border border-orange-200">
        <div className="flex items-center gap-2 mb-1">
          <TrendingUp className="h-4 w-4 text-orange-500" />
          <span className="text-sm font-medium text-orange-800">Tasa Letalidad</span>
        </div>
        <div className="text-lg font-bold text-orange-900">
          {mortalityRate.toFixed(2)}%
        </div>
        <div className="text-sm text-orange-700">
          Porcentaje fatal
        </div>
      </div>

      <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
        <div className="flex items-center gap-2 mb-1">
          <Users className="h-4 w-4 text-blue-500" />
          <span className="text-sm font-medium text-blue-800">Grupo Principal</span>
        </div>
        <div className="text-lg font-bold text-blue-900 truncate">
          {Object.keys(demographics?.ageGroups || {}).reduce(
            (a, b) => (demographics.ageGroups[a] || 0) > (demographics.ageGroups[b] || 0) ? a : b,
            Object.keys(demographics?.ageGroups || {})[0] || 'N/A'
          )}
        </div>
        <div className="text-sm text-blue-700">
          Mayor incidencia
        </div>
      </div>
    </div>
  );
};

export const SuicideAttemptChart: React.FC<SuicideAttemptChartProps> = ({
  filters,
  chartConfig = {},
  onTimeRangeSelect,
  showDemographics = true,
  defaultView = 'temporal',
}) => {
  const [activeTab, setActiveTab] = useState(defaultView);
  
  const {
    processedData,
    loading,
    error,
    refetch,
  } = useSuicideAttemptData(filters);

  // Procesar datos para visualización
  const { 
    timeSeriesData, 
    ageGroupsData, 
    genderData, 
    demographics, 
    statistics, 
    title 
  } = useMemo(() => {
    if (!processedData) {
      return { 
        timeSeriesData: [], 
        ageGroupsData: [], 
        genderData: [], 
        demographics: null, 
        statistics: null,
        title: '' 
      };
    }

    const { timeSeriesData, ageGroupsData, genderData, demographics } = processedData;

    // Calcular estadísticas totales
    const totalAttempts = timeSeriesData.reduce((sum, point) => sum + point.attempts, 0);
    const totalDeaths = timeSeriesData.reduce((sum, point) => sum + point.deaths, 0);
    const overallMortalityRate = totalAttempts > 0 ? (totalDeaths / totalAttempts) * 100 : 0;

    // Agregar colores a datos demográficos
    const coloredAgeData = ageGroupsData.map((item, index) => ({
      ...item,
      color: COLORS.ageGroups[index % COLORS.ageGroups.length],
    }));

    const coloredGenderData = genderData.map((item) => ({
      ...item,
      color: item.name.toLowerCase().includes('mascul') ? COLORS.male : COLORS.female,
    }));

    const chartTitle = `Análisis de Intentos de Suicidio - ${totalAttempts} casos registrados`;

    return {
      timeSeriesData,
      ageGroupsData: coloredAgeData,
      genderData: coloredGenderData,
      demographics,
      statistics: {
        totalAttempts,
        totalDeaths,
        mortalityRate: overallMortalityRate,
      },
      title: chartTitle,
    };
  }, [processedData]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="flex items-center gap-2">
          <div className="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full" />
          <span>Cargando análisis de intento de suicidio...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-4">
        <AlertTriangle className="h-12 w-12 text-red-500" />
        <div className="text-center">
          <p className="text-lg font-semibold text-gray-800">Error al cargar datos</p>
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
        
        {statistics && demographics && (
          <SuicideStats
            demographics={demographics}
            totalAttempts={statistics.totalAttempts}
            totalDeaths={statistics.totalDeaths}
            mortalityRate={statistics.mortalityRate}
          />
        )}
      </div>

      <div>
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="temporal">
              <Calendar className="h-4 w-4 mr-2" />
              Serie Temporal
            </TabsTrigger>
            <TabsTrigger value="demographics">
              <Users className="h-4 w-4 mr-2" />
              Demografía
            </TabsTrigger>
            <TabsTrigger value="analysis">
              <TrendingUp className="h-4 w-4 mr-2" />
              Análisis
            </TabsTrigger>
          </TabsList>

          <TabsContent value="temporal" className="mt-4">
            <div 
              className="w-full"
              style={{ height: chartConfig.height || 400 }}
            >
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart
                  data={timeSeriesData}
                  margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
                  onClick={(data) => {
                    if (data?.activePayload?.[0]?.payload && onTimeRangeSelect) {
                      const point = data.activePayload[0].payload;
                      onTimeRangeSelect(point.week - 2, point.week + 2, point.year);
                    }
                  }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(128, 128, 128, 0.2)" />
                  
                  <XAxis
                    dataKey="week"
                    tick={{ fontSize: 12 }}
                    tickLine={{ stroke: '#666' }}
                    axisLine={{ stroke: '#666' }}
                    label={{ value: 'Semana Epidemiológica', position: 'insideBottom', offset: -40 }}
                  />
                  
                  <YAxis
                    tick={{ fontSize: 12 }}
                    tickLine={{ stroke: '#666' }}
                    axisLine={{ stroke: '#666' }}
                    label={{ value: 'Casos', angle: -90, position: 'insideLeft' }}
                  />

                  <Area
                    type="monotone"
                    dataKey="attempts"
                    stackId="1"
                    stroke={COLORS.attempts}
                    fill={COLORS.attempts}
                    fillOpacity={0.6}
                    name="Intentos"
                  />
                  
                  <Area
                    type="monotone"
                    dataKey="deaths"
                    stackId="2"
                    stroke={COLORS.deaths}
                    fill={COLORS.deaths}
                    fillOpacity={0.8}
                    name="Fallecimientos"
                  />

                  <Tooltip content={<TimeSeriesTooltip />} />
                  <Legend />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </TabsContent>

          <TabsContent value="demographics" className="mt-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Distribución por edad */}
              <div>
                <h4 className="text-sm font-semibold text-gray-800 mb-3">
                  Distribución por Grupo Etario
                </h4>
                <div style={{ height: 300 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={ageGroupsData}
                        cx="50%"
                        cy="50%"
                        innerRadius={40}
                        outerRadius={80}
                        paddingAngle={5}
                        dataKey="value"
                      >
                        {ageGroupsData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip content={<DemographicTooltip />} />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Distribución por sexo */}
              <div>
                <h4 className="text-sm font-semibold text-gray-800 mb-3">
                  Distribución por Sexo
                </h4>
                <div style={{ height: 300 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={genderData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(128, 128, 128, 0.2)" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip content={<DemographicTooltip />} />
                      <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                        {genderData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>

            {/* Tabla de detalles demográficos */}
            <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-3 bg-gray-50 rounded-lg">
                <h4 className="text-sm font-semibold text-gray-800 mb-2">
                  Ranking por Edad
                </h4>
                <div className="space-y-1">
                  {ageGroupsData
                    .sort((a, b) => b.value - a.value)
                    .map((group, index) => (
                      <div key={group.name} className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className="text-xs">
                            {index + 1}
                          </Badge>
                          <div 
                            className="w-3 h-3 rounded" 
                            style={{ backgroundColor: group.color }}
                          />
                          <span className="text-sm text-gray-700">{group.name}</span>
                        </div>
                        <span className="text-sm font-medium">
                          {group.value.toLocaleString()}
                        </span>
                      </div>
                    ))
                  }
                </div>
              </div>

              <div className="p-3 bg-gray-50 rounded-lg">
                <h4 className="text-sm font-semibold text-gray-800 mb-2">
                  Estadísticas por Sexo
                </h4>
                <div className="space-y-2">
                  {genderData.map((gender) => {
                    const percentage = statistics?.totalAttempts > 0 
                      ? (gender.value / statistics.totalAttempts) * 100 
                      : 0;
                    
                    return (
                      <div key={gender.name} className="flex justify-between items-center">
                        <div className="flex items-center gap-2">
                          <div 
                            className="w-3 h-3 rounded" 
                            style={{ backgroundColor: gender.color }}
                          />
                          <span className="text-sm text-gray-700">{gender.name}</span>
                        </div>
                        <div className="text-right">
                          <span className="text-sm font-medium">
                            {gender.value.toLocaleString()}
                          </span>
                          <span className="text-xs text-gray-500 block">
                            {percentage.toFixed(1)}%
                          </span>
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
              {/* Tendencia de letalidad */}
              <div>
                <h4 className="text-sm font-semibold text-gray-800 mb-3">
                  Tendencia de Tasa de Letalidad
                </h4>
                <div style={{ height: 300 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart
                      data={timeSeriesData.filter(d => d.attempts > 0)}
                      margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(128, 128, 128, 0.2)" />
                      <XAxis
                        dataKey="week"
                        tick={{ fontSize: 12 }}
                        tickLine={{ stroke: '#666' }}
                        axisLine={{ stroke: '#666' }}
                        label={{ value: 'Semana', position: 'insideBottom', offset: -40 }}
                      />
                      <YAxis
                        tick={{ fontSize: 12 }}
                        tickLine={{ stroke: '#666' }}
                        axisLine={{ stroke: '#666' }}
                        label={{ value: 'Tasa de Letalidad (%)', angle: -90, position: 'insideLeft' }}
                      />
                      <Line
                        type="monotone"
                        dataKey="mortalityRate"
                        stroke={COLORS.mortalityRate}
                        strokeWidth={3}
                        dot={{ fill: COLORS.mortalityRate, strokeWidth: 2, r: 4 }}
                        name="Tasa de Letalidad"
                      />
                      <Tooltip content={<TimeSeriesTooltip />} />
                      <Legend />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Análisis estadístico */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 bg-red-50 rounded-lg border border-red-200">
                  <h5 className="text-sm font-semibold text-red-800 mb-2">
                    Alto Riesgo
                  </h5>
                  <div className="text-2xl font-bold text-red-900 mb-1">
                    {statistics?.mortalityRate.toFixed(1)}%
                  </div>
                  <p className="text-sm text-red-700">
                    Tasa de letalidad general
                  </p>
                </div>

                <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                  <h5 className="text-sm font-semibold text-blue-800 mb-2">
                    Incidencia Semanal
                  </h5>
                  <div className="text-2xl font-bold text-blue-900 mb-1">
                    {timeSeriesData.length > 0 
                      ? (statistics?.totalAttempts / timeSeriesData.length).toFixed(1)
                      : '0'
                    }
                  </div>
                  <p className="text-sm text-blue-700">
                    Promedio por semana
                  </p>
                </div>

                <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                  <h5 className="text-sm font-semibold text-green-800 mb-2">
                    Supervivencia
                  </h5>
                  <div className="text-2xl font-bold text-green-900 mb-1">
                    {(100 - (statistics?.mortalityRate || 0)).toFixed(1)}%
                  </div>
                  <p className="text-sm text-green-700">
                    Tasa de supervivencia
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

export default SuicideAttemptChart;