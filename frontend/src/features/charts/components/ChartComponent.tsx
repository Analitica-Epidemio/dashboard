"use client";

import React, { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, AlertCircle } from "lucide-react";
import { executeChart } from "../services/api";

interface ChartComponentProps {
  chartCode: string;
  title?: string;
  description?: string;
  filtros?: Record<string, any>;
  parametros?: Record<string, any>;
  className?: string;
  showHeader?: boolean;
  autoLoad?: boolean;
}

interface ChartData {
  chart_id: number;
  chart_codigo: string;
  titulo: string;
  tipo_visualizacion: string;
  data: any;
  filtros_aplicados: Record<string, any>;
  timestamp_generacion: string;
  tiempo_ejecucion_ms: number;
  mensaje?: string;
}

export function ChartComponent({
  chartCode,
  title,
  description,
  filtros = {},
  parametros = {},
  className = "",
  showHeader = true,
  autoLoad = true
}: ChartComponentProps) {
  const [chartData, setChartData] = useState<ChartData | null>(null);
  const [isLoading, setIsLoading] = useState(autoLoad);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (autoLoad) {
      loadChart();
    }
  }, [chartCode, filtros, parametros, autoLoad]);

  const loadChart = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const result = await executeChart({
        chart_codigo: chartCode,
        filtros,
        parametros
      });
      
      setChartData(result.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error cargando chart');
    } finally {
      setIsLoading(false);
    }
  };

  const renderChartContent = () => {
    if (isLoading) {
      return (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin mr-2" />
          <span>Cargando chart...</span>
        </div>
      );
    }

    if (error) {
      return (
        <div className="flex items-center justify-center py-8 text-red-600">
          <AlertCircle className="h-6 w-6 mr-2" />
          <span>{error}</span>
        </div>
      );
    }

    if (!chartData) {
      return (
        <div className="flex items-center justify-center py-8 text-muted-foreground">
          <span>No hay datos para mostrar</span>
        </div>
      );
    }

    // Renderizar según tipo de visualización
    switch (chartData.tipo_visualizacion) {
      case 'metric':
        return <MetricChart data={chartData.data} />;
      case 'line':
        return <LineChart data={chartData.data} />;
      case 'bar':
        return <BarChart data={chartData.data} />;
      case 'pie':
        return <PieChart data={chartData.data} />;
      case 'map':
        return <MapChart data={chartData.data} />;
      default:
        return <GenericChart data={chartData.data} />;
    }
  };

  return (
    <Card className={`h-full ${className}`}>
      {showHeader && (
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">
              {title || chartData?.titulo || chartCode}
            </CardTitle>
            {chartData && (
              <Badge variant="outline" className="text-xs">
                {chartData.tiempo_ejecucion_ms}ms
              </Badge>
            )}
          </div>
          {(description || chartData?.descripcion) && (
            <CardDescription>
              {description || chartData?.descripcion}
            </CardDescription>
          )}
        </CardHeader>
      )}
      <CardContent>
        {renderChartContent()}
      </CardContent>
    </Card>
  );
}

// Componentes específicos por tipo de chart (mock implementations)
function MetricChart({ data }: { data: any }) {
  return (
    <div className="text-center py-4">
      <div className="text-4xl font-bold text-primary mb-2">
        {data.data?.value}{data.data?.unit}
      </div>
      <div className="text-sm text-muted-foreground">
        {data.title}
      </div>
      {data.data?.comparison && (
        <div className="text-xs mt-2">
          <Badge variant={data.data.trend === 'up' ? 'destructive' : 'default'}>
            {data.data.comparison.change_percent > 0 ? '+' : ''}{data.data.comparison.change_percent}%
          </Badge>
        </div>
      )}
    </div>
  );
}

function LineChart({ data }: { data: any }) {
  return (
    <div className="h-64 flex items-center justify-center bg-muted rounded">
      <div className="text-center">
        <div className="text-lg font-semibold mb-2">{data.title}</div>
        <div className="text-sm text-muted-foreground">
          📈 Gráfico de líneas con {data.data?.datasets?.[0]?.data?.length || 0} puntos
        </div>
        <div className="mt-2 text-xs">
          {JSON.stringify(data.data?.datasets?.[0]?.data || [])}
        </div>
      </div>
    </div>
  );
}

function BarChart({ data }: { data: any }) {
  return (
    <div className="h-64 flex items-center justify-center bg-muted rounded">
      <div className="text-center">
        <div className="text-lg font-semibold mb-2">{data.title}</div>
        <div className="text-sm text-muted-foreground">
          📊 Gráfico de barras con {data.data?.labels?.length || 0} categorías
        </div>
        <div className="mt-2 text-xs">
          {data.data?.labels?.join(', ') || 'Sin datos'}
        </div>
      </div>
    </div>
  );
}

function PieChart({ data }: { data: any }) {
  return (
    <div className="h-64 flex items-center justify-center bg-muted rounded">
      <div className="text-center">
        <div className="text-lg font-semibold mb-2">{data.title}</div>
        <div className="text-sm text-muted-foreground">
          🥧 Gráfico circular
        </div>
      </div>
    </div>
  );
}

function MapChart({ data }: { data: any }) {
  return (
    <div className="h-64 flex items-center justify-center bg-muted rounded">
      <div className="text-center">
        <div className="text-lg font-semibold mb-2">{data.title}</div>
        <div className="text-sm text-muted-foreground">
          🗺️ Mapa con {data.data?.locations?.length || 0} ubicaciones
        </div>
        <div className="mt-2 text-xs">
          {data.data?.locations?.join(', ') || 'Sin ubicaciones'}
        </div>
      </div>
    </div>
  );
}

function GenericChart({ data }: { data: any }) {
  return (
    <div className="h-64 flex items-center justify-center bg-muted rounded">
      <div className="text-center">
        <div className="text-lg font-semibold mb-2">{data.title}</div>
        <div className="text-sm text-muted-foreground">
          📈 Chart genérico
        </div>
        <div className="mt-4 p-4 bg-background rounded text-xs">
          <pre className="text-left overflow-auto max-h-32">
            {JSON.stringify(data, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  );
}