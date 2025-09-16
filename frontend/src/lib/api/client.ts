/**
 * API Client with OpenAPI Types + TanStack Query
 * Modern implementation using openapi-react-query
 */

import createFetchClient from 'openapi-fetch';
import createClient from 'openapi-react-query';
import type { paths } from './types';
import { env } from '@/env';

/**
 * Create fetch client with auth interceptors
 */
const fetchClient = createFetchClient<paths>({
  baseUrl: env.NEXT_PUBLIC_API_HOST,
});

// Add request interceptor for auth token
fetchClient.use({
  async onRequest({ request }) {
    const token = localStorage.getItem('auth_access_token');

    if (token) {
      request.headers.set('Authorization', `Bearer ${token}`);
    }

    return request;
  },

  async onResponse({ response, request }) {
    // Handle 401 - token expired
    if (response.status === 401) {
      // Try to refresh token
      const refreshToken = localStorage.getItem('auth_refresh_token');

      if (refreshToken) {
        try {
          const refreshResponse = await fetch(`${env.NEXT_PUBLIC_API_HOST}/api/v1/auth/refresh`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refreshToken }),
          });

          if (refreshResponse.ok) {
            const tokens = await refreshResponse.json();
            localStorage.setItem('auth_access_token', tokens.access_token);
            localStorage.setItem('auth_refresh_token', tokens.refresh_token);

            // Retry original request with new token
            const newRequest = request.clone();
            newRequest.headers.set('Authorization', `Bearer ${tokens.access_token}`);
            return fetch(newRequest);
          }
        } catch {
          // Refresh failed
        }
      }

      // Clear tokens and redirect to login
      localStorage.removeItem('auth_access_token');
      localStorage.removeItem('auth_refresh_token');

      // Only redirect if we're in the browser and not already on login page
      if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
        window.location.href = '/';
      }
    }

    return response;
  },
});

/**
 * Create the TanStack Query client
 */
export const $api = createClient(fetchClient);

/**
 * Export the raw fetch client for custom requests
 */
export const apiClient = fetchClient;