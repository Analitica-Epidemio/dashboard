/**
 * Hook para usar charts en dashboards
 */

import { useState, useEffect } from 'react';
import { executeChart } from '../services/api';

interface UseChartOptions {
  chartCode: string;
  filtros?: Record<string, any>;
  parametros?: Record<string, any>;
  autoLoad?: boolean;
  refetchOnFilterChange?: boolean;
}

interface UseChartReturn {
  data: any;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  executionTime: number | null;
}

export function useChart({
  chartCode,
  filtros = {},
  parametros = {},
  autoLoad = true,
  refetchOnFilterChange = true
}: UseChartOptions): UseChartReturn {
  const [data, setData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(autoLoad);
  const [error, setError] = useState<string | null>(null);
  const [executionTime, setExecutionTime] = useState<number | null>(null);

  const fetchChart = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const result = await executeChart({
        chart_codigo: chartCode,
        filtros,
        parametros
      });
      
      setData(result.data);
      setExecutionTime(result.data.tiempo_ejecucion_ms || null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error cargando chart');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (autoLoad) {
      fetchChart();
    }
  }, [chartCode]);

  useEffect(() => {
    if (refetchOnFilterChange && !isLoading && data) {
      fetchChart();
    }
  }, [filtros, parametros]);

  return {
    data,
    isLoading,
    error,
    refetch: fetchChart,
    executionTime
  };
}

/**
 * Hook para usar múltiples charts
 */
interface UseMultipleChartsOptions {
  charts: Array<{
    code: string;
    filtros?: Record<string, any>;
    parametros?: Record<string, any>;
  }>;
  autoLoad?: boolean;
}

export function useMultipleCharts({
  charts,
  autoLoad = true
}: UseMultipleChartsOptions) {
  const [chartsData, setChartsData] = useState<Record<string, any>>({});
  const [loadingCharts, setLoadingCharts] = useState<Set<string>>(new Set());
  const [errors, setErrors] = useState<Record<string, string>>({});

  const fetchChart = async (chartConfig: typeof charts[0]) => {
    setLoadingCharts(prev => new Set(prev).add(chartConfig.code));
    setErrors(prev => {
      const newErrors = { ...prev };
      delete newErrors[chartConfig.code];
      return newErrors;
    });

    try {
      const result = await executeChart({
        chart_codigo: chartConfig.code,
        filtros: chartConfig.filtros || {},
        parametros: chartConfig.parametros || {}
      });
      
      setChartsData(prev => ({
        ...prev,
        [chartConfig.code]: result.data
      }));
    } catch (err) {
      setErrors(prev => ({
        ...prev,
        [chartConfig.code]: err instanceof Error ? err.message : 'Error cargando chart'
      }));
    } finally {
      setLoadingCharts(prev => {
        const newSet = new Set(prev);
        newSet.delete(chartConfig.code);
        return newSet;
      });
    }
  };

  const fetchAllCharts = async () => {
    await Promise.all(charts.map(fetchChart));
  };

  useEffect(() => {
    if (autoLoad && charts.length > 0) {
      fetchAllCharts();
    }
  }, [charts.length]);

  return {
    chartsData,
    loadingCharts,
    errors,
    refetchAll: fetchAllCharts,
    refetchChart: fetchChart
  };
}