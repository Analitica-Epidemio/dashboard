/**
 * API Client with OpenAPI Types + TanStack Query
 * Modern implementation using openapi-react-query with NextAuth
 */

import createFetchClient from 'openapi-fetch';
import createClient from 'openapi-react-query';
import type { paths } from './types';
import { getSession } from 'next-auth/react';
import { env } from '@/env';

/**
 * Create fetch client pointing to FastAPI backend
 */
const fetchClient = createFetchClient<paths>({
  baseUrl: env.NEXT_PUBLIC_API_HOST,
});

// Add request interceptor for auth token
fetchClient.use({
  async onRequest({ request }) {
    // Get the session - this will include the access token
    const session = await getSession();

    if (session?.accessToken) {
      request.headers.set('Authorization', `Bearer ${session.accessToken}`);
    }

    // Log for debugging (only in development)
    if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
      console.log('API Request:', request.url);
      console.log('Has session:', !!session);
      console.log('Has token:', !!session?.accessToken);
    }

    return request;
  },

  async onResponse({ response }) {
    // Log for debugging (only in development)
    if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
      console.log('API Response:', response.url, 'Status:', response.status);
    }

    // Handle 401 - redirect to login
    if (response.status === 401) {
      if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
        // Redirect to login page (NextAuth will handle session cleanup)
        window.location.href = '/login';
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