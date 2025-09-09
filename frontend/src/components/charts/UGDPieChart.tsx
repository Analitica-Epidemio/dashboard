/**
 * Componente de Gráfico de Torta para Casos por UGD
 * Muestra distribución de casos por Unidad de Gestión Descentralizada
 */

import React, { useMemo, useState } from 'react';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from 'recharts';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { AlertTriangle, MapPin, BarChart3, Percent } from 'lucide-react';
import {
  EpidemiologicalFilters,
  ChartConfig,
} from '../../types/epidemiological';
import { useUGDCases } from '../../hooks/useEpidemiologicalData';

// Configuración de colores para UGDs
const UGD_COLORS = [
  'rgb(31, 119, 180)',   // Azul
  'rgb(255, 127, 14)',   // Naranja
  'rgb(44, 160, 44)',    // Verde
  'rgb(214, 39, 40)',    // Rojo
  'rgb(148, 103, 189)',  // Púrpura
  'rgb(140, 86, 75)',    // Marrón
  'rgb(227, 119, 194)',  // Rosa
  'rgb(127, 127, 127)',  // Gris
  'rgb(188, 189, 34)',   // Verde oliva
  'rgb(23, 190, 207)',   // Cian
] as const;

interface UGDPieChartProps {
  filters?: EpidemiologicalFilters;
  chartConfig?: ChartConfig;
  onUGDSelect?: (ugdId: string) => void;
  showMortalityData?: boolean;
  chartType?: 'pie' | 'donut';
}

// Tooltip personalizado
const CustomTooltip = ({ active, payload }: any) => {
  if (!active || !payload || !payload.length) return null;

  const data = payload[0]?.payload;

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3">
      <p className="font-semibold text-gray-800 mb-2">{data?.name}</p>
      
      <div className="space-y-1">
        <div className="flex items-center justify-between gap-4">
          <span className="text-sm text-gray-700">Casos:</span>
          <span className="text-sm font-medium text-gray-900">
            {data?.value?.toLocaleString()}
          </span>
        </div>
        
        <div className="flex items-center justify-between gap-4">
          <span className="text-sm text-gray-700">Porcentaje:</span>
          <span className="text-sm font-medium text-gray-900">
            {data?.percentage?.toFixed(1)}%
          </span>
        </div>
        
        {data?.mortalityRate && (
          <div className="border-t border-gray-200 pt-1 mt-2">
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

// Etiquetas personalizadas para el gráfico
const CustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }: any) => {
  const RADIAN = Math.PI / 180;
  const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);

  // Solo mostrar etiqueta si el porcentaje es mayor al 5%
  if (percent < 0.05) return null;

  return (
    <text
      x={x}
      y={y}
      fill="white"
      textAnchor={x > cx ? 'start' : 'end'}
      dominantBaseline="central"
      className="text-xs font-semibold drop-shadow"
    >
      {`${(percent * 100).toFixed(0)}%`}
    </text>
  );
};

// Leyenda personalizada
const CustomLegend = ({ payload, onItemClick }: any) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mt-4">
      {payload.map((entry: any, index: number) => (
        <div
          key={index}
          className="flex items-center gap-2 cursor-pointer hover:bg-gray-50 p-2 rounded"
          onClick={() => onItemClick?.(entry.payload)}
        >
          <div
            className="w-3 h-3 rounded flex-shrink-0"
            style={{ backgroundColor: entry.color }}
          />
          <div className="min-w-0 flex-1">
            <span className="text-sm text-gray-700 truncate block">
              {entry.value}
            </span>
            <span className="text-xs text-gray-500">
              {entry.payload?.value?.toLocaleString()} casos ({entry.payload?.percentage?.toFixed(1)}%)
            </span>
          </div>
        </div>
      ))}
    </div>
  );
};

// Panel de estadísticas
const StatisticsPanel: React.FC<{
  statistics: any;
  totalCases: number;
  showMortalityData: boolean;
}> = ({ statistics, totalCases, showMortalityData }) => {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
      <div className="text-center p-3 bg-blue-50 rounded-lg">
        <div className="text-2xl font-bold text-blue-600">
          {totalCases.toLocaleString()}
        </div>
        <div className="text-sm text-blue-800">Casos Totales</div>
      </div>
      
      <div className="text-center p-3 bg-green-50 rounded-lg">
        <div className="text-xl font-bold text-green-600">
          {statistics.mostAffectedUGD}
        </div>
        <div className="text-sm text-green-800">UGD Más Afectada</div>
      </div>

      {showMortalityData && (
        <div className="text-center p-3 bg-red-50 rounded-lg">
          <div className="text-2xl font-bold text-red-600">
            Variable
          </div>
          <div className="text-sm text-red-800">Tasa Letalidad</div>
        </div>
      )}
    </div>
  );
};

export const UGDPieChart: React.FC<UGDPieChartProps> = ({
  filters,
  chartConfig = {},
  onUGDSelect,
  showMortalityData = false,
  chartType = 'pie',
}) => {
  const [selectedSegment, setSelectedSegment] = useState<string | null>(null);

  const {
    processedData,
    loading,
    error,
    refetch,
  } = useUGDCases(filters);

  // Preparar datos con colores
  const { chartData, statistics, totalCases, title } = useMemo(() => {
    if (!processedData) {
      return { chartData: [], statistics: null, totalCases: 0, title: '' };
    }

    const { chartData, statistics } = processedData;

    // Asignar colores a los datos
    const dataWithColors = chartData.map((item, index) => ({
      ...item,
      fill: UGD_COLORS[index % UGD_COLORS.length],
    }));

    const total = chartData.reduce((sum, item) => sum + item.value, 0);
    
    const chartTitle = `Distribución de Casos por Unidad de Gestión Descentralizada - Total: ${total.toLocaleString()} casos`;

    return {
      chartData: dataWithColors,
      statistics,
      totalCases: total,
      title: chartTitle,
    };
  }, [processedData]);

  const handlePieClick = (data: any) => {
    if (data && onUGDSelect) {
      onUGDSelect(data.ugdId);
    }
    setSelectedSegment(data?.name || null);
  };

  if (loading) {
    return (
      <Card className="w-full">
        <CardContent className="flex items-center justify-center h-96">
          <div className="flex items-center gap-2">
            <div className="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full" />
            <span>Cargando distribución por UGD...</span>
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
        <div className="flex justify-between items-start">
          <h3 className="text-lg font-semibold">{title}</h3>
          
          <div className="flex gap-2">
            <Badge 
              variant={chartType === 'pie' ? 'default' : 'outline'}
              className="cursor-pointer"
            >
              <BarChart3 className="h-3 w-3 mr-1" />
              Torta
            </Badge>
            
            <Badge 
              variant={showMortalityData ? 'default' : 'secondary'}
              className="cursor-pointer"
            >
              <Percent className="h-3 w-3 mr-1" />
              Letalidad
            </Badge>
          </div>
        </div>
        
        {statistics && (
          <StatisticsPanel 
            statistics={statistics} 
            totalCases={totalCases}
            showMortalityData={showMortalityData}
          />
        )}
      </CardHeader>

      <CardContent>
        <div 
          className="w-full"
          style={{ height: chartConfig.height || 500 }}
        >
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={CustomLabel}
                outerRadius={chartType === 'donut' ? 120 : 140}
                innerRadius={chartType === 'donut' ? 60 : 0}
                fill="#8884d8"
                dataKey="value"
                onClick={handlePieClick}
              >
                {chartData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={entry.fill}
                    stroke={selectedSegment === entry.name ? '#333' : 'none'}
                    strokeWidth={selectedSegment === entry.name ? 2 : 0}
                    style={{
                      cursor: 'pointer',
                      opacity: selectedSegment && selectedSegment !== entry.name ? 0.6 : 1,
                    }}
                  />
                ))}
              </Pie>
              
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Leyenda personalizada */}
        <CustomLegend 
          payload={chartData.map((item, index) => ({
            value: item.name,
            color: item.fill,
            payload: item,
          }))}
          onItemClick={handlePieClick}
        />

        {/* Información del segmento seleccionado */}
        {selectedSegment && (
          <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
            <div className="flex items-center gap-2">
              <MapPin className="h-4 w-4 text-blue-600" />
              <span className="text-sm font-medium text-blue-800">
                Seleccionado: {selectedSegment}
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSelectedSegment(null)}
                className="ml-auto"
              >
                ✕
              </Button>
            </div>
          </div>
        )}

        {/* Información adicional */}
        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <MapPin className="h-4 w-4 text-gray-600" />
            <span className="text-sm font-medium text-gray-700">
              Unidades de Gestión Descentralizada (UGD)
            </span>
          </div>
          
          <div className="text-sm text-gray-600 space-y-1">
            <p>
              • UGD más afectada: <strong>{statistics?.mostAffectedUGD}</strong>
            </p>
            <p>
              • Total de UGDs con casos: <strong>{chartData.length}</strong>
            </p>
            <p className="text-xs text-gray-500 mt-2">
              Haz clic en un segmento o en la leyenda para seleccionar una UGD específica
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default UGDPieChart;