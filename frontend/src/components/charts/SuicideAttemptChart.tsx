/**
 * Componente de Chart para Intento de Suicidio
 * Análisis temporal y demográfico con mortalidad
 */

import React, { useMemo, useState } from 'react';
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AlertTriangle, Heart, Users, TrendingUp, Calendar } from 'lucide-react';
import {
  EpidemiologicalFilters,
  ChartConfig,
} from '../../types/epidemiological';
import { useSuicideAttemptData } from '../../hooks/useEpidemiologicalData';

// Configuración de colores
const COLORS = {
  attempts: 'rgb(54, 162, 235)',     // Azul para intentos
  deaths: 'rgb(255, 99, 132)',       // Rojo para muertes
  mortalityRate: 'rgb(255, 206, 86)', // Amarillo para tasa
  demographic: [
    'rgb(31, 119, 180)',
    'rgb(255, 127, 14)',
    'rgb(44, 160, 44)',
    'rgb(214, 39, 40)',
    'rgb(148, 103, 189)',
    'rgb(140, 86, 75)',
    'rgb(227, 119, 194)',
    'rgb(127, 127, 127)',
  ],
} as const;

interface SuicideAttemptChartProps {
  filters?: EpidemiologicalFilters;
  chartConfig?: ChartConfig;
  onTimePointSelect?: (week: number, year: number) => void;
}

// Tooltip para serie temporal
const TemporalTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload || !payload.length) return null;

  const data = payload[0]?.payload;
  
  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-4">
      <p className="font-semibold text-gray-800 mb-2">
        Semana {label} - Año {data?.year}
      </p>
      
      <div className="space-y-2">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded" style={{ backgroundColor: COLORS.attempts }} />
            <span className="text-sm text-gray-700">Intentos:</span>
          </div>
          <span className="text-sm font-medium text-blue-600">
            {data?.attempts || 0}
          </span>
        </div>
        
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded" style={{ backgroundColor: COLORS.deaths }} />
            <span className="text-sm text-gray-700">Fallecimientos:</span>
          </div>
          <span className="text-sm font-medium text-red-600">
            {data?.deaths || 0}
          </span>
        </div>
        
        {data?.mortalityRate > 0 && (
          <div className="border-t border-gray-200 pt-2">
            <div className="flex items-center justify-between gap-4">
              <span className="text-sm text-orange-600">Tasa mortalidad:</span>
              <span className="text-sm font-medium text-orange-700">
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
const DemographicTooltip = ({ active, payload }: any) => {
  if (!active || !payload || !payload.length) return null;

  const data = payload[0]?.payload;
  
  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3">
      <p className="font-semibold text-gray-800">{data?.name}</p>
      <p className="text-sm text-gray-600">
        Casos: <span className="font-medium">{data?.value}</span>
      </p>
    </div>
  );
};

// Panel de estadísticas generales
const StatisticsPanel: React.FC<{
  timeSeriesData: any[];
  demographics: any;
}> = ({ timeSeriesData, demographics }) => {
  const totalAttempts = timeSeriesData.reduce((sum, point) => sum + point.attempts, 0);
  const totalDeaths = timeSeriesData.reduce((sum, point) => sum + point.deaths, 0);
  const overallMortalityRate = totalAttempts > 0 ? (totalDeaths / totalAttempts) * 100 : 0;

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div className="text-center p-3 bg-blue-50 rounded-lg">
        <div className="text-2xl font-bold text-blue-600">
          {totalAttempts.toLocaleString()}
        </div>
        <div className="text-sm text-blue-800">Intentos Totales</div>
      </div>
      
      <div className="text-center p-3 bg-red-50 rounded-lg">
        <div className="text-2xl font-bold text-red-600">
          {totalDeaths}
        </div>
        <div className="text-sm text-red-800">Fallecimientos</div>
      </div>
      
      <div className="text-center p-3 bg-orange-50 rounded-lg">
        <div className="text-2xl font-bold text-orange-600">
          {overallMortalityRate.toFixed(1)}%
        </div>
        <div className="text-sm text-orange-800">Tasa Mortalidad</div>
      </div>
      
      <div className="text-center p-3 bg-purple-50 rounded-lg">
        <div className="text-2xl font-bold text-purple-600">
          {Object.keys(demographics.ageGroups).length}
        </div>
        <div className="text-sm text-purple-800">Grupos Etarios</div>
      </div>
    </div>
  );
};

// Componente de gráfico demográfico
const DemographicChart: React.FC<{
  data: { name: string; value: number }[];
  title: string;
  colors: string[];
}> = ({ data, title, colors }) => (
  <Card className="h-full">
    <CardHeader>
      <h4 className="text-md font-semibold">{title}</h4>
    </CardHeader>
    <CardContent>
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            outerRadius={80}
            dataKey="value"
            label={({ percent }) => `${(percent * 100).toFixed(0)}%`}
          >
            {data.map((entry, index) => (
              <Cell 
                key={`cell-${index}`} 
                fill={colors[index % colors.length]} 
              />
            ))}
          </Pie>
          <Tooltip content={<DemographicTooltip />} />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </CardContent>
  </Card>
);

export const SuicideAttemptChart: React.FC<SuicideAttemptChartProps> = ({
  filters,
  chartConfig = {},
  onTimePointSelect,
}) => {
  const [activeTab, setActiveTab] = useState('temporal');

  const {
    processedData,
    loading,
    error,
    refetch,
  } = useSuicideAttemptData(filters);

  // Preparar datos
  const { timeSeriesData, ageGroupsData, genderData, demographics, title } = useMemo(() => {
    if (!processedData) {
      return { 
        timeSeriesData: [], 
        ageGroupsData: [], 
        genderData: [],
        demographics: null,
        title: '' 
      };
    }

    const { timeSeriesData, ageGroupsData, genderData, demographics } = processedData;

    const totalAttempts = timeSeriesData.reduce((sum, point) => sum + point.attempts, 0);
    const totalDeaths = timeSeriesData.reduce((sum, point) => sum + point.deaths, 0);
    
    const years = [...new Set(timeSeriesData.map(d => d.year))];
    const yearText = years.length === 1 ? `${years[0]}` : `${Math.min(...years)}-${Math.max(...years)}`;
    
    const chartTitle = `Análisis de Intentos de Suicidio - ${yearText} (${totalAttempts} casos, ${totalDeaths} fallecimientos)`;

    return {
      timeSeriesData,
      ageGroupsData,
      genderData,
      demographics,
      title: chartTitle,
    };
  }, [processedData]);

  if (loading) {
    return (
      <Card className="w-full">
        <CardContent className="flex items-center justify-center h-96">
          <div className="flex items-center gap-2">
            <div className="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full" />
            <span>Cargando datos de intento de suicidio...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="w-full">
        <CardContent className="flex flex-col items-center justify-center h-96 gap-4">
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
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <h3 className="text-lg font-semibold">{title}</h3>
        
        {demographics && (
          <StatisticsPanel 
            timeSeriesData={timeSeriesData}
            demographics={demographics}
          />
        )}
      </CardHeader>

      <CardContent>
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="temporal" className="flex items-center gap-2">
              <Calendar className="h-4 w-4" />
              Temporal
            </TabsTrigger>
            <TabsTrigger value="demographics" className="flex items-center gap-2">
              <Users className="h-4 w-4" />
              Demografía
            </TabsTrigger>
            <TabsTrigger value="analysis" className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              Análisis
            </TabsTrigger>
          </TabsList>

          {/* Análisis Temporal */}
          <TabsContent value="temporal">
            <div style={{ height: chartConfig.height || 500 }}>
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart
                  data={timeSeriesData}
                  margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
                  onClick={(data) => {
                    if (data?.activePayload?.[0]?.payload && onTimePointSelect) {
                      const point = data.activePayload[0].payload;
                      onTimePointSelect(point.week, point.year);
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
                    yAxisId="cases"
                    tick={{ fontSize: 12 }}
                    tickLine={{ stroke: '#666' }}
                    axisLine={{ stroke: '#666' }}
                    label={{ value: 'Casos', angle: -90, position: 'insideLeft' }}
                  />

                  <YAxis
                    yAxisId="rate"
                    orientation="right"
                    tick={{ fontSize: 12 }}
                    tickLine={{ stroke: '#666' }}
                    axisLine={{ stroke: '#666' }}
                    label={{ value: 'Tasa (%)', angle: 90, position: 'insideRight' }}
                  />

                  <Bar
                    yAxisId="cases"
                    dataKey="attempts"
                    fill={COLORS.attempts}
                    name="Intentos"
                    opacity={0.7}
                  />

                  <Bar
                    yAxisId="cases"
                    dataKey="deaths"
                    fill={COLORS.deaths}
                    name="Fallecimientos"
                  />

                  <Line
                    yAxisId="rate"
                    type="monotone"
                    dataKey="mortalityRate"
                    stroke={COLORS.mortalityRate}
                    strokeWidth={2}
                    dot={{ fill: COLORS.mortalityRate, strokeWidth: 2, r: 3 }}
                    name="Tasa Mortalidad (%)"
                  />

                  <Tooltip content={<TemporalTooltip />} />
                  <Legend />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </TabsContent>

          {/* Análisis Demográfico */}
          <TabsContent value="demographics">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <DemographicChart
                data={ageGroupsData}
                title="Distribución por Grupos de Edad"
                colors={COLORS.demographic}
              />
              
              <DemographicChart
                data={genderData}
                title="Distribución por Sexo"
                colors={['rgb(54, 162, 235)', 'rgb(255, 99, 132)']}
              />
            </div>
          </TabsContent>

          {/* Análisis Detallado */}
          <TabsContent value="analysis">
            <div className="space-y-6">
              {/* Métodos utilizados */}
              {demographics?.methodsUsed && (
                <Card>
                  <CardHeader>
                    <h4 className="text-md font-semibold flex items-center gap-2">
                      <Heart className="h-4 w-4" />
                      Métodos Más Utilizados
                    </h4>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {Object.entries(demographics.methodsUsed)
                        .sort(([,a], [,b]) => (b as number) - (a as number))
                        .slice(0, 5)
                        .map(([method, count], index) => (
                          <div key={method} className="text-center p-3 bg-gray-50 rounded-lg">
                            <div className="text-lg font-bold text-gray-700">
                              {(count as number).toLocaleString()}
                            </div>
                            <div className="text-sm text-gray-600">
                              {method}
                            </div>
                          </div>
                        ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Información adicional */}
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <AlertTriangle className="h-5 w-5 text-red-600" />
                  <h4 className="font-semibold text-red-800">
                    Información Importante
                  </h4>
                </div>
                <div className="text-sm text-red-700 space-y-1">
                  <p>• Los datos de intento de suicidio requieren tratamiento confidencial</p>
                  <p>• Es fundamental el seguimiento de casos y prevención</p>
                  <p>• Contactar servicios de salud mental para intervención temprana</p>
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};

export default SuicideAttemptChart;