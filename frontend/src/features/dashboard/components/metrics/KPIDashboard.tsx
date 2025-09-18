/**
 * Dashboard de KPIs epidemiológicos
 * Métricas clave con indicadores de tendencia y alertas visuales
 */

import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  TrendingUp, 
  TrendingDown, 
  AlertTriangle, 
  Activity,
  Users,
  Calendar,
  Target,
  Heart,
  Minus,
  Info
} from 'lucide-react';

interface KPIMetric {
  id: string;
  label: string;
  value: number | string;
  previousValue?: number;
  unit?: string;
  trend?: 'up' | 'down' | 'stable';
  trendPercentage?: number;
  status?: 'normal' | 'warning' | 'critical';
  icon: React.ElementType;
  description?: string;
}

interface KPIDashboardProps {
  selectedGroup?: { name: string } | null;
  selectedEvent?: { name: string } | null;
  loading?: boolean;
}

export const KPIDashboard: React.FC<KPIDashboardProps> = ({
  selectedGroup,
  selectedEvent,
  loading = false,
}) => {
  // Simulación de datos KPI (en producción vendrían de la API)
  const kpiMetrics: KPIMetric[] = [
    {
      id: 'total_casos',
      label: 'Total de Casos',
      value: loading ? '---' : '2,847',
      previousValue: 2650,
      trend: 'up',
      trendPercentage: 7.4,
      status: 'normal',
      icon: Activity,
      description: 'Casos registrados en el período seleccionado',
    },
    {
      id: 'casos_nuevos',
      label: 'Casos Nuevos (7d)',
      value: loading ? '---' : '184',
      previousValue: 156,
      trend: 'up',
      trendPercentage: 17.9,
      status: 'normal',
      icon: TrendingUp,
      description: 'Nuevos casos en los últimos 7 días',
    },
    {
      id: 'tasa_incidencia',
      label: 'Tasa de Incidencia',
      value: loading ? '---' : '45.2',
      unit: '/100k hab',
      previousValue: 42.1,
      trend: 'up',
      trendPercentage: 7.4,
      status: 'normal',
      icon: Target,
      description: 'Casos por 100,000 habitantes',
    },
    {
      id: 'mortalidad',
      label: 'Tasa de Letalidad',
      value: loading ? '---' : '2.3',
      unit: '%',
      previousValue: 2.1,
      trend: 'up',
      trendPercentage: 9.5,
      status: 'normal',
      icon: Heart,
      description: 'Porcentaje de casos fatales',
    },
    {
      id: 'areas_afectadas',
      label: 'Áreas Afectadas',
      value: loading ? '---' : '12',
      unit: 'de 24',
      previousValue: 10,
      trend: 'up',
      trendPercentage: 20.0,
      status: 'normal',
      icon: Users,
      description: 'Áreas programáticas con casos activos',
    },
    {
      id: 'tiempo_promedio',
      label: 'Tiempo Resp. Promedio',
      value: loading ? '---' : '1.8',
      unit: 'días',
      previousValue: 2.3,
      trend: 'down',
      trendPercentage: 21.7,
      status: 'normal',
      icon: Calendar,
      description: 'Tiempo promedio de respuesta epidemiológica',
    },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'critical': return 'border-red-200 bg-red-50';
      case 'warning': return 'border-yellow-200 bg-yellow-50';
      default: return 'border-green-200 bg-green-50';
    }
  };

  const getStatusBadgeColor = (status: string) => {
    switch (status) {
      case 'critical': return 'bg-red-100 text-red-800';
      case 'warning': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-green-100 text-green-800';
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up': return TrendingUp;
      case 'down': return TrendingDown;
      default: return Minus;
    }
  };

  const getTrendColor = (trend: string, isGoodTrend = false) => {
    if (trend === 'stable') return 'text-gray-500';
    
    const isPositiveTrend = trend === 'up';
    const shouldBeGreen = isGoodTrend ? !isPositiveTrend : isPositiveTrend;
    
    return shouldBeGreen ? 'text-green-600' : 'text-red-600';
  };

  if (!selectedGroup || !selectedEvent) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-8">
        <div className="text-center">
          <Info className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Selecciona Grupo y Evento
          </h3>
          <p className="text-sm text-gray-600">
            Configura los filtros en el sidebar para ver las métricas epidemiológicas
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header con contexto */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">
              Indicadores Epidemiológicos Clave
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              {selectedGroup.name} • {selectedEvent.name}
            </p>
          </div>
          
          <div className="flex items-center space-x-2">
            <Badge variant="outline" className="text-xs">
              Actualizado hace 15 min
            </Badge>
            <Badge variant="outline" className="text-xs">
              SE {(() => {
                const date = new Date();
                const tempDate = new Date(date.getTime());
                tempDate.setHours(0, 0, 0, 0);
                tempDate.setDate(tempDate.getDate() + 3 - (tempDate.getDay() + 6) % 7);
                const week1 = new Date(tempDate.getFullYear(), 0, 4);
                return 1 + Math.round(((tempDate.getTime() - week1.getTime()) / 86400000 - 3 + (week1.getDay() + 6) % 7) / 7);
              })()}/2024
            </Badge>
          </div>
        </div>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3">
        {kpiMetrics.map((metric) => {
          const Icon = metric.icon;
          const TrendIcon = getTrendIcon(metric.trend || 'stable');
          const isGoodTrend = metric.id === 'tiempo_promedio'; // Tiempo menor es mejor
          
          return (
            <Card 
              key={metric.id} 
              className={`border ${
                getStatusColor(metric.status || 'normal')
              }`}
            >
              <CardContent className="p-2">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    {/* Header con icono y estado */}
                    <div className="flex items-center justify-between mb-1">
                      <Icon className={`h-4 w-4 ${
                        metric.status === 'critical' ? 'text-red-600' :
                        metric.status === 'warning' ? 'text-yellow-600' :
                        'text-green-600'
                      }`} />
                      
                      {metric.status && metric.status !== 'normal' && (
                        <Badge 
                          className={`text-xs ${getStatusBadgeColor(metric.status)}`}
                          variant="secondary"
                        >
                          {metric.status === 'critical' && <AlertTriangle className="h-3 w-3 mr-1" />}
                          {metric.status === 'critical' ? 'Crítico' : 'Alerta'}
                        </Badge>
                      )}
                    </div>

                    {/* Valor principal */}
                    <div className="mb-1">
                      <div className="flex items-baseline gap-1">
                        <span className="text-base font-bold text-gray-900">
                          {metric.value}
                        </span>
                        {metric.unit && (
                          <span className="text-xs text-gray-500">
                            {metric.unit}
                          </span>
                        )}
                      </div>
                      
                      <h3 className="text-xs font-medium text-gray-700">
                        {metric.label}
                      </h3>
                    </div>

                    {/* Tendencia */}
                    {metric.trend && metric.trendPercentage && (
                      <div className="flex items-center gap-1">
                        <TrendIcon className={`h-3 w-3 ${
                          getTrendColor(metric.trend, isGoodTrend)
                        }`} />
                        <span className={`text-xs font-medium ${
                          getTrendColor(metric.trend, isGoodTrend)
                        }`}>
                          {metric.trendPercentage.toFixed(1)}%
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
};