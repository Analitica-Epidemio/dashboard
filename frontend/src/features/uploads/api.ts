/**
 * Uploads API Layer
 *
 * Semantic hooks for CSV file upload and job management endpoints.
 * Uses $api client internally - all types from OpenAPI schema.
 *
 * @module features/uploads/api
 */

import { useQueryClient } from '@tanstack/react-query';
import { useCallback, useRef } from 'react';
import { $api } from '@/lib/api/client';

// ============================================================================
// QUERY HOOKS - Job status
// ============================================================================

/**
 * Poll upload job status
 *
 * Automatically polls the status of an upload job until completion.
 * Includes smart refetch interval that stops when job is finished.
 *
 * @param jobId - Job ID to poll
 * @param options - Polling configuration (enabled, pollingInterval)
 * @returns Query with job status data
 *
 * @example
 * ```tsx
 * const { data } = useJobStatus('job-123', {
 *   enabled: true,
 *   pollingInterval: 2000  // Poll every 2 seconds
 * });
 * ```
 */
export function useJobStatus(jobId: string | null, options?: {
  enabled?: boolean;
  pollingInterval?: number;
}) {
  const { enabled = true, pollingInterval = 2000 } = options || {};

  return $api.useQuery(
    'get',
    '/api/v1/uploads/jobs/{job_id}/status',
    {
      params: {
        path: {
          job_id: jobId as string
        },
      },
    },
    {
      enabled: enabled && !!jobId,
      refetchInterval: (query) => {
        const status = query.state.data?.data?.status;
        if (status && ['completed', 'failed', 'cancelled'].includes(status)) {
          return false;
        }
        return pollingInterval;
      },
      refetchOnWindowFocus: false,
    }
  );
}

// ============================================================================
// MUTATION HOOKS - Upload operations
// ============================================================================

/**
 * Upload CSV file for async processing
 *
 * Uploads a CSV file and returns a job ID for tracking the processing status.
 *
 * @returns Mutation to upload CSV file
 *
 * @example
 * ```tsx
 * const upload = useUploadCsv();
 * const formData = new FormData();
 * formData.append('file', file);
 * formData.append('original_filename', 'data.csv');
 * formData.append('sheet_name', 'Sheet1');
 *
 * await upload.mutateAsync({ body: formData });
 * ```
 */
export function useUploadCsv() {
  return $api.useMutation('post', '/api/v1/uploads/csv-async');
}

/**
 * Cancel running upload job
 *
 * Cancels an in-progress upload job by ID.
 *
 * @returns Mutation to cancel job
 *
 * @example
 * ```tsx
 * const cancel = useCancelJob();
 * await cancel.mutateAsync({
 *   params: { path: { job_id: 'job-123' } }
 * });
 * ```
 */
export function useCancelJob() {
  return $api.useMutation('delete', '/api/v1/uploads/jobs/{job_id}');
}

// ============================================================================
// COMPOSITE HOOKS - Complete workflows
// ============================================================================

/**
 * Complete upload workflow with job tracking
 *
 * Provides a complete upload workflow including:
 * - File upload
 * - Job status polling
 * - Cancellation support
 * - Progress tracking
 *
 * @returns Upload workflow controller
 *
 * @example
 * ```tsx
 * const {
 *   startUpload,
 *   cancelCurrentJob,
 *   reset,
 *   currentJob,
 *   progress,
 *   isProcessing
 * } = useUploadWorkflow();
 *
 * // Start upload
 * await startUpload(file, 'data.csv', 'Sheet1');
 *
 * // Monitor progress
 * console.log(progress); // 0-100
 *
 * // Cancel if needed
 * cancelCurrentJob();
 * ```
 */
export function useUploadWorkflow() {
  const uploadMutation = useUploadCsv();
  const cancelMutation = useCancelJob();
  const queryClient = useQueryClient();

  const currentJobIdRef = useRef<string | null>(null);

  const jobStatusQuery = useJobStatus(currentJobIdRef.current);

  const startUpload = useCallback(async (file: File, originalFilename: string, sheetName: string) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('original_filename', originalFilename);
    formData.append('sheet_name', sheetName);

    try {
      uploadMutation.mutate(
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        { body: formData as any }, // FormData not properly typed in generated client
        {
          onSuccess: (data) => {
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            const jobId = (data as any)?.data?.data?.job_id;
            if (jobId) {
              currentJobIdRef.current = jobId;
            }
          },
          onError: () => {
            currentJobIdRef.current = null;
          },
        }
      );
    } catch (error) {
      currentJobIdRef.current = null;
      throw error;
    }
  }, [uploadMutation]);

  const cancelCurrentJob = useCallback(() => {
    if (currentJobIdRef.current) {
      cancelMutation.mutate({
        params: {
          path: { job_id: currentJobIdRef.current },
        },
      });
      currentJobIdRef.current = null;
    }
  }, [cancelMutation]);

  const reset = useCallback(() => {
    currentJobIdRef.current = null;
    uploadMutation.reset();
    cancelMutation.reset();
  }, [uploadMutation, cancelMutation]);

  const jobData = jobStatusQuery.data?.data;
  const isProcessing = jobData && ['pending', 'in_progress'].includes(jobData.status);

  return {
    startUpload,
    cancelCurrentJob,
    reset,
    currentJob: jobData,
    currentJobId: currentJobIdRef.current,
    isUploading: uploadMutation.isPending,
    isProcessing,
    isCancelling: cancelMutation.isPending,
    progress: jobData?.progress_percentage || 0,
    currentStep: jobData?.current_step,
    uploadError: uploadMutation.error,
    jobError: jobStatusQuery.error,
    cancelError: cancelMutation.error,
  };
}