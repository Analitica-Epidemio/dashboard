"use client";

import React, { useState } from "react";
import { Search, Loader2, MapPin, Check } from "lucide-react";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";

import {
  useBuscarEstablecimientosIGN,
  useCrearMapeoEstablecimiento,
  type EstablecimientoSinMapear,
  type EstablecimientoIGNResult,
} from "@/features/establecimientos/api";

interface BuscarEstablecimientoIGNDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  establecimientoSNVS: EstablecimientoSinMapear;
  onMapeoCreado: () => void;
}

export function BuscarEstablecimientoIGNDialog({
  open,
  onOpenChange,
  establecimientoSNVS,
  onMapeoCreado,
}: BuscarEstablecimientoIGNDialogProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [hasSearched, setHasSearched] = useState(false);

  const { data, isLoading } = useBuscarEstablecimientosIGN({
    q: searchQuery,
    provincia: establecimientoSNVS.provincia_nombre || undefined,
    page_size: 20,
    enabled: hasSearched && open,
  });

  const crearMapeoMutation = useCrearMapeoEstablecimiento();

  const resultados = data?.data?.items || [];

  const handleSearch = () => {
    if (searchQuery.trim()) {
      setHasSearched(true);
    }
  };

  const handleSeleccionar = async (establecimientoIGN: EstablecimientoIGNResult) => {
    try {
      await crearMapeoMutation.mutateAsync({
        body: {
          id_establecimiento_snvs: establecimientoSNVS.id,
          id_establecimiento_ign: establecimientoIGN.id,
          razon: `Mapeo manual: ${establecimientoSNVS.nombre} → ${establecimientoIGN.nombre}`,
        },
      });

      toast.success("Mapeo creado", {
        description: `${establecimientoSNVS.nombre} mapeado a ${establecimientoIGN.nombre}`,
      });

      onMapeoCreado();
      onOpenChange(false);

      // Reset state
      setSearchQuery("");
      setHasSearched(false);
    } catch (error) {
      toast.error("Error creando mapeo", {
        description: error instanceof Error ? error.message : "Error desconocido",
      });
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleSearch();
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>Buscar establecimiento IGN</DialogTitle>
          <DialogDescription>
            Mapeando: <span className="font-medium">{establecimientoSNVS.nombre}</span>
            {establecimientoSNVS.codigo_snvs && ` (SNVS: ${establecimientoSNVS.codigo_snvs})`}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 flex-1 overflow-hidden flex flex-col">
          {/* Barra de búsqueda */}
          <div className="flex gap-2">
            <Input
              placeholder="Buscar por nombre o código REFES..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={crearMapeoMutation.isPending}
            />
            <Button
              onClick={handleSearch}
              disabled={!searchQuery.trim() || isLoading || crearMapeoMutation.isPending}
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Search className="h-4 w-4" />
              )}
            </Button>
          </div>

          {/* Filtros aplicados */}
          {establecimientoSNVS.provincia_nombre && (
            <div className="text-sm text-muted-foreground">
              Filtrando por provincia: <Badge variant="outline">{establecimientoSNVS.provincia_nombre}</Badge>
            </div>
          )}

          {/* Resultados */}
          <div className="flex-1 overflow-y-auto space-y-2">
            {!hasSearched && (
              <div className="text-center py-8 text-muted-foreground">
                <Search className="h-12 w-12 mx-auto mb-3 opacity-50" />
                <p className="text-sm">Ingresa un término de búsqueda</p>
              </div>
            )}

            {hasSearched && isLoading && (
              <div className="text-center py-8">
                <Loader2 className="h-8 w-8 mx-auto animate-spin text-muted-foreground mb-3" />
                <p className="text-sm text-muted-foreground">Buscando...</p>
              </div>
            )}

            {hasSearched && !isLoading && resultados.length === 0 && (
              <div className="text-center py-8 text-muted-foreground">
                <p className="text-sm">No se encontraron resultados</p>
              </div>
            )}

            {hasSearched && !isLoading && resultados.length > 0 && (
              <>
                <p className="text-sm text-muted-foreground mb-2">
                  {resultados.length} resultado{resultados.length !== 1 ? "s" : ""}:
                </p>
                {resultados.map((estab) => (
                  <div
                    key={estab.id}
                    className="border rounded-lg p-3 hover:border-primary transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="font-medium mb-1">{estab.nombre}</div>
                        <div className="text-xs text-muted-foreground space-y-0.5">
                          {estab.codigo_refes && (
                            <div>REFES: {estab.codigo_refes}</div>
                          )}
                          {(estab.localidad_nombre || estab.departamento_nombre || estab.provincia_nombre) && (
                            <div className="flex items-center gap-1">
                              <MapPin className="h-3 w-3" />
                              {estab.localidad_nombre && `${estab.localidad_nombre}`}
                              {estab.departamento_nombre && `, ${estab.departamento_nombre}`}
                              {estab.provincia_nombre && `, ${estab.provincia_nombre}`}
                            </div>
                          )}
                          {estab.latitud && estab.longitud && (
                            <div className="text-xs font-mono">
                              {estab.latitud.toFixed(4)}, {estab.longitud.toFixed(4)}
                            </div>
                          )}
                        </div>
                      </div>
                      <Button
                        onClick={() => handleSeleccionar(estab)}
                        disabled={crearMapeoMutation.isPending}
                        size="sm"
                        className="ml-3"
                      >
                        {crearMapeoMutation.isPending ? (
                          <Loader2 className="h-3 w-3 animate-spin" />
                        ) : (
                          <>
                            <Check className="h-3 w-3 mr-2" />
                            Seleccionar
                          </>
                        )}
                      </Button>
                    </div>
                  </div>
                ))}
              </>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
