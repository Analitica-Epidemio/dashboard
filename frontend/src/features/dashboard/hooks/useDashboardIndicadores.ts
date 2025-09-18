/**
 * Hook para obtener indicadores del dashboard
 */
import { useQuery } from '@tanstack/react-query';
import { env } from '@/env';

interface DashboardIndicadoresParams {
  grupoId?: number | null;
  eventoId?: number | null;
  fechaDesde?: string | null;
  fechaHasta?: string | null;
  clasificaciones?: string[];
}

interface DashboardIndicadoresResponse {
  total_casos: number;
  tasa_incidencia: number;
  areas_afectadas: number;
  letalidad: number;
  filtros_aplicados: any;
}

export function useDashboardIndicadores(params: DashboardIndicadoresParams) {
  return useQuery<DashboardIndicadoresResponse>({
    queryKey: ['dashboard-indicadores', params],
    queryFn: async () => {
      const queryParams = new URLSearchParams();
      
      if (params.grupoId) queryParams.append('grupo_id', params.grupoId.toString());
      if (params.eventoId) queryParams.append('evento_id', params.eventoId.toString());
      if (params.fechaDesde) queryParams.append('fecha_desde', params.fechaDesde);
      if (params.fechaHasta) queryParams.append('fecha_hasta', params.fechaHasta);
      if (params.clasificaciones && params.clasificaciones.length > 0) {
        params.clasificaciones.forEach(c => queryParams.append('clasificaciones', c));
      }
      
      const response = await fetch(`${env.NEXT_PUBLIC_API_HOST}/api/v1/charts/indicadores?${queryParams.toString()}`);
      
      if (!response.ok) {
        throw new Error(`Error fetching indicadores: ${response.statusText}`);
      }
      
      return response.json();
    },
    enabled: !!params.grupoId, // Solo ejecutar si hay grupo seleccionado
  });
}