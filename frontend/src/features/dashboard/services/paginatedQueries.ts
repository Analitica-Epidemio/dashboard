'use client'

import { useInfiniteQuery, type UseInfiniteQueryResult, type InfiniteData } from '@tanstack/react-query'
import { env } from '@/env'
import type { Group, Event } from '../types'

// Tipos para las respuestas de la API
interface ApiGroupResponse {
  id: number;
  nombre: string;
  descripcion?: string | null;
}

interface ApiEventResponse {
  id: number;
  nombre: string;
  id_grupo_eno: number;
  descripcion?: string | null;
  grupo_nombre?: string | null;
}

interface ApiPaginatedResponse<T> {
  data: T[];
  meta: {
    total: number;
    page: number;
    per_page: number;
  };
}

interface ApiPageResult<T> {
  data: ApiPaginatedResponse<T>;
}

// Tipo para errores de query
interface QueryError {
  message: string;
  name?: string;
  cause?: unknown;
}

// Tipos para los hooks
interface UseInfiniteGroupsResult {
  groups: Group[];
  hasMore: boolean;
  isLoading: boolean;
  loadMore: () => void;
  error: QueryError | null;
  isError: boolean;
  isFetchingNextPage: boolean;
  hasNextPage: boolean;
}

interface UseInfiniteEventsResult {
  events: Event[];
  hasMore: boolean;
  isLoading: boolean;
  loadMore: () => void;
  error: QueryError | null;
  isError: boolean;
  isFetchingNextPage: boolean;
  hasNextPage: boolean;
}

// Hook for paginated groups with search
export const useInfiniteGroups = (search?: string): UseInfiniteGroupsResult => {
  console.log('[useInfiniteGroups] Search term:', search);

  const query = useInfiniteQuery<ApiPageResult<ApiGroupResponse>, QueryError, InfiniteData<ApiPageResult<ApiGroupResponse>>, string[], number>({
    queryKey: ['groups', 'infinite', search || ''],
    queryFn: async ({ pageParam = 1 }): Promise<ApiPageResult<ApiGroupResponse>> => {
      const queryParams: Record<string, string | number> = {
        page: pageParam as number,
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
          'Content-Type': 'application/json',
          ...(session?.accessToken && {
            'Authorization': `Bearer ${session.accessToken}`
          })
        }
      });

      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }

      const result: ApiPaginatedResponse<ApiGroupResponse> = await response.json();

      console.log('[useInfiniteGroups] API result:', result);
      return { data: result };
    },
    getNextPageParam: (lastPage: ApiPageResult<ApiGroupResponse>, allPages: ApiPageResult<ApiGroupResponse>[]): number | undefined => {
      // Check if there are more items to load
      const currentPage = allPages.length;
      const totalItems = lastPage?.data?.meta?.total ?? 0;
      const itemsLoaded = allPages.reduce((acc, page) => acc + (page?.data?.data?.length ?? 0), 0);

      console.log('[useInfiniteGroups] Pagination check - Current page:', currentPage, 'Total items:', totalItems, 'Items loaded:', itemsLoaded);

      if (itemsLoaded < totalItems) {
        return currentPage + 1;
      }
      return undefined;
    },
    initialPageParam: 1,
  })

  // Flatten pages into single array and map data
  const allGroups: Group[] = query.data?.pages?.flatMap((page) =>
    page?.data?.data?.map((grupo): Group => ({
      id: String(grupo.id),
      name: grupo.nombre,
      description: grupo.descripcion ?? undefined,
    })) ?? []
  ) ?? [];

  console.log('[useInfiniteGroups] Total groups loaded:', allGroups.length);
  console.log('[useInfiniteGroups] Has more pages:', query.hasNextPage);

  const hasMore: boolean = query.hasNextPage ?? false;
  const isLoading: boolean = query.isLoading || query.isFetchingNextPage;

  return {
    groups: allGroups,
    hasMore,
    isLoading,
    loadMore: () => query.fetchNextPage(),
    error: query.error,
    isError: query.isError,
    isFetchingNextPage: query.isFetchingNextPage,
    hasNextPage: query.hasNextPage ?? false,
  };
}

// Hook for paginated events with search
export const useInfiniteEvents = (groupId?: string, search?: string): UseInfiniteEventsResult => {
  console.log('[useInfiniteEvents] Group ID:', groupId, 'Search term:', search);

  const query = useInfiniteQuery<ApiPageResult<ApiEventResponse>, QueryError, InfiniteData<ApiPageResult<ApiEventResponse>>, string[], number>({
    queryKey: ['events', 'infinite', groupId || '', search || ''],
    queryFn: async ({ pageParam = 1 }): Promise<ApiPageResult<ApiEventResponse>> => {
      const queryParams: Record<string, string | number> = {
        page: pageParam as number,
        per_page: 20,
        ...(search && search.trim() && { nombre: search.trim() }),
        ...(groupId && { grupo_id: parseInt(groupId, 10) }),
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
          'Content-Type': 'application/json',
          ...(session?.accessToken && {
            'Authorization': `Bearer ${session.accessToken}`
          })
        }
      });

      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }

      const result: ApiPaginatedResponse<ApiEventResponse> = await response.json();

      console.log('[useInfiniteEvents] API result:', result);
      return { data: result };
    },
    getNextPageParam: (lastPage: ApiPageResult<ApiEventResponse>, allPages: ApiPageResult<ApiEventResponse>[]): number | undefined => {
      // Check if there are more items to load
      const currentPage = allPages.length;
      const totalItems = lastPage?.data?.meta?.total ?? 0;
      const itemsLoaded = allPages.reduce((acc, page) => acc + (page?.data?.data?.length ?? 0), 0);

      console.log('[useInfiniteEvents] Pagination check - Current page:', currentPage, 'Total items:', totalItems, 'Items loaded:', itemsLoaded);

      if (itemsLoaded < totalItems) {
        return currentPage + 1;
      }
      return undefined;
    },
    initialPageParam: 1,
    enabled: !!groupId, // Only fetch when groupId is provided
  })

  // Flatten pages into single array and map data
  const allEvents: Event[] = query.data?.pages?.flatMap((page) =>
    page?.data?.data?.map((tipo): Event => ({
      id: String(tipo.id),
      name: tipo.nombre,
      groupId: String(tipo.id_grupo_eno),
      description: tipo.descripcion ?? undefined,
      groupName: tipo.grupo_nombre ?? undefined,
    })) ?? []
  ) ?? [];

  console.log('[useInfiniteEvents] Total events loaded:', allEvents.length);
  console.log('[useInfiniteEvents] Has more pages:', query.hasNextPage);

  const hasMore: boolean = query.hasNextPage ?? false;
  const isLoading: boolean = query.isLoading || query.isFetchingNextPage;

  return {
    events: allEvents,
    hasMore,
    isLoading,
    loadMore: () => query.fetchNextPage(),
    error: query.error,
    isError: query.isError,
    isFetchingNextPage: query.isFetchingNextPage,
    hasNextPage: query.hasNextPage ?? false,
  };
}