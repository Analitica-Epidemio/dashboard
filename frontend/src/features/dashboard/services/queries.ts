'use client'

import { useQuery } from '@tanstack/react-query'
import type { Group, Event, ChartData } from '../types'

// Simulated API delays for realistic loading states
const simulateDelay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

// Mock API functions with delays
const fetchGroups = async (): Promise<Group[]> => {
  await simulateDelay(800) // Simulate network delay
  
  const groups: Group[] = [
    { id: '1', name: 'Enfermedades Respiratorias' },
    { id: '2', name: 'Enfermedades Gastrointestinales' },
    { id: '3', name: 'Enfermedades Vectoriales' },
    { id: '4', name: 'Zoonosis' },
  ]
  
  // Simulate occasional failures
  if (Math.random() < 0.1) {
    throw new Error('Error al cargar grupos')
  }
  
  return groups
}

// All events data
const ALL_EVENTS: Event[] = [
  // Enfermedades Respiratorias
  { id: '1-1', name: 'COVID-19', groupId: '1', description: 'Casos de COVID-19' },
  { id: '1-2', name: 'Influenza', groupId: '1', description: 'Casos de Influenza' },
  { id: '1-3', name: 'Neumonía', groupId: '1', description: 'Casos de Neumonía' },
  
  // Enfermedades Gastrointestinales
  { id: '2-1', name: 'Diarrea Aguda', groupId: '2', description: 'Casos de Diarrea Aguda' },
  { id: '2-2', name: 'Hepatitis A', groupId: '2', description: 'Casos de Hepatitis A' },
  { id: '2-3', name: 'Salmonelosis', groupId: '2', description: 'Casos de Salmonelosis' },
  
  // Enfermedades Vectoriales
  { id: '3-1', name: 'Dengue', groupId: '3', description: 'Casos de Dengue' },
  { id: '3-2', name: 'Zika', groupId: '3', description: 'Casos de Zika' },
  { id: '3-3', name: 'Chikungunya', groupId: '3', description: 'Casos de Chikungunya' },
  
  // Zoonosis
  { id: '4-1', name: 'Hantavirus', groupId: '4', description: 'Casos de Hantavirus' },
  { id: '4-2', name: 'Leptospirosis', groupId: '4', description: 'Casos de Leptospirosis' },
  { id: '4-3', name: 'Rabia', groupId: '4', description: 'Casos de Rabia' },
]

const fetchAllEvents = async (): Promise<Event[]> => {
  await simulateDelay(400) // Simulate network delay
  
  // Simulate occasional failures
  if (Math.random() < 0.1) {
    throw new Error('Error al cargar todos los eventos')
  }
  
  return ALL_EVENTS
}

const fetchEventsByGroup = async (groupId: string): Promise<Event[]> => {
  await simulateDelay(600) // Simulate network delay
  
  const events = ALL_EVENTS.filter(event => event.groupId === groupId)
  
  // Simulate occasional failures
  if (Math.random() < 0.1) {
    throw new Error('Error al cargar eventos')
  }
  
  return events
}

const fetchChartData = async (eventId: string): Promise<ChartData[]> => {
  await simulateDelay(1000) // Simulate longer delay for chart data
  
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

  // Get event name for titles
  const allEvents = [
    { id: '1-1', name: 'COVID-19' }, { id: '1-2', name: 'Influenza' }, { id: '1-3', name: 'Neumonía' },
    { id: '2-1', name: 'Diarrea Aguda' }, { id: '2-2', name: 'Hepatitis A' }, { id: '2-3', name: 'Salmonelosis' },
    { id: '3-1', name: 'Dengue' }, { id: '3-2', name: 'Zika' }, { id: '3-3', name: 'Chikungunya' },
    { id: '4-1', name: 'Hantavirus' }, { id: '4-2', name: 'Leptospirosis' }, { id: '4-3', name: 'Rabia' },
  ]
  
  const event = allEvents.find(e => e.id === eventId)
  if (!event) {
    throw new Error('Evento no encontrado')
  }

  const baseValue = Math.floor(Math.random() * 100 + 20)
  
  const charts: ChartData[] = [
    {
      title: `Evolución mensual - ${event.name}`,
      data: generateRandomData(baseValue),
      type: 'line',
      color: '#8884d8'
    },
    {
      title: `Casos por mes - ${event.name}`,
      data: generateRandomData(baseValue * 0.8),
      type: 'bar',
      color: '#82ca9d'
    },
    {
      title: `Área de casos - ${event.name}`,
      data: generateRandomData(baseValue * 1.2),
      type: 'area',
      color: '#ffc658'
    },
    {
      title: `Distribución por región - ${event.name}`,
      data: generatePieData(['Norte', 'Centro', 'Sur', 'Costa']),
      type: 'pie',
      color: '#ff7c7c'
    }
  ]

  // Simulate occasional failures
  if (Math.random() < 0.1) {
    throw new Error('Error al cargar datos de gráficos')
  }
  
  return charts
}

// React Query hooks
export const useGroups = () => {
  return useQuery({
    queryKey: ['groups'],
    queryFn: fetchGroups,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

export const useAllEvents = () => {
  return useQuery({
    queryKey: ['allEvents'],
    queryFn: fetchAllEvents,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

export const useEventsByGroup = (groupId: string | null) => {
  return useQuery({
    queryKey: ['events', groupId],
    queryFn: () => fetchEventsByGroup(groupId!),
    enabled: !!groupId, // Only run query if groupId exists
    staleTime: 3 * 60 * 1000, // 3 minutes
  })
}

export const useChartData = (eventId: string | null) => {
  return useQuery({
    queryKey: ['chartData', eventId],
    queryFn: () => fetchChartData(eventId!),
    enabled: !!eventId, // Only run query if eventId exists
    staleTime: 2 * 60 * 1000, // 2 minutes
  })
}