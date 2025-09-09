/**
 * Servicio API para datos epidemiológicos
 * Integración con backend FastAPI
 */

import {
  ApiResponse,
  EpidemiologicalFilters,
  EndemicCorridorData,
  EndemicCorridorConfig,
  EpidemiologicalCurveData,
  HistoricalTotalsData,
  AgeCasesData,
  UGDCasesData,
  SuicideAttemptData,
  AnimalRabiesData,
  KPIData,
} from '../types';

// Configuración base del API
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
const API_VERSION = '/api/v1';

// Configuración base
const baseUrl = `${API_BASE_URL}${API_VERSION}`;

// Función genérica para peticiones HTTP
async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${baseUrl}${endpoint}`;
  
  const config: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  try {
    const response = await fetch(url, config);

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(
        `HTTP ${response.status}: ${errorText || response.statusText}`
      );
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error(`Error en petición a ${url}:`, error);
    throw error;
  }
}

// Construir query string para filtros
function buildQueryString(
  filters?: EpidemiologicalFilters,
  additionalParams?: Record<string, any>
): string {
    const params = new URLSearchParams();

    if (filters) {
      // Filtros base existentes
      if (filters.selectedGroupId) {
        params.append('group_id', filters.selectedGroupId);
      }
      
      if (filters.selectedEventId) {
        params.append('event_id', filters.selectedEventId);
      }

      // Filtros epidemiológicos extendidos
      if (filters.dateRange) {
        params.append('start_date', filters.dateRange.startDate);
        params.append('end_date', filters.dateRange.endDate);
      }
      
      if (filters.geographicAreas?.length) {
        filters.geographicAreas.forEach(area => 
          params.append('geographic_areas', area)
        );
      }

      if (filters.ageGroups?.length) {
        filters.ageGroups.forEach(group => 
          params.append('age_groups', group)
        );
      }

      if (filters.eventTypes?.length) {
        filters.eventTypes.forEach(type => 
          params.append('event_types', type)
        );
      }

      if (filters.includeDeaths !== undefined) {
        params.append('include_deaths', filters.includeDeaths.toString());
      }
    }

    if (additionalParams) {
      Object.entries(additionalParams).forEach(([key, value]) => {
        if (Array.isArray(value)) {
          value.forEach(v => params.append(key, v.toString()));
        } else if (value !== undefined && value !== null) {
          params.append(key, value.toString());
        }
      });
    }

    const queryString = params.toString();
    return queryString ? `?${queryString}` : '';
  }

// CORREDOR ENDÉMICO
export async function getEndemicCorridorData(
  config: EndemicCorridorConfig,
  filters?: EpidemiologicalFilters
): Promise<EndemicCorridorData> {
  const queryString = buildQueryString(filters, {
    calculation: config.calculation,
    cumulative: config.cumulative,
    logarithmic: config.logarithmic,
    moving_window: config.movingWindow,
    last_week: config.lastWeek,
  });

  const response = await request<ApiResponse<EndemicCorridorData>>(
    `/charts/endemic-corridor${queryString}`
  );

  return response.data;
}

// CURVA EPIDEMIOLÓGICA
export async function getEpidemiologicalCurveData(
  filters?: EpidemiologicalFilters
): Promise<EpidemiologicalCurveData> {
  const queryString = buildQueryString(filters);

  const response = await request<ApiResponse<EpidemiologicalCurveData>>(
    `/charts/epidemiological-curve${queryString}`
  );

  return response.data;
}

// TOTALES HISTÓRICOS
export async function getHistoricalTotalsData(
  filters?: EpidemiologicalFilters
): Promise<HistoricalTotalsData> {
  const queryString = buildQueryString(filters);

  const response = await request<ApiResponse<HistoricalTotalsData>>(
    `/charts/historical-totals${queryString}`
  );

  return response.data;
}



// Mock data temporal hasta que el backend esté disponible
function createMockDelay() {
  return new Promise(resolve => setTimeout(resolve, 500 + Math.random() * 1000));
}

// Exportar todas las funciones principales con mock data
export const epidemiologicalApi = {
  getEndemicCorridorData: async (config: EndemicCorridorConfig, filters?: EpidemiologicalFilters): Promise<EndemicCorridorData> => {
    await createMockDelay();
    
    // Generar datos mock del corredor endémico
    const zones = Array.from({ length: 52 }, (_, i) => ({
      week: i + 1,
      successZone: Math.max(0, 50 + Math.sin(i * 0.3) * 30 + Math.random() * 10),
      securityZone: Math.max(0, 80 + Math.sin(i * 0.3) * 40 + Math.random() * 15),
      alertZone: Math.max(0, 120 + Math.sin(i * 0.3) * 50 + Math.random() * 20),
    }));

    const currentYear = Array.from({ length: 52 }, (_, i) => ({
      week: i + 1,
      cases: Math.max(0, 75 + Math.sin(i * 0.4) * 45 + Math.random() * 25),
    }));

    return {
      zones,
      currentYear,
      statistics: {
        historicalYears: 5,
        tValue: 2.45,
        currentYear: 2024,
      },
    };
  },

  getEpidemiologicalCurveData: async (filters?: EpidemiologicalFilters): Promise<EpidemiologicalCurveData> => {
    await createMockDelay();
    
    // Agentes virales disponibles
    const viralAgents = [
      { id: 'influenza', name: 'Influenza', color: '#3b82f6' },
      { id: 'rsv', name: 'VSR', color: '#ef4444' },
      { id: 'adenovirus', name: 'Adenovirus', color: '#10b981' },
      { id: 'parainfluenza', name: 'Parainfluenza', color: '#f59e0b' },
      { id: 'rhinovirus', name: 'Rhinovirus', color: '#8b5cf6' },
      { id: 'otros', name: 'Otros', color: '#6b7280' },
    ];

    // Generar datos mock de curva epidemiológica
    const points = Array.from({ length: 52 }, (_, i) => ({
      week: i + 1,
      year: 2024,
      cases: {
        influenza: Math.floor(Math.random() * 50 + 10),
        rsv: Math.floor(Math.random() * 30 + 5),
        adenovirus: Math.floor(Math.random() * 25 + 3),
        parainfluenza: Math.floor(Math.random() * 20 + 2),
        rhinovirus: Math.floor(Math.random() * 35 + 8),
        otros: Math.floor(Math.random() * 15 + 1),
      },
      deaths: Math.floor(Math.random() * 5),
      mortalityRate: Math.random() * 10 + 2,
      cumulativeMortality: Math.floor(Math.random() * 100 + 50),
    }));

    return {
      points,
      viralAgents,
      statistics: {
        totalCases: 3554,
        totalDeaths: 156,
        overallMortalityRate: 4.39,
      },
    };
  },

  getHistoricalTotalsData: async (filters?: EpidemiologicalFilters): Promise<HistoricalTotalsData> => {
    await createMockDelay();
    
    const areas = [
      { id: 'area1', name: 'Área Programática Norte', code: 'APN' },
      { id: 'area2', name: 'Área Programática Sur', code: 'APS' },
      { id: 'area3', name: 'Área Programática Centro', code: 'APC' },
      { id: 'area4', name: 'Área Programática Rural', code: 'APR' },
    ];

    const points = [
      { 
        year: 2020, 
        total: 2456, 
        areas: { area1: 456, area2: 334, area3: 298, area4: 234 },
        mortalityRate: 4.2 
      },
      { 
        year: 2021, 
        total: 2789, 
        areas: { area1: 523, area2: 389, area3: 334, area4: 267 },
        mortalityRate: 4.5 
      },
      { 
        year: 2022, 
        total: 3123, 
        areas: { area1: 598, area2: 445, area3: 378, area4: 312 },
        mortalityRate: 3.8 
      },
      { 
        year: 2023, 
        total: 3456, 
        areas: { area1: 634, area2: 489, area3: 423, area4: 367 },
        mortalityRate: 4.1 
      },
      { 
        year: 2024, 
        total: 3234, 
        areas: { area1: 612, area2: 467, area3: 398, area4: 334 },
        mortalityRate: 3.9 
      },
    ];

    return {
      points,
      areas,
      statistics: {
        yearsRange: [2020, 2024] as [number, number],
        totalCases: points.reduce((sum, d) => sum + d.total, 0),
        averageMortalityRate: points.reduce((sum, d) => sum + (d.mortalityRate || 0), 0) / points.length,
      },
    };
  },
  getAgeCasesData: async (filters?: EpidemiologicalFilters): Promise<AgeCasesData> => {
    await createMockDelay();
    
    const points = [
      { ageGroup: '0-4', male: 234, female: 198, total: 432 },
      { ageGroup: '5-14', male: 456, female: 423, total: 879 },
      { ageGroup: '15-24', male: 789, female: 667, total: 1456 },
      { ageGroup: '25-44', male: 1234, female: 1098, total: 2332 },
      { ageGroup: '45-64', male: 987, female: 876, total: 1863 },
      { ageGroup: '65+', male: 654, female: 789, total: 1443 },
    ];

    return {
      points,
      statistics: {
        totalCases: points.reduce((sum, d) => sum + d.total, 0),
        mostAffectedAgeGroup: '25-44',
        genderDistribution: {
          male: points.reduce((sum, d) => sum + d.male, 0),
          female: points.reduce((sum, d) => sum + d.female, 0),
        },
      },
    };
  },
  getUGDCasesData: async (filters?: EpidemiologicalFilters): Promise<UGDCasesData> => {
    await createMockDelay();
    
    const points = [
      { ugdId: 'ugd1', ugdName: 'Hospital Regional Comodoro Rivadavia', cases: 456, percentage: 22.3, mortalityRate: 4.5 },
      { ugdId: 'ugd2', ugdName: 'Hospital Zonal Trelew', cases: 334, percentage: 16.4, mortalityRate: 3.2 },
      { ugdId: 'ugd3', ugdName: 'Hospital Puerto Madryn', cases: 298, percentage: 14.6, mortalityRate: 5.1 },
      { ugdId: 'ugd4', ugdName: 'Hospital Rural Esquel', cases: 234, percentage: 11.5, mortalityRate: 2.8 },
      { ugdId: 'ugd5', ugdName: 'Hospital Rawson', cases: 187, percentage: 9.2, mortalityRate: 3.9 },
    ];

    return {
      points,
      statistics: {
        totalCases: points.reduce((sum, d) => sum + d.cases, 0),
        mostAffectedUGD: 'Hospital Regional Comodoro Rivadavia',
      },
    };
  },
  getSuicideAttemptData: async (filters?: EpidemiologicalFilters): Promise<SuicideAttemptData> => {
    await createMockDelay();
    
    const points = Array.from({ length: 52 }, (_, i) => ({
      week: i + 1,
      year: 2024,
      attempts: Math.floor(Math.random() * 15 + 2),
      deaths: Math.floor(Math.random() * 3),
      mortalityRate: Math.random() * 20 + 5,
    }));

    return {
      points,
      demographics: {
        ageGroups: {
          '15-24': 89,
          '25-34': 67,
          '35-44': 45,
          '45-54': 34,
          '55+': 23,
        },
        genderDistribution: {
          'Femenino': 156,
          'Masculino': 102,
        },
        methodsUsed: {
          'Intoxicación': 89,
          'Lesión autoinfligida': 67,
          'Otros': 45,
        },
      },
    };
  },
  getAnimalRabiesData: async (filters?: EpidemiologicalFilters): Promise<AnimalRabiesData> => {
    await createMockDelay();
    
    const points = Array.from({ length: 30 }, (_, i) => ({
      date: new Date(2024, 0, i * 12).toISOString(),
      species: ['Perro', 'Gato', 'Murciélago', 'Bovino'][Math.floor(Math.random() * 4)],
      location: ['Área Norte', 'Área Sur', 'Área Centro', 'Área Rural'][Math.floor(Math.random() * 4)],
      cases: Math.floor(Math.random() * 8 + 1),
      tested: Math.floor(Math.random() * 12 + 3),
      positive: Math.floor(Math.random() * 4),
    }));

    return {
      points,
      statistics: {
        speciesDistribution: {
          'Perros': 45,
          'Gatos': 23,
          'Murciélagos': 12,
          'Bovinos': 8,
          'Otros': 5,
        },
        locationDistribution: {
          'Área Norte': 34,
          'Área Sur': 28,
          'Área Centro': 21,
          'Área Rural': 10,
        },
        positivityRate: 21.8,
      },
    };
  },
  
  getKPIData: async (filters?: EpidemiologicalFilters): Promise<KPIData> => {
    await createMockDelay();
    
    // Calculate current week number
    const currentDate = new Date();
    const startDate = new Date(currentDate.getFullYear(), 0, 1);
    const days = Math.floor((currentDate.getTime() - startDate.getTime()) / (24 * 60 * 60 * 1000));
    const weekNumber = Math.ceil(days / 7);
    
    // Generate realistic KPI data based on filters
    const baseMultiplier = filters?.selectedEventId ? 0.7 : 1.0; // Less cases if filtered by event
    const areaMultiplier = filters?.selectedGroupId ? 0.8 : 1.0; // Less cases if filtered by group
    
    const totalCases = Math.floor(2847 * baseMultiplier * areaMultiplier);
    const newCases7Days = Math.floor(184 * baseMultiplier * areaMultiplier);
    const incidenceRate = parseFloat((45.2 * baseMultiplier).toFixed(1));
    const mortalityRate = parseFloat((2.3 + Math.random() * 0.5).toFixed(1));
    const affectedAreas = Math.floor(12 * areaMultiplier);
    const averageResponseTime = parseFloat((1.8 + Math.random() * 0.5).toFixed(1));
    
    // Calculate previous period values (simulate ~10% variation)
    const previousTotalCases = Math.floor(totalCases * (0.9 + Math.random() * 0.2));
    const previousNewCases = Math.floor(newCases7Days * (0.9 + Math.random() * 0.2));
    const previousIncidenceRate = parseFloat((incidenceRate * (0.9 + Math.random() * 0.2)).toFixed(1));
    const previousMortalityRate = parseFloat((mortalityRate * (0.9 + Math.random() * 0.2)).toFixed(1));
    const previousAffectedAreas = Math.floor(affectedAreas * (0.9 + Math.random() * 0.2));
    const previousResponseTime = parseFloat((averageResponseTime * (1.1 + Math.random() * 0.2)).toFixed(1));
    
    // Calculate trends
    const calculateTrend = (current: number, previous: number): 'up' | 'down' | 'stable' => {
      const change = ((current - previous) / previous) * 100;
      if (Math.abs(change) < 2) return 'stable';
      return change > 0 ? 'up' : 'down';
    };
    
    return {
      totalCases,
      newCases7Days,
      incidenceRate,
      mortalityRate,
      affectedAreas,
      totalAreas: 24, // Total areas in Chubut
      averageResponseTime,
      previousPeriod: {
        totalCases: previousTotalCases,
        newCases7Days: previousNewCases,
        incidenceRate: previousIncidenceRate,
        mortalityRate: previousMortalityRate,
        affectedAreas: previousAffectedAreas,
        averageResponseTime: previousResponseTime,
      },
      trends: {
        totalCases: calculateTrend(totalCases, previousTotalCases),
        newCases7Days: calculateTrend(newCases7Days, previousNewCases),
        incidenceRate: calculateTrend(incidenceRate, previousIncidenceRate),
        mortalityRate: calculateTrend(mortalityRate, previousMortalityRate),
        affectedAreas: calculateTrend(affectedAreas, previousAffectedAreas),
        averageResponseTime: calculateTrend(averageResponseTime, previousResponseTime),
      },
      lastUpdated: new Date().toISOString(),
      weekNumber,
    };
  },
};

// Helper para manejo de errores específicos
export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public code?: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// Interceptor para manejo de errores común
export function handleApiError(error: unknown): string {
  if (error instanceof ApiError) {
    switch (error.status) {
      case 404:
        return 'Datos no encontrados. Verifique los filtros seleccionados.';
      case 422:
        return 'Parámetros inválidos. Revise los filtros aplicados.';
      case 500:
        return 'Error interno del servidor. Intente nuevamente más tarde.';
      case 503:
        return 'Servicio temporalmente no disponible.';
      default:
        return error.message;
    }
  }

  if (error instanceof Error) {
    return error.message;
  }

  return 'Error desconocido. Intente nuevamente.';
}