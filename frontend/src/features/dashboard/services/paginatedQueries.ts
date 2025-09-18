'use client'

import { useInfiniteQuery } from '@tanstack/react-query'
import { env } from '@/env'

// Hook for paginated groups with search
export const useInfiniteGroups = (search?: string) => {
  console.log('[useInfiniteGroups] Search term:', search);

  const query = useInfiniteQuery({
    queryKey: ['groups', 'infinite', search || ''],
    queryFn: async ({ pageParam = 1 }) => {
      const queryParams = {
        page: pageParam,
        per_page: 20,
        ...(search && search.trim() && { nombre: search.trim() }),
      };
      console.log('[useInfiniteGroups] Building query with params:', queryParams);

      // Get auth token
      const { getSession } = await import('next-auth/react');
      const session = await getSession();

      const url = new URL('/api/v1/gruposEno/', env.NEXT_PUBLIC_API_HOST);
      Object.entries(queryParams).forEach(([key, value]) => {
        url.searchParams.append(key, String(value));
      });

      const response = await fetch(url.toString(), {
        headers: {
          ...(session?.accessToken && {
            'Authorization': `Bearer ${session.accessToken}`
          })
        }
      });
      const result = await response.json();

      console.log('[useInfiniteGroups] API result:', result);
      return { data: result };
    },
    getNextPageParam: (lastPage, allPages) => {
      // Check if there are more items to load
      const currentPage = allPages.length
      const totalItems = lastPage?.data?.meta?.total || 0
      const itemsLoaded = allPages.reduce((acc, page) => acc + (page?.data?.data?.length || 0), 0)

      console.log('[useInfiniteGroups] Pagination check - Current page:', currentPage, 'Total items:', totalItems, 'Items loaded:', itemsLoaded);

      if (itemsLoaded < totalItems) {
        return currentPage + 1
      }
      return undefined
    },
    initialPageParam: 1,
  })

  // Flatten pages into single array and map data
  const allGroups = query.data?.pages.flatMap(page =>
    page?.data?.data?.map((grupo) => ({
      id: String(grupo.id),
      name: grupo.nombre,
      description: grupo.descripcion,
    })) || []
  ) || []

  console.log('[useInfiniteGroups] Total groups loaded:', allGroups.length);
  console.log('[useInfiniteGroups] Has more pages:', query.hasNextPage);

  const hasMore = query.hasNextPage || false
  const isLoading = query.isLoading || query.isFetchingNextPage

  return {
    ...query,
    groups: allGroups,
    hasMore,
    isLoading,
    loadMore: () => query.fetchNextPage(),
  }
}

// Hook for paginated events with search
export const useInfiniteEvents = (groupId?: string, search?: string) => {
  console.log('[useInfiniteEvents] Group ID:', groupId, 'Search term:', search);

  const query = useInfiniteQuery({
    queryKey: ['events', 'infinite', groupId || '', search || ''],
    queryFn: async ({ pageParam = 1 }) => {
      const queryParams = {
        page: pageParam,
        per_page: 20,
        ...(search && search.trim() && { nombre: search.trim() }),
        ...(groupId && { grupo_id: parseInt(groupId) }),
      };
      console.log('[useInfiniteEvents] Building query with params:', queryParams);

      // Get auth token
      const { getSession } = await import('next-auth/react');
      const session = await getSession();

      const url = new URL('/api/v1/tiposEno/', env.NEXT_PUBLIC_API_HOST);
      Object.entries(queryParams).forEach(([key, value]) => {
        url.searchParams.append(key, String(value));
      });

      const response = await fetch(url.toString(), {
        headers: {
          ...(session?.accessToken && {
            'Authorization': `Bearer ${session.accessToken}`
          })
        }
      });
      const result = await response.json();

      console.log('[useInfiniteEvents] API result:', result);
      return { data: result };
    },
    getNextPageParam: (lastPage, allPages) => {
      // Check if there are more items to load
      const currentPage = allPages.length
      const totalItems = lastPage?.data?.meta?.total || 0
      const itemsLoaded = allPages.reduce((acc, page) => acc + (page?.data?.data?.length || 0), 0)

      console.log('[useInfiniteEvents] Pagination check - Current page:', currentPage, 'Total items:', totalItems, 'Items loaded:', itemsLoaded);

      if (itemsLoaded < totalItems) {
        return currentPage + 1
      }
      return undefined
    },
    initialPageParam: 1,
    enabled: !!groupId, // Only fetch when groupId is provided
  })

  // Flatten pages into single array and map data
  const allEvents = query.data?.pages.flatMap(page =>
    page?.data?.data?.map((tipo) => ({
      id: String(tipo.id),
      name: tipo.nombre,
      groupId: String(tipo.id_grupo_eno),
      description: tipo.descripcion,
      groupName: tipo.grupo_nombre,
    })) || []
  ) || []

  console.log('[useInfiniteEvents] Total events loaded:', allEvents.length);
  console.log('[useInfiniteEvents] Has more pages:', query.hasNextPage);

  const hasMore = query.hasNextPage || false
  const isLoading = query.isLoading || query.isFetchingNextPage

  return {
    ...query,
    events: allEvents,
    hasMore,
    isLoading,
    loadMore: () => query.fetchNextPage(),
  }
}