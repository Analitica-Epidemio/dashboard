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
 * Get the URL for uploading file for preview (new modern flow)
 */
export function getUploadPreviewUrl(): string {
  return `${env.NEXT_PUBLIC_API_HOST}/api/v1/uploads/preview`;
}

/**
 * Get the URL for processing from preview (new modern flow)
 */
export function getUploadProcessUrl(): string {
  return `${env.NEXT_PUBLIC_API_HOST}/api/v1/uploads/process`;
}

/**
 * Get the base API URL
 */
export function getApiBaseUrl(): string {
  return env.NEXT_PUBLIC_API_HOST;
}