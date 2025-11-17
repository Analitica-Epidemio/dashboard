"use client";

import { useState } from "react";
import {
  Building2,
  MapPin,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { AppSidebar } from "@/features/layout/components";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import { useEstablecimientos } from "@/features/establecimientos/api";
import type { EstablecimientoListItem } from "@/features/establecimientos/api";
import { EstablecimientoDetalleSheet } from "@/features/establecimientos/components/establecimiento-detalle-sheet";

export default function EstablecimientosPage() {
  const [detailSheetOpen, setDetailSheetOpen] = useState(false);
  const [selectedEstablecimientoId, setSelectedEstablecimientoId] = useState<number | null>(
    null
  );

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

  const establecimientosQuery = useEstablecimientos(filters);

  const establecimientosData = establecimientosQuery.data;
  const establecimientos = establecimientosData?.data?.items || [];
  const isLoading = establecimientosQuery.isLoading;

  const handleViewDetail = (establecimiento: EstablecimientoListItem) => {
    setSelectedEstablecimientoId(establecimiento.id);
    setDetailSheetOpen(true);
  };

  // Calcular estadísticas
  const totalEstablecimientos = establecimientosData?.data?.total || 0;
  const conEventos = establecimientos.filter((e) => e.total_eventos > 0).length;
  const deIGN = establecimientos.filter((e) => e.source === "IGN").length;
  const deSNVS = establecimientos.filter((e) => e.source === "SNVS").length;

  // Skeleton para carga de tabla
  const EstablecimientoRowSkeleton = () => (
    <div className="px-4 py-3 flex items-center gap-4">
      <Skeleton className="h-4 w-64" />
      <Skeleton className="h-4 w-32" />
      <Skeleton className="h-4 w-16" />
      <Skeleton className="h-6 w-24" />
      <Skeleton className="h-4 w-32" />
    </div>
  );

  return (
    <SidebarProvider>
      <AppSidebar variant="inset" />
      <SidebarInset>
        {/* Header */}
        <header className="flex h-14 items-center gap-4 border-b bg-background px-6">
          <SidebarTrigger className="-ml-2" />
          <Separator orientation="vertical" className="h-6" />
          <h1 className="text-lg font-semibold">Establecimientos</h1>
        </header>

        {/* Main Content */}
        <main className="flex-1 p-6 overflow-y-scroll bg-muted/40">
          {/* Stats and Filters */}
          <div className="mb-6">
            {/* Stats */}
            <div className="grid grid-cols-4 gap-4 mb-4">
              <div className="bg-white rounded-lg border p-3">
                <div className="text-xs text-muted-foreground">Total</div>
                <div className="text-2xl font-bold">{totalEstablecimientos}</div>
              </div>
              <div className="bg-blue-50 rounded-lg border border-blue-200 p-3">
                <div className="text-xs text-blue-700">Con eventos</div>
                <div className="text-2xl font-bold text-blue-700">
                  {conEventos}
                </div>
              </div>
              <div className="bg-green-50 rounded-lg border border-green-200 p-3">
                <div className="text-xs text-green-700">IGN</div>
                <div className="text-2xl font-bold text-green-700">
                  {deIGN}
                </div>
              </div>
              <div className="bg-purple-50 rounded-lg border border-purple-200 p-3">
                <div className="text-xs text-purple-700">SNVS</div>
                <div className="text-2xl font-bold text-purple-700">
                  {deSNVS}
                </div>
              </div>
            </div>

            {/* Ordenar */}
            <div className="flex items-center gap-4">
              <label className="text-sm text-muted-foreground">
                Ordenar por:
              </label>
              <Select
                value={filters.order_by}
                onValueChange={(value) => handleFilterChange("order_by", value)}
              >
                <SelectTrigger className="w-[220px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="eventos_desc">
                    Más eventos primero
                  </SelectItem>
                  <SelectItem value="eventos_asc">
                    Menos eventos primero
                  </SelectItem>
                  <SelectItem value="nombre_asc">Por nombre (A-Z)</SelectItem>
                  <SelectItem value="source_asc">Por fuente</SelectItem>
                </SelectContent>
              </Select>

              <label className="text-sm text-muted-foreground ml-auto">
                Mostrar:
              </label>
              <Select
                value={filters.page_size.toString()}
                onValueChange={(value) =>
                  handleFilterChange("page_size", parseInt(value))
                }
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
                  <EstablecimientoRowSkeleton key={i} />
                ))}
              </div>
            ) : establecimientos.length === 0 ? (
              <div className="p-12">
                <div className="text-center">
                  <Building2 className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
                  <h3 className="text-lg font-medium mb-2">
                    No se encontraron establecimientos
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    Intenta ajustar los filtros
                  </p>
                </div>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="border-b border-border bg-muted/50">
                    <tr>
                      <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">
                        Nombre
                      </th>
                      <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">
                        Códigos
                      </th>
                      <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">
                        Localidad
                      </th>
                      <th className="text-center text-xs font-medium text-muted-foreground px-4 py-3">
                        Eventos
                      </th>
                      <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">
                        Fuente
                      </th>
                      <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">
                        Coordenadas
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {establecimientos.map((establecimiento) => (
                      <tr
                        key={establecimiento.id}
                        className="group hover:bg-muted/50 cursor-pointer transition-colors"
                        onClick={() => handleViewDetail(establecimiento)}
                      >
                        {/* Nombre */}
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2 min-w-0">
                            <Building2 className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                            <div className="min-w-0">
                              <p className="font-medium text-sm truncate max-w-[250px]">
                                {establecimiento.nombre}
                              </p>
                              {establecimiento.provincia_nombre && (
                                <p className="text-xs text-muted-foreground truncate">
                                  {establecimiento.provincia_nombre}
                                </p>
                              )}
                            </div>
                          </div>
                        </td>

                        {/* Códigos */}
                        <td className="px-4 py-3">
                          <div className="text-xs space-y-1">
                            {establecimiento.codigo_refes && (
                              <div className="font-mono text-gray-600">
                                REFES: {establecimiento.codigo_refes}
                              </div>
                            )}
                            {establecimiento.codigo_snvs && (
                              <div className="font-mono text-gray-600">
                                SNVS: {establecimiento.codigo_snvs}
                              </div>
                            )}
                            {!establecimiento.codigo_refes && !establecimiento.codigo_snvs && (
                              <span className="text-muted-foreground">N/A</span>
                            )}
                          </div>
                        </td>

                        {/* Localidad */}
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-1">
                            <MapPin className="h-3 w-3 text-muted-foreground" />
                            <span className="text-sm truncate max-w-[150px]">
                              {establecimiento.localidad_nombre || "N/A"}
                            </span>
                          </div>
                        </td>

                        {/* Eventos */}
                        <td className="px-4 py-3 text-center">
                          {establecimiento.total_eventos > 0 ? (
                            <Badge variant="default">
                              {establecimiento.total_eventos}
                            </Badge>
                          ) : (
                            <span className="text-xs text-muted-foreground">
                              0
                            </span>
                          )}
                        </td>

                        {/* Fuente */}
                        <td className="px-4 py-3">
                          <Badge
                            variant="outline"
                            className={
                              establecimiento.source === "IGN"
                                ? "bg-green-100 text-green-700 border-green-200"
                                : establecimiento.source === "SNVS"
                                ? "bg-purple-100 text-purple-700 border-purple-200"
                                : "bg-gray-100 text-gray-700 border-gray-200"
                            }
                          >
                            {establecimiento.source || "N/A"}
                          </Badge>
                        </td>

                        {/* Coordenadas */}
                        <td className="px-4 py-3 text-xs text-muted-foreground font-mono">
                          {establecimiento.latitud && establecimiento.longitud
                            ? `${establecimiento.latitud.toFixed(
                                4
                              )}, ${establecimiento.longitud.toFixed(4)}`
                            : "N/A"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Pagination */}
            {!isLoading &&
              establecimientosData?.data &&
              establecimientosData.data.total_pages > 1 && (
                <div className="flex items-center justify-between border-t border-border px-4 py-3 bg-muted/30">
                  <p className="text-xs text-muted-foreground">
                    Mostrando{" "}
                    {(establecimientosData.data.page - 1) * filters.page_size + 1}-
                    {Math.min(
                      establecimientosData.data.page * filters.page_size,
                      establecimientosData.data.total
                    )}{" "}
                    de {establecimientosData.data.total}
                  </p>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() =>
                        handleFilterChange("page", filters.page - 1)
                      }
                      disabled={filters.page === 1}
                    >
                      Anterior
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() =>
                        handleFilterChange("page", filters.page + 1)
                      }
                      disabled={filters.page >= establecimientosData.data.total_pages}
                    >
                      Siguiente
                    </Button>
                  </div>
                </div>
              )}
          </div>
        </main>

        {/* Detail Sheet */}
        <EstablecimientoDetalleSheet
          open={detailSheetOpen}
          onOpenChange={setDetailSheetOpen}
          idEstablecimiento={selectedEstablecimientoId}
        />
      </SidebarInset>
    </SidebarProvider>
  );
}
