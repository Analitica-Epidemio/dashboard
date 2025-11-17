"use client";

import { useState } from "react";
import { useDebounce } from "use-debounce";
import { Download, Users, ChevronRight } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { AppSidebar } from "@/features/layout/components";

// Shared filter components
import { FilterToolbar, StatsBar, type StatItem } from "@/components/filters";

import { usePersonas, type PersonaFilters } from "@/features/personas/api";
import { PersonaFiltersAdvanced } from "@/features/personas/components/persona-filters";
import { PersonaDetailModern } from "@/features/personas/components/persona-detail-modern";
import type { components } from "@/lib/api/types";

export default function PersonasPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedSearch] = useDebounce(searchQuery, 300);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [detailSheetOpen, setDetailSheetOpen] = useState(false);
  const [selectedPersona, setSelectedPersona] = useState<{ tipo: string; id: number } | null>(null);

  const [filters, setFilters] = useState<PersonaFilters>({
    page: 1,
    page_size: 50,
    sort_by: "ultimo_evento_desc",
  });

  const handleFilterChange = (key: string, value: unknown) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value,
      page: 1, // Reset a primera página cuando cambian filtros
    }));
  };

  const personasQuery = usePersonas({
    ...filters,
    search: debouncedSearch || undefined,
  });

  const personasData = personasQuery.data;
  const personas = personasData?.data.data || [];
  const pagination = personasData?.data.pagination;
  const aggregatedStats = personasData?.data.stats;
  const isLoading = personasQuery.isLoading;

  const handleViewDetail = (persona: components["schemas"]["PersonaListItem"]) => {
    setSelectedPersona({ tipo: persona.tipo_sujeto, id: persona.persona_id });
    setDetailSheetOpen(true);
  };

  // Usar estadísticas agregadas del backend (calculadas sobre TODA la DB filtrada)
  const stats = {
    total: aggregatedStats?.total_personas || 0,
    conMultiplesEventos: aggregatedStats?.personas_con_multiples_eventos || 0,
    confirmados: aggregatedStats?.personas_con_confirmados || 0,
    activos: aggregatedStats?.personas_activas || 0,
  };

  // Preparar stats para StatsBar
  const statsItems: StatItem[] = [
    { id: "total", label: "Total", value: stats.total },
    { id: "multiples", label: "Múltiples eventos", value: stats.conMultiplesEventos, color: "text-orange-600" },
    { id: "confirmados", label: "Con confirmados", value: stats.confirmados, color: "text-red-600" },
    { id: "activos", label: "Activos", value: stats.activos, color: "text-green-600" },
  ];

  // Contar filtros activos (excluyendo page, page_size, sort_by)
  const activeFiltersCount = Object.entries(filters ?? {}).filter(
    ([key, value]) => value && !["page", "page_size", "sort_by"].includes(key)
  ).length;

  // Skeleton para carga de tabla
  const PersonaRowSkeleton = () => (
    <div className="px-4 py-3 flex items-center gap-4">
      <Skeleton className="h-4 w-48" />
      <Skeleton className="h-4 w-32" />
      <Skeleton className="h-4 w-16" />
      <Skeleton className="h-4 w-40" />
      <Skeleton className="h-6 w-20" />
      <Skeleton className="h-4 w-32" />
    </div>
  );

  return (
    <SidebarProvider>
      <AppSidebar variant="inset" />
      <SidebarInset>
        <header className="flex h-14 items-center gap-4 border-b bg-background px-6">
          <SidebarTrigger className="-ml-2" />
          <Separator orientation="vertical" className="h-6" />
          <h1 className="text-lg font-semibold">Personas</h1>
        </header>

        <main className="flex-1 p-6 overflow-y-scroll bg-muted/40">
          {/* Toolbar moderno con componentes compartidos */}
          <div className="mb-6">
            <FilterToolbar
              searchPlaceholder="Buscar por nombre o documento..."
              searchValue={searchQuery}
              onSearchChange={setSearchQuery}
              onFiltersClick={() => setFiltersOpen(!filtersOpen)}
              activeFiltersCount={activeFiltersCount}
              actions={[
                {
                  id: "export",
                  label: "Exportar",
                  icon: <Download className="h-4 w-4" />,
                  onClick: () => console.log("Exportar"),
                  hideOnMobile: true,
                },
              ]}
            >
              <StatsBar stats={statsItems} />
            </FilterToolbar>
          </div>


          {/* Lista de personas - Tabla moderna estilo eventos */}
          <div className="border border-border bg-background rounded-lg overflow-hidden">
            {isLoading ? (
              // Loading state
              <div className="divide-y divide-border">
                {[...Array(5)].map((_, i) => (
                  <PersonaRowSkeleton key={i} />
                ))}
              </div>
            ) : personas.length === 0 ? (
              // Empty state
              <div className="p-12">
                <div className="text-center">
                  <Users className="mx-auto h-12 w-12 text-muted-foreground opacity-50 mb-4" />
                  <h3 className="text-lg font-medium mb-2">No se encontraron personas</h3>
                  <p className="text-sm text-muted-foreground">
                    {debouncedSearch ? "Prueba con otros términos de búsqueda" : "No hay personas registradas"}
                  </p>
                </div>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="border-b border-border bg-muted/50">
                    <tr>
                      <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">Nombre</th>
                      <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">Documento</th>
                      <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">Edad</th>
                      <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">Ubicación</th>
                      <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">Eventos</th>
                      <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">Último Evento</th>
                      <th className="w-[40px]"></th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {personas.map((persona: components["schemas"]["PersonaListItem"]) => (
                      <tr
                        key={`${persona.tipo_sujeto}-${persona.persona_id}`}
                        onClick={() => handleViewDetail(persona)}
                        className="group hover:bg-muted/50 cursor-pointer transition-colors"
                      >
                        {/* Nombre */}
                        <td className="px-4 py-3">
                          <div className="flex flex-col gap-0.5">
                            <span className="text-sm font-medium truncate max-w-[200px]">
                              {persona.nombre_completo || "Sin identificar"}
                            </span>
                            {persona.tipo_sujeto === 'animal' && (
                              <span className="text-xs text-muted-foreground">Animal</span>
                            )}
                          </div>
                        </td>

                        {/* Documento */}
                        <td className="px-4 py-3 text-sm text-muted-foreground">
                          {persona.documento || "-"}
                        </td>

                        {/* Edad */}
                        <td className="px-4 py-3 text-sm text-muted-foreground">
                          {persona.edad_actual ? `${persona.edad_actual} años` : "-"}
                        </td>

                        {/* Ubicación */}
                        <td className="px-4 py-3 text-sm text-muted-foreground max-w-[150px] truncate">
                          {persona.provincia ? (
                            <>
                              {persona.localidad && `${persona.localidad}, `}
                              {persona.provincia}
                            </>
                          ) : (
                            "-"
                          )}
                        </td>

                        {/* Eventos */}
                        <td className="px-4 py-3">
                          <Badge variant={persona.total_eventos > 3 ? "destructive" : "secondary"}>
                            {persona.total_eventos} {persona.total_eventos === 1 ? 'evento' : 'eventos'}
                          </Badge>
                        </td>

                        {/* Último Evento */}
                        <td className="px-4 py-3 text-sm text-muted-foreground max-w-[200px] truncate">
                          {persona.ultimo_evento_tipo || "-"}
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
                    onClick={() => setFilters((prev) => ({ ...prev, page: pagination.page - 1 }))}
                    disabled={!pagination.has_prev}
                  >
                    Anterior
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setFilters((prev) => ({ ...prev, page: pagination.page + 1 }))}
                    disabled={!pagination.has_next}
                  >
                    Siguiente
                  </Button>
                </div>
              </div>
            )}
          </div>
        </main>
      </SidebarInset>

      {/* Sheet de filtros avanzados */}
      <Sheet open={filtersOpen} onOpenChange={setFiltersOpen}>
        <SheetContent className="w-full sm:max-w-2xl p-0 flex flex-col">
          <SheetHeader className="flex-shrink-0 border-b bg-background px-6 py-4">
            <SheetTitle className="text-lg font-semibold">Filtros Avanzados</SheetTitle>
          </SheetHeader>
          <div className="flex-1 overflow-y-auto px-6 py-6">
            <PersonaFiltersAdvanced
              filters={filters}
              onFilterChange={handleFilterChange}
              onClose={() => setFiltersOpen(false)}
            />
          </div>
        </SheetContent>
      </Sheet>

      {/* Sheet de detalle (Quick view - matching eventos style) */}
      <Sheet open={detailSheetOpen} onOpenChange={setDetailSheetOpen}>
        <SheetContent className="w-full overflow-y-auto sm:max-w-3xl lg:max-w-5xl p-0">
          <SheetHeader className="sticky top-0 z-10 border-b bg-background/95 backdrop-blur p-4">
            <SheetTitle className="text-lg">
              Persona {selectedPersona?.tipo}/{selectedPersona?.id}
            </SheetTitle>
          </SheetHeader>
          {selectedPersona && (
            <PersonaDetailModern
              tipoSujeto={selectedPersona.tipo as "humano" | "animal"}
              personaId={selectedPersona.id}
              onClose={() => setDetailSheetOpen(false)}
            />
          )}
        </SheetContent>
      </Sheet>
    </SidebarProvider>
  );
}
