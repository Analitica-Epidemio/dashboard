/**
 * Componente de Curva Epidemiológica
 * Gráfico de barras apiladas con datos de virus respiratorios
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
} from 'recharts';
import { AlertTriangle, Activity, TrendingUp } from 'lucide-react';
import {
  EpidemiologicalFilters,
  ChartConfig,
} from '../../types';
import { useEpidemiologicalCurve } from '../../hooks/useEpidemiologicalData';

// Configuración de colores para virus respiratorios (replicando el original)
const VIRAL_AGENT_COLORS = {
  'VSR': 'rgb(255, 127, 14)',           // Naranja
  'INFLUENZA_A': 'rgb(31, 119, 180)',   // Azul
  'INFLUENZA_B': 'rgb(44, 160, 44)',    // Verde
  'SARS_COV_2': 'rgb(214, 39, 40)',     // Rojo
  'RINOVIRUS': 'rgb(148, 103, 189)',    // Púrpura
  'ADENOVIRUS': 'rgb(140, 86, 75)',     // Marrón
  'PARAINFLUENZA': 'rgb(227, 119, 194)', // Rosa
  'METANEUMOVIRUS': 'rgb(127, 127, 127)', // Gris
  'CORONAVIRUS': 'rgb(188, 189, 34)',   // Verde oliva
} as const;

interface EpidemiologicalCurveChartProps {
  filters?: EpidemiologicalFilters;
  chartConfig?: ChartConfig;
  onWeekSelect?: (week: number, year: number) => void;
  showMortalityData?: boolean;
}

// Tooltip personalizado con datos de letalidad
const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload || !payload.length) return null;

  const data = payload[0]?.payload;
  const week = label;

  // Calcular total de casos
  const totalCases = payload.reduce((sum: number, entry: any) => {
    if (entry.dataKey !== 'deaths' && entry.dataKey !== 'mortalityRate') {
      return sum + (entry.value || 0);
    }
    return sum;
  }, 0);

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-4 max-w-sm">
      <div className="border-b border-gray-200 pb-2 mb-2">
        <p className="font-semibold text-gray-800">
          Semana {week} - Año {data?.year}
        </p>
        <p className="text-sm text-gray-600">
          Total casos: {totalCases}
        </p>
      </div>

      <div className="space-y-1">
        {payload.map((entry: any, index: number) => {
          if (entry.dataKey === 'deaths' || entry.dataKey === 'mortalityRate') {
            return null; // Los mostramos por separado
          }

          return (
            <div key={index} className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-2 min-w-0">
                <div 
                  className="w-3 h-3 rounded flex-shrink-0" 
                  style={{ backgroundColor: entry.color }}
                />
                <span className="text-sm text-gray-700 truncate">
                  {entry.name?.replace('_', ' ')}
                </span>
              </div>
              <span className="text-sm font-medium text-gray-900">
                {entry.value}
              </span>
            </div>
          );
        })}
      </div>

      {data?.deaths > 0 && (
        <div className="border-t border-gray-200 pt-2 mt-2">
          <div className="flex items-center justify-between">
            <span className="text-sm text-red-600">Fallecimientos:</span>
            <span className="text-sm font-medium text-red-700">{data.deaths}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-red-600">Tasa letalidad:</span>
            <span className="text-sm font-medium text-red-700">
              {data.mortalityRate?.toFixed(2)}%
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

// Leyenda personalizada con colores específicos
const CustomLegend = ({ viralAgents }: { viralAgents: any[] }) => {
  return (
    <div className="flex flex-wrap gap-4 justify-center mt-4">
      {viralAgents.map((agent) => (
        <div key={agent.id} className="flex items-center gap-2">
          <div 
            className="w-3 h-3 rounded" 
            style={{ backgroundColor: VIRAL_AGENT_COLORS[agent.id as keyof typeof VIRAL_AGENT_COLORS] || agent.color }}
          />
          <span className="text-sm text-gray-700">
            {agent.name.replace('_', ' ')}
          </span>
        </div>
      ))}
    </div>
  );
};

export const EpidemiologicalCurveChart: React.FC<EpidemiologicalCurveChartProps> = ({
  filters,
  chartConfig = {},
  onWeekSelect,
  showMortalityData = true,
}) => {
  const {
    processedData,
    loading,
    error,
    refetch,
  } = useEpidemiologicalCurve(filters);

  // Preparar datos y configuración
  const { chartData, viralAgents, statistics, totalCases, title } = useMemo(() => {
    if (!processedData) {
      return { 
        chartData: [], 
        viralAgents: [], 
        statistics: null, 
        totalCases: 0, 
        title: '' 
      };
    }

    const { chartData, viralAgents, statistics } = processedData;

    // Calcular total de casos
    const total = chartData.reduce((sum, point) => {
      return sum + Object.values(point)
        .filter((value, key) => 
          typeof value === 'number' && 
          !['week', 'year', 'deaths', 'mortalityRate', 'cumulativeMortality'].includes(
            Object.keys(point)[key]
          )
        )
        .reduce((pointSum: number, cases) => pointSum + (cases as number), 0);
    }, 0);

    // Generar título
    const years = [...new Set(chartData.map(d => d.year))];
    const yearText = years.length === 1 ? `${years[0]}` : `${Math.min(...years)}-${Math.max(...years)}`;
    
    const mortalityText = statistics.totalDeaths > 0 
      ? ` - Tasa de letalidad: ${statistics.overallMortalityRate.toFixed(2)}% (100,000 hab.)`
      : '';

    const chartTitle = `Casos de Infecciones Respiratorias Agudas (IRA) por Año y Área Programática${mortalityText}. ${yearText}.`;

    return {
      chartData,
      viralAgents,
      statistics,
      totalCases: total,
      title: chartTitle,
    };
  }, [processedData]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="flex items-center gap-2">
          <div className="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full" />
          <span>Cargando curva epidemiológica...</span>
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
        <h3 className="text-lg font-semibold mb-2">{title}</h3>
        
        {statistics && (
          <div className="flex flex-wrap gap-4">
            <div className="flex items-center gap-2">
              <Activity className="h-4 w-4 text-blue-500" />
              <span className="text-sm font-medium">
                Casos totales: {totalCases.toLocaleString()}
              </span>
            </div>
            
            {statistics.totalDeaths > 0 && (
              <>
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 text-red-500" />
                  <span className="text-sm font-medium">
                    Fallecimientos: {statistics.totalDeaths}
                  </span>
                </div>
                
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-orange-500" />
                  <span className="text-sm font-medium">
                    Tasa letalidad: {statistics.overallMortalityRate.toFixed(2)}%
                  </span>
                </div>
              </>
            )}
          </div>
        )}
      </div>

      <div>
        <div 
          className="w-full"
          style={{ height: chartConfig.height || 600 }}
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={chartData}
              margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
              onClick={(data) => {
                if (data?.activePayload?.[0]?.payload && onWeekSelect) {
                  const point = data.activePayload[0].payload;
                  onWeekSelect(point.week, point.year);
                }
              }}
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
                label={{ value: 'Cantidad', angle: -90, position: 'insideLeft' }}
              />

              {/* Barras para cada virus */}
              {viralAgents.map((agent) => (
                <Bar
                  key={agent.id}
                  dataKey={agent.id}
                  stackId="viral-agents"
                  fill={VIRAL_AGENT_COLORS[agent.id as keyof typeof VIRAL_AGENT_COLORS] || agent.color}
                  stroke="rgba(255, 255, 255, 0.8)"
                  strokeWidth={0.5}
                />
              ))}

              <Tooltip content={<CustomTooltip />} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Leyenda personalizada */}
        <CustomLegend viralAgents={viralAgents} />

        {/* Nota sobre casos totales */}
        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
          <p className="text-xs text-gray-600">
            Casos totales: {totalCases.toLocaleString()}
            {statistics?.totalDeaths === 0 && " - Tasa de letalidad nula (Sin defunciones)"}
          </p>
        </div>
      </div>
    </div>
  );
};

export default EpidemiologicalCurveChart;