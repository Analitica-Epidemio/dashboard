/**
 * API Configuration and URL builders
 */

import { env } from '@/env';

const API_BASE = env.NEXT_PUBLIC_API_HOST;

/**
 * Upload endpoints
 */
export function getUploadCsvAsyncUrl(): string {
  return `${API_BASE}/api/v1/uploads/csv/async`;
}

export function getUploadPreviewUrl(): string {
  return `${API_BASE}/api/v1/uploads/preview`;
}

export function getUploadProcessUrl(): string {
  return `${API_BASE}/api/v1/uploads/process`;
}

/**
 * Job management endpoints
 */
export function getJobStatusUrl(jobId: string): string {
  return `${API_BASE}/api/v1/jobs/${jobId}/status`;
}

export function getCancelJobUrl(jobId: string): string {
  return `${API_BASE}/api/v1/jobs/${jobId}/cancel`;
}
