/**
 * Auth Hook using openapi-react-query
 * Modern implementation with proper library usage
 */

import { useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { $api } from '@/lib/api/client';

/**
 * Main authentication hook
 */
export function useAuth() {
  const queryClient = useQueryClient();
  const router = useRouter();

  // Get current user
  const userQuery = $api.useQuery(
    'get',
    '/api/v1/auth/me',
    undefined,
    {
      enabled: !!localStorage.getItem('auth_access_token'),
      retry: false,
      staleTime: 5 * 60 * 1000,
    }
  );

  // Login mutation
  const loginMutation = $api.useMutation('post', '/api/v1/auth/login', {
    onSuccess: (data) => {
      // Store tokens
      if (data?.data) {
        localStorage.setItem('auth_access_token', data.data.access_token);
        localStorage.setItem('auth_refresh_token', data.data.refresh_token);

        // Invalidate queries and redirect
        queryClient.invalidateQueries();
        router.push('/dashboard');
      }
    },
    onError: () => {
      // Clear any stale data
      localStorage.removeItem('auth_access_token');
      localStorage.removeItem('auth_refresh_token');
    },
  });

  // Logout mutation
  const logoutMutation = $api.useMutation('post', '/api/v1/auth/logout', {
    onSettled: () => {
      // Clear tokens
      localStorage.removeItem('auth_access_token');
      localStorage.removeItem('auth_refresh_token');

      // Clear cache and redirect
      queryClient.clear();
      router.push('/');
    },
  });

  // Helper functions
  const login = (credentials: { email: string; password: string; remember_me?: boolean }) => {
    return loginMutation.mutate({ body: credentials });
  };

  const logout = () => {
    logoutMutation.mutate({ body: {} });
  };

  const user = userQuery.data?.data;
  const isAuthenticated = !!user;
  const isSuperadmin = user?.role === 'superadmin';
  const isEpidemiologist = user?.role === 'epidemiologo';

  return {
    // State
    user,
    isLoading: userQuery.isLoading,
    error: userQuery.error,
    isAuthenticated,
    isSuperadmin,
    isEpidemiologist,

    // Actions
    login,
    logout,
    refetchUser: userQuery.refetch,

    // Mutation states
    isLoggingIn: loginMutation.isPending,
    isLoggingOut: logoutMutation.isPending,
    loginError: loginMutation.error,
  };
}