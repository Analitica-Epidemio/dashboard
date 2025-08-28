/**
 * API hooks para gestión de analytics epidemiológicos
 */

import React from 'react'
import { $api } from './client'
import type { components } from './types'

// Tipos extraídos del schema OpenAPI generado (se generarán automáticamente)
export type GrupoEvento = {
  id: number
  nombre: string
  tipo: "simple" | "grupo"
  descripcion?: string
  activo: boolean
  clasificaciones_disponibles: string[]
  graficos_especiales: string[]
  orden: number
}

export type EventoDentroGrupo = {
  id: number
  tipo_eno_id: number
  nombre: string
  grupo_id: number
  grupo_nombre: string
  clasificaciones?: string[] | null
  estrategia?: string | null
  total_casos: number
  casos_confirmados: number
  casos_sospechosos: number
  ultimo_caso?: string | null
}

export type ConfiguracionVisualizacion = {
  id: string
  nombre: string
  descripcion?: string | null
  tipo: string
  parametros: Record<string, any>
  requiere_parametros: string[]
  disponible_para_grupos: string[]
  disponible_para_todos: boolean
}

export type ListaGruposResponse = {
  grupos: GrupoEvento[]
  total: number
}

export type GrupoEventoResponse = {
  grupo: GrupoEvento
  eventos: EventoDentroGrupo[]
  graficos_disponibles: ConfiguracionVisualizacion[]
}

export type DatosVisualizacionRequest = {
  grupo_id: number
  evento_ids?: number[]
  clasificacion?: string
  fecha_desde?: string
  fecha_hasta?: string
  tipo_grafico: string
  parametros_extra?: Record<string, any>
}

export type DatosVisualizacionResponse = {
  grupo: string
  eventos: string[]
  clasificacion: string
  tipo_grafico: string
  datos: Array<Record<string, any>>
  metadatos: Record<string, any>
  total_casos: number
  fecha_generacion: string
  filtros_aplicados: Record<string, any>
}

// Query keys para react-query
const analyticsKeys = {
  all: ['analytics'] as const,
  grupos: () => [...analyticsKeys.all, 'grupos'] as const,
  grupoDetalle: (id: number) => [...analyticsKeys.all, 'grupo', id] as const,
  visualizacion: (params: DatosVisualizacionRequest) => [...analyticsKeys.all, 'visualizacion', params] as const,
  preview: (grupoId: number, clasificacion: string) => [...analyticsKeys.all, 'preview', grupoId, clasificacion] as const,
}

// Hooks para consultas
export function useGrupos() {
  return $api.useQuery(
    'get',
    '/api/v1/analytics/grupos',
    {},
    {
      queryKey: analyticsKeys.grupos(),
      staleTime: 5 * 60 * 1000, // 5 minutos - los grupos no cambian frecuentemente
    }
  )
}

export function useGrupoDetalle(grupoId: number | null) {
  return $api.useQuery(
    'get',
    '/api/v1/analytics/grupos/{grupo_id}',
    {
      params: {
        path: {
          grupo_id: grupoId!,
        },
      },
    },
    {
      queryKey: analyticsKeys.grupoDetalle(grupoId!),
      enabled: !!grupoId,
      staleTime: 2 * 60 * 1000, // 2 minutos
    }
  )
}

export function useDatosVisualizacion(params: DatosVisualizacionRequest) {
  return $api.useMutation(
    'post',
    '/api/v1/analytics/datos',
    {
      onSuccess: (data) => {
        // Log para debugging
        console.log('Datos de visualización recibidos:', data)
      },
    }
  )
}

// Hook personalizado que envuelve la mutation para comportarse como query
export function useDatosVisualizacionQuery(params: DatosVisualizacionRequest, enabled = true) {
  const mutation = useDatosVisualizacion(params)
  
  React.useEffect(() => {
    if (enabled && params.grupo_id && params.tipo_grafico) {
      mutation.mutate({ body: params } as any)
    }
  }, [enabled, params.grupo_id, params.tipo_grafico, params.clasificacion, params.fecha_desde, params.fecha_hasta, JSON.stringify(params.evento_ids)])

  return {
    data: mutation.data,
    isLoading: mutation.isPending,
    error: mutation.error,
    refetch: () => mutation.mutate({ body: params } as any),
  }
}

export function usePreviewGrupo(grupoId: number | null, clasificacion = "todos") {
  return $api.useQuery(
    'get',
    '/api/v1/analytics/grupos/{grupo_id}/preview',
    {
      params: {
        path: {
          grupo_id: grupoId!,
        },
        query: {
          clasificacion,
        },
      },
    },
    {
      queryKey: analyticsKeys.preview(grupoId!, clasificacion),
      enabled: !!grupoId,
      staleTime: 60 * 1000, // 1 minuto - para preview rápido
    }
  )
}

// Utilidades
export function getTituloGrafico(tipoGrafico: string): string {
  const titulos: Record<string, string> = {
    casos_por_edad: "Casos por Grupo Etario",
    casos_por_ugd: "Casos por Zona UGD (tasa)",
    torta_ugd: "Casos por Zona UGD (torta)",
    torta_sexo: "Distribución por Sexo",
    casos_mensual: "Evolución Mensual",
    historicos: "Datos Históricos",
    tabla: "Tabla de Datos",
    corredor_endemico: "Corredor Endémico",
    curva_epidemiologica: "Curva Epidemiológica",
    grafico_edad_departamento: "Edad y Departamento",
    grafico_rabia_animal_comparacion: "Comparación Rabia Animal",
  }
  return titulos[tipoGrafico] || tipoGrafico
}

export function getDescripcionGrafico(tipoGrafico: string): string {
  const descripciones: Record<string, string> = {
    casos_por_edad: "Distribución de casos por grupos etarios",
    casos_por_ugd: "Tasa de casos por unidad geográfica de distribución",
    torta_ugd: "Proporción de casos por zona UGD",
    torta_sexo: "Distribución por sexo en formato circular",
    casos_mensual: "Evolución temporal mensual de casos",
    historicos: "Comparación con datos históricos",
    tabla: "Vista tabular detallada de los datos",
    corredor_endemico: "Análisis de corredor endémico epidemiológico",
    curva_epidemiologica: "Curva epidemiológica clásica",
    grafico_edad_departamento: "Mapa de calor edad vs departamento",
    grafico_rabia_animal_comparacion: "Comparativa sospechosos vs confirmados",
  }
  return descripciones[tipoGrafico] || "Visualización de datos epidemiológicos"
}

export function getIconoTipoGrafico(tipoGrafico: string): string {
  const iconos: Record<string, string> = {
    casos_por_edad: "📊",
    casos_por_ugd: "📈",
    torta_ugd: "🥧",
    torta_sexo: "🥧",
    casos_mensual: "📈",
    historicos: "📊",
    tabla: "📋",
    corredor_endemico: "📈",
    curva_epidemiologica: "📈",
    grafico_edad_departamento: "🗺️",
    grafico_rabia_animal_comparacion: "📊",
  }
  return iconos[tipoGrafico] || "📊"
}

export function getClasificacionLabel(clasificacion: string): string {
  const labels: Record<string, string> = {
    todos: "Todos los casos",
    confirmados: "Casos Confirmados",
    sospechosos: "Casos Sospechosos", 
    probables: "Casos Probables",
    en_estudio: "En Estudio",
    negativos: "Casos Negativos",
    descartados: "Casos Descartados",
    requiere_revision: "Requiere Revisión",
    con_resultado_mortal: "Con Resultado Mortal",
    sin_resultado_mortal: "Sin Resultado Mortal"
  }
  return labels[clasificacion] || clasificacion
}

export function getClasificacionVariant(clasificacion: string): "default" | "secondary" | "destructive" | "outline" {
  const variants: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
    confirmados: "default",
    sospechosos: "secondary", 
    probables: "secondary",
    en_estudio: "secondary",
    negativos: "outline",
    descartados: "outline",
    requiere_revision: "destructive",
    con_resultado_mortal: "destructive",
    sin_resultado_mortal: "outline"
  }
  return variants[clasificacion] || "outline"
}