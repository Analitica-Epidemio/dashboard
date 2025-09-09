"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { getJobStatusUrl, getCancelJobUrl } from "@/lib/api/config";
import type { components } from "@/lib/api/types";

// Usar tipos generados automáticamente desde OpenAPI
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
 * Hook moderno para tracking de progress de jobs asíncronos.
 * 
 * Características senior-level:
 * - Auto-polling con cleanup
 * - Error handling robusto  
 * - Cancelación de jobs
 * - Estado optimizado
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

      const response = await fetch(getJobStatusUrl(jobId));
      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error?.message || "Error fetching job status");
      }

      const jobStatus = result.data as JobStatus;
      setState(prev => ({ 
        ...prev, 
        status: jobStatus, 
        isLoading: false,
        error: null 
      }));

      // Detener polling si el job terminó
      if (jobStatus.status === "completed" || 
          jobStatus.status === "failed" || 
          jobStatus.status === "cancelled") {
        
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
        
        setState(prev => ({ ...prev, isPolling: false }));
      }

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Unknown error";
      setState(prev => ({ 
        ...prev, 
        error: errorMessage, 
        isLoading: false 
      }));

      // Detener polling en caso de error
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      setState(prev => ({ ...prev, isPolling: false }));
    }
  }, []);

  const startPolling = useCallback((jobId: string) => {
    // Limpiar polling anterior si existe
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    currentJobIdRef.current = jobId;
    setState(prev => ({ ...prev, isPolling: true }));

    // Fetch inicial inmediato
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

      const response = await fetch(getCancelJobUrl(currentJobIdRef.current), {
        method: "DELETE",
      });

      if (!response.ok) {
        const result = await response.json();
        throw new Error(result.error?.message || "Error canceling job");
      }

      // Actualizar estado local inmediatamente
      setState(prev => ({
        ...prev,
        status: prev.status ? { ...prev.status, status: "cancelled" } : null,
        isLoading: false,
        isPolling: false
      }));

      // Detener polling
      stopPolling();
      return true;

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Unknown error";
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