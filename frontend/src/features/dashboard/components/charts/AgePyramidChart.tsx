/**
 * Componente de Pirámide Poblacional por Edad
 * Gráfico de barras horizontales con distribución por sexo
 */

import React, { useMemo } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AlertTriangle, Users, User, UserCheck } from 'lucide-react';
import {
  EpidemiologicalFilters,
  ChartConfig,
} from '../../types';
import { useAgeCases } from '../../hooks/useEpidemiologicalData';

// Configuración de colores (replicando el original)
const GENDER_COLORS = {
  male: 'rgb(54, 162, 235)',     // Azul para masculino
  female: 'rgb(255, 99, 132)',   // Rosa para femenino
  total: 'rgb(75, 192, 192)',    // Verde para total
} as const;

interface AgePyramidChartProps {
  filters?: EpidemiologicalFilters;
  chartConfig?: ChartConfig;
  onAgeGroupSelect?: (ageGroup: string) => void;
  showPercentages?: boolean;
  orientation?: 'horizontal' | 'vertical';
}

// Tooltip personalizado para pirámide poblacional
const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload || !payload.length) return null;

  const ageGroup = label;
  const data = payload[0]?.payload;

  // Obtener valores absolutos para mostrar
  const maleValue = Math.abs(data?.male || 0);
  const femaleValue = data?.female || 0;
  const total = maleValue + femaleValue;

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-4 max-w-sm">
      <div className="border-b border-gray-200 pb-2 mb-2">
        <p className="font-semibold text-gray-800">Grupo etario: {ageGroup}</p>
        <p className="text-sm text-gray-600">
          Total casos: {total.toLocaleString()}
        </p>
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div 
              className="w-3 h-3 rounded" 
              style={{ backgroundColor: GENDER_COLORS.male }}
            />
            <User className="h-3 w-3 text-blue-500" />
            <span className="text-sm text-gray-700">Masculino:</span>
          </div>
          <div className="text-right">
            <span className="text-sm font-medium text-gray-900">
              {maleValue.toLocaleString()}
            </span>
            <span className="text-xs text-gray-500 block">
              {total > 0 ? ((maleValue / total) * 100).toFixed(1) : 0}%
            </span>
          </div>
        </div>

        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div 
              className="w-3 h-3 rounded" 
              style={{ backgroundColor: GENDER_COLORS.female }}
            />
            <UserCheck className="h-3 w-3 text-pink-500" />
            <span className="text-sm text-gray-700">Femenino:</span>
          </div>
          <div className="text-right">
            <span className="text-sm font-medium text-gray-900">
              {femaleValue.toLocaleString()}
            </span>
            <span className="text-xs text-gray-500 block">
              {total > 0 ? ((femaleValue / total) * 100).toFixed(1) : 0}%
            </span>
          </div>
        </div>
      </div>

      <div className="border-t border-gray-200 pt-2 mt-2">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700">Ratio M/F:</span>
          <span className="text-sm font-medium text-gray-900">
            {femaleValue > 0 ? (maleValue / femaleValue).toFixed(2) : 'N/A'}
          </span>
        </div>
      </div>
    </div>
  );
};

// Componente de estadísticas demográficas
const DemographicStats: React.FC<{
  statistics: any;
  showPercentages: boolean;
}> = ({ statistics, showPercentages }) => {
  const totalCases = statistics.totalCases;
  const maleTotal = statistics.genderDistribution?.male || 0;
  const femaleTotal = statistics.genderDistribution?.female || 0;
  const malePercentage = totalCases > 0 ? (maleTotal / totalCases) * 100 : 0;
  const femalePercentage = totalCases > 0 ? (femaleTotal / totalCases) * 100 : 0;

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
      <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
        <div className="flex items-center gap-2 mb-1">
          <User className="h-4 w-4 text-blue-500" />
          <span className="text-sm font-medium text-blue-800">Masculino</span>
        </div>
        <div className="text-lg font-bold text-blue-900">
          {maleTotal.toLocaleString()}
        </div>
        {showPercentages && (
          <div className="text-sm text-blue-700">
            {malePercentage.toFixed(1)}%
          </div>
        )}
      </div>

      <div className="p-3 bg-pink-50 rounded-lg border border-pink-200">
        <div className="flex items-center gap-2 mb-1">
          <UserCheck className="h-4 w-4 text-pink-500" />
          <span className="text-sm font-medium text-pink-800">Femenino</span>
        </div>
        <div className="text-lg font-bold text-pink-900">
          {femaleTotal.toLocaleString()}
        </div>
        {showPercentages && (
          <div className="text-sm text-pink-700">
            {femalePercentage.toFixed(1)}%
          </div>
        )}
      </div>

      <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
        <div className="flex items-center gap-2 mb-1">
          <Users className="h-4 w-4 text-gray-500" />
          <span className="text-sm font-medium text-gray-800">Total</span>
        </div>
        <div className="text-lg font-bold text-gray-900">
          {totalCases.toLocaleString()}
        </div>
        <div className="text-sm text-gray-700">
          Ratio M/F: {femaleTotal > 0 ? (maleTotal / femaleTotal).toFixed(2) : 'N/A'}
        </div>
      </div>
    </div>
  );
};

// Función para formatear etiquetas de edad
const formatAgeGroup = (ageGroup: string): string => {
  return ageGroup
    .replace('_', '-')
    .replace('YEARS', 'años')
    .replace('MONTHS', 'meses')
    .replace('PLUS', '+');
};

export const AgePyramidChart: React.FC<AgePyramidChartProps> = ({
  filters,
  chartConfig = {},
  onAgeGroupSelect,
  showPercentages = false,
  orientation = 'horizontal',
}) => {
  const {
    processedData,
    loading,
    error,
    refetch,
  } = useAgeCases(filters);

  // Preparar datos para la pirámide
  const { chartData, statistics, title, maxValue } = useMemo(() => {
    if (!processedData) {
      return { 
        chartData: [], 
        statistics: null, 
        title: '', 
        maxValue: 0 
      };
    }

    const { chartData, statistics } = processedData;

    // Encontrar el valor máximo para escalar el gráfico
    const maxCases = Math.max(
      ...chartData.map(d => Math.max(Math.abs(d.male), d.female))
    );

    // Ordenar grupos etarios de menor a mayor edad
    const sortedData = [...chartData].sort((a, b) => {
      // Extraer números de los grupos etarios para ordenamiento
      const aNum = parseInt(a.ageGroup.match(/\d+/)?.[0] || '0');
      const bNum = parseInt(b.ageGroup.match(/\d+/)?.[0] || '0');
      return aNum - bNum;
    });

    const chartTitle = `Distribución por Edad y Sexo - ${
      statistics.totalCases.toLocaleString()
    } casos totales`;

    return {
      chartData: sortedData.map(d => ({
        ...d,
        ageGroup: formatAgeGroup(d.ageGroup),
      })),
      statistics,
      title: chartTitle,
      maxValue: maxCases,
    };
  }, [processedData]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="flex items-center gap-2">
          <div className="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full" />
          <span>Cargando pirámide poblacional...</span>
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
      {statistics && (
        <div className="mb-4">
          <DemographicStats 
            statistics={statistics} 
            showPercentages={showPercentages} 
          />
        </div>
      )}

      <div>
        <div 
          className="w-full"
          style={{ height: chartConfig.height || 600 }}
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={chartData}
              layout={orientation === 'horizontal' ? 'horizontal' : 'vertical'}
              margin={{ top: 20, right: 30, left: 40, bottom: 60 }}
              onClick={(data) => {
                if (data?.activePayload?.[0]?.payload && onAgeGroupSelect) {
                  const point = data.activePayload[0].payload;
                  onAgeGroupSelect(point.ageGroup);
                }
              }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(128, 128, 128, 0.2)" />
              
              {orientation === 'horizontal' ? (
                <>
                  <XAxis 
                    type="number"
                    domain={[-maxValue * 1.1, maxValue * 1.1]}
                    tick={{ fontSize: 12 }}
                    tickLine={{ stroke: '#666' }}
                    axisLine={{ stroke: '#666' }}
                    label={{ value: 'Casos', position: 'insideBottom', offset: -10 }}
                    tickFormatter={(value) => Math.abs(value).toLocaleString()}
                  />
                  <YAxis
                    type="category"
                    dataKey="ageGroup"
                    tick={{ fontSize: 11 }}
                    tickLine={{ stroke: '#666' }}
                    axisLine={{ stroke: '#666' }}
                    width={80}
                  />
                </>
              ) : (
                <>
                  <XAxis
                    dataKey="ageGroup"
                    tick={{ fontSize: 11, angle: -45 }}
                    tickLine={{ stroke: '#666' }}
                    axisLine={{ stroke: '#666' }}
                    height={80}
                  />
                  <YAxis
                    domain={[0, maxValue * 1.1]}
                    tick={{ fontSize: 12 }}
                    tickLine={{ stroke: '#666' }}
                    axisLine={{ stroke: '#666' }}
                    label={{ value: 'Casos', angle: -90, position: 'insideLeft' }}
                  />
                </>
              )}

              {/* Barra para masculino (valores negativos en horizontal) */}
              <Bar
                dataKey="male"
                fill={GENDER_COLORS.male}
                stroke="rgba(255, 255, 255, 0.8)"
                strokeWidth={1}
                name="Masculino"
                radius={orientation === 'vertical' ? [4, 4, 0, 0] : undefined}
              />

              {/* Barra para femenino */}
              <Bar
                dataKey="female"
                fill={GENDER_COLORS.female}
                stroke="rgba(255, 255, 255, 0.8)"
                strokeWidth={1}
                name="Femenino"
                radius={orientation === 'vertical' ? [4, 4, 0, 0] : undefined}
              />

              <Tooltip content={<CustomTooltip />} />
              
              <Legend
                layout="horizontal"
                verticalAlign="top"
                align="center"
                wrapperStyle={{ paddingBottom: '20px' }}
                payload={[
                  { value: 'Masculino', type: 'rect', color: GENDER_COLORS.male },
                  { value: 'Femenino', type: 'rect', color: GENDER_COLORS.female },
                ]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Línea central para pirámide horizontal */}
        {orientation === 'horizontal' && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="w-px bg-gray-300 opacity-50" style={{ height: '80%' }} />
          </div>
        )}

        {/* Ranking de grupos etarios */}
        {statistics && chartData.length > 0 && (
          <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-3 bg-gray-50 rounded-lg">
              <h4 className="text-sm font-semibold text-gray-800 mb-2">
                Grupos con más casos
              </h4>
              <div className="space-y-1">
                {chartData
                  .map(d => ({
                    ageGroup: d.ageGroup,
                    total: Math.abs(d.male) + d.female,
                  }))
                  .sort((a, b) => b.total - a.total)
                  .slice(0, 5)
                  .map((group, index) => (
                    <div key={group.ageGroup} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="text-xs">
                          {index + 1}
                        </Badge>
                        <span className="text-sm text-gray-700">{group.ageGroup}</span>
                      </div>
                      <span className="text-sm font-medium">
                        {group.total.toLocaleString()}
                      </span>
                    </div>
                  ))
                }
              </div>
            </div>

            <div className="p-3 bg-gray-50 rounded-lg">
              <h4 className="text-sm font-semibold text-gray-800 mb-2">
                Distribución por sexo
              </h4>
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-700">Casos masculinos:</span>
                  <div className="text-right">
                    <span className="text-sm font-medium">
                      {statistics.genderDistribution.male.toLocaleString()}
                    </span>
                    {showPercentages && (
                      <span className="text-xs text-gray-500 block">
                        {((statistics.genderDistribution.male / statistics.totalCases) * 100).toFixed(1)}%
                      </span>
                    )}
                  </div>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-700">Casos femeninos:</span>
                  <div className="text-right">
                    <span className="text-sm font-medium">
                      {statistics.genderDistribution.female.toLocaleString()}
                    </span>
                    {showPercentages && (
                      <span className="text-xs text-gray-500 block">
                        {((statistics.genderDistribution.female / statistics.totalCases) * 100).toFixed(1)}%
                      </span>
                    )}
                  </div>
                </div>

                <div className="pt-2 border-t border-gray-200">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-gray-800">Ratio M/F:</span>
                    <span className="text-sm font-bold text-gray-900">
                      {statistics.genderDistribution.female > 0 
                        ? (statistics.genderDistribution.male / statistics.genderDistribution.female).toFixed(2)
                        : 'N/A'
                      }
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AgePyramidChart;