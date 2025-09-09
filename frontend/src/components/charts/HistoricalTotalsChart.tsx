/**
 * Componente de Totales Históricos
 * Comparación multi-año por áreas programáticas con subplots
 */

import React, { useMemo, useState } from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
} from 'recharts';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  AlertTriangle, 
  BarChart3, 
  LineChart as LineChartIcon,
  TrendingUp,
  MapPin
} from 'lucide-react';
import {
  EpidemiologicalFilters,
  ChartConfig,
} from '../../types/epidemiological';
import { useHistoricalTotals } from '../../hooks/useEpidemiologicalData';

// Configuración de colores para áreas programáticas
const AREA_COLORS = {
  'SUR_AP_COMODORO': 'rgb(31, 119, 180)',      // Azul - Sur
  'NORTE_AP_NORTE': 'rgb(255, 127, 14)',       // Naranja - Norte  
  'NORESTE_AP_TRELEW': 'rgb(44, 160, 44)',     // Verde - Trelew
  'NOROESTE_AP_ESQUEL': 'rgb(214, 39, 40)',    // Rojo - Esquel
  'TOTAL': 'rgb(148, 103, 189)',               // Púrpura - Total provincial
} as const;

type ChartType = 'line' | 'bar' | 'composed';

interface HistoricalTotalsChartProps {
  filters?: EpidemiologicalFilters;
  chartConfig?: ChartConfig;
  onYearSelect?: (year: number) => void;
  showMortalityData?: boolean;
  defaultChartType?: ChartType;
}

// Tooltip personalizado con información detallada
const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload || !payload.length) return null;

  const year = label;
  const data = payload[0]?.payload;

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-4 max-w-sm">
      <div className="border-b border-gray-200 pb-2 mb-2">
        <p className="font-semibold text-gray-800">Año {year}</p>
        <p className="text-sm text-gray-600">
          Total provincial: {data?.total?.toLocaleString()} casos
        </p>
      </div>

      <div className="space-y-2">
        {payload.map((entry: any, index: number) => {
          if (entry.dataKey === 'total' || entry.dataKey === 'mortalityRate') {
            return null; // Los mostramos por separado
          }

          const areaName = entry.name?.replace(/_/g, ' ').replace('AP ', '- ');

          return (
            <div key={index} className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-2 min-w-0">
                <div 
                  className="w-3 h-3 rounded flex-shrink-0" 
                  style={{ backgroundColor: entry.color }}
                />
                <span className="text-sm text-gray-700 truncate">
                  {areaName}
                </span>
              </div>
              <span className="text-sm font-medium text-gray-900">
                {entry.value?.toLocaleString()}
              </span>
            </div>
          );
        })}
      </div>

      {data?.mortalityRate && data.mortalityRate > 0 && (
        <div className="border-t border-gray-200 pt-2 mt-2">
          <div className="flex items-center justify-between">
            <span className="text-sm text-red-600">Tasa letalidad:</span>
            <span className="text-sm font-medium text-red-700">
              {data.mortalityRate.toFixed(2)}%
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

// Panel de control del gráfico
const ChartControls: React.FC<{
  chartType: ChartType;
  onChartTypeChange: (type: ChartType) => void;
  showMortalityData: boolean;
  onToggleMortality: (show: boolean) => void;
}> = ({ chartType, onChartTypeChange, showMortalityData, onToggleMortality }) => {
  return (
    <div className="flex flex-wrap gap-2 mb-4">
      <div className="flex gap-1">
        <Button
          variant={chartType === 'line' ? 'default' : 'outline'}
          size="sm"
          onClick={() => onChartTypeChange('line')}
        >
          <LineChartIcon className="h-4 w-4" />
          Líneas
        </Button>
        
        <Button
          variant={chartType === 'bar' ? 'default' : 'outline'}
          size="sm"
          onClick={() => onChartTypeChange('bar')}
        >
          <BarChart3 className="h-4 w-4" />
          Barras
        </Button>
        
        <Button
          variant={chartType === 'composed' ? 'default' : 'outline'}
          size="sm"
          onClick={() => onChartTypeChange('composed')}
        >
          <TrendingUp className="h-4 w-4" />
          Mixto
        </Button>
      </div>

      <Badge
        variant={showMortalityData ? 'default' : 'secondary'}
        className="cursor-pointer"
        onClick={() => onToggleMortality(!showMortalityData)}
      >
        Tasa Letalidad
      </Badge>
    </div>
  );
};

// Componente de estadísticas
const StatisticsPanel: React.FC<{
  statistics: any;
  areas: any[];
}> = ({ statistics, areas }) => {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
      <div className="text-center p-3 bg-blue-50 rounded-lg">
        <div className="text-2xl font-bold text-blue-600">
          {statistics.totalCases.toLocaleString()}
        </div>
        <div className="text-sm text-blue-800">Casos Totales</div>
      </div>
      
      <div className="text-center p-3 bg-green-50 rounded-lg">
        <div className="text-2xl font-bold text-green-600">
          {areas.length}
        </div>
        <div className="text-sm text-green-800">Áreas Programáticas</div>
      </div>
      
      <div className="text-center p-3 bg-orange-50 rounded-lg">
        <div className="text-2xl font-bold text-orange-600">
          {statistics.yearsRange[1] - statistics.yearsRange[0] + 1}
        </div>
        <div className="text-sm text-orange-800">Años de Datos</div>
      </div>
      
      {statistics.averageMortalityRate && (
        <div className="text-center p-3 bg-red-50 rounded-lg">
          <div className="text-2xl font-bold text-red-600">
            {statistics.averageMortalityRate.toFixed(2)}%
          </div>
          <div className="text-sm text-red-800">Letalidad Promedio</div>
        </div>
      )}
    </div>
  );
};

export const HistoricalTotalsChart: React.FC<HistoricalTotalsChartProps> = ({
  filters,
  chartConfig = {},
  onYearSelect,
  showMortalityData = true,
  defaultChartType = 'line',
}) => {
  const [chartType, setChartType] = useState<ChartType>(defaultChartType);
  const [showMortality, setShowMortality] = useState(showMortalityData);

  const {
    processedData,
    loading,
    error,
    refetch,
  } = useHistoricalTotals(filters);

  // Preparar datos para el gráfico
  const { chartData, areas, statistics, title } = useMemo(() => {
    if (!processedData) {
      return { chartData: [], areas: [], statistics: null, title: '' };
    }

    const { chartData, areas, statistics } = processedData;

    // Generar título
    const yearRange = `${statistics.yearsRange[0]}-${statistics.yearsRange[1]}`;
    const mortalityText = statistics.averageMortalityRate 
      ? ` - Letalidad promedio: ${statistics.averageMortalityRate.toFixed(2)}%`
      : '';

    const chartTitle = `Totales históricos por Área Programática ${yearRange}${mortalityText}`;

    return {
      chartData,
      areas,
      statistics,
      title: chartTitle,
    };
  }, [processedData]);

  // Renderizar gráfico según tipo seleccionado
  const renderChart = () => {
    const commonProps = {
      data: chartData,
      margin: { top: 20, right: 30, left: 20, bottom: 60 },
      onClick: (data: any) => {
        if (data?.activeLabel && onYearSelect) {
          onYearSelect(data.activeLabel as number);
        }
      },
    };

    const commonElements = (
      <>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(128, 128, 128, 0.2)" />
        
        <XAxis
          dataKey="year"
          tick={{ fontSize: 12 }}
          tickLine={{ stroke: '#666' }}
          axisLine={{ stroke: '#666' }}
          label={{ value: 'Año', position: 'insideBottom', offset: -40 }}
        />
        
        <YAxis
          yAxisId="cases"
          tick={{ fontSize: 12 }}
          tickLine={{ stroke: '#666' }}
          axisLine={{ stroke: '#666' }}
          label={{ value: 'Casos', angle: -90, position: 'insideLeft' }}
        />

        {showMortality && (
          <YAxis
            yAxisId="mortality"
            orientation="right"
            tick={{ fontSize: 12 }}
            tickLine={{ stroke: '#666' }}
            axisLine={{ stroke: '#666' }}
            label={{ value: 'Letalidad (%)', angle: 90, position: 'insideRight' }}
          />
        )}

        <Tooltip content={<CustomTooltip />} />
        <Legend />
      </>
    );

    switch (chartType) {
      case 'bar':
        return (
          <BarChart {...commonProps}>
            {commonElements}
            {areas.map((area) => (
              <Bar
                key={area.id}
                yAxisId="cases"
                dataKey={area.id}
                fill={AREA_COLORS[area.id as keyof typeof AREA_COLORS] || '#8884d8'}
                name={area.name}
              />
            ))}
          </BarChart>
        );

      case 'composed':
        return (
          <ComposedChart {...commonProps}>
            {commonElements}
            {areas.map((area) => (
              <Bar
                key={area.id}
                yAxisId="cases"
                dataKey={area.id}
                fill={AREA_COLORS[area.id as keyof typeof AREA_COLORS] || '#8884d8'}
                name={area.name}
                opacity={0.7}
              />
            ))}
            <Line
              yAxisId="cases"
              type="monotone"
              dataKey="total"
              stroke={AREA_COLORS.TOTAL}
              strokeWidth={3}
              dot={{ fill: AREA_COLORS.TOTAL, strokeWidth: 2, r: 4 }}
              name="Total Provincial"
            />
            {showMortality && (
              <Line
                yAxisId="mortality"
                type="monotone"
                dataKey="mortalityRate"
                stroke="#dc2626"
                strokeWidth={2}
                strokeDasharray="5 5"
                dot={{ fill: '#dc2626', strokeWidth: 2, r: 3 }}
                name="Tasa Letalidad"
              />
            )}
          </ComposedChart>
        );

      default: // 'line'
        return (
          <LineChart {...commonProps}>
            {commonElements}
            {areas.map((area) => (
              <Line
                key={area.id}
                yAxisId="cases"
                type="monotone"
                dataKey={area.id}
                stroke={AREA_COLORS[area.id as keyof typeof AREA_COLORS] || '#8884d8'}
                strokeWidth={2}
                dot={{ fill: AREA_COLORS[area.id as keyof typeof AREA_COLORS], strokeWidth: 2, r: 4 }}
                name={area.name}
              />
            ))}
            <Line
              yAxisId="cases"
              type="monotone"
              dataKey="total"
              stroke={AREA_COLORS.TOTAL}
              strokeWidth={3}
              strokeDasharray="3 3"
              dot={{ fill: AREA_COLORS.TOTAL, strokeWidth: 2, r: 5 }}
              name="Total Provincial"
            />
            {showMortality && (
              <Line
                yAxisId="mortality"
                type="monotone"
                dataKey="mortalityRate"
                stroke="#dc2626"
                strokeWidth={2}
                strokeDasharray="5 5"
                dot={{ fill: '#dc2626', strokeWidth: 2, r: 3 }}
                name="Tasa Letalidad"
              />
            )}
          </LineChart>
        );
    }
  };

  if (loading) {
    return (
      <Card className="w-full">
        <CardContent className="flex items-center justify-center h-96">
          <div className="flex items-center gap-2">
            <div className="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full" />
            <span>Cargando totales históricos...</span>
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
            areas={areas}
          />
        )}

        <ChartControls
          chartType={chartType}
          onChartTypeChange={setChartType}
          showMortalityData={showMortality}
          onToggleMortality={setShowMortality}
        />
      </CardHeader>

      <CardContent>
        <div 
          className="w-full"
          style={{ height: chartConfig.height || 600 }}
        >
          <ResponsiveContainer width="100%" height="100%">
            {renderChart()}
          </ResponsiveContainer>
        </div>

        {/* Información adicional */}
        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <MapPin className="h-4 w-4 text-gray-600" />
            <span className="text-sm font-medium text-gray-700">
              Áreas Programáticas
            </span>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs text-gray-600">
            {areas.map((area) => (
              <div key={area.id} className="flex items-center gap-2">
                <div 
                  className="w-3 h-3 rounded"
                  style={{ backgroundColor: AREA_COLORS[area.id as keyof typeof AREA_COLORS] }}
                />
                <span>{area.name}</span>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default HistoricalTotalsChart;