/**
 * Componente de Chart para Rabia Animal
 * Análisis por especies, ubicaciones y temporalidad
 */

import React, { useMemo, useState } from 'react';
import {
  BarChart,
  Bar,
  LineChart,
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
  ScatterChart,
  Scatter,
} from 'recharts';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  AlertTriangle, 
  MapPin, 
  Calendar, 
  BarChart3, 
  Target,
  Microscope
} from 'lucide-react';
import {
  EpidemiologicalFilters,
  ChartConfig,
} from '../../types/epidemiological';
import { useAnimalRabiesData } from '../../hooks/useEpidemiologicalData';

// Configuración de colores por especies
const SPECIES_COLORS = {
  'PERRO': 'rgb(31, 119, 180)',
  'GATO': 'rgb(255, 127, 14)', 
  'BOVINO': 'rgb(44, 160, 44)',
  'MURCIELAGO': 'rgb(214, 39, 40)',
  'OTROS': 'rgb(148, 103, 189)',
} as const;

const STATUS_COLORS = {
  tested: 'rgb(54, 162, 235)',
  positive: 'rgb(255, 99, 132)', 
  negative: 'rgb(75, 192, 192)',
} as const;

interface AnimalRabiesChartProps {
  filters?: EpidemiologicalFilters;
  chartConfig?: ChartConfig;
  onLocationSelect?: (location: string) => void;
  onSpeciesSelect?: (species: string) => void;
}

// Tooltip para datos temporales
const TemporalTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload || !payload.length) return null;

  const data = payload[0]?.payload;
  
  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-4">
      <p className="font-semibold text-gray-800 mb-2">{label}</p>
      <p className="text-sm text-gray-600 mb-2">
        <strong>{data?.species}</strong> - {data?.location}
      </p>
      
      <div className="space-y-1">
        <div className="flex items-center justify-between gap-4">
          <span className="text-sm text-gray-700">Casos:</span>
          <span className="text-sm font-medium text-blue-600">
            {data?.cases || 0}
          </span>
        </div>
        
        <div className="flex items-center justify-between gap-4">
          <span className="text-sm text-gray-700">Testeos:</span>
          <span className="text-sm font-medium text-gray-600">
            {data?.tested || 0}
          </span>
        </div>
        
        <div className="flex items-center justify-between gap-4">
          <span className="text-sm text-gray-700">Positivos:</span>
          <span className="text-sm font-medium text-red-600">
            {data?.positive || 0}
          </span>
        </div>
        
        <div className="border-t border-gray-200 pt-1 mt-2">
          <div className="flex items-center justify-between gap-4">
            <span className="text-sm text-orange-600">% Positividad:</span>
            <span className="text-sm font-medium text-orange-700">
              {data?.positivityRate?.toFixed(1)}%
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

// Tooltip para gráficos categóricos
const CategoryTooltip = ({ active, payload }: any) => {
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

// Panel de estadísticas
const StatisticsPanel: React.FC<{
  statistics: any;
  timeSeriesData: any[];
}> = ({ statistics, timeSeriesData }) => {
  const totalCases = timeSeriesData.reduce((sum, point) => sum + point.cases, 0);
  const totalTested = timeSeriesData.reduce((sum, point) => sum + point.tested, 0);
  const totalPositive = timeSeriesData.reduce((sum, point) => sum + point.positive, 0);

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div className="text-center p-3 bg-blue-50 rounded-lg">
        <div className="text-2xl font-bold text-blue-600">
          {totalCases.toLocaleString()}
        </div>
        <div className="text-sm text-blue-800">Casos Totales</div>
      </div>
      
      <div className="text-center p-3 bg-gray-50 rounded-lg">
        <div className="text-2xl font-bold text-gray-600">
          {totalTested.toLocaleString()}
        </div>
        <div className="text-sm text-gray-800">Testeos</div>
      </div>
      
      <div className="text-center p-3 bg-red-50 rounded-lg">
        <div className="text-2xl font-bold text-red-600">
          {totalPositive}
        </div>
        <div className="text-sm text-red-800">Positivos</div>
      </div>
      
      <div className="text-center p-3 bg-orange-50 rounded-lg">
        <div className="text-2xl font-bold text-orange-600">
          {statistics.positivityRate.toFixed(1)}%
        </div>
        <div className="text-sm text-orange-800">% Positividad</div>
      </div>
    </div>
  );
};

export const AnimalRabiesChart: React.FC<AnimalRabiesChartProps> = ({
  filters,
  chartConfig = {},
  onLocationSelect,
  onSpeciesSelect,
}) => {
  const [activeTab, setActiveTab] = useState('temporal');

  const {
    processedData,
    loading,
    error,
    refetch,
  } = useAnimalRabiesData(filters);

  // Preparar datos
  const { 
    timeSeriesData, 
    speciesData, 
    locationData, 
    statistics, 
    title,
    positiveCases 
  } = useMemo(() => {
    if (!processedData) {
      return { 
        timeSeriesData: [], 
        speciesData: [], 
        locationData: [],
        statistics: null,
        title: '',
        positiveCases: []
      };
    }

    const { timeSeriesData, speciesData, locationData, statistics } = processedData;

    // Casos positivos para análisis de scatter
    const positive = timeSeriesData.filter(point => point.positive > 0);

    const totalCases = timeSeriesData.reduce((sum, point) => sum + point.cases, 0);
    const totalPositive = timeSeriesData.reduce((sum, point) => sum + point.positive, 0);
    
    const chartTitle = `Vigilancia de Rabia Animal - ${totalCases} casos analizados (${totalPositive} positivos - ${statistics.positivityRate.toFixed(1)}% positividad)`;

    return {
      timeSeriesData,
      speciesData,
      locationData,
      statistics,
      title: chartTitle,
      positiveCases: positive,
    };
  }, [processedData]);

  if (loading) {
    return (
      <Card className="w-full">
        <CardContent className="flex items-center justify-center h-96">
          <div className="flex items-center gap-2">
            <div className="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full" />
            <span>Cargando datos de rabia animal...</span>
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
        
        {statistics && (
          <StatisticsPanel 
            statistics={statistics}
            timeSeriesData={timeSeriesData}
          />
        )}
      </CardHeader>

      <CardContent>
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="temporal" className="flex items-center gap-2">
              <Calendar className="h-4 w-4" />
              Temporal
            </TabsTrigger>
            <TabsTrigger value="species" className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              Especies
            </TabsTrigger>
            <TabsTrigger value="locations" className="flex items-center gap-2">
              <MapPin className="h-4 w-4" />
              Ubicaciones
            </TabsTrigger>
            <TabsTrigger value="analysis" className="flex items-center gap-2">
              <Microscope className="h-4 w-4" />
              Análisis
            </TabsTrigger>
          </TabsList>

          {/* Análisis Temporal */}
          <TabsContent value="temporal">
            <div style={{ height: chartConfig.height || 500 }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={timeSeriesData}
                  margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(128, 128, 128, 0.2)" />
                  
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 12 }}
                    tickLine={{ stroke: '#666' }}
                    axisLine={{ stroke: '#666' }}
                    label={{ value: 'Fecha', position: 'insideBottom', offset: -40 }}
                  />
                  
                  <YAxis
                    tick={{ fontSize: 12 }}
                    tickLine={{ stroke: '#666' }}
                    axisLine={{ stroke: '#666' }}
                    label={{ value: 'Casos', angle: -90, position: 'insideLeft' }}
                  />

                  <Line
                    type="monotone"
                    dataKey="cases"
                    stroke={STATUS_COLORS.tested}
                    strokeWidth={2}
                    dot={{ fill: STATUS_COLORS.tested, strokeWidth: 2, r: 4 }}
                    name="Casos totales"
                  />

                  <Line
                    type="monotone"
                    dataKey="tested"
                    stroke={STATUS_COLORS.negative}
                    strokeWidth={2}
                    strokeDasharray="5 5"
                    dot={{ fill: STATUS_COLORS.negative, strokeWidth: 2, r: 3 }}
                    name="Testeos realizados"
                  />

                  <Line
                    type="monotone"
                    dataKey="positive"
                    stroke={STATUS_COLORS.positive}
                    strokeWidth={3}
                    dot={{ fill: STATUS_COLORS.positive, strokeWidth: 2, r: 5 }}
                    name="Casos positivos"
                  />

                  <Tooltip content={<TemporalTooltip />} />
                  <Legend />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </TabsContent>

          {/* Análisis por Especies */}
          <TabsContent value="species">
            <div className="space-y-6">
              <div style={{ height: 400 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={speciesData}
                    margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="name" 
                      angle={-45}
                      textAnchor="end"
                      height={80}
                    />
                    <YAxis />
                    <Bar
                      dataKey="value"
                      fill={(entry: any, index: number) => 
                        SPECIES_COLORS[entry?.name as keyof typeof SPECIES_COLORS] || 
                        SPECIES_COLORS.OTROS
                      }
                      onClick={(data) => onSpeciesSelect?.(data.name)}
                    >
                      {speciesData.map((entry, index) => (
                        <Cell 
                          key={`cell-${index}`} 
                          fill={SPECIES_COLORS[entry.name as keyof typeof SPECIES_COLORS] || SPECIES_COLORS.OTROS}
                        />
                      ))}
                    </Bar>
                    <Tooltip content={<CategoryTooltip />} />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Torta de especies */}
              <div style={{ height: 300 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={speciesData}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      dataKey="value"
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    >
                      {speciesData.map((entry, index) => (
                        <Cell 
                          key={`cell-${index}`} 
                          fill={SPECIES_COLORS[entry.name as keyof typeof SPECIES_COLORS] || SPECIES_COLORS.OTROS}
                        />
                      ))}
                    </Pie>
                    <Tooltip content={<CategoryTooltip />} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          </TabsContent>

          {/* Análisis por Ubicaciones */}
          <TabsContent value="locations">
            <div style={{ height: chartConfig.height || 500 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={locationData.slice(0, 10)} // Top 10 ubicaciones
                  layout="horizontal"
                  margin={{ top: 20, right: 30, left: 100, bottom: 20 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis 
                    type="category" 
                    dataKey="name"
                    width={90}
                    tick={{ fontSize: 12 }}
                  />
                  <Bar
                    dataKey="value"
                    fill="rgb(31, 119, 180)"
                    onClick={(data) => onLocationSelect?.(data.name)}
                  />
                  <Tooltip content={<CategoryTooltip />} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </TabsContent>

          {/* Análisis Detallado */}
          <TabsContent value="analysis">
            <div className="space-y-6">
              {/* Scatter plot: Casos vs Positividad */}
              <Card>
                <CardHeader>
                  <h4 className="text-md font-semibold flex items-center gap-2">
                    <Target className="h-4 w-4" />
                    Relación Casos vs Tasa de Positividad
                  </h4>
                </CardHeader>
                <CardContent>
                  <div style={{ height: 300 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <ScatterChart>
                        <CartesianGrid />
                        <XAxis 
                          type="number" 
                          dataKey="tested" 
                          name="Testeos"
                          label={{ value: 'Testeos realizados', position: 'insideBottom', offset: -10 }}
                        />
                        <YAxis 
                          type="number" 
                          dataKey="positivityRate" 
                          name="Positividad"
                          label={{ value: '% Positividad', angle: -90, position: 'insideLeft' }}
                        />
                        <Scatter 
                          data={positiveCases} 
                          fill={STATUS_COLORS.positive}
                        />
                        <Tooltip content={<TemporalTooltip />} />
                      </ScatterChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>

              {/* Alerta de casos positivos */}
              {positiveCases.length > 0 && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <AlertTriangle className="h-5 w-5 text-red-600" />
                    <h4 className="font-semibold text-red-800">
                      Casos Positivos Detectados
                    </h4>
                  </div>
                  <div className="text-sm text-red-700 space-y-1">
                    <p>• Total de casos positivos: <strong>{positiveCases.length}</strong></p>
                    <p>• Tasa de positividad general: <strong>{statistics.positivityRate.toFixed(2)}%</strong></p>
                    <p>• Requiere seguimiento epidemiológico inmediato</p>
                    <p>• Implementar medidas de control vectorial</p>
                  </div>
                </div>
              )}

              {/* Recomendaciones */}
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <Microscope className="h-5 w-5 text-blue-600" />
                  <h4 className="font-semibold text-blue-800">
                    Vigilancia Epidemiológica
                  </h4>
                </div>
                <div className="text-sm text-blue-700 space-y-1">
                  <p>• Mantener vigilancia activa en especies de alto riesgo</p>
                  <p>• Coordinar con servicios veterinarios locales</p>
                  <p>• Reforzar campañas de vacunación preventiva</p>
                  <p>• Educar a la población sobre medidas preventivas</p>
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};

export default AnimalRabiesChart;