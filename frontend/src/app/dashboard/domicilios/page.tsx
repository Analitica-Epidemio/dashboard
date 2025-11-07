"use client";

import { useState } from "react";
import { MapPin, Building2, CheckCircle2, XCircle, AlertCircle } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/features/layout/components";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import { useDomicilios } from "@/lib/api/domicilios";
import type { DomicilioListItem } from "@/lib/api/domicilios";
import { DomicilioDetalleSheet } from "./_components/domicilio-detalle-sheet";

export default function DomiciliosPage() {
  const [detailSheetOpen, setDetailSheetOpen] = useState(false);
  const [selectedDomicilioId, setSelectedDomicilioId] = useState<number | null>(null);

  const [filters, setFilters] = useState({
    page: 1,
    page_size: 50,
    order_by: "eventos_desc" as const,
  });

  const handleFilterChange = (key: string, value: string | number) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value,
      // Solo resetear page a 1 si NO estamos cambiando la página
      ...(key !== "page" && { page: 1 }),
    }));
  };

  const domiciliosQuery = useDomicilios(filters);

  const domiciliosData = domiciliosQuery.data;
  const domicilios = domiciliosData?.data?.items || [];
  const isLoading = domiciliosQuery.isLoading;

  const handleViewDetail = (domicilio: DomicilioListItem) => {
    setSelectedDomicilioId(domicilio.id);
    setDetailSheetOpen(true);
  };

  // Calcular estadísticas
  const totalDomicilios = domiciliosData?.data?.total || 0;
  const geocodificados = domicilios.filter(
    (d) => d.estado_geocodificacion === "GEOCODIFICADO"
  ).length;
  const conEventos = domicilios.filter((d) => d.total_eventos > 0).length;
  const pendientes = domicilios.filter(
    (d) => d.estado_geocodificacion === "PENDIENTE"
  ).length;

  // Skeleton para carga de tabla
  const DomicilioRowSkeleton = () => (
    <div className="px-4 py-3 flex items-center gap-4">
      <Skeleton className="h-4 w-64" />
      <Skeleton className="h-4 w-32" />
      <Skeleton className="h-4 w-16" />
      <Skeleton className="h-6 w-24" />
      <Skeleton className="h-4 w-32" />
    </div>
  );

  const getEstadoBadgeClasses = (estado: string) => {
    switch (estado.toLowerCase()) {
      case "geocodificado":
        return "bg-green-100 text-green-700 border-green-200 hover:bg-green-100";
      case "error":
        return "bg-red-100 text-red-700 border-red-200 hover:bg-red-100";
      case "pendiente":
        return "bg-yellow-100 text-yellow-700 border-yellow-200 hover:bg-yellow-100";
      case "no_geocodificable":
        return "bg-gray-100 text-gray-700 border-gray-200 hover:bg-gray-100";
      default:
        return "bg-gray-100 text-gray-700 border-gray-200 hover:bg-gray-100";
    }
  };

  const getEstadoLabel = (estado: string) => {
    switch (estado.toLowerCase()) {
      case "geocodificado":
        return "Geocodificado";
      case "error":
        return "Error";
      case "pendiente":
        return "Pendiente";
      case "no_geocodificable":
        return "No geocodificable";
      default:
        return estado;
    }
  };

  const getEstadoIcon = (estado: string) => {
    switch (estado.toLowerCase()) {
      case "geocodificado":
        return <CheckCircle2 className="h-3 w-3" />;
      case "error":
        return <XCircle className="h-3 w-3" />;
      case "pendiente":
        return <AlertCircle className="h-3 w-3" />;
      case "no_geocodificable":
        return <XCircle className="h-3 w-3" />;
      default:
        return null;
    }
  };

  return (
    <SidebarProvider>
      <AppSidebar variant="inset" />
      <SidebarInset>
        {/* Header */}
        <header className="flex h-14 items-center gap-4 border-b bg-background px-6">
          <SidebarTrigger className="-ml-2" />
          <Separator orientation="vertical" className="h-6" />
          <h1 className="text-lg font-semibold">Domicilios</h1>
        </header>

        {/* Main Content */}
        <main className="flex-1 p-6 overflow-y-scroll bg-muted/40">
          {/* Stats and Filters */}
          <div className="mb-6">
            {/* Stats */}
            <div className="grid grid-cols-4 gap-4 mb-4">
              <div className="bg-white rounded-lg border p-3">
                <div className="text-xs text-muted-foreground">Total</div>
                <div className="text-2xl font-bold">{totalDomicilios}</div>
              </div>
              <div className="bg-green-50 rounded-lg border border-green-200 p-3">
                <div className="text-xs text-green-700">Geocodificados</div>
                <div className="text-2xl font-bold text-green-700">{geocodificados}</div>
              </div>
              <div className="bg-blue-50 rounded-lg border border-blue-200 p-3">
                <div className="text-xs text-blue-700">Con eventos</div>
                <div className="text-2xl font-bold text-blue-700">{conEventos}</div>
              </div>
              <div className="bg-yellow-50 rounded-lg border border-yellow-200 p-3">
                <div className="text-xs text-yellow-700">Pendientes</div>
                <div className="text-2xl font-bold text-yellow-700">{pendientes}</div>
              </div>
            </div>

            {/* Ordenar */}
            <div className="flex items-center gap-4">
              <label className="text-sm text-muted-foreground">Ordenar por:</label>
              <Select
                value={filters.order_by}
                onValueChange={(value) => handleFilterChange("order_by", value)}
              >
                <SelectTrigger className="w-[220px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="eventos_desc">Más eventos primero</SelectItem>
                  <SelectItem value="eventos_asc">Menos eventos primero</SelectItem>
                  <SelectItem value="calle_asc">Por calle (A-Z)</SelectItem>
                  <SelectItem value="localidad_asc">Por localidad (A-Z)</SelectItem>
                </SelectContent>
              </Select>

              <label className="text-sm text-muted-foreground ml-auto">Mostrar:</label>
              <Select
                value={filters.page_size.toString()}
                onValueChange={(value) => handleFilterChange("page_size", parseInt(value))}
              >
                <SelectTrigger className="w-[100px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="25">25</SelectItem>
                  <SelectItem value="50">50</SelectItem>
                  <SelectItem value="100">100</SelectItem>
                  <SelectItem value="200">200</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Table */}
          <div className="border border-border bg-background rounded-lg overflow-hidden">
            {isLoading ? (
              <div className="divide-y divide-border">
                {[...Array(10)].map((_, i) => (
                  <DomicilioRowSkeleton key={i} />
                ))}
              </div>
            ) : domicilios.length === 0 ? (
              <div className="p-12">
                <div className="text-center">
                  <Building2 className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
                  <h3 className="text-lg font-medium mb-2">No se encontraron domicilios</h3>
                  <p className="text-sm text-muted-foreground">Intenta ajustar los filtros</p>
                </div>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="border-b border-border bg-muted/50">
                    <tr>
                      <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3 col-span-5">Dirección</th>
                      <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3 col-span-2">Localidad</th>
                      <th className="text-center text-xs font-medium text-muted-foreground px-4 py-3 col-span-1">Eventos</th>
                      <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3 col-span-2">Estado</th>
                      <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3 col-span-2">Coordenadas</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {domicilios.map((domicilio) => (
                      <tr
                        key={domicilio.id}
                        className="group hover:bg-muted/50 cursor-pointer transition-colors"
                        onClick={() => handleViewDetail(domicilio)}
                      >
                        {/* Dirección */}
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2 min-w-0">
                            <MapPin className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                            <div className="min-w-0">
                              <p className="font-medium text-sm truncate max-w-[200px]">
                                {domicilio.calle && domicilio.numero
                                  ? `${domicilio.calle} ${domicilio.numero}`
                                  : domicilio.calle || "Sin calle"}
                              </p>
                              <p className="text-xs text-muted-foreground truncate">
                                {domicilio.provincia_nombre}
                              </p>
                            </div>
                          </div>
                        </td>

                        {/* Localidad */}
                        <td className="px-4 py-3 text-sm truncate max-w-[150px]">
                          {domicilio.localidad_nombre}
                        </td>

                        {/* Eventos */}
                        <td className="px-4 py-3 text-center">
                          {domicilio.total_eventos > 0 ? (
                            <Badge variant="default">{domicilio.total_eventos}</Badge>
                          ) : (
                            <span className="text-xs text-muted-foreground">0</span>
                          )}
                        </td>

                        {/* Estado */}
                        <td className="px-4 py-3">
                          <Badge
                            variant="outline"
                            className={`gap-1 ${getEstadoBadgeClasses(domicilio.estado_geocodificacion)}`}
                          >
                            {getEstadoIcon(domicilio.estado_geocodificacion)}
                            {getEstadoLabel(domicilio.estado_geocodificacion)}
                          </Badge>
                        </td>

                        {/* Coordenadas */}
                        <td className="px-4 py-3 text-xs text-muted-foreground font-mono">
                          {domicilio.latitud && domicilio.longitud
                            ? `${domicilio.latitud.toFixed(4)}, ${domicilio.longitud.toFixed(4)}`
                            : "N/A"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Pagination */}
            {!isLoading && domiciliosData?.data && domiciliosData.data.total_pages > 1 && (
              <div className="flex items-center justify-between border-t border-border px-4 py-3 bg-muted/30">
                <p className="text-xs text-muted-foreground">
                  Mostrando {(domiciliosData.data.page - 1) * filters.page_size + 1}-
                  {Math.min(domiciliosData.data.page * filters.page_size, domiciliosData.data.total)} de {domiciliosData.data.total}
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleFilterChange("page", filters.page - 1)}
                    disabled={filters.page === 1}
                  >
                    Anterior
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleFilterChange("page", filters.page + 1)}
                    disabled={filters.page >= domiciliosData.data.total_pages}
                  >
                    Siguiente
                  </Button>
                </div>
              </div>
            )}
          </div>
        </main>

        {/* Detail Sheet */}
        <DomicilioDetalleSheet
          open={detailSheetOpen}
          onOpenChange={setDetailSheetOpen}
          idDomicilio={selectedDomicilioId}
        />
      </SidebarInset>
    </SidebarProvider>
  );
}
