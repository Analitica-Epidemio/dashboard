/**
 * Grid responsive de charts epidemiológicos
 * Layout inteligente que prioriza los análisis más importantes
 */

import React, { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Maximize2, 
  Minimize2, 
  RefreshCw, 
  Download,
  Settings,
  Eye,
  EyeOff,
  Info
} from 'lucide-react';
import {
  EpidemiologicalCurveChart,
  EndemicCorridorChart,
  HistoricalTotalsChart,
  AgePyramidChart,
  UGDPieChart,
  SuicideAttemptChart,
  AnimalRabiesChart,
  type EpidemiologicalFilters,
  type EndemicCorridorConfig,
} from './charts';

interface ChartConfig {
  id: string;
  title: string;
  component: React.ComponentType<any>;
  priority: number; // 1 = más alta, 5 = más baja
  size: 'small' | 'medium' | 'large' | 'full';
  category: 'primary' | 'secondary' | 'specialized';
  props?: any;
  visible: boolean;
  loading?: boolean;
}

interface ChartGridProps {
  selectedGroup?: { name: string } | null;
  selectedEvent?: { name: string } | null;
  filters: EpidemiologicalFilters;
}

// Configuración del corredor endémico
const DEFAULT_ENDEMIC_CONFIG: EndemicCorridorConfig = {
  calculation: 'media',
  cumulative: false,
  logarithmic: false,
  movingWindow: 4,
  lastWeek: new Date().getWeek ? new Date().getWeek() : 1,
};

// Función para obtener la semana del año
const getWeekNumber = (date: Date): number => {
  const tempDate = new Date(date.getTime());
  tempDate.setHours(0, 0, 0, 0);
  tempDate.setDate(tempDate.getDate() + 3 - (tempDate.getDay() + 6) % 7);
  const week1 = new Date(tempDate.getFullYear(), 0, 4);
  return 1 + Math.round(((tempDate.getTime() - week1.getTime()) / 86400000 - 3 + (week1.getDay() + 6) % 7) / 7);
};

export const ChartGrid: React.FC<ChartGridProps> = ({
  selectedGroup,
  selectedEvent,
  filters,
}) => {
  const [expandedChart, setExpandedChart] = useState<string | null>(null);
  const [chartVisibility, setChartVisibility] = useState<Record<string, boolean>>({
    'epidemiological-curve': true,
    'endemic-corridor': true,
    'age-pyramid': true,
    'ugd-distribution': true,
    'historical-totals': false,
    'suicide-attempt': false,
    'animal-rabies': false,
  });

  // Configuración de todos los charts
  const chartConfigs: ChartConfig[] = useMemo(() => [
    {
      id: 'epidemiological-curve',
      title: 'Curva Epidemiológica',
      component: EpidemiologicalCurveChart,
      priority: 1,
      size: expandedChart === 'epidemiological-curve' ? 'full' : 'large',
      category: 'primary',
      visible: chartVisibility['epidemiological-curve'],
      props: {
        filters,
        chartConfig: { height: expandedChart === 'epidemiological-curve' ? 800 : 400 },
        showMortalityData: true,
      },
    },
    {
      id: 'endemic-corridor',
      title: 'Corredor Endémico',
      component: EndemicCorridorChart,
      priority: 2,
      size: expandedChart === 'endemic-corridor' ? 'full' : 'large',
      category: 'primary',
      visible: chartVisibility['endemic-corridor'],
      props: {
        filters,
        config: DEFAULT_ENDEMIC_CONFIG,
        chartConfig: { height: expandedChart === 'endemic-corridor' ? 800 : 400 },
        showCurrentWeekIndicator: true,
      },
    },
    {
      id: 'age-pyramid',
      title: 'Distribución por Edad y Sexo',
      component: AgePyramidChart,
      priority: 3,
      size: expandedChart === 'age-pyramid' ? 'full' : 'medium',
      category: 'secondary',
      visible: chartVisibility['age-pyramid'],
      props: {
        filters,
        chartConfig: { height: expandedChart === 'age-pyramid' ? 700 : 350 },
        showPercentages: true,
        orientation: 'horizontal',
      },
    },
    {
      id: 'ugd-distribution',
      title: 'Distribución por UGD',
      component: UGDPieChart,
      priority: 4,
      size: expandedChart === 'ugd-distribution' ? 'full' : 'medium',
      category: 'secondary',
      visible: chartVisibility['ugd-distribution'],
      props: {
        filters,
        chartConfig: { height: expandedChart === 'ugd-distribution' ? 700 : 350 },
        chartType: 'pie',
        showMortalityData: true,
      },
    },
    {
      id: 'historical-totals',
      title: 'Totales Históricos',
      component: HistoricalTotalsChart,
      priority: 5,
      size: expandedChart === 'historical-totals' ? 'full' : 'large',
      category: 'secondary',
      visible: chartVisibility['historical-totals'],
      props: {
        filters,
        chartConfig: { height: expandedChart === 'historical-totals' ? 800 : 400 },
        chartType: 'line',
        showTrendIndicators: true,
      },
    },
    {
      id: 'suicide-attempt',
      title: 'Análisis de Intento de Suicidio',
      component: SuicideAttemptChart,
      priority: 6,
      size: expandedChart === 'suicide-attempt' ? 'full' : 'large',
      category: 'specialized',
      visible: chartVisibility['suicide-attempt'],
      props: {
        filters,
        chartConfig: { height: expandedChart === 'suicide-attempt' ? 800 : 500 },
        showDemographics: true,
        defaultView: 'temporal',
      },
    },
    {
      id: 'animal-rabies',
      title: 'Vigilancia de Rabia Animal',
      component: AnimalRabiesChart,
      priority: 7,
      size: expandedChart === 'animal-rabies' ? 'full' : 'large',
      category: 'specialized',
      visible: chartVisibility['animal-rabies'],
      props: {
        filters,
        chartConfig: { height: expandedChart === 'animal-rabies' ? 800 : 500 },
        defaultView: 'temporal',
        showPositivityRate: true,
      },
    },
  ], [filters, expandedChart, chartVisibility]);

  // Filtrar y ordenar charts visibles
  const visibleCharts = chartConfigs
    .filter(chart => chart.visible)
    .sort((a, b) => a.priority - b.priority);

  // Función para obtener clases CSS del grid según el tamaño
  const getGridClasses = (size: string, isExpanded: boolean) => {
    if (isExpanded) return 'col-span-full';
    
    switch (size) {
      case 'full': return 'col-span-full';
      case 'large': return 'col-span-full xl:col-span-2';
      case 'medium': return 'col-span-full lg:col-span-1 xl:col-span-1';
      case 'small': return 'col-span-full md:col-span-1 lg:col-span-1';
      default: return 'col-span-full';
    }
  };

  const toggleChartVisibility = (chartId: string) => {
    setChartVisibility(prev => ({
      ...prev,
      [chartId]: !prev[chartId],
    }));
  };

  const toggleExpanded = (chartId: string) => {
    setExpandedChart(expandedChart === chartId ? null : chartId);
  };

  if (!selectedGroup || !selectedEvent) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-12">
        <div className="text-center">
          <Info className="h-16 w-16 text-gray-400 mx-auto mb-6" />
          <h3 className="text-xl font-medium text-gray-900 mb-4">
            Configuración Requerida
          </h3>
          <p className="text-gray-600 max-w-md mx-auto">
            Selecciona un grupo de eventos y un evento específico en el sidebar 
            para visualizar los análisis epidemiológicos correspondientes.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Control Panel */}
      <div className="flex items-center justify-between bg-white rounded-lg border border-gray-200 p-4">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">
            Análisis Epidemiológicos
          </h2>
          <p className="text-sm text-gray-600">
            {visibleCharts.length} de {chartConfigs.length} gráficos activos
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          {/* Controles de visibilidad rápidos */}
          <div className="hidden lg:flex items-center space-x-1">
            {chartConfigs.map(chart => (
              <Button
                key={chart.id}
                variant={chart.visible ? "default" : "outline"}
                size="sm"
                onClick={() => toggleChartVisibility(chart.id)}
                className="text-xs"
              >
                {chart.visible ? <Eye className="h-3 w-3 mr-1" /> : <EyeOff className="h-3 w-3 mr-1" />}
                {chart.title.split(' ')[0]}
              </Button>
            ))}
          </div>
          
          <Button variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-1" />
            Actualizar
          </Button>
          
          <Button variant="outline" size="sm">
            <Settings className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 lg:gap-6">
        {visibleCharts.map((chart) => {
          const ChartComponent = chart.component;
          const isExpanded = expandedChart === chart.id;
          
          return (
            <div
              key={chart.id}
              className={getGridClasses(chart.size, isExpanded)}
            >
              <Card className="h-full border border-gray-200">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <CardTitle className="text-lg font-medium">
                        {chart.title}
                      </CardTitle>
                      <Badge 
                        variant="outline" 
                        className={`text-xs ${
                          chart.category === 'primary' ? 'bg-blue-50 text-blue-700' :
                          chart.category === 'secondary' ? 'bg-green-50 text-green-700' :
                          'bg-purple-50 text-purple-700'
                        }`}
                      >
                        {chart.category === 'primary' ? 'Principal' :
                         chart.category === 'secondary' ? 'Secundario' :
                         'Especializado'}
                      </Badge>
                    </div>
                    
                    <div className="flex items-center space-x-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => toggleExpanded(chart.id)}
                      >
                        {isExpanded ? 
                          <Minimize2 className="h-4 w-4" /> : 
                          <Maximize2 className="h-4 w-4" />
                        }
                      </Button>
                      
                      <Button variant="ghost" size="sm">
                        <Download className="h-4 w-4" />
                      </Button>
                      
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => toggleChartVisibility(chart.id)}
                      >
                        <EyeOff className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                
                <CardContent className="pt-0">
                  <div className={isExpanded ? 'min-h-[800px]' : ''}>
                    <ChartComponent {...chart.props} />
                  </div>
                </CardContent>
              </Card>
            </div>
          );
        })}
      </div>

      {/* Footer con información */}
      <div className="bg-gray-50 rounded-lg border border-gray-200 p-4">
        <div className="flex items-center justify-between text-sm text-gray-600">
          <div>
            Datos actualizados: {new Date().toLocaleString('es-ES')}
          </div>
          <div className="flex items-center space-x-4">
            <span>SE {getWeekNumber(new Date())}/2024</span>
            <Badge variant="outline" className="text-xs">
              {selectedGroup.name} • {selectedEvent.name}
            </Badge>
          </div>
        </div>
      </div>
    </div>
  );
};