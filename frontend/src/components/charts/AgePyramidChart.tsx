/**
 * Componente de Pirámide Poblacional por Edad
 * Muestra distribución de casos por grupos de edad y sexo
 */

import React, { useMemo } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AlertTriangle, Users, User, UserCheck } from 'lucide-react';
import {
  EpidemiologicalFilters,
  ChartConfig,
} from '../../types/epidemiological';
import { useAgeCases } from '../../hooks/useEpidemiologicalData';

// Configuración de colores por sexo
const GENDER_COLORS = {
  male: 'rgb(54, 162, 235)',     // Azul para masculino
  female: 'rgb(255, 99, 132)',   // Rosa para femenino
} as const;

interface AgePyramidChartProps {
  filters?: EpidemiologicalFilters;
  chartConfig?: ChartConfig;
  onAgeGroupSelect?: (ageGroup: string) => void;
  showAbsoluteNumbers?: boolean;
}

// Tooltip personalizado para pirámide
const PyramidTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload || !payload.length) return null;

  const ageGroup = label;
  const data = payload[0]?.payload;

  // Los valores negativos son para mostrar a la izquierda
  const maleValue = Math.abs(data?.male || 0);
  const femaleValue = data?.female || 0;
  const total = data?.total || 0;

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3">
      <p className="font-semibold text-gray-800 mb-2">{ageGroup}</p>
      
      <div className="space-y-1">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded" style={{ backgroundColor: GENDER_COLORS.male }} />
            <span className="text-sm text-gray-700">Masculino:</span>
          </div>
          <span className="text-sm font-medium text-gray-900">
            {maleValue.toLocaleString()}
          </span>
        </div>
        
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded" style={{ backgroundColor: GENDER_COLORS.female }} />
            <span className="text-sm text-gray-700">Femenino:</span>
          </div>
          <span className="text-sm font-medium text-gray-900">
            {femaleValue.toLocaleString()}
          </span>
        </div>
        
        <div className="border-t border-gray-200 pt-1 mt-2">
          <div className="flex items-center justify-between gap-4">
            <span className="text-sm font-medium text-gray-700">Total:</span>
            <span className="text-sm font-bold text-gray-900">
              {total.toLocaleString()}
            </span>
          </div>
        </div>
        
        {total > 0 && (
          <div className="text-xs text-gray-500 mt-1">
            Distribución: {((maleValue / total) * 100).toFixed(1)}% M / {((femaleValue / total) * 100).toFixed(1)}% F
          </div>
        )}
      </div>
    </div>
  );
};

// Componente de estadísticas demográficas
const DemographicStats: React.FC<{
  statistics: any;
  totalCases: number;
}> = ({ statistics, totalCases }) => {
  const { genderDistribution, mostAffectedAgeGroup } = statistics;

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
      <div className="text-center p-3 bg-blue-50 rounded-lg">
        <div className="text-2xl font-bold text-blue-600">
          {totalCases.toLocaleString()}
        </div>
        <div className="text-sm text-blue-800">Casos Totales</div>
      </div>
      
      <div className="text-center p-3 bg-cyan-50 rounded-lg">
        <div className="text-2xl font-bold text-cyan-600">
          {genderDistribution.male.toLocaleString()}
        </div>
        <div className="text-sm text-cyan-800">Masculino</div>
      </div>
      
      <div className="text-center p-3 bg-pink-50 rounded-lg">
        <div className="text-2xl font-bold text-pink-600">
          {genderDistribution.female.toLocaleString()}
        </div>
        <div className="text-sm text-pink-800">Femenino</div>
      </div>
      
      <div className="text-center p-3 bg-orange-50 rounded-lg">
        <div className="text-xl font-bold text-orange-600">
          {mostAffectedAgeGroup}
        </div>
        <div className="text-sm text-orange-800">Grupo Más Afectado</div>
      </div>
    </div>
  );
};

// Etiquetas personalizadas para los ejes
const CustomYAxisLabel = ({ value }: { value: string }) => (
  <text className="text-xs fill-gray-600" textAnchor="middle" dominantBaseline="middle">
    {value}
  </text>
);

export const AgePyramidChart: React.FC<AgePyramidChartProps> = ({
  filters,
  chartConfig = {},
  onAgeGroupSelect,
  showAbsoluteNumbers = true,
}) => {
  const {
    processedData,
    loading,
    error,
    refetch,
  } = useAgeCases(filters);

  // Preparar datos y calcular estadísticas
  const { chartData, statistics, totalCases, maxValue, title } = useMemo(() => {
    if (!processedData) {
      return { 
        chartData: [], 
        statistics: null, 
        totalCases: 0, 
        maxValue: 0, 
        title: '' 
      };
    }

    const { chartData, statistics } = processedData;

    // Calcular total y valor máximo para escala
    const total = chartData.reduce((sum, point) => sum + point.total, 0);
    const maxVal = Math.max(
      ...chartData.map(point => Math.max(Math.abs(point.male), point.female))
    );

    const chartTitle = `Distribución de Casos por Edad y Sexo - Total: ${total.toLocaleString()} casos`;

    return {
      chartData,
      statistics,
      totalCases: total,
      maxValue: maxVal,
      title: chartTitle,
    };
  }, [processedData]);

  if (loading) {
    return (
      <Card className="w-full">
        <CardContent className="flex items-center justify-center h-96">
          <div className="flex items-center gap-2">
            <div className="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full" />
            <span>Cargando pirámide de edad...</span>
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
          <DemographicStats 
            statistics={statistics} 
            totalCases={totalCases}
          />
        )}
      </CardHeader>

      <CardContent>
        <div 
          className="w-full"
          style={{ height: chartConfig.height || 500 }}
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={chartData}
              layout="horizontal"
              margin={{ top: 20, right: 30, left: 50, bottom: 20 }}
              onClick={(data) => {
                if (data?.activePayload?.[0]?.payload && onAgeGroupSelect) {
                  const point = data.activePayload[0].payload;
                  onAgeGroupSelect(point.ageGroup);
                }
              }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(128, 128, 128, 0.2)" />
              
              {/* Eje Y para grupos de edad */}
              <YAxis
                type="category"
                dataKey="ageGroup"
                axisLine={false}
                tickLine={false}
                tick={{ fontSize: 12, fill: '#666' }}
                width={80}
              />
              
              {/* Eje X para masculinos (izquierda, valores negativos) */}
              <XAxis
                type="number"
                orientation="top"
                domain={[-maxValue * 1.1, 0]}
                tickFormatter={(value) => Math.abs(value).toString()}
                tick={{ fontSize: 12, fill: '#666' }}
                axisLine={false}
                tickLine={false}
              />
              
              {/* Eje X para femeninos (derecha, valores positivos) */}
              <XAxis
                type="number"
                orientation="top"
                domain={[0, maxValue * 1.1]}
                tick={{ fontSize: 12, fill: '#666' }}
                axisLine={false}
                tickLine={false}
              />

              {/* Barra para masculinos (lado izquierdo) */}
              <Bar
                dataKey="male"
                fill={GENDER_COLORS.male}
                name="Masculino"
                radius={[2, 0, 0, 2]}
              />

              {/* Barra para femeninos (lado derecho) */}
              <Bar
                dataKey="female"
                fill={GENDER_COLORS.female}
                name="Femenino"
                radius={[0, 2, 2, 0]}
              />

              <Tooltip content={<PyramidTooltip />} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Leyenda personalizada */}
        <div className="flex justify-center gap-6 mt-4">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: GENDER_COLORS.male }} />
            <span className="text-sm text-gray-700">
              Masculino ({statistics?.genderDistribution.male.toLocaleString()})
            </span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: GENDER_COLORS.female }} />
            <span className="text-sm text-gray-700">
              Femenino ({statistics?.genderDistribution.female.toLocaleString()})
            </span>
          </div>
        </div>

        {/* Información adicional */}
        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <Users className="h-4 w-4 text-gray-600" />
            <span className="text-sm font-medium text-gray-700">
              Análisis Demográfico
            </span>
          </div>
          
          <div className="text-sm text-gray-600 space-y-1">
            <p>
              • Grupo más afectado: <strong>{statistics?.mostAffectedAgeGroup}</strong>
            </p>
            <p>
              • Distribución por sexo: {statistics && (
                <>
                  <strong>{((statistics.genderDistribution.male / totalCases) * 100).toFixed(1)}% M</strong>
                  {' / '}
                  <strong>{((statistics.genderDistribution.female / totalCases) * 100).toFixed(1)}% F</strong>
                </>
              )}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default AgePyramidChart;