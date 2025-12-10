"use client";

import { useState, useEffect } from "react";
import { useDebounce } from "use-debounce";
import {
  Download,
  ChevronRight,
  AlertTriangle,
  FileText,
} from "lucide-react";

// UI Components
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { AppSidebar } from "@/features/layout/components";
import { TooltipProvider } from "@/components/ui/tooltip";

// Shared filter components
import { FilterToolbar, StatsBar, type StatItem } from "@/components/filters";

// API y tipos
import {
  useEventos,
  getClasificacionLabel,
  getClasificacionColorClasses,
  type EventoFilters,
} from "@/features/eventos/api";

// Componentes
import { EventoDetailModern } from "@/features/eventos/components/evento-detail-modern";
import { EventoFiltersModern } from "@/features/eventos/components/evento-filters-modern";

export default function EventosPage() {
  // Estados de filtros y búsqueda
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedSearch] = useDebounce(searchQuery, 300);
  const [filters, setFilters] = useState<EventoFilters>({
    page: 1,
    page_size: 50,
    sort_by: "fecha_desc",
  });

  // Estado para Sheet de detalle
  const [selectedEventoId, setSelectedEventoId] = useState<number | null>(null);
  const [detailSheetOpen, setDetailSheetOpen] = useState(false);
  const [filtersOpen, setFiltersOpen] = useState(false);

  // Reset page to 1 when search query changes
  useEffect(() => {
    setFilters((prev) => ({ ...prev, page: 1 }));
  }, [debouncedSearch]);

  // Query de eventos
  const eventosQuery = useEventos({
    ...filters,
    search: debouncedSearch || undefined,
  });

  const eventosData = eventosQuery.data;
  const eventos = eventosData?.data.data || [];
  const pagination = eventosData?.data.pagination;
  const stats = eventosData?.data.stats;
  const isLoading = eventosQuery.isLoading;
  const error = eventosQuery.error;

  // Handlers
  const handleViewDetalle = (eventoId: number) => {
    setSelectedEventoId(eventoId);
    setDetailSheetOpen(true);
  };

  const handlePageChange = (newPage: number) => {
    setFilters((prev) => ({ ...prev, page: newPage }));
  };

  const handleFilterChange = (key: string, value: unknown) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value,
      page: 1, // Reset a primera página cuando cambian filtros
    }));
  };

  const handleExport = async () => {
    // TODO: Implementar exportación
    console.log("Exportando eventos...");
  };

  // Preparar stats para StatsBar
  const statsItems: StatItem[] = stats ? [
    { id: "total", label: "Total", value: stats.total || 0 },
    { id: "confirmados", label: "Confirmados", value: stats.confirmados || 0, color: "text-red-600" },
    { id: "sospechosos", label: "Sospechosos", value: stats.sospechosos || 0, color: "text-yellow-600" },
    { id: "probables", label: "Probables", value: stats.probables || 0, color: "text-orange-600" },
    { id: "en_estudio", label: "En Estudio", value: stats.en_estudio || 0, color: "text-blue-600" },
    { id: "negativos", label: "Negativos", value: stats.negativos || 0, color: "text-green-600" },
    { id: "descartados", label: "Descartados", value: stats.descartados || 0, color: "text-gray-600" },
    ...(stats.requiere_revision ? [{ id: "requiere_revision", label: "Requiere Revisión", value: stats.requiere_revision, color: "text-purple-600" }] : []),
    ...(stats.sin_clasificar ? [{ id: "sin_clasificar", label: "Sin Clasificar", value: stats.sin_clasificar, color: "text-muted-foreground" }] : []),
  ] : [];

  // Contar filtros activos (excluyendo page, page_size, sort_by)
  const activeFiltersCount = Object.entries(filters ?? {}).filter(
    ([key, value]) => value && !["page", "page_size", "sort_by"].includes(key)
  ).length;

  // Skeleton para carga de tabla
  const EventoRowSkeleton = () => (
    <div className="px-4 py-3 flex items-center gap-4">
      <Skeleton className="h-4 w-12" />
      <Skeleton className="h-4 w-40" />
      <Skeleton className="h-4 w-32" />
      <Skeleton className="h-4 w-24" />
      <Skeleton className="h-6 w-20" />
      <Skeleton className="h-4 w-32" />
      <Skeleton className="h-4 w-16" />
    </div>
  );

  return (
    <TooltipProvider>
      <SidebarProvider>
        <AppSidebar variant="inset" />
        <SidebarInset>
          {/* Header */}
          <header className="flex h-14 items-center gap-4 border-b bg-background px-6">
            <SidebarTrigger className="-ml-2" />
            <Separator orientation="vertical" className="h-6" />
            <h1 className="text-lg font-semibold">Eventos</h1>
          </header>

          {/* Main Content */}
          <main className="flex-1 p-6 overflow-y-scroll bg-muted/40">
            {/* Toolbar moderno con componentes compartidos */}
            <div className="mb-6">
              <FilterToolbar
                searchPlaceholder="Buscar por nombre, DNI o ID de evento..."
                searchValue={searchQuery}
                onSearchChange={setSearchQuery}
                onFiltersClick={() => setFiltersOpen(!filtersOpen)}
                activeFiltersCount={activeFiltersCount}
                actions={[
                  {
                    id: "export",
                    label: "Exportar",
                    icon: <Download className="h-4 w-4" />,
                    onClick: handleExport,
                    hideOnMobile: true,
                  },
                ]}
              >
                <StatsBar stats={statsItems} />
              </FilterToolbar>
            </div>


            {/* Error State */}
            {error && (
              <Alert variant="destructive" className="mb-6">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  <strong>Error al cargar eventos.</strong> Por favor, recarga
                  la página o contacta soporte.
                </AlertDescription>
              </Alert>
            )}

            {/* Lista de eventos - Table moderna estilo Linear/GitHub */}
            {!error && (
              <div className="border border-border bg-background rounded-lg overflow-hidden">
                {isLoading ? (
                  // Loading state
                  <div className="divide-y divide-border">
                    {[...Array(5)].map((_, i) => (
                      <EventoRowSkeleton key={i} />
                    ))}
                  </div>
                ) : eventos.length === 0 ? (
                  // Empty state
                  <div className="p-12">
                    <div className="text-center">
                      <FileText className="mx-auto h-12 w-12 text-muted-foreground opacity-50 mb-4" />
                      <h3 className="text-lg font-medium mb-2">
                        No se encontraron eventos
                      </h3>
                      <p className="text-sm text-muted-foreground">
                        {debouncedSearch ||
                          Object.values(filters ?? {}).some((v) => v)
                          ? "Prueba con otros filtros o términos de búsqueda"
                          : "No hay eventos registrados aún"}
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="border-b border-border bg-muted/50">
                        <tr>
                          <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3 w-[50px]">ID</th>
                          <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">Persona</th>
                          <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">Tipo ENO</th>
                          <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">Fecha</th>
                          <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">Clasificación</th>
                          <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">Ubicación</th>
                          <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3 w-[100px]">Estado</th>
                          <th className="w-[40px]"></th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border">
                        {eventos.map((evento) => (
                          <tr
                            key={evento.id}
                            onClick={() => handleViewDetalle(evento.id)}
                            className="group hover:bg-muted/50 cursor-pointer transition-colors"
                          >
                            {/* ID */}
                            <td className="px-4 py-3 text-sm text-muted-foreground font-mono">
                              #{evento.id_evento_caso}
                            </td>

                            {/* Persona */}
                            <td className="px-4 py-3">
                              <div className="flex flex-col gap-0.5">
                                <span className="text-sm font-medium truncate max-w-[200px]">
                                  {evento.nombre_sujeto || "Sin identificar"}
                                </span>
                                {evento.documento_sujeto && (
                                  <span className="text-xs text-muted-foreground">
                                    DNI {evento.documento_sujeto}
                                  </span>
                                )}
                              </div>
                            </td>

                            {/* Tipo ENO */}
                            <td className="px-4 py-3 text-sm max-w-[200px] truncate">
                              {evento.tipo_eno_nombre || "-"}
                            </td>

                            {/* Fecha */}
                            <td className="px-4 py-3 whitespace-nowrap">
                              <div className="flex flex-col gap-0.5">
                                <span className="text-sm text-foreground">
                                  {evento.fecha_minima_caso ? (
                                    new Date(evento.fecha_minima_caso).toLocaleDateString("es-ES", {
                                      day: "2-digit",
                                      month: "short",
                                      year: "numeric"
                                    })
                                  ) : (
                                    <span className="text-muted-foreground">Sin fecha</span>
                                  )}
                                </span>
                                {evento.semana_epidemiologica_apertura && evento.anio_epidemiologico_apertura && (
                                  <span className="text-xs text-muted-foreground">
                                    SE {evento.semana_epidemiologica_apertura}/{evento.anio_epidemiologico_apertura}
                                  </span>
                                )}
                              </div>
                            </td>

                            {/* Clasificación */}
                            <td className="px-4 py-3">
                              {evento.clasificacion_estrategia ? (
                                <span
                                  className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium border ${getClasificacionColorClasses(evento.clasificacion_estrategia)}`}
                                >
                                  {getClasificacionLabel(evento.clasificacion_estrategia)}
                                </span>
                              ) : (
                                <span className="text-xs text-muted-foreground">Sin clasificar</span>
                              )}
                            </td>

                            {/* Ubicación */}
                            <td className="px-4 py-3 text-sm text-muted-foreground max-w-[150px] truncate">
                              {evento.provincia ? (
                                <>
                                  {evento.provincia}
                                  {evento.localidad && `, ${evento.localidad}`}
                                </>
                              ) : (
                                "-"
                              )}
                            </td>

                            {/* Estado */}
                            <td className="px-4 py-3">
                              <div className="flex items-center gap-1.5">
                                {evento.requiere_revision_especie && (
                                  <div className="h-2 w-2 rounded-full bg-red-500" title="Requiere revisión" />
                                )}
                                {evento.es_caso_sintomatico && (
                                  <div className="h-2 w-2 rounded-full bg-yellow-500" title="Sintomático" />
                                )}
                              </div>
                            </td>

                            {/* Chevron */}
                            <td className="px-4 py-3">
                              <ChevronRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* Paginación */}
                {!isLoading && pagination && pagination.total_pages > 1 && (
                  <div className="flex items-center justify-between border-t border-border px-4 py-3 bg-muted/30">
                    <p className="text-xs text-muted-foreground">
                      Mostrando {(pagination.page - 1) * pagination.page_size + 1}-
                      {Math.min(pagination.page * pagination.page_size, pagination.total)} de {pagination.total}
                    </p>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handlePageChange(pagination.page - 1)}
                        disabled={!pagination.has_prev}
                      >
                        Anterior
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handlePageChange(pagination.page + 1)}
                        disabled={!pagination.has_next}
                      >
                        Siguiente
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </main>
        </SidebarInset>

        {/* Sheet de detalle (Quick view - Linear/GitHub style) */}
        <Sheet open={detailSheetOpen} onOpenChange={setDetailSheetOpen}>
          <SheetContent className="w-full overflow-y-auto sm:max-w-3xl lg:max-w-5xl p-0">
            <SheetHeader className="sticky top-0 z-10 border-b bg-background/95 backdrop-blur p-4">
              <SheetTitle className="text-lg">
                Evento #{selectedEventoId}
              </SheetTitle>
              <p className="text-xs text-muted-foreground mt-1">
                Presiona <kbd className="px-1.5 py-0.5 bg-muted rounded text-xs">ESC</kbd> para cerrar
              </p>
            </SheetHeader>
            {selectedEventoId && (
              <EventoDetailModern
                eventoId={selectedEventoId}
                onClose={() => setDetailSheetOpen(false)}
              />
            )}
          </SheetContent>
        </Sheet>

        {/* Sheet de filtros modernos */}
        <Sheet open={filtersOpen} onOpenChange={setFiltersOpen}>
          <SheetContent className="w-full sm:max-w-2xl p-0 flex flex-col">
            <SheetHeader className="flex-shrink-0 border-b bg-background px-6 py-4">
              <SheetTitle className="text-lg font-semibold">Filtros Avanzados</SheetTitle>
            </SheetHeader>
            <div className="flex-1 overflow-y-auto px-6 py-6">
              <EventoFiltersModern
                filters={filters}
                onFilterChange={handleFilterChange}
                onClose={() => setFiltersOpen(false)}
              />
            </div>
          </SheetContent>
        </Sheet>
      </SidebarProvider>
    </TooltipProvider>
  );
}
