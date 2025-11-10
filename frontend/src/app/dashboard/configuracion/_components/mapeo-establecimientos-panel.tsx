"use client";

import React, { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle,
  Building2,
  Check,
  Search,
  SkipForward,
  Loader2,
  MapPin,
  TrendingUp,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";

import {
  useEstablecimientosSinMapear,
  crearMapeo,
  aceptarSugerenciasBulk,
  type EstablecimientoSinMapear,
  type SugerenciaMapeo,
} from "@/lib/api/establecimientos";
import { BuscarEstablecimientoIGNDialog } from "./buscar-establecimiento-ign-dialog";

export function MapeoEstablecimientosPanel() {
  const queryClient = useQueryClient();
  const [expandedIds, setExpandedIds] = useState<Set<number>>(new Set());
  const [processingIds, setProcessingIds] = useState<Set<number>>(new Set());
  const [buscarDialogOpen, setBuscarDialogOpen] = useState(false);
  const [selectedEstabSNVS, setSelectedEstabSNVS] = useState<EstablecimientoSinMapear | null>(null);
  const [isBulkProcessing, setIsBulkProcessing] = useState(false);

  const { data, isLoading } = useEstablecimientosSinMapear({
    limit: 10,
    con_eventos_solo: true,
    incluir_sugerencias: true,
  });

  const establecimientos = data?.items || [];
  const sinMapearCount = data?.sin_mapear_count || 0;
  const eventosSinMapear = data?.eventos_sin_mapear_count || 0;

  // Calcular cuántos tienen sugerencias de alta confianza
  const conAltaConfianza = establecimientos.filter(
    (e) => e.sugerencias.length > 0 && e.sugerencias[0].confianza === "HIGH"
  ).length;

  const toggleExpanded = (id: number) => {
    const newExpanded = new Set(expandedIds);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedIds(newExpanded);
  };

  const handleAceptarSugerencia = async (
    estab: EstablecimientoSinMapear,
    sugerencia: SugerenciaMapeo
  ) => {
    setProcessingIds((prev) => new Set(prev).add(estab.id));

    try {
      await crearMapeo({
        id_establecimiento_snvs: estab.id,
        id_establecimiento_ign: sugerencia.id_establecimiento_ign,
        razon: sugerencia.razon,
      });

      toast.success("Mapeo creado", {
        description: `${estab.nombre} mapeado a ${sugerencia.nombre_ign}`,
      });

      // Refrescar datos
      queryClient.invalidateQueries({ queryKey: ["establecimientos-sin-mapear"] });
    } catch (error) {
      toast.error("Error creando mapeo", {
        description: error instanceof Error ? error.message : "Error desconocido",
      });
    } finally {
      setProcessingIds((prev) => {
        const next = new Set(prev);
        next.delete(estab.id);
        return next;
      });
    }
  };

  const handleBuscarManualmente = (estab: EstablecimientoSinMapear) => {
    setSelectedEstabSNVS(estab);
    setBuscarDialogOpen(true);
  };

  const handleAceptarTodasAltaConfianza = async () => {
    if (conAltaConfianza === 0) return;

    setIsBulkProcessing(true);

    try {
      const mapeos = establecimientos
        .filter((e) => e.sugerencias.length > 0 && e.sugerencias[0].confianza === "HIGH")
        .map((e) => ({
          id_establecimiento_snvs: e.id,
          id_establecimiento_ign: e.sugerencias[0].id_establecimiento_ign,
          razon: e.sugerencias[0].razon,
        }));

      await aceptarSugerenciasBulk(mapeos);

      toast.success("Mapeos creados", {
        description: `Se mapearon ${mapeos.length} establecimientos exitosamente`,
      });

      // Refrescar datos
      queryClient.invalidateQueries({ queryKey: ["establecimientos-sin-mapear"] });
    } catch (error) {
      toast.error("Error procesando mapeos", {
        description: error instanceof Error ? error.message : "Error desconocido",
      });
    } finally {
      setIsBulkProcessing(false);
    }
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Mapeo de Establecimientos</CardTitle>
          <CardDescription>
            Vincula establecimientos SNVS con el catálogo IGN para geolocalización
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-32 w-full" />
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle>Mapeo de Establecimientos</CardTitle>
          <CardDescription>
            Vincula establecimientos SNVS con el catálogo IGN para geolocalización
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Alerta de estado */}
          {sinMapearCount > 0 && (
            <div className="rounded-lg border border-orange-200 bg-orange-50 p-4">
              <div className="flex items-start gap-3">
                <AlertTriangle className="h-5 w-5 text-orange-600 mt-0.5" />
                <div className="flex-1">
                  <h4 className="font-semibold text-orange-900 mb-1">
                    {sinMapearCount} establecimiento{sinMapearCount !== 1 ? "s" : ""} sin mapear
                  </h4>
                  <p className="text-sm text-orange-700 mb-3">
                    Afectando {eventosSinMapear.toLocaleString()} eventos sin geolocalizar
                  </p>

                  {conAltaConfianza > 0 && (
                    <Button
                      onClick={handleAceptarTodasAltaConfianza}
                      disabled={isBulkProcessing}
                      size="sm"
                      className="bg-orange-600 hover:bg-orange-700"
                    >
                      {isBulkProcessing ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          Procesando...
                        </>
                      ) : (
                        <>
                          <Check className="h-4 w-4 mr-2" />
                          Aceptar todas las sugerencias de alta confianza ({conAltaConfianza})
                        </>
                      )}
                    </Button>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Lista de establecimientos */}
          {establecimientos.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Building2 className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p className="text-sm">No hay establecimientos sin mapear con eventos</p>
            </div>
          ) : (
            <div className="space-y-3">
              <h4 className="text-sm font-medium text-muted-foreground">
                Establecimientos por revisar (ordenados por impacto)
              </h4>

              {establecimientos.map((estab) => {
                const isExpanded = expandedIds.has(estab.id);
                const isProcessing = processingIds.has(estab.id);
                const topSugerencia = estab.sugerencias[0];
                const hasHighConfidence = topSugerencia?.confianza === "HIGH";

                return (
                  <Card key={estab.id} className={isProcessing ? "opacity-50" : ""}>
                    <CardContent className="pt-4">
                      {/* Header */}
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <Building2 className="h-4 w-4 text-muted-foreground" />
                            <h5 className="font-medium">{estab.nombre}</h5>
                          </div>
                          <div className="text-xs text-muted-foreground mt-1">
                            {estab.codigo_snvs && `SNVS: ${estab.codigo_snvs} • `}
                            {estab.localidad_nombre && `${estab.localidad_nombre}, `}
                            {estab.departamento_nombre && `${estab.departamento_nombre}, `}
                            {estab.provincia_nombre}
                          </div>
                        </div>
                        <Badge variant="secondary" className="ml-2">
                          <TrendingUp className="h-3 w-3 mr-1" />
                          {estab.total_eventos} eventos
                        </Badge>
                      </div>

                      {/* Sugerencia principal */}
                      {topSugerencia ? (
                        <div className="bg-muted/50 rounded-lg p-3 mb-3">
                          <div className="flex items-start justify-between mb-2">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="text-sm font-medium">
                                  Sugerencia automática
                                </span>
                                <Badge
                                  variant={
                                    hasHighConfidence
                                      ? "default"
                                      : topSugerencia.confianza === "MEDIUM"
                                      ? "secondary"
                                      : "outline"
                                  }
                                  className={
                                    hasHighConfidence
                                      ? "bg-green-600 hover:bg-green-700"
                                      : ""
                                  }
                                >
                                  {topSugerencia.similitud_nombre.toFixed(0)}% match •{" "}
                                  {topSugerencia.confianza === "HIGH"
                                    ? "Alta"
                                    : topSugerencia.confianza === "MEDIUM"
                                    ? "Media"
                                    : "Baja"}{" "}
                                  confianza
                                </Badge>
                              </div>
                              <div className="flex items-center gap-2 text-sm">
                                <MapPin className="h-3 w-3 text-muted-foreground" />
                                <span className="font-medium">
                                  {topSugerencia.nombre_ign}
                                </span>
                              </div>
                              <div className="text-xs text-muted-foreground mt-1">
                                {topSugerencia.codigo_refes && `REFES: ${topSugerencia.codigo_refes}`}
                                {topSugerencia.localidad_nombre &&
                                  ` • ${topSugerencia.localidad_nombre}`}
                                {topSugerencia.departamento_nombre &&
                                  `, ${topSugerencia.departamento_nombre}`}
                              </div>
                            </div>
                          </div>

                          {/* Acciones */}
                          <div className="flex items-center gap-2 mt-3">
                            <Button
                              onClick={() => handleAceptarSugerencia(estab, topSugerencia)}
                              disabled={isProcessing}
                              size="sm"
                              variant={hasHighConfidence ? "default" : "secondary"}
                            >
                              {isProcessing ? (
                                <Loader2 className="h-3 w-3 mr-2 animate-spin" />
                              ) : (
                                <Check className="h-3 w-3 mr-2" />
                              )}
                              Aceptar
                            </Button>

                            {estab.sugerencias.length > 1 && (
                              <Button
                                onClick={() => toggleExpanded(estab.id)}
                                size="sm"
                                variant="ghost"
                              >
                                {isExpanded ? "Ocultar" : "Ver"} {estab.sugerencias.length - 1}{" "}
                                más
                              </Button>
                            )}

                            <Button
                              onClick={() => handleBuscarManualmente(estab)}
                              disabled={isProcessing}
                              size="sm"
                              variant="outline"
                            >
                              <Search className="h-3 w-3 mr-2" />
                              Buscar otro
                            </Button>

                            <Button
                              disabled={isProcessing}
                              size="sm"
                              variant="ghost"
                            >
                              <SkipForward className="h-3 w-3 mr-2" />
                              Omitir
                            </Button>
                          </div>

                          {/* Sugerencias adicionales (expandible) */}
                          {isExpanded && estab.sugerencias.length > 1 && (
                            <div className="mt-3 pt-3 border-t space-y-2">
                              {estab.sugerencias.slice(1).map((sug, idx) => (
                                <div
                                  key={idx}
                                  className="flex items-center justify-between py-2"
                                >
                                  <div className="flex-1">
                                    <div className="text-sm font-medium">
                                      {sug.nombre_ign}
                                    </div>
                                    <div className="text-xs text-muted-foreground">
                                      {sug.codigo_refes && `REFES: ${sug.codigo_refes}`}
                                      {sug.localidad_nombre && ` • ${sug.localidad_nombre}`}
                                    </div>
                                  </div>
                                  <div className="flex items-center gap-2">
                                    <Badge variant="outline">
                                      {sug.similitud_nombre.toFixed(0)}%
                                    </Badge>
                                    <Button
                                      onClick={() => handleAceptarSugerencia(estab, sug)}
                                      disabled={isProcessing}
                                      size="sm"
                                      variant="ghost"
                                    >
                                      <Check className="h-3 w-3" />
                                    </Button>
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="bg-muted/30 rounded-lg p-3 mb-3">
                          <p className="text-sm text-muted-foreground mb-3">
                            ⚠️ Sin sugerencias automáticas
                          </p>
                          <Button
                            onClick={() => handleBuscarManualmente(estab)}
                            disabled={isProcessing}
                            size="sm"
                          >
                            <Search className="h-3 w-3 mr-2" />
                            Buscar manualmente
                          </Button>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                );
              })}

              <div className="text-center text-sm text-muted-foreground pt-2">
                Mostrando {establecimientos.length} de {sinMapearCount}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Dialog de búsqueda manual */}
      {selectedEstabSNVS && (
        <BuscarEstablecimientoIGNDialog
          open={buscarDialogOpen}
          onOpenChange={setBuscarDialogOpen}
          establecimientoSNVS={selectedEstabSNVS}
          onMapeoCreado={() => {
            queryClient.invalidateQueries({ queryKey: ["establecimientos-sin-mapear"] });
          }}
        />
      )}
    </>
  );
}
