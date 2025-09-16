import { env } from '@/env';

/**
 * API configuration helpers
 */

/**
 * Get the URL for uploading CSV files asynchronously
 */
export function getUploadCsvAsyncUrl(): string {
  return `${env.NEXT_PUBLIC_API_HOST}/api/v1/uploads/csv-async`;
}

/**
 * Get the URL for checking job status
 */
export function getJobStatusUrl(jobId: string): string {
  return `${env.NEXT_PUBLIC_API_HOST}/api/v1/uploads/jobs/${jobId}/status`;
}

/**
 * Get the URL for canceling a job
 */
export function getCancelJobUrl(jobId: string): string {
  return `${env.NEXT_PUBLIC_API_HOST}/api/v1/uploads/jobs/${jobId}`;
}

/**
 * Get the base API URL
 */
export function getApiBaseUrl(): string {
  return env.NEXT_PUBLIC_API_HOST;
}