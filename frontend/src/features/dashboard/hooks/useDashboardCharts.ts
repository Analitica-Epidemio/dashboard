/**
 * Hook para obtener charts dinámicos del dashboard
 */
import { useQuery } from '@tanstack/react-query';
import { env } from '@/env';

export interface DashboardChartsParams {
  grupoId?: number | null;
  eventoId?: number | null;
  fechaDesde?: string | null;
  fechaHasta?: string | null;
  clasificaciones?: string[];
}

export interface ChartConfig {
  height?: number;
  [key: string]: any;
}

export interface ChartDataset {
  label: string;
  data: number[];
  backgroundColor?: string | string[];
  borderColor?: string;
  [key: string]: any;
}

export interface ChartDataStructure {
  type: 'line' | 'bar' | 'pie' | 'doughnut' | 'radar' | string;
  data: {
    labels: string[];
    datasets: ChartDataset[];
  };
}

export interface ChartData {
  codigo: string;
  nombre: string;
  descripcion?: string;
  tipo: string;
  data: ChartDataStructure;
  config: ChartConfig;
}

export interface DashboardChartsData {
  charts: ChartData[];
  total: number;
  filtros_aplicados: any;
}

export interface DashboardChartsApiResponse {
  data: DashboardChartsData;
  meta: any;
}

export function useDashboardCharts(params: DashboardChartsParams) {
  return useQuery<DashboardChartsApiResponse>({
    queryKey: ['dashboard-charts', params],
    queryFn: async () => {
      const queryParams = new URLSearchParams();

      if (params.grupoId) queryParams.append('grupo_id', params.grupoId.toString());
      if (params.eventoId) queryParams.append('evento_id', params.eventoId.toString());
      if (params.fechaDesde) queryParams.append('fecha_desde', params.fechaDesde);
      if (params.fechaHasta) queryParams.append('fecha_hasta', params.fechaHasta);
      if (params.clasificaciones && params.clasificaciones.length > 0) {
        params.clasificaciones.forEach(c => queryParams.append('clasificaciones', c));
      }

      // Obtener el token de la sesión
      const { getSession } = await import('next-auth/react');
      const session = await getSession();

      const url = `${env.NEXT_PUBLIC_API_HOST}/api/v1/charts/dashboard?${queryParams.toString()}`;
      console.log('Fetching dashboard charts from:', url);

      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...(session?.accessToken && {
            'Authorization': `Bearer ${session.accessToken}`
          })
        }
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Error response:', errorText);
        throw new Error(`Error fetching charts: ${response.statusText}`);
      }

      const jsonData = await response.json();
      console.log('Dashboard charts response:', jsonData);
      return jsonData;
    },
    enabled: !!params.grupoId, // Solo ejecutar si hay grupo seleccionado
  });
}