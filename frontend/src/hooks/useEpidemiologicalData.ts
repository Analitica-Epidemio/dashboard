/**
 * Hooks personalizados para manejo de datos epidemiológicos
 * Separación de lógica de negocio y manejo de estado
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import {
  ChartState,
  EpidemiologicalFilters,
  EndemicCorridorData,
  EndemicCorridorConfig,
  EpidemiologicalCurveData,
  HistoricalTotalsData,
  AgeCasesData,
  UGDCasesData,
  SuicideAttemptData,
  AnimalRabiesData,
} from '../types/epidemiological';
import { epidemiologicalApi } from '../services/epidemiologicalApi';

// Hook genérico para manejo de estado de charts
export function useChartData<T>(
  fetchFunction: (filters?: EpidemiologicalFilters) => Promise<T>,
  filters?: EpidemiologicalFilters,
  autoRefresh = false,
  refreshInterval = 300000 // 5 minutos
): ChartState<T> & { refetch: () => Promise<void> } {
  const [state, setState] = useState<ChartState<T>>({
    data: null,
    loading: false,
    error: null,
    lastUpdated: null,
  });

  const fetchData = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const data = await fetchFunction(filters);
      setState({
        data,
        loading: false,
        error: null,
        lastUpdated: new Date(),
      });
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Error desconocido',
      }));
    }
  }, [fetchFunction, filters]);

  // Efecto inicial y cuando cambian los filtros
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(fetchData, refreshInterval);
    return () => clearInterval(interval);
  }, [fetchData, autoRefresh, refreshInterval]);

  return {
    ...state,
    refetch: fetchData,
  };
}

// Hook específico para Corredor Endémico
export function useEndemicCorridor(
  config: EndemicCorridorConfig,
  filters?: EpidemiologicalFilters
) {
  const chartState = useChartData(
    useCallback(
      (f) => epidemiologicalApi.getEndemicCorridorData(config, f),
      [config]
    ),
    filters
  );

  // Procesamiento específico para Recharts
  const processedData = useMemo(() => {
    if (!chartState.data) return null;

    const { zones, currentYear, statistics } = chartState.data;

    // Combinar datos de zonas y año actual
    const chartData = zones.map(zone => {
      const currentYearPoint = currentYear.find(cy => cy.week === zone.week);
      
      return {
        week: zone.week,
        success: zone.successZone,
        security: zone.securityZone,
        alert: zone.alertZone,
        currentCases: currentYearPoint?.cases || null,
      };
    });

    return {
      chartData,
      metadata: statistics,
    };
  }, [chartState.data]);

  return {
    ...chartState,
    processedData,
  };
}

// Hook específico para Curva Epidemiológica
export function useEpidemiologicalCurve(filters?: EpidemiologicalFilters) {
  const chartState = useChartData(
    epidemiologicalApi.getEpidemiologicalCurveData,
    filters
  );

  const processedData = useMemo(() => {
    if (!chartState.data) return null;

    const { points, viralAgents, statistics } = chartState.data;

    // Transformar para Recharts - barras apiladas
    const chartData = points.map(point => ({
      week: point.week,
      year: point.year,
      ...point.cases, // spread viral agents cases
      deaths: point.deaths,
      mortalityRate: point.mortalityRate,
      cumulativeMortality: point.cumulativeMortality,
    }));

    return {
      chartData,
      viralAgents,
      statistics,
    };
  }, [chartState.data]);

  return {
    ...chartState,
    processedData,
  };
}

// Hook específico para Totales Históricos
export function useHistoricalTotals(filters?: EpidemiologicalFilters) {
  const chartState = useChartData(
    epidemiologicalApi.getHistoricalTotalsData,
    filters
  );

  const processedData = useMemo(() => {
    if (!chartState.data) return null;

    const { points, areas, statistics } = chartState.data;

    // Transformar para múltiples series
    const chartData = points.map(point => ({
      year: point.year,
      ...point.areas, // spread area cases
      total: point.total,
      mortalityRate: point.mortalityRate,
    }));

    return {
      chartData,
      areas,
      statistics,
    };
  }, [chartState.data]);

  return {
    ...chartState,
    processedData,
  };
}

// Hook específico para Casos por Edad
export function useAgeCases(filters?: EpidemiologicalFilters) {
  const chartState = useChartData(
    epidemiologicalApi.getAgeCasesData,
    filters
  );

  const processedData = useMemo(() => {
    if (!chartState.data) return null;

    const { points, statistics } = chartState.data;

    // Para pirámide poblacional - valores negativos para un lado
    const chartData = points.map(point => ({
      ageGroup: point.ageGroup,
      male: -point.male, // Negativo para mostrar a la izquierda
      female: point.female,
      total: point.total,
    }));

    return {
      chartData,
      statistics,
    };
  }, [chartState.data]);

  return {
    ...chartState,
    processedData,
  };
}

// Hook específico para Casos por UGD
export function useUGDCases(filters?: EpidemiologicalFilters) {
  const chartState = useChartData(
    epidemiologicalApi.getUGDCasesData,
    filters
  );

  const processedData = useMemo(() => {
    if (!chartState.data) return null;

    const { points, statistics } = chartState.data;

    // Para gráfico de torta
    const chartData = points.map(point => ({
      name: point.ugdName,
      value: point.cases,
      percentage: point.percentage,
      mortalityRate: point.mortalityRate,
    }));

    return {
      chartData,
      statistics,
    };
  }, [chartState.data]);

  return {
    ...chartState,
    processedData,
  };
}

// Hook específico para Intento de Suicidio
export function useSuicideAttemptData(filters?: EpidemiologicalFilters) {
  const chartState = useChartData(
    epidemiologicalApi.getSuicideAttemptData,
    filters
  );

  const processedData = useMemo(() => {
    if (!chartState.data) return null;

    const { points, demographics } = chartState.data;

    // Datos temporales
    const timeSeriesData = points.map(point => ({
      week: point.week,
      year: point.year,
      attempts: point.attempts,
      deaths: point.deaths,
      mortalityRate: point.mortalityRate,
    }));

    // Datos demográficos para charts secundarios
    const ageGroupsData = Object.entries(demographics.ageGroups).map(
      ([group, count]) => ({
        name: group,
        value: count,
      })
    );

    const genderData = Object.entries(demographics.genderDistribution).map(
      ([gender, count]) => ({
        name: gender,
        value: count,
      })
    );

    return {
      timeSeriesData,
      ageGroupsData,
      genderData,
      demographics,
    };
  }, [chartState.data]);

  return {
    ...chartState,
    processedData,
  };
}

// Hook específico para Rabia Animal
export function useAnimalRabiesData(filters?: EpidemiologicalFilters) {
  const chartState = useChartData(
    epidemiologicalApi.getAnimalRabiesData,
    filters
  );

  const processedData = useMemo(() => {
    if (!chartState.data) return null;

    const { points, statistics } = chartState.data;

    // Datos temporales
    const timeSeriesData = points.map(point => ({
      date: point.date,
      species: point.species,
      location: point.location,
      cases: point.cases,
      tested: point.tested,
      positive: point.positive,
      positivityRate: point.tested > 0 ? (point.positive / point.tested) * 100 : 0,
    }));

    // Datos por especies
    const speciesData = Object.entries(statistics.speciesDistribution).map(
      ([species, count]) => ({
        name: species,
        value: count,
      })
    );

    // Datos por ubicación
    const locationData = Object.entries(statistics.locationDistribution).map(
      ([location, count]) => ({
        name: location,
        value: count,
      })
    );

    return {
      timeSeriesData,
      speciesData,
      locationData,
      statistics,
    };
  }, [chartState.data]);

  return {
    ...chartState,
    processedData,
  };
}

// Hook para manejo de filtros
export function useEpidemiologicalFilters(initialFilters?: EpidemiologicalFilters) {
  const [filters, setFilters] = useState<EpidemiologicalFilters>(
    initialFilters || {}
  );

  const updateFilters = useCallback((updates: Partial<EpidemiologicalFilters>) => {
    setFilters(prev => ({ ...prev, ...updates }));
  }, []);

  const resetFilters = useCallback(() => {
    setFilters(initialFilters || {});
  }, [initialFilters]);

  return {
    filters,
    updateFilters,
    resetFilters,
  };
}