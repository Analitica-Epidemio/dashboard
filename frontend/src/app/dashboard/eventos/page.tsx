"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useDebounce } from "use-debounce";
import {
  Search,
  Filter,
  Calendar,
  Download,
  ChevronRight,
  Info,
  AlertTriangle,
  Eye,
  Clock,
  MapPin,
  Hash,
  User,
  Activity,
  TrendingUp,
  AlertCircle,
  FileText,
} from "lucide-react";

// UI Components
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
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
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

// API y tipos
import {
  useEventos,
  extractEventosData,
  getClasificacionLabel,
  getClasificacionVariant,
  getClasificacionEstrategiaColor,
  getTipoSujetoIcon,
  type EventoFilters,
} from "@/lib/api/eventos";
import type { components } from "@/lib/api/types";
import { TipoClasificacion } from "@/lib/types/clasificacion";

// Componentes
import { EventoDetail } from "./_components/evento-detail";
import { EventoFiltersPanel } from "./_components/evento-filters";
import { useMediaQuery } from "@/hooks/use-mobile";

export default function EventosPage() {
  const router = useRouter();
  const isMobile = useMediaQuery("(max-width: 768px)");

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
  const isLoading = eventosQuery.isLoading;
  const error = eventosQuery.error;

  // Handlers
  const handleViewDetalle = (eventoId: number) => {
    if (isMobile) {
      router.push(`/eventos/${eventoId}`);
    } else {
      setSelectedEventoId(eventoId);
      setDetailSheetOpen(true);
    }
  };

  const handlePageChange = (newPage: number) => {
    setFilters((prev) => ({ ...prev, page: newPage }));
  };

  const handleFilterChange = (key: string, value) => {
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

  // Calcular estadísticas rápidas
  const stats = {
    total: pagination?.total || 0,
    confirmados: eventos.filter(
      (e) =>
        e.clasificacion_estrategia === TipoClasificacion.CONFIRMADOS ||
        e.clasificacion === "confirmados"
    ).length,
    sospechosos: eventos.filter(
      (e) =>
        e.clasificacion_estrategia === TipoClasificacion.SOSPECHOSOS ||
        e.clasificacion === "sospechosos"
    ).length,
    requiereRevision: eventos.filter(
      (e) => e.clasificacion_estrategia === TipoClasificacion.REQUIERE_REVISION
    ).length,
    sinClasificar: eventos.filter(
      (e) => !e.clasificacion_estrategia && !e.clasificacion
    ).length,
  };

  // Skeleton para carga
  const EventoCardSkeleton = () => (
    <Card className="p-4">
      <div className="space-y-3">
        <div className="flex justify-between items-start">
          <Skeleton className="h-5 w-32" />
          <Skeleton className="h-6 w-20" />
        </div>
        <div className="space-y-2">
          <Skeleton className="h-4 w-48" />
          <Skeleton className="h-4 w-36" />
        </div>
        <div className="flex gap-2">
          <Skeleton className="h-5 w-16" />
          <Skeleton className="h-5 w-24" />
        </div>
      </div>
    </Card>
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
            <div className="flex flex-1 items-center justify-between">
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-semibold">
                  Eventos Epidemiológicos
                </h1>
                <Badge variant="secondary" className="ml-2">
                  {stats.total} eventos
                </Badge>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setFiltersOpen(!filtersOpen)}
                >
                  <Filter className="mr-2 h-4 w-4" />
                  Filtros
                </Button>
                <Button variant="outline" size="sm" onClick={handleExport}>
                  <Download className="mr-2 h-4 w-4" />
                  <span className="hidden sm:inline">Exportar</span>
                </Button>
              </div>
            </div>
          </header>

          {/* Main Content */}
          <main className="flex-1 p-6">
            {/* Info Banner */}
            <Alert className="mb-6 border-blue-200 bg-blue-50/50 dark:border-blue-900 dark:bg-blue-950/20">
              <Info className="h-4 w-4 text-blue-600 dark:text-blue-400" />
              <AlertDescription className="text-sm">
                <strong>Vista de Eventos Epidemiológicos</strong> - Aquí puedes
                ver todos los eventos procesados, filtrar por tipo, fecha,
                clasificación y más. Haz clic en un evento para ver su
                información completa.
              </AlertDescription>
            </Alert>

            {/* Estadísticas rápidas */}
            <div className="grid gap-4 md:grid-cols-4 mb-6">
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">
                        Total Eventos
                      </p>
                      <p className="text-2xl font-bold">{stats.total}</p>
                    </div>
                    <Activity className="h-8 w-8 text-muted-foreground opacity-50" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">
                        Confirmados
                      </p>
                      <p className="text-2xl font-bold text-green-600">
                        {stats.confirmados}
                      </p>
                    </div>
                    <TrendingUp className="h-8 w-8 text-green-600 opacity-50" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">
                        Sospechosos
                      </p>
                      <p className="text-2xl font-bold text-yellow-600">
                        {stats.sospechosos}
                      </p>
                    </div>
                    <AlertCircle className="h-8 w-8 text-yellow-600 opacity-50" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">
                        Requiere Revisión
                      </p>
                      <p className="text-2xl font-bold text-red-600">
                        {stats.requiereRevision}
                      </p>
                    </div>
                    <AlertTriangle className="h-8 w-8 text-red-600 opacity-50" />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Barra de búsqueda */}
            <div className="mb-6">
              <div className="relative max-w-md">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Buscar por ID, nombre o documento..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9"
                />
              </div>
            </div>

            {/* Panel de filtros (cuando está abierto) */}
            {filtersOpen && (
              <Card className="mb-6">
                <CardContent className="p-4">
                  <EventoFiltersPanel
                    filters={filters}
                    onFilterChange={handleFilterChange}
                    onClose={() => setFiltersOpen(false)}
                  />
                </CardContent>
              </Card>
            )}

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

            {/* Lista de eventos */}
            {!error && (
              <div className="space-y-4">
                {isLoading ? (
                  // Loading state
                  <>
                    <EventoCardSkeleton />
                    <EventoCardSkeleton />
                    <EventoCardSkeleton />
                  </>
                ) : eventos.length === 0 ? (
                  // Empty state
                  <Card className="p-12">
                    <div className="text-center">
                      <FileText className="mx-auto h-12 w-12 text-muted-foreground opacity-50 mb-4" />
                      <h3 className="text-lg font-medium mb-2">
                        No se encontraron eventos
                      </h3>
                      <p className="text-sm text-muted-foreground">
                        {debouncedSearch ||
                        Object.values(filters).some((v) => v)
                          ? "Prueba con otros filtros o términos de búsqueda"
                          : "No hay eventos registrados aún"}
                      </p>
                    </div>
                  </Card>
                ) : (
                  // Lista de eventos
                  eventos.map((evento) => (
                    <Card
                      key={evento.id}
                      className="p-4 hover:bg-muted/30 transition-colors cursor-pointer"
                      onClick={() => handleViewDetalle(evento.id)}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1 space-y-2">
                          {/* Header del evento */}
                          <div className="flex items-start justify-between">
                            <div>
                              <div className="flex items-center gap-2">
                                <span className="text-lg font-medium">
                                  {getTipoSujetoIcon(evento.tipo_sujeto)}{" "}
                                  {evento.nombre_sujeto || "Sin identificar"}
                                </span>
                                {evento.clasificacion_estrategia && (
                                  <span
                                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getClasificacionEstrategiaColor(
                                      evento.clasificacion_estrategia
                                    )}`}
                                  >
                                    {getClasificacionLabel(
                                      evento.clasificacion_estrategia
                                    )}
                                  </span>
                                )}
                                {evento.clasificacion && (
                                  <Badge
                                    variant={getClasificacionVariant(
                                      evento.clasificacion
                                    )}
                                  >
                                    {getClasificacionLabel(
                                      evento.clasificacion
                                    )}
                                  </Badge>
                                )}
                              </div>
                              <div className="flex items-center gap-4 mt-1 text-sm text-muted-foreground">
                                <span className="flex items-center gap-1">
                                  <Hash className="h-3 w-3" />
                                  {evento.id_evento_caso}
                                </span>
                                <span className="flex items-center gap-1">
                                  <Calendar className="h-3 w-3" />
                                  {new Date(
                                    evento.fecha_minima_evento
                                  ).toLocaleDateString("es-ES")}
                                </span>
                                {evento.tipo_eno_nombre && (
                                  <span className="flex items-center gap-1">
                                    <Activity className="h-3 w-3" />
                                    {evento.tipo_eno_nombre}
                                  </span>
                                )}
                              </div>
                            </div>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleViewDetalle(evento.id);
                              }}
                            >
                              Ver detalle
                              <ChevronRight className="ml-1 h-4 w-4" />
                            </Button>
                          </div>

                          {/* Información adicional */}
                          <div className="flex flex-wrap gap-4 text-sm">
                            {evento.provincia && (
                              <span className="flex items-center gap-1 text-muted-foreground">
                                <MapPin className="h-3 w-3" />
                                {evento.provincia}
                                {evento.localidad && `, ${evento.localidad}`}
                              </span>
                            )}
                            {evento.edad && (
                              <span className="flex items-center gap-1 text-muted-foreground">
                                <User className="h-3 w-3" />
                                {evento.edad} años
                              </span>
                            )}
                            {evento.documento_sujeto && (
                              <span className="flex items-center gap-1 text-muted-foreground">
                                <FileText className="h-3 w-3" />
                                DNI: {evento.documento_sujeto}
                              </span>
                            )}
                          </div>

                          {/* Badges de estado */}
                          <div className="flex flex-wrap gap-2">
                            {evento.es_caso_sintomatico && (
                              <Badge variant="outline" className="text-xs">
                                Sintomático
                              </Badge>
                            )}
                            {evento.requiere_revision_especie && (
                              <Badge variant="destructive" className="text-xs">
                                Requiere Revisión
                              </Badge>
                            )}
                            {evento.confidence_score && (
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <Badge
                                    variant="secondary"
                                    className="text-xs"
                                  >
                                    Confianza:{" "}
                                    {(evento.confidence_score * 100).toFixed(0)}
                                    %
                                  </Badge>
                                </TooltipTrigger>
                                <TooltipContent>
                                  <p>
                                    Nivel de confianza de la clasificación
                                    automática
                                  </p>
                                </TooltipContent>
                              </Tooltip>
                            )}
                          </div>
                        </div>
                      </div>
                    </Card>
                  ))
                )}

                {/* Paginación */}
                {pagination && pagination.total_pages > 1 && (
                  <div className="flex items-center justify-between pt-4">
                    <p className="text-sm text-muted-foreground">
                      Mostrando{" "}
                      {(pagination.page - 1) * pagination.page_size + 1} -{" "}
                      {Math.min(
                        pagination.page * pagination.page_size,
                        pagination.total
                      )}{" "}
                      de {pagination.total} eventos
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

        {/* Sheet de detalle */}
        <Sheet open={detailSheetOpen} onOpenChange={setDetailSheetOpen}>
          <SheetContent className="w-full overflow-y-auto sm:max-w-3xl lg:max-w-5xl p-0">
            <SheetHeader className="sr-only">
              <SheetTitle>Detalle del Evento Epidemiológico</SheetTitle>
            </SheetHeader>
            {selectedEventoId && (
              <div className="p-6">
                <EventoDetail
                  eventoId={selectedEventoId}
                  onClose={() => setDetailSheetOpen(false)}
                />
              </div>
            )}
          </SheetContent>
        </Sheet>
      </SidebarProvider>
    </TooltipProvider>
  );
}
