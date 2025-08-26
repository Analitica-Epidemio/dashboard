"use client";

import React from "react";
import Link from "next/link";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { CheckCircle2, XCircle, Clock, Loader2, AlertCircle, ExternalLink } from "lucide-react";
import { useJobProgress } from "../_hooks/use-job-progress";

interface UploadProgressProps {
  jobId: string | null;
  onComplete?: (result: { total_rows?: number; columns?: string[]; file_path?: string }) => void;
  onError?: (error: string) => void;
  dashboardHref?: string;
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
  dashboardHref = "/dashboard",
  className = "" 
}: UploadProgressProps) {
  const { 
    jobStatus, 
    isLoading, 
    error, 
    isPolling, 
    startPolling, 
    cancelJob,
    reset 
  } = useJobProgress();

  // Auto-start polling cuando recibimos un jobId
  React.useEffect(() => {
    if (jobId && !isPolling) {
      startPolling(jobId);
    }
  }, [jobId, isPolling, startPolling]);

  // Callbacks cuando cambia el estado
  React.useEffect(() => {
    if (jobStatus?.status === "completed" && onComplete && jobStatus.result_data) {
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
      <div className={`space-y-3 ${className}`}>
        <div className="flex items-center space-x-2">
          <Loader2 className="h-4 w-4 animate-spin" />
          <span className="text-sm text-muted-foreground">
            Iniciando procesamiento...
          </span>
        </div>
      </div>
    );
  }

  // Error en el polling
  if (error && !jobStatus) {
    return (
      <div className={`space-y-3 ${className}`}>
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
    );
  }

  if (!jobStatus) {
    return null;
  }

  // Función para obtener icono según estado
  const getStatusIcon = () => {
    switch (jobStatus.status) {
      case "completed":
        return <CheckCircle2 className="h-5 w-5 text-green-600" />;
      case "failed":
      case "cancelled":
        return <XCircle className="h-5 w-5 text-destructive" />;
      case "in_progress":
        return <Loader2 className="h-5 w-5 animate-spin text-blue-600" />;
      case "pending":
        return <Clock className="h-5 w-5 text-yellow-600" />;
      default:
        return <Clock className="h-5 w-5 text-muted-foreground" />;
    }
  };

  // Función para obtener texto del estado
  const getStatusText = () => {
    switch (jobStatus.status) {
      case "completed":
        return "Completado exitosamente";
      case "failed":
        return "Error en procesamiento";
      case "cancelled":
        return "Cancelado";
      case "in_progress":
        return jobStatus.current_step || "Procesando archivo...";
      case "pending":
        return "En cola de procesamiento";
      default:
        return "Estado desconocido";
    }
  };


  const canCancel = jobStatus.status === "pending" || jobStatus.status === "in_progress";
  const isFinished = jobStatus.status === "completed" || jobStatus.status === "failed" || jobStatus.status === "cancelled";

  return (
    <div className={`space-y-4 p-4 border rounded-lg bg-card ${className}`}>
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
        
        {/* Botón de cancelar */}
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
          <span>
            Paso {jobStatus.completed_steps} de {jobStatus.total_steps}
          </span>
          <span>{jobStatus.progress_percentage}%</span>
        </div>
      </div>

      {/* Resultados o errores */}
      {jobStatus.status === "completed" && jobStatus.result_data && (
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
        <div className="space-y-2 p-3 bg-red-50 rounded-md border border-red-200">
          <p className="text-sm font-medium text-red-800">
            Error en procesamiento
          </p>
          <p className="text-xs text-red-700">
            {jobStatus.error_message}
          </p>
        </div>
      )}

      {/* Información adicional e instrucciones */}
      <div className="space-y-3">
        {jobStatus.status === "pending" && (
          <div className="text-xs text-muted-foreground">
            <p>Tu archivo está en cola. El procesamiento comenzará pronto.</p>
          </div>
        )}
        
        {/* Mensaje informativo y botón dashboard */}
        <div className="p-3 bg-blue-50 rounded-md border border-blue-200">
          <div className="space-y-3">
            <div className="text-sm">
              <p className="font-medium text-blue-800 mb-1">
                {jobStatus.status === "completed" ? "✅ Procesamiento completado" : "📊 Procesamiento en curso"}
              </p>
              <p className="text-blue-700 text-xs">
                {jobStatus.status === "completed" 
                  ? "Los datos han sido procesados y están disponibles en el dashboard."
                  : "Los datos se están analizando en segundo plano. Una vez terminado, la información se actualizará automáticamente en el dashboard."
                }
              </p>
            </div>
            
            {dashboardHref && (
              <Button 
                variant="outline" 
                size="sm"
                asChild
                className="w-full bg-white hover:bg-blue-50 border-blue-200 text-blue-700"
              >
                <Link href={dashboardHref}>
                  <ExternalLink className="w-4 h-4 mr-2" />
                  Ir al Dashboard
                </Link>
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}