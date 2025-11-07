"use client";

import React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Loader2, MapPin, Play, CheckCircle2, XCircle, AlertCircle } from "lucide-react";
import { toast } from "sonner";
import { apiClient } from "@/lib/api/client";

interface GeocodingStats {
  total_domicilios: number;
  geocoded: number;
  pending: number;
  processing: number;
  failed: number;
  not_geocodable: number;
  percentage_geocoded: number;
  by_estado?: Record<string, number>;
}

interface TriggerGeocodingResponse {
  message: string;
  pending_count: number;
  task_id: string | null;
  batch_size?: number;
  estimated_batches?: number;
}

export function GeocodingConfigPanel() {
  const queryClient = useQueryClient();

  // Fetch geocoding stats
  const { data: stats, isLoading } = useQuery<GeocodingStats>({
    queryKey: ["geocoding-stats"],
    queryFn: async () => {
      const response = await apiClient.GET("/api/v1/geocoding/stats");
      if (response.error) {
        throw new Error("Failed to fetch geocoding stats");
      }
      // Type assertion since API returns generic unknown
      return response.data as any as GeocodingStats;
    },
    refetchInterval: 5000, // Refetch every 5 seconds to see progress
  });

  // Trigger geocoding mutation
  const triggerMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.POST("/api/v1/geocoding/trigger", {
        params: {
          query: {
            batch_size: 500,
          },
        },
      });
      if (response.error) {
        throw new Error("Failed to trigger geocoding");
      }
      // Type assertion since API returns generic unknown
      return response.data as any as TriggerGeocodingResponse;
    },
    onSuccess: (data) => {
      toast.success(data.message, {
        description: data.task_id
          ? `Tarea encolada: ${data.task_id.slice(0, 8)}...`
          : undefined,
      });
      // Refetch stats immediately
      queryClient.invalidateQueries({ queryKey: ["geocoding-stats"] });
    },
    onError: (error: Error) => {
      toast.error("Error al triggear geocodificación", {
        description: error.message,
      });
    },
  });

  const handleTriggerGeocoding = () => {
    triggerMutation.mutate();
  };

  const isProcessing = stats?.processing && stats.processing > 0;
  const hasPending = stats?.pending && stats.pending > 0;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <CardTitle className="flex items-center gap-2">
              <MapPin className="h-5 w-5" />
              Geocodificación de Domicilios
            </CardTitle>
            <CardDescription>
              Conversión automática de direcciones a coordenadas geográficas
            </CardDescription>
          </div>
          <Button
            onClick={handleTriggerGeocoding}
            disabled={triggerMutation.isPending || isProcessing || !hasPending}
            size="sm"
          >
            {triggerMutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Encolando...
              </>
            ) : (
              <>
                <Play className="mr-2 h-4 w-4" />
                Triggear Geocodificación
              </>
            )}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : stats ? (
          <div className="space-y-6">
            {/* Progress bar */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium">Progreso de Geocodificación</span>
                <span className="text-muted-foreground">
                  {stats.percentage_geocoded.toFixed(1)}%
                </span>
              </div>
              <Progress value={stats.percentage_geocoded} className="h-2" />
              <p className="text-xs text-muted-foreground">
                {stats.geocoded.toLocaleString()} de {stats.total_domicilios.toLocaleString()} domicilios geocodificados
              </p>
            </div>

            {/* Stats grid */}
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {/* Geocoded */}
              <div className="flex flex-col space-y-2 rounded-lg border p-4">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                  <span className="text-sm font-medium text-muted-foreground">
                    Geocodificados
                  </span>
                </div>
                <div className="text-2xl font-bold">{stats.geocoded.toLocaleString()}</div>
              </div>

              {/* Pending */}
              <div className="flex flex-col space-y-2 rounded-lg border p-4">
                <div className="flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 text-yellow-500" />
                  <span className="text-sm font-medium text-muted-foreground">
                    Pendientes
                  </span>
                </div>
                <div className="text-2xl font-bold">{stats.pending.toLocaleString()}</div>
              </div>

              {/* Processing */}
              <div className="flex flex-col space-y-2 rounded-lg border p-4">
                <div className="flex items-center gap-2">
                  <Loader2
                    className={`h-4 w-4 text-blue-500 ${isProcessing ? "animate-spin" : ""}`}
                  />
                  <span className="text-sm font-medium text-muted-foreground">
                    Procesando
                  </span>
                </div>
                <div className="text-2xl font-bold">{stats.processing.toLocaleString()}</div>
              </div>

              {/* Failed */}
              <div className="flex flex-col space-y-2 rounded-lg border p-4">
                <div className="flex items-center gap-2">
                  <XCircle className="h-4 w-4 text-red-500" />
                  <span className="text-sm font-medium text-muted-foreground">
                    Fallidos
                  </span>
                </div>
                <div className="text-2xl font-bold">{stats.failed.toLocaleString()}</div>
              </div>

              {/* Not geocodable */}
              <div className="flex flex-col space-y-2 rounded-lg border p-4">
                <div className="flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 text-orange-500" />
                  <span className="text-sm font-medium text-muted-foreground">
                    No Geocodificables
                  </span>
                </div>
                <div className="text-2xl font-bold">{stats.not_geocodable.toLocaleString()}</div>
              </div>

              {/* Total */}
              <div className="flex flex-col space-y-2 rounded-lg border p-4 bg-muted/50">
                <div className="flex items-center gap-2">
                  <MapPin className="h-4 w-4" />
                  <span className="text-sm font-medium text-muted-foreground">
                    Total
                  </span>
                </div>
                <div className="text-2xl font-bold">{stats.total_domicilios.toLocaleString()}</div>
              </div>
            </div>

            {/* Status message */}
            {isProcessing && (
              <div className="flex items-center gap-2 rounded-lg bg-blue-50 dark:bg-blue-950/20 p-4">
                <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-blue-900 dark:text-blue-100">
                    Geocodificación en progreso
                  </p>
                  <p className="text-xs text-blue-700 dark:text-blue-300">
                    {stats.processing} domicilios siendo procesados. Las estadísticas se actualizan automáticamente.
                  </p>
                </div>
              </div>
            )}

            {!hasPending && !isProcessing && (
              <div className="flex items-center gap-2 rounded-lg bg-green-50 dark:bg-green-950/20 p-4">
                <CheckCircle2 className="h-5 w-5 text-green-500" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-green-900 dark:text-green-100">
                    ¡Geocodificación completa!
                  </p>
                  <p className="text-xs text-green-700 dark:text-green-300">
                    No hay domicilios pendientes de geocodificar
                  </p>
                </div>
              </div>
            )}
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
