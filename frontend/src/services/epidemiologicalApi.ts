/**
 * Servicio API para datos epidemiológicos
 * Integración con backend FastAPI
 */

import { env } from '@/env';
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
} from '../types/epidemiological';

// Configuración base del API
const API_BASE_URL = env.NEXT_PUBLIC_API_HOST;
const API_VERSION = '/api/v1';

class EpidemiologicalApiService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = `${API_BASE_URL}${API_VERSION}`;
  }

  // Método genérico para peticiones HTTP
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

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
  private buildQueryString(
    filters?: EpidemiologicalFilters,
    additionalParams?: Record<string, any>
  ): string {
    const params = new URLSearchParams();

    if (filters) {
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
  async getEndemicCorridorData(
    config: EndemicCorridorConfig,
    filters?: EpidemiologicalFilters
  ): Promise<EndemicCorridorData> {
    const queryString = this.buildQueryString(filters, {
      calculation: config.calculation,
      cumulative: config.cumulative,
      logarithmic: config.logarithmic,
      moving_window: config.movingWindow,
      last_week: config.lastWeek,
    });

    const response = await this.request<ApiResponse<EndemicCorridorData>>(
      `/charts/endemic-corridor${queryString}`
    );

    return response.data;
  }

  // CURVA EPIDEMIOLÓGICA
  async getEpidemiologicalCurveData(
    filters?: EpidemiologicalFilters
  ): Promise<EpidemiologicalCurveData> {
    const queryString = this.buildQueryString(filters);

    const response = await this.request<ApiResponse<EpidemiologicalCurveData>>(
      `/charts/epidemiological-curve${queryString}`
    );

    return response.data;
  }

  // TOTALES HISTÓRICOS
  async getHistoricalTotalsData(
    filters?: EpidemiologicalFilters
  ): Promise<HistoricalTotalsData> {
    const queryString = this.buildQueryString(filters);

    const response = await this.request<ApiResponse<HistoricalTotalsData>>(
      `/charts/historical-totals${queryString}`
    );

    return response.data;
  }

  // CASOS POR EDAD
  async getAgeCasesData(
    filters?: EpidemiologicalFilters
  ): Promise<AgeCasesData> {
    const queryString = this.buildQueryString(filters);

    const response = await this.request<ApiResponse<AgeCasesData>>(
      `/charts/age-cases${queryString}`
    );

    return response.data;
  }

  // CASOS POR UGD
  async getUGDCasesData(
    filters?: EpidemiologicalFilters
  ): Promise<UGDCasesData> {
    const queryString = this.buildQueryString(filters);

    const response = await this.request<ApiResponse<UGDCasesData>>(
      `/charts/ugd-cases${queryString}`
    );

    return response.data;
  }

  // INTENTO DE SUICIDIO
  async getSuicideAttemptData(
    filters?: EpidemiologicalFilters
  ): Promise<SuicideAttemptData> {
    const queryString = this.buildQueryString(filters);

    const response = await this.request<ApiResponse<SuicideAttemptData>>(
      `/charts/suicide-attempt${queryString}`
    );

    return response.data;
  }

  // RABIA ANIMAL
  async getAnimalRabiesData(
    filters?: EpidemiologicalFilters
  ): Promise<AnimalRabiesData> {
    const queryString = this.buildQueryString(filters);

    const response = await this.request<ApiResponse<AnimalRabiesData>>(
      `/charts/animal-rabies${queryString}`
    );

    return response.data;
  }

  // MÉTODOS AUXILIARES

  // Obtener opciones de filtros disponibles
  async getFilterOptions(): Promise<{
    geographicAreas: { id: string; name: string }[];
    ageGroups: string[];
    eventTypes: string[];
    dateRange: { min: string; max: string };
  }> {
    const response = await this.request<any>('/filters/options');
    return response.data;
  }

  // Obtener metadatos de gráficos
  async getChartMetadata(chartType: string): Promise<{
    title: string;
    description: string;
    lastUpdated: string;
    dataSource: string;
  }> {
    const response = await this.request<any>(`/charts/${chartType}/metadata`);
    return response.data;
  }

  // Exportar datos de gráfico
  async exportChartData(
    chartType: string,
    format: 'csv' | 'excel' | 'json',
    filters?: EpidemiologicalFilters
  ): Promise<Blob> {
    const queryString = this.buildQueryString(filters, { format });

    const response = await fetch(
      `${this.baseUrl}/charts/${chartType}/export${queryString}`,
      {
        method: 'GET',
        headers: {
          'Accept': format === 'json' ? 'application/json' : 'application/octet-stream',
        },
      }
    );

    if (!response.ok) {
      throw new Error(`Error al exportar: ${response.statusText}`);
    }

    return response.blob();
  }

  // Health check del API
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    return this.request('/health');
  }
}

// Instancia singleton del servicio
export const epidemiologicalApi = new EpidemiologicalApiService();

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