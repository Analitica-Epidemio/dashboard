'use client'

import { $api } from '@/lib/api/client'

// React Query hooks for dashboard using $api directly
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