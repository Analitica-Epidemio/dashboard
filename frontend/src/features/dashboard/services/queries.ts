'use client'

import { useQuery } from '@tanstack/react-query'
import type { ChartData } from '../types'
import { $api } from '@/lib/api/client'

// Fetch chart data - mock data for now
const fetchChartData = async (eventId: string): Promise<ChartData[]> => {
  // TODO: Connect to actual chart endpoints when available
  // For now, return mock data to keep the UI functional

  const generateRandomData = (baseValue: number, points: number = 12) => {
    const months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    return months.slice(0, points).map((month) => ({
      date: month,
      value: Math.floor(baseValue + (Math.random() - 0.5) * baseValue * 0.5)
    }))
  }

  const generatePieData = (categories: string[]) => {
    return categories.map(category => ({
      date: category,
      value: Math.floor(Math.random() * 100 + 10),
      category
    }))
  }

  const baseValue = Math.floor(Math.random() * 100 + 20)

  const charts: ChartData[] = [
    {
      title: `Evolución mensual - Evento ${eventId}`,
      data: generateRandomData(baseValue),
      type: 'line',
      color: '#8884d8'
    },
    {
      title: `Casos por mes - Evento ${eventId}`,
      data: generateRandomData(baseValue * 0.8),
      type: 'bar',
      color: '#82ca9d'
    },
    {
      title: `Área de casos - Evento ${eventId}`,
      data: generateRandomData(baseValue * 1.2),
      type: 'area',
      color: '#ffc658'
    },
    {
      title: `Distribución por región - Evento ${eventId}`,
      data: generatePieData(['Norte', 'Centro', 'Sur', 'Costa']),
      type: 'pie',
      color: '#ff7c7c'
    }
  ]

  return charts
}

// React Query hooks using $api directly
export const useGroups = () => {
  const query = $api.useQuery('get', '/api/v1/gruposEno/', {
    params: {
      query: {
        per_page: 100
      }
    }
  })

  const mappedData = query.data?.data?.map((grupo) => ({
    id: String(grupo.id),
    name: grupo.nombre,
    description: grupo.descripcion
  }));

  return {
    ...query,
    data: mappedData
  }
}

export const useAllEvents = () => {
  const query = $api.useQuery('get', '/api/v1/tiposEno/', {
    params: {
      query: {
        per_page: 100
      }
    }
  })

  const mappedData = query.data?.data?.map((tipo) => ({
    id: String(tipo.id),
    name: tipo.nombre,
    groupId: String(tipo.id_grupo_eno),
    description: tipo.descripcion,
    groupName: tipo.grupo_nombre
  }));

  return {
    ...query,
    data: mappedData
  }
}

export const useEventsByGroup = (groupId: string | null) => {
  const query = $api.useQuery('get', '/api/v1/tiposEno/', {
    params: {
      query: {
        per_page: 100,
        id_grupo_eno: groupId ? Number(groupId) : undefined
      }
    },
    enabled: !!groupId
  })

  const mappedData = query.data?.data?.map((tipo) => ({
    id: String(tipo.id),
    name: tipo.nombre,
    groupId: String(tipo.id_grupo_eno),
    description: tipo.descripcion,
    groupName: tipo.grupo_nombre
  }));

  return {
    ...query,
    data: mappedData
  }
}

export const useChartData = (eventId: string | null) => {
  return useQuery({
    queryKey: ['chartData', eventId],
    queryFn: () => fetchChartData(eventId!),
    enabled: !!eventId, // Only run query if eventId exists
    staleTime: 2 * 60 * 1000, // 2 minutes
  })
}