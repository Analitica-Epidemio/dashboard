/**
 * Upload Hooks using openapi-react-query
 * File upload with job polling
 */

import { useQueryClient } from '@tanstack/react-query';
import { useCallback, useRef } from 'react';
import { $api } from '@/lib/api/client';

/**
 * Hook for CSV upload
 */
export function useUploadCsv() {
  return $api.useMutation('post', '/api/v1/uploads/csv-async');
}

/**
 * Hook for job status polling
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

/**
 * Hook for cancelling jobs
 */
export function useCancelJob() {
  const queryClient = useQueryClient();

  return $api.useMutation('delete', '/api/v1/uploads/jobs/{job_id}', {
    onSuccess: (_, variables) => {
      // Invalidate job status
      const jobId = (variables)?.params?.path?.job_id;
      if (jobId) {
        queryClient.invalidateQueries({
          queryKey: ['get', '/api/v1/uploads/jobs/{job_id}/status', { params: { path: { job_id: jobId } } }],
        });
      }
    },
  });
}

/**
 * Complete upload workflow
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
        { body: formData as any },
        {
          onSuccess: (data: any) => {
            const jobId = data?.data?.data?.job_id;
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