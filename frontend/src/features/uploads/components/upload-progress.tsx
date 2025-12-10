"use client";

import React from "react";
import Link from "next/link";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { CheckCircle2, XCircle, Clock, Loader2, AlertCircle, ExternalLink } from "lucide-react";
import { useJobProgress } from "../hooks/use-job-progress";

interface UploadProgressProps {
  jobId: string | null;
  onComplete?: (result: { total_rows?: number; columns?: string[]; file_path?: string }) => void;
  onError?: (error: string) => void;
  className?: string;
}

/**
 * Componente moderno para mostrar progreso de upload asíncrono.
 * 
 * Características:
 * - Auto-polling del estado
 * - Progress bar animada
 * - Estados visuales claros
 * - Cancelación de jobs
 */
export function UploadProgress({
  jobId,
  onComplete,
  onError,
  className = ""
}: UploadProgressProps) {
  const {
    jobStatus,
    isLoading,
    error,
    startPolling,
    cancelJob,
    reset
  } = useJobProgress();

  // Auto-start polling cuando recibimos un jobId
  // Solo iniciar polling una vez cuando se monta el componente
  React.useEffect(() => {
    if (jobId) {
      startPolling(jobId);
    }
    // Cleanup al desmontar
    return () => {
      if (jobId) {
        // stopPolling se llama automáticamente en useJobProgress cleanup
      }
    };
  }, [jobId, startPolling]);

  // Callbacks cuando cambia el estado
  React.useEffect(() => {
    if (jobStatus?.status === "COMPLETED" && onComplete && jobStatus.result_data) {
      onComplete(jobStatus.result_data);
    }
  }, [jobStatus?.status, jobStatus?.result_data, onComplete]);

  React.useEffect(() => {
    if (error && onError) {
      onError(error);
    }
  }, [error, onError]);

  React.useEffect(() => {
    if (jobStatus?.error_message && onError) {
      onError(jobStatus.error_message);
    }
  }, [jobStatus?.error_message, onError]);

  // No mostrar nada si no hay jobId
  if (!jobId) {
    return null;
  }

  // Estado de carga inicial
  if (isLoading && !jobStatus) {
    return (
      <div className={`max-w-2xl mx-auto ${className}`}>
        <div className="border rounded-lg bg-card p-6 space-y-4">
          <div className="flex items-center space-x-3">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span className="text-sm text-muted-foreground">
              Iniciando procesamiento...
            </span>
          </div>
        </div>
      </div>
    );
  }

  // Error en el polling
  if (error && !jobStatus) {
    return (
      <div className={`max-w-2xl mx-auto ${className}`}>
        <div className="border rounded-lg bg-card p-6 space-y-4">
          <div className="flex items-center space-x-2 text-destructive">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm font-medium">Error de conexión</span>
          </div>
          <p className="text-sm text-muted-foreground">{error}</p>
          <Button
            variant="outline"
            size="sm"
            onClick={reset}
            className="w-full"
          >
            Reintentar
          </Button>
        </div>
      </div>
    );
  }

  if (!jobStatus) {
    return null;
  }

  // Función para obtener icono según estado
  const getStatusIcon = () => {
    switch (jobStatus.status) {
      case "COMPLETED":
        return <CheckCircle2 className="h-5 w-5 text-green-500" />;
      case "FAILED":
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      case "CANCELLED":
        return <XCircle className="h-5 w-5 text-gray-500" />;
      case "IN_PROGRESS":
        return <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />;
      case "PENDING":
        return <Clock className="h-5 w-5 text-gray-400" />;
      default:
        return <Clock className="h-5 w-5 text-muted-foreground" />;
    }
  };

  // Función para obtener texto del estado
  const getStatusText = () => {
    switch (jobStatus.status) {
      case "COMPLETED":
        return "Procesamiento completado";
      case "FAILED":
        return "Error en el procesamiento";
      case "CANCELLED":
        return "Procesamiento cancelado";
      case "IN_PROGRESS":
        return "Procesando archivo...";
      case "PENDING":
        return "En cola de procesamiento";
      default:
        return "Estado desconocido";
    }
  };


  const canCancel = jobStatus.status === "PENDING" || jobStatus.status === "IN_PROGRESS";
  const isFinished = jobStatus.status === "COMPLETED" || jobStatus.status === "FAILED" || jobStatus.status === "CANCELLED";
  const isFailed = jobStatus.status === "FAILED";

  return (
    <div className={`max-w-2xl mx-auto ${className}`}>
      <div className="space-y-4 p-6 border rounded-lg bg-card">
        {/* Header con estado */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {getStatusIcon()}
            <div>
              <p className="text-sm font-medium">
                {getStatusText()}
              </p>
              {jobStatus.duration_seconds && isFinished && (
                <p className="text-xs text-muted-foreground">
                  Duración: {jobStatus.duration_seconds.toFixed(1)}s
                </p>
              )}
            </div>
          </div>

          {/* Botón de cancelar o reintentar */}
          {canCancel && (
            <Button
              variant="outline"
              size="sm"
              onClick={cancelJob}
              disabled={isLoading}
            >
              Cancelar
            </Button>
          )}
        </div>

        {/* Progress bar */}
        <div className="space-y-2">
          <Progress
            value={jobStatus.progress_percentage}
            className="h-2"
          />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>{jobStatus.current_step || "Procesando..."}</span>
            <span>{jobStatus.progress_percentage}%</span>
          </div>
        </div>

        {/* Resultados o errores */}
        {jobStatus.status === "COMPLETED" && jobStatus.result_data && (
          <div className="space-y-2 p-3 bg-green-50 rounded-md border border-green-200">
            <p className="text-sm font-medium text-green-800">
              Archivo procesado exitosamente
            </p>
            <div className="text-xs text-green-700 space-y-1">
              <div>Filas procesadas: {jobStatus.result_data.total_rows?.toLocaleString()}</div>
              <div>Columnas: {Array.isArray(jobStatus.result_data.columns) ? jobStatus.result_data.columns.length : 0}</div>
            </div>
          </div>
        )}

        {jobStatus.error_message && (
          <div className="space-y-3 p-3 bg-red-50 rounded-md border border-red-200">
            <div className="space-y-2">
              <p className="text-sm font-medium text-red-800">
                El procesamiento falló
              </p>
              <p className="text-xs text-red-700">
                {jobStatus.error_message}
              </p>
            </div>

            {/* Opciones cuando falla */}
            {isFailed && (
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => window.location.reload()}
                  className="flex-1 bg-white hover:bg-red-50 border-red-200 text-red-700"
                >
                  Intentar con otro archivo
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    // Reintentar el mismo archivo
                    if (onError) {
                      onError("retry");
                    }
                  }}
                  className="flex-1 bg-white hover:bg-red-50 border-red-200 text-red-700"
                >
                  Reintentar
                </Button>
              </div>
            )}
          </div>
        )}

        {/* Información adicional e instrucciones */}
        <div className="space-y-3">
          {jobStatus.status === "PENDING" && (
            <div className="text-xs text-muted-foreground">
              <p>Tu archivo está en cola. El procesamiento comenzará pronto.</p>
            </div>
          )}

          {/* Mensaje informativo y botón dashboard - Solo si NO falló */}
          {!isFailed && (
            <div className="p-3 bg-blue-50 rounded-md border border-blue-200">
              <div className="space-y-3">
                <div className="text-sm">
                  <p className="font-medium text-blue-800 mb-1">
                    {jobStatus.status === "COMPLETED" ? "✅ Procesamiento completado" : "📊 Procesamiento en curso"}
                  </p>
                  <p className="text-blue-700 text-xs">
                    {jobStatus.status === "COMPLETED"
                      ? "Los datos han sido procesados y están disponibles en el dashboard."
                      : "Los datos se están analizando en segundo plano. Una vez terminado, la información se actualizará automáticamente en el dashboard."
                    }
                  </p>
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  asChild
                  className="w-full bg-white hover:bg-blue-50 border-blue-200 text-blue-700"
                >
                  <Link href="/dashboard">
                    <ExternalLink className="w-4 h-4 mr-2" />
                    Ir al Dashboard
                  </Link>
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}