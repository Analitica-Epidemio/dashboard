/**
 * Componente de Distribución por UGD (Unidad de Gestión de Datos)
 * Gráfico de torta con estadísticas detalladas
 */

import React, { useMemo, useState } from 'react';
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
} from 'recharts';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { AlertTriangle, PieChart as PieChartIcon, BarChart3, MapPin } from 'lucide-react';
import {
  EpidemiologicalFilters,
  ChartConfig,
} from '../../types';
import { useUGDCases } from '../../hooks/useEpidemiologicalData';

// Paleta de colores para UGDs (replicando el original)
const UGD_COLORS = [
  'rgb(255, 99, 132)',    // Rosa
  'rgb(54, 162, 235)',    // Azul
  'rgb(255, 205, 86)',    // Amarillo
  'rgb(75, 192, 192)',    // Verde agua
  'rgb(153, 102, 255)',   // Púrpura
  'rgb(255, 159, 64)',    // Naranja
  'rgb(199, 199, 199)',   // Gris
  'rgb(83, 102, 255)',    // Azul índigo
  'rgb(255, 99, 255)',    // Magenta
  'rgb(99, 255, 132)',    // Verde claro
  'rgb(132, 99, 255)',    // Violeta
  'rgb(255, 132, 99)',    // Salmón
] as const;

interface UGDPieChartProps {
  filters?: EpidemiologicalFilters;
  chartConfig?: ChartConfig;
  onUGDSelect?: (ugdName: string) => void;
  chartType?: 'pie' | 'bar';
  showMortalityData?: boolean;
  minPercentageForLabel?: number;
}

// Tooltip personalizado para gráfico de torta
const CustomTooltip = ({ active, payload }: any) => {
  if (!active || !payload || !payload.length) return null;

  const data = payload[0].payload;

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-4 max-w-sm">
      <div className="border-b border-gray-200 pb-2 mb-2">
        <p className="font-semibold text-gray-800">{data.name}</p>
      </div>

      <div className="space-y-1">
        <div className="flex items-center justify-between gap-4">
          <span className="text-sm text-gray-700">Casos:</span>
          <span className="text-sm font-medium text-gray-900">
            {data.value.toLocaleString()}
          </span>
        </div>
        
        <div className="flex items-center justify-between gap-4">
          <span className="text-sm text-gray-700">Porcentaje:</span>
          <span className="text-sm font-medium text-gray-900">
            {data.percentage.toFixed(1)}%
          </span>
        </div>

        {data.mortalityRate > 0 && (
          <div className="border-t border-gray-200 pt-2 mt-2">
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

// Etiquetas personalizadas para el gráfico de torta
const renderCustomizedLabel = ({
  cx, cy, midAngle, innerRadius, outerRadius, percent, name
}: any) => {
  // Solo mostrar etiqueta si el porcentaje es significativo
  if (percent < 0.05) return null; // 5% mínimo

  const RADIAN = Math.PI / 180;
  const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);

  return (
    <text
      x={x}
      y={y}
      fill="white"
      textAnchor={x > cx ? 'start' : 'end'}
      dominantBaseline="central"
      fontSize={12}
      fontWeight="bold"
      style={{ textShadow: '1px 1px 1px rgba(0,0,0,0.5)' }}
    >
      {`${(percent * 100).toFixed(0)}%`}
    </text>
  );
};

// Componente de estadísticas de UGD
const UGDStats: React.FC<{
  statistics: any;
  topUGDs: any[];
}> = ({ statistics, topUGDs }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
      <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
        <div className="flex items-center gap-2 mb-1">
          <MapPin className="h-4 w-4 text-blue-500" />
          <span className="text-sm font-medium text-blue-800">Total UGDs</span>
        </div>
        <div className="text-lg font-bold text-blue-900">
          {statistics.totalUGDs}
        </div>
        <div className="text-sm text-blue-700">
          Unidades activas
        </div>
      </div>

      <div className="p-3 bg-green-50 rounded-lg border border-green-200">
        <div className="flex items-center gap-2 mb-1">
          <PieChartIcon className="h-4 w-4 text-green-500" />
          <span className="text-sm font-medium text-green-800">UGD Principal</span>
        </div>
        <div className="text-lg font-bold text-green-900 truncate">
          {topUGDs[0]?.name || 'N/A'}
        </div>
        <div className="text-sm text-green-700">
          {topUGDs[0]?.percentage.toFixed(1)}% del total
        </div>
      </div>

      <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
        <div className="flex items-center gap-2 mb-1">
          <BarChart3 className="h-4 w-4 text-gray-500" />
          <span className="text-sm font-medium text-gray-800">Concentración</span>
        </div>
        <div className="text-lg font-bold text-gray-900">
          {topUGDs.slice(0, 3).reduce((sum, ugd) => sum + ugd.percentage, 0).toFixed(1)}%
        </div>
        <div className="text-sm text-gray-700">
          Top 3 UGDs
        </div>
      </div>
    </div>
  );
};

export const UGDPieChart: React.FC<UGDPieChartProps> = ({
  filters,
  chartConfig = {},
  onUGDSelect,
  chartType = 'pie',
  showMortalityData = true,
  minPercentageForLabel = 5,
}) => {
  const [selectedUGD, setSelectedUGD] = useState<string | null>(null);
  
  const {
    processedData,
    loading,
    error,
    refetch,
  } = useUGDCases(filters);

  // Preparar datos para visualización
  const { chartData, statistics, title, topUGDs } = useMemo(() => {
    if (!processedData) {
      return { 
        chartData: [], 
        statistics: null, 
        title: '', 
        topUGDs: [] 
      };
    }

    const { chartData, statistics } = processedData;

    // Asignar colores a cada UGD
    const dataWithColors = chartData.map((item, index) => ({
      ...item,
      color: UGD_COLORS[index % UGD_COLORS.length],
    }));

    // Ordenar por casos para ranking
    const sortedForRanking = [...dataWithColors].sort((a, b) => b.value - a.value);

    const chartTitle = `Distribución por Unidad de Gestión de Datos (UGD) - ${
      statistics.totalCases.toLocaleString()
    } casos`;

    return {
      chartData: dataWithColors,
      statistics,
      title: chartTitle,
      topUGDs: sortedForRanking,
    };
  }, [processedData]);

  const handleUGDClick = (data: any) => {
    const ugdName = data.name;
    setSelectedUGD(selectedUGD === ugdName ? null : ugdName);
    if (onUGDSelect) {
      onUGDSelect(ugdName);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="flex items-center gap-2">
          <div className="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full" />
          <span>Cargando distribución por UGD...</span>
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
        <div className="flex justify-between items-start">
          <div>
            <h3 className="text-lg font-semibold">{title}</h3>
          </div>
          <div className="flex gap-2">
            <Button
              variant={chartType === 'pie' ? 'default' : 'outline'}
              size="sm"
              onClick={() => {/* toggle chart type */}}
            >
              <PieChartIcon className="h-4 w-4" />
            </Button>
            <Button
              variant={chartType === 'bar' ? 'default' : 'outline'}
              size="sm"
              onClick={() => {/* toggle chart type */}}
            >
              <BarChart3 className="h-4 w-4" />
            </Button>
          </div>
        </div>
        
        {statistics && (
          <UGDStats statistics={statistics} topUGDs={topUGDs} />
        )}
      </div>

      <div>
        <div 
          className="w-full"
          style={{ height: chartConfig.height || 400 }}
        >
          <ResponsiveContainer width="100%" height="100%">
            {chartType === 'pie' ? (
              <PieChart>
                <Pie
                  data={chartData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={renderCustomizedLabel}
                  outerRadius="80%"
                  fill="#8884d8"
                  dataKey="value"
                  onClick={handleUGDClick}
                  cursor="pointer"
                >
                  {chartData.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={entry.color}
                      stroke={selectedUGD === entry.name ? '#333' : 'none'}
                      strokeWidth={selectedUGD === entry.name ? 2 : 0}
                    />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
                <Legend
                  layout="vertical"
                  align="right"
                  verticalAlign="middle"
                  wrapperStyle={{ paddingLeft: '20px' }}
                  formatter={(value, entry: any) => (
                    <span style={{ color: entry.color }}>
                      {value} ({entry.payload.percentage.toFixed(1)}%)
                    </span>
                  )}
                />
              </PieChart>
            ) : (
              <BarChart
                data={topUGDs}
                margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
                onClick={handleUGDClick}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(128, 128, 128, 0.2)" />
                <XAxis
                  dataKey="name"
                  tick={{ fontSize: 11, angle: -45 }}
                  tickLine={{ stroke: '#666' }}
                  axisLine={{ stroke: '#666' }}
                  height={80}
                />
                <YAxis
                  tick={{ fontSize: 12 }}
                  tickLine={{ stroke: '#666' }}
                  axisLine={{ stroke: '#666' }}
                  label={{ value: 'Casos', angle: -90, position: 'insideLeft' }}
                />
                <Bar
                  dataKey="value"
                  stroke="rgba(255, 255, 255, 0.8)"
                  strokeWidth={1}
                >
                  {topUGDs.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={entry.color}
                    />
                  ))}
                </Bar>
                <Tooltip content={<CustomTooltip />} />
              </BarChart>
            )}
          </ResponsiveContainer>
        </div>

        {/* Ranking detallado */}
        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-3 bg-gray-50 rounded-lg">
            <h4 className="text-sm font-semibold text-gray-800 mb-2">
              Ranking por casos
            </h4>
            <div className="space-y-1 max-h-48 overflow-y-auto">
              {topUGDs.slice(0, 10).map((ugd, index) => (
                <div 
                  key={ugd.name} 
                  className={`flex items-center justify-between p-2 rounded cursor-pointer transition-colors ${
                    selectedUGD === ugd.name ? 'bg-blue-100 border border-blue-300' : 'hover:bg-gray-100'
                  }`}
                  onClick={() => handleUGDClick(ugd)}
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <Badge variant="outline" className="text-xs flex-shrink-0">
                      {index + 1}
                    </Badge>
                    <div 
                      className="w-3 h-3 rounded flex-shrink-0" 
                      style={{ backgroundColor: ugd.color }}
                    />
                    <span className="text-sm text-gray-700 truncate">
                      {ugd.name}
                    </span>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <span className="text-sm font-medium">
                      {ugd.value.toLocaleString()}
                    </span>
                    <span className="text-xs text-gray-500 block">
                      {ugd.percentage.toFixed(1)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {showMortalityData && (
            <div className="p-3 bg-gray-50 rounded-lg">
              <h4 className="text-sm font-semibold text-gray-800 mb-2">
                Tasas de letalidad por UGD
              </h4>
              <div className="space-y-1 max-h-48 overflow-y-auto">
                {topUGDs
                  .filter(ugd => ugd.mortalityRate > 0)
                  .sort((a, b) => b.mortalityRate - a.mortalityRate)
                  .slice(0, 8)
                  .map((ugd) => (
                    <div 
                      key={ugd.name} 
                      className="flex items-center justify-between p-2 rounded hover:bg-gray-100"
                    >
                      <div className="flex items-center gap-2 min-w-0">
                        <div 
                          className="w-3 h-3 rounded flex-shrink-0" 
                          style={{ backgroundColor: ugd.color }}
                        />
                        <span className="text-sm text-gray-700 truncate">
                          {ugd.name}
                        </span>
                      </div>
                      <span className="text-sm font-medium text-red-600">
                        {ugd.mortalityRate.toFixed(2)}%
                      </span>
                    </div>
                  ))
                }
                {topUGDs.filter(ugd => ugd.mortalityRate > 0).length === 0 && (
                  <p className="text-sm text-gray-500 text-center py-4">
                    Sin datos de letalidad disponibles
                  </p>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Información seleccionada */}
        {selectedUGD && (
          <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
            <h4 className="text-sm font-semibold text-blue-800 mb-2">
              UGD Seleccionada: {selectedUGD}
            </h4>
            {(() => {
              const ugdData = topUGDs.find(ugd => ugd.name === selectedUGD);
              return ugdData ? (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-blue-700">Casos:</span>
                    <div className="font-medium text-blue-900">
                      {ugdData.value.toLocaleString()}
                    </div>
                  </div>
                  <div>
                    <span className="text-blue-700">Porcentaje:</span>
                    <div className="font-medium text-blue-900">
                      {ugdData.percentage.toFixed(1)}%
                    </div>
                  </div>
                  <div>
                    <span className="text-blue-700">Ranking:</span>
                    <div className="font-medium text-blue-900">
                      #{topUGDs.findIndex(u => u.name === selectedUGD) + 1}
                    </div>
                  </div>
                  <div>
                    <span className="text-blue-700">Tasa letalidad:</span>
                    <div className="font-medium text-blue-900">
                      {ugdData.mortalityRate > 0 ? `${ugdData.mortalityRate.toFixed(2)}%` : 'N/A'}
                    </div>
                  </div>
                </div>
              ) : null;
            })()}
          </div>
        )}
      </div>
    </div>
  );
};

export default UGDPieChart;