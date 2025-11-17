"use client";

import { useState, useMemo } from "react";
import { useDebounce } from "use-debounce";
import {
  Plus,
  ChevronRight,
  ChevronDown,
  Edit,
  Eye,
  CheckCircle2,
  AlertTriangle,
  Calendar,
  MoreHorizontal,
  Sparkles,
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AppSidebar } from "@/features/layout/components";
import { FilterToolbar, StatsBar, type StatItem } from "@/components/filters";

import {
  useEstrategias,
  useEliminarEstrategia,
  type EventStrategy,
} from "@/features/estrategias/api";
import { StrategyPreview } from "@/features/estrategias/components/strategy-preview";
import { StrategyForm } from "@/features/estrategias/components/strategy-form";

// Tipo para agrupar estrategias por evento
interface EventStrategiesGroup {
  tipo_eno_id: number;
  tipo_eno_name: string;
  strategies: EventStrategy[];
  hasActive: boolean;
  totalRules: number;
}

export default function EstrategiasPageNew() {
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedSearch] = useDebounce(searchQuery, 300);
  const [filterStatus] = useState<"all" | "active" | "inactive">("all");

  const [page, setPage] = useState(1);
  const pageSize = 50;

  const [selectedStrategy, setSelectedStrategy] = useState<EventStrategy | null>(null);
  const [viewSheetOpen, setViewSheetOpen] = useState(false);
  const [editSheetOpen, setEditSheetOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [strategyToDelete, setStrategyToDelete] = useState<EventStrategy | null>(null);

  // Estado para controlar qué acordeones están abiertos
  const [openGroups, setOpenGroups] = useState<Set<number>>(new Set());

  // API Query con paginación
  const strategiesQuery = useEstrategias({
    page,
    page_size: pageSize,
    active_only: filterStatus === "active" ? true : filterStatus === "inactive" ? false : undefined,
  });

  const deleteStrategyMutation = useEliminarEstrategia();

  const strategiesData = useMemo(() => strategiesQuery.data?.data || [], [strategiesQuery.data]);
  const pagination = strategiesQuery.data?.meta;
  const isLoading = strategiesQuery.isLoading;
  const error = strategiesQuery.error;

  // Agrupar estrategias por tipo_eno_id
  const groupedStrategies = useMemo(() => {
    const groups = new Map<number, EventStrategiesGroup>();

    // Filtrar por búsqueda primero
    const filteredStrats = strategiesData.filter((s: EventStrategy) => {
      const matchesSearch =
        s.name.toLowerCase().includes(debouncedSearch.toLowerCase()) ||
        s.tipo_eno_name?.toLowerCase().includes(debouncedSearch.toLowerCase());
      return matchesSearch;
    });

    filteredStrats.forEach((strategy: EventStrategy) => {
      const key = strategy.tipo_eno_id;
      if (!groups.has(key)) {
        groups.set(key, {
          tipo_eno_id: key,
          tipo_eno_name: strategy.tipo_eno_name || `Evento ${key}`,
          strategies: [],
          hasActive: false,
          totalRules: 0,
        });
      }

      const group = groups.get(key)!;
      group.strategies.push(strategy);

      const now = new Date();
      const from = new Date(strategy.valid_from || 0);
      const until = strategy.valid_until ? new Date(strategy.valid_until) : null;
      const isActive = from <= now && (!until || until > now) && strategy.active;

      if (isActive) {
        group.hasActive = true;
      }
      group.totalRules += strategy.classification_rules_count || 0;
    });

    return Array.from(groups.values()).sort((a, b) =>
      a.tipo_eno_name.localeCompare(b.tipo_eno_name)
    );
  }, [strategiesData, debouncedSearch]);

  // Estadísticas
  const stats = useMemo(() => {
    const allStrategies = strategiesData as EventStrategy[];
    const totalStrategies = allStrategies.length;
    const activeStrategies = allStrategies.filter((s) => s.active).length;
    const eventsWithStrategy = new Set(allStrategies.map((s) => s.tipo_eno_id)).size;

    return {
      totalStrategies,
      activeStrategies,
      eventsWithStrategy,
    };
  }, [strategiesData]);

  const statsItems: StatItem[] = [
    { id: "events", label: "Eventos configurados", value: stats.eventsWithStrategy },
    { id: "total", label: "Total estrategias", value: stats.totalStrategies },
    { id: "active", label: "Activas", value: stats.activeStrategies, color: "text-green-600" },
  ];

  const toggleGroup = (tipo_eno_id: number) => {
    const newOpen = new Set(openGroups);
    if (newOpen.has(tipo_eno_id)) {
      newOpen.delete(tipo_eno_id);
    } else {
      newOpen.add(tipo_eno_id);
    }
    setOpenGroups(newOpen);
  };

  const handleView = (strategy: EventStrategy) => {
    setSelectedStrategy(strategy);
    setViewSheetOpen(true);
  };

  const handleEdit = (strategy: EventStrategy) => {
    setSelectedStrategy(strategy);
    setEditSheetOpen(true);
  };

  const handleDelete = async () => {
    if (!strategyToDelete) return;

    try {
      await deleteStrategyMutation.mutateAsync({
        params: {
          path: { strategy_id: strategyToDelete.id },
        },
      });

      toast.success("Estrategia eliminada correctamente");
      setDeleteDialogOpen(false);
      setStrategyToDelete(null);
      strategiesQuery.refetch();
    } catch {
      toast.error("Error al eliminar la estrategia");
    }
  };

  const formatDate = (dateStr: string | undefined) => {
    if (!dateStr) return "Sin fecha";
    return new Date(dateStr).toLocaleDateString("es-ES", {
      day: "numeric",
      month: "short",
      year: "numeric",
    });
  };

  const StrategyRowSkeleton = () => (
    <div className="px-4 py-3 flex items-center gap-4">
      <Skeleton className="h-4 w-48" />
      <Skeleton className="h-4 w-32" />
      <Skeleton className="h-6 w-20" />
      <Skeleton className="h-4 w-40" />
    </div>
  );

  return (
    <SidebarProvider>
      <AppSidebar variant="inset" />
      <SidebarInset>
        <header className="flex h-14 items-center gap-4 border-b bg-background px-6">
          <SidebarTrigger className="-ml-2" />
          <Separator orientation="vertical" className="h-6" />
          <div className="flex flex-1 items-center justify-between">
            <h1 className="text-lg font-semibold">Estrategias de Vinculación</h1>
            <Button
              size="sm"
              onClick={() => {
                setSelectedStrategy(null);
                setEditSheetOpen(true);
              }}
            >
              <Plus className="mr-2 h-4 w-4" />
              Nueva
            </Button>
          </div>
        </header>

        <main className="flex-1 p-6 overflow-y-scroll bg-muted/40">
          {/* Toolbar */}
          <div className="mb-6">
            <FilterToolbar
              searchPlaceholder="Buscar por nombre de estrategia o evento..."
              searchValue={searchQuery}
              onSearchChange={setSearchQuery}
              activeFiltersCount={0}
            >
              <StatsBar stats={statsItems} />
            </FilterToolbar>
          </div>

          {/* Table */}
          <div className="border border-border bg-background rounded-lg overflow-hidden">
            {error ? (
              <div className="p-12">
                <div className="text-center">
                  <div className="rounded-full bg-destructive/10 p-3 w-fit mx-auto mb-4">
                    <AlertTriangle className="h-6 w-6 text-destructive" />
                  </div>
                  <h3 className="text-lg font-medium mb-2">Error al cargar estrategias</h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    Intenta recargar la página. Si el problema persiste, contacta a soporte.
                  </p>
                  <Button onClick={() => strategiesQuery.refetch()}>
                    Reintentar
                  </Button>
                </div>
              </div>
            ) : isLoading ? (
              <div className="divide-y divide-border">
                {[...Array(5)].map((_, i) => (
                  <StrategyRowSkeleton key={i} />
                ))}
              </div>
            ) : groupedStrategies.length === 0 ? (
              <div className="p-12">
                <div className="text-center">
                  <div className="rounded-full bg-muted p-3 w-fit mx-auto mb-4">
                    <Sparkles className="h-6 w-6 text-muted-foreground" />
                  </div>
                  <h3 className="text-lg font-medium mb-2">
                    {debouncedSearch || filterStatus !== "all"
                      ? "No se encontraron estrategias"
                      : "No hay estrategias configuradas"}
                  </h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    {debouncedSearch || filterStatus !== "all"
                      ? "Prueba con otros filtros"
                      : "Crea tu primera estrategia para vincular eventos automáticamente"}
                  </p>
                  {!debouncedSearch && filterStatus === "all" && (
                    <Button
                      onClick={() => {
                        setSelectedStrategy(null);
                        setEditSheetOpen(true);
                      }}
                    >
                      <Plus className="mr-2 h-4 w-4" />
                      Crear primera estrategia
                    </Button>
                  )}
                </div>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="border-b border-border bg-muted/50">
                    <tr>
                      <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3 w-[40px]"></th>
                      <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">Tipo de Evento</th>
                      <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">Estrategias</th>
                      <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">Reglas Totales</th>
                      <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">Estado</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {groupedStrategies.map((group) => {
                      const isOpen = openGroups.has(group.tipo_eno_id);
                      const hasMultiple = group.strategies.length > 1;

                      // SI TIENE UNA SOLA ESTRATEGIA: Mostrar fila simple sin acordeón
                      if (!hasMultiple) {
                        const strategy = group.strategies[0];
                        const now = new Date();
                        const from = new Date(strategy.valid_from || 0);
                        const until = strategy.valid_until ? new Date(strategy.valid_until) : null;
                        const isActive = from <= now && (!until || until > now) && strategy.active;
                        const isPast = until && until < now;
                        const isFuture = from > now;

                        return (
                          <tr
                            key={group.tipo_eno_id}
                            className="group hover:bg-muted/50 cursor-pointer transition-colors"
                            onClick={() => handleView(strategy)}
                          >
                            <td className="px-4 py-3">
                              {/* Chevron para indicar que es clickeable */}
                              <ChevronRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                            </td>
                            <td className="px-4 py-3">
                              <div className="space-y-0.5">
                                <span className="text-sm font-medium block">{group.tipo_eno_name}</span>
                                <span className="text-xs text-muted-foreground">{strategy.name}</span>
                              </div>
                            </td>
                            <td className="px-4 py-3">
                              <span className="text-sm text-muted-foreground">
                                {strategy.classification_rules_count || 0} reglas
                              </span>
                            </td>
                            <td className="px-4 py-3">
                              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                                <Calendar className="h-3 w-3" />
                                <span>
                                  {formatDate(strategy.valid_from)} - {until && strategy.valid_until ? formatDate(strategy.valid_until) : "∞"}
                                </span>
                              </div>
                            </td>
                            <td className="px-4 py-3">
                              <div className="flex items-center gap-2">
                                {isActive && (
                                  <Badge className="bg-green-500 text-white">
                                    <CheckCircle2 className="mr-1 h-3 w-3" />
                                    Activa
                                  </Badge>
                                )}
                                {isPast && <Badge variant="secondary">Finalizada</Badge>}
                                {isFuture && <Badge variant="outline">Programada</Badge>}

                                <DropdownMenu>
                                  <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                                    <Button variant="ghost" size="sm" className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100">
                                      <MoreHorizontal className="h-4 w-4" />
                                    </Button>
                                  </DropdownMenuTrigger>
                                  <DropdownMenuContent align="end">
                                    <DropdownMenuItem
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        handleView(strategy);
                                      }}
                                    >
                                      <Eye className="mr-2 h-4 w-4" />
                                      Ver detalles
                                    </DropdownMenuItem>
                                    <DropdownMenuItem
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        handleEdit(strategy);
                                      }}
                                    >
                                      <Edit className="mr-2 h-4 w-4" />
                                      Editar
                                    </DropdownMenuItem>
                                    <DropdownMenuSeparator />
                                    <DropdownMenuItem
                                      className="text-destructive focus:text-destructive"
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        setStrategyToDelete(strategy);
                                        setDeleteDialogOpen(true);
                                      }}
                                    >
                                      <AlertTriangle className="mr-2 h-4 w-4" />
                                      Eliminar
                                    </DropdownMenuItem>
                                  </DropdownMenuContent>
                                </DropdownMenu>
                              </div>
                            </td>
                          </tr>
                        );
                      }

                      // SI TIENE MÚLTIPLES ESTRATEGIAS: Mostrar con acordeón
                      return (
                        <Collapsible
                          key={group.tipo_eno_id}
                          open={isOpen}
                          onOpenChange={() => toggleGroup(group.tipo_eno_id)}
                          asChild
                        >
                          <>
                            {/* Fila principal del grupo - NO clickeable, solo el chevron expande */}
                            <tr className="hover:bg-muted/50 transition-colors bg-amber-50/50 border-l-4 border-l-amber-500">
                              <td className="px-4 py-3">
                                <CollapsibleTrigger asChild>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    className="h-6 w-6 p-0 hover:bg-muted"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      toggleGroup(group.tipo_eno_id);
                                    }}
                                  >
                                    {isOpen ? (
                                      <ChevronDown className="h-4 w-4" />
                                    ) : (
                                      <ChevronRight className="h-4 w-4" />
                                    )}
                                  </Button>
                                </CollapsibleTrigger>
                              </td>
                              <td className="px-4 py-3">
                                <div className="flex items-center gap-2">
                                  <span className="text-sm font-semibold">{group.tipo_eno_name}</span>
                                  <Badge variant="outline" className="text-xs">
                                    {group.strategies.length} estrategias
                                  </Badge>
                                </div>
                              </td>
                              <td className="px-4 py-3">
                                <span className="text-sm text-muted-foreground font-medium">{group.totalRules} reglas totales</span>
                              </td>
                              <td className="px-4 py-3">
                                <span className="text-xs text-muted-foreground italic">
                                  {isOpen ? "Click en una estrategia para ver" : "Click en ◀ para expandir"}
                                </span>
                              </td>
                              <td className="px-4 py-3">
                                {group.hasActive ? (
                                  <Badge className="bg-green-500 text-white">
                                    <CheckCircle2 className="mr-1 h-3 w-3" />
                                    Tiene activas
                                  </Badge>
                                ) : (
                                  <Badge variant="secondary">Sin activas</Badge>
                                )}
                              </td>
                            </tr>

                            {/* Estrategias individuales (acordeón) */}
                            <CollapsibleContent asChild>
                              <>
                                {group.strategies.map((strategy) => {
                                  const now = new Date();
                                  const from = new Date(strategy.valid_from || 0);
                                  const until = strategy.valid_until ? new Date(strategy.valid_until) : null;
                                  const isActive = from <= now && (!until || until > now) && strategy.active;
                                  const isPast = until && until < now;
                                  const isFuture = from > now;

                                  return (
                                    <tr
                                      key={strategy.id}
                                      className="group hover:bg-muted/30 cursor-pointer transition-colors bg-muted/20"
                                      onClick={() => handleView(strategy)}
                                    >
                                      <td className="px-4 py-2"></td>
                                      <td className="px-4 py-2 pl-12">
                                        <div className="flex items-center gap-2">
                                          <span className="text-sm text-muted-foreground">└</span>
                                          <span className="text-sm font-medium">{strategy.name}</span>
                                        </div>
                                      </td>
                                      <td className="px-4 py-2">
                                        <span className="text-xs text-muted-foreground">
                                          {strategy.classification_rules_count || 0} reglas
                                        </span>
                                      </td>
                                      <td className="px-4 py-2">
                                        <div className="flex items-center gap-1 text-xs text-muted-foreground">
                                          <Calendar className="h-3 w-3" />
                                          <span>
                                            {formatDate(strategy.valid_from)} - {until && strategy.valid_until ? formatDate(strategy.valid_until) : "∞"}
                                          </span>
                                        </div>
                                      </td>
                                      <td className="px-4 py-2">
                                        <div className="flex items-center gap-2">
                                          {isActive && (
                                            <Badge variant="outline" className="border-green-500 text-green-700 text-xs">
                                              Activa
                                            </Badge>
                                          )}
                                          {isPast && <Badge variant="secondary" className="text-xs">Finalizada</Badge>}
                                          {isFuture && <Badge variant="outline" className="text-xs">Programada</Badge>}

                                          <DropdownMenu>
                                            <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                                              <Button variant="ghost" size="sm" className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100">
                                                <MoreHorizontal className="h-4 w-4" />
                                              </Button>
                                            </DropdownMenuTrigger>
                                            <DropdownMenuContent align="end">
                                              <DropdownMenuItem
                                                onClick={(e) => {
                                                  e.stopPropagation();
                                                  handleView(strategy);
                                                }}
                                              >
                                                <Eye className="mr-2 h-4 w-4" />
                                                Ver detalles
                                              </DropdownMenuItem>
                                              <DropdownMenuItem
                                                onClick={(e) => {
                                                  e.stopPropagation();
                                                  handleEdit(strategy);
                                                }}
                                              >
                                                <Edit className="mr-2 h-4 w-4" />
                                                Editar
                                              </DropdownMenuItem>
                                              <DropdownMenuSeparator />
                                              <DropdownMenuItem
                                                className="text-destructive focus:text-destructive"
                                                onClick={(e) => {
                                                  e.stopPropagation();
                                                  setStrategyToDelete(strategy);
                                                  setDeleteDialogOpen(true);
                                                }}
                                              >
                                                <AlertTriangle className="mr-2 h-4 w-4" />
                                                Eliminar
                                              </DropdownMenuItem>
                                            </DropdownMenuContent>
                                          </DropdownMenu>
                                        </div>
                                      </td>
                                    </tr>
                                  );
                                })}
                              </>
                            </CollapsibleContent>
                          </>
                        </Collapsible>
                      );
                    })}
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
                    onClick={() => setPage(page - 1)}
                    disabled={!pagination.has_prev}
                  >
                    Anterior
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(page + 1)}
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

      {/* View Sheet */}
      <Sheet open={viewSheetOpen} onOpenChange={setViewSheetOpen}>
        <SheetContent className="w-full overflow-y-auto sm:max-w-3xl lg:max-w-4xl p-0">
          <div className="p-6">
            <SheetHeader className="mb-6">
              <SheetTitle>Detalles de la Estrategia</SheetTitle>
              <SheetDescription>
                Visualiza las reglas y configuración de esta estrategia
              </SheetDescription>
            </SheetHeader>
            {selectedStrategy && (
              <StrategyPreview
                strategy={selectedStrategy}
                onClose={() => setViewSheetOpen(false)}
                onEdit={() => {
                  setViewSheetOpen(false);
                  handleEdit(selectedStrategy);
                }}
              />
            )}
          </div>
        </SheetContent>
      </Sheet>

      {/* Edit Sheet */}
      <Sheet open={editSheetOpen} onOpenChange={setEditSheetOpen}>
        <SheetContent className="w-full overflow-y-auto sm:max-w-4xl lg:max-w-5xl p-0">
          <div className="p-6 space-y-6">
            <SheetHeader>
              <SheetTitle>
                {selectedStrategy ? "Editar Estrategia" : "Nueva Estrategia"}
              </SheetTitle>
              <SheetDescription>
                {selectedStrategy
                  ? "Modifica las reglas y configuración"
                  : "Configura reglas para vincular eventos automáticamente"}
              </SheetDescription>
            </SheetHeader>
            <StrategyForm
              strategy={selectedStrategy}
              onClose={() => {
                setEditSheetOpen(false);
                setSelectedStrategy(null);
              }}
              onSuccess={(message: string) => {
                toast.success(message);
                setEditSheetOpen(false);
                setSelectedStrategy(null);
                strategiesQuery.refetch();
              }}
            />
          </div>
        </SheetContent>
      </Sheet>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>¿Eliminar estrategia?</AlertDialogTitle>
            <AlertDialogDescription asChild>
              <div className="space-y-3">
                <p>Esta acción no se puede deshacer.</p>
                <div className="rounded-lg border bg-muted/50 p-3">
                  <p className="font-medium text-foreground">
                    {strategyToDelete?.name}
                  </p>
                  <p className="text-sm text-muted-foreground mt-1">
                    {strategyToDelete?.classification_rules_count || 0} reglas
                  </p>
                </div>
                {strategyToDelete?.active && (
                  <Alert className="border-amber-200 bg-amber-50/50">
                    <AlertTriangle className="h-4 w-4 text-amber-600" />
                    <AlertDescription className="text-sm">
                      Esta estrategia está activa. Los eventos dejarán de vincularse automáticamente.
                    </AlertDescription>
                  </Alert>
                )}
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel
              onClick={() => {
                setStrategyToDelete(null);
                setDeleteDialogOpen(false);
              }}
            >
              Cancelar
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              disabled={deleteStrategyMutation.isPending}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {deleteStrategyMutation.isPending ? "Eliminando..." : "Eliminar"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </SidebarProvider>
  );
}
