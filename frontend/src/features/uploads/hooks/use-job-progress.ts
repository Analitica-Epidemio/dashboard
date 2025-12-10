"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { apiClient } from "@/lib/api/client";
import type { components } from "@/lib/api/types";

type JobStatus = components["schemas"]["JobStatusResponse"];

interface JobProgressState {
  status: JobStatus | null;
  isLoading: boolean;
  error: string | null;
  isPolling: boolean;
}

interface UseJobProgressReturn {
  jobStatus: JobStatus | null;
  isLoading: boolean;
  error: string | null;
  isPolling: boolean;
  startPolling: (jobId: string) => void;
  stopPolling: () => void;
  cancelJob: () => Promise<boolean>;
  reset: () => void;
}

/**
 * Hook para tracking de progress de jobs asíncronos.
 * Usa el apiClient tipado con OpenAPI.
 */
export function useJobProgress(): UseJobProgressReturn {
  const [state, setState] = useState<JobProgressState>({
    status: null,
    isLoading: false,
    error: null,
    isPolling: false,
  });

  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const currentJobIdRef = useRef<string | null>(null);

  // Limpiar polling al desmontar
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  const fetchJobStatus = useCallback(async (jobId: string): Promise<void> => {
    try {
      setState(prev => ({ ...prev, isLoading: true, error: null }));

      const { data, error, response } = await apiClient.GET(
        "/api/v1/uploads/jobs/{job_id}/status",
        { params: { path: { job_id: jobId } } }
      );

      if (error || !response.ok) {
        const err = error as { error?: { message?: string }; detail?: { msg: string }[] } | undefined;
        const errorMsg = err?.error?.message || (Array.isArray(err?.detail) ? err.detail[0]?.msg : undefined);
        throw new Error(
          errorMsg ||
          `Error obteniendo estado del job (${response.status})`
        );
      }

      const jobStatus = data?.data as JobStatus;
      setState(prev => ({
        ...prev,
        status: jobStatus,
        isLoading: false,
        error: null
      }));

      // Detener polling si el job terminó
      if (
        jobStatus.status === "COMPLETED" ||
        jobStatus.status === "FAILED" ||
        jobStatus.status === "CANCELLED"
      ) {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
        setState(prev => ({ ...prev, isPolling: false }));
      }

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Error desconocido";
      setState(prev => ({
        ...prev,
        error: errorMessage,
        isLoading: false,
        isPolling: false
      }));

      // Detener polling en caso de error
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }
  }, []);

  const startPolling = useCallback((jobId: string) => {
    // Limpiar polling anterior si existe
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    currentJobIdRef.current = jobId;
    setState(prev => ({ ...prev, isPolling: true, error: null }));

    // Fetch inicial
    fetchJobStatus(jobId);

    // Polling cada 2 segundos
    intervalRef.current = setInterval(() => {
      if (currentJobIdRef.current === jobId) {
        fetchJobStatus(jobId);
      }
    }, 2000);

  }, [fetchJobStatus]);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    currentJobIdRef.current = null;
    setState(prev => ({ ...prev, isPolling: false }));
  }, []);

  const cancelJob = useCallback(async (): Promise<boolean> => {
    if (!currentJobIdRef.current) {
      return false;
    }

    try {
      setState(prev => ({ ...prev, isLoading: true, error: null }));

      const { error, response } = await apiClient.DELETE(
        "/api/v1/uploads/jobs/{job_id}",
        { params: { path: { job_id: currentJobIdRef.current } } }
      );

      if (error || !response.ok) {
        const err = error as { error?: { message?: string }; detail?: { msg: string }[] } | undefined;
        const errorMsg = err?.error?.message || (Array.isArray(err?.detail) ? err.detail[0]?.msg : undefined);
        throw new Error(
          errorMsg || "Error cancelando job"
        );
      }

      // Actualizar estado local inmediatamente
      setState(prev => ({
        ...prev,
        status: prev.status ? { ...prev.status, status: "CANCELLED" } : null,
        isLoading: false,
        isPolling: false
      }));

      stopPolling();
      return true;

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Error desconocido";
      setState(prev => ({
        ...prev,
        error: errorMessage,
        isLoading: false
      }));
      return false;
    }
  }, [stopPolling]);

  const reset = useCallback(() => {
    stopPolling();
    setState({
      status: null,
      isLoading: false,
      error: null,
      isPolling: false,
    });
  }, [stopPolling]);

  return {
    jobStatus: state.status,
    isLoading: state.isLoading,
    error: state.error,
    isPolling: state.isPolling,
    startPolling,
    stopPolling,
    cancelJob,
    reset,
  };
}
