import { env } from "@/env";

/**
 * API Configuration
 * Centralizes all API endpoints and configuration
 */
export const API_CONFIG = {
  // Base URL for all API calls
  BASE_URL: env.NEXT_PUBLIC_API_HOST,
  
  // API Endpoints
  ENDPOINTS: {
    // Upload endpoints
    UPLOAD_SHEET: "/api/v1/uploads/sheet",
    
    // Add more endpoints here as needed
    // USERS: "/api/v1/users",
    // ANALYTICS: "/api/v1/analytics",
  },
  
  // Request configuration
  DEFAULT_HEADERS: {
    "Content-Type": "application/json",
  },
  
  // Timeouts
  TIMEOUTS: {
    DEFAULT: 30000, // 30 seconds
    UPLOAD: 300000, // 5 minutes for file uploads
  },
} as const;

/**
 * Helper function to build full API URLs
 */
export function buildApiUrl(endpoint: string): string {
  return `${API_CONFIG.BASE_URL}${endpoint}`;
}

/**
 * Helper function to get upload endpoint URL
 */
export function getUploadSheetUrl(): string {
  return buildApiUrl(API_CONFIG.ENDPOINTS.UPLOAD_SHEET);
}

/**
 * Environment info
 */
export const ENV_INFO = {
  API_HOST: env.NEXT_PUBLIC_API_HOST,
  APP_ENV: env.NEXT_PUBLIC_APP_ENV,
  IS_DEVELOPMENT: env.NEXT_PUBLIC_APP_ENV === "development",
  IS_PRODUCTION: env.NEXT_PUBLIC_APP_ENV === "production",
} as const;