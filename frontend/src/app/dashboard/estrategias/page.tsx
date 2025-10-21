"use client";

import { useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import {
  Plus,
  Search,
  AlertTriangle,
  CheckCircle2,
  Eye,
  Edit,
  MoreHorizontal,
  Calendar,
  Sparkles,
} from "lucide-react";
import { toast } from "sonner";

// UI Components
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
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
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Separator } from "@/components/ui/separator";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AppSidebar } from "@/features/layout/components";
import { Card, CardContent } from "@/components/ui/card";

// API and types
import {
  useStrategies,
  useDeleteStrategy,
  extractSuccessData,
  type EventStrategy,
} from "@/lib/api/strategies";

// Components
import { StrategyPreview } from "./_components/strategy-preview";
import { StrategyForm } from "./_components/strategy-form";

// Utils
import { useMediaQuery } from "@/hooks/use-mobile";
import { cn } from "@/lib/utils";

export default function EstrategiasPage() {
  const router = useRouter();
  const isMobile = useMediaQuery("(max-width: 768px)");

  // State
  const [searchQuery, setSearchQuery] = useState("");
  const [filterStatus, setFilterStatus] = useState<
    "all" | "active" | "inactive"
  >("all");
  const [selectedStrategy, setSelectedStrategy] =
    useState<EventStrategy | null>(null);
  const [viewSheetOpen, setViewSheetOpen] = useState(false);
  const [editSheetOpen, setEditSheetOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [strategyToDelete, setStrategyToDelete] =
    useState<EventStrategy | null>(null);

  // API
  const strategiesQuery = useStrategies();
  const strategiesData = extractSuccessData<EventStrategy[]>(
    strategiesQuery.data
  );

  // Memoize strategies to avoid recreating on every render
  const strategies = useMemo(() => {
    return Array.isArray(strategiesData) ? strategiesData : [];
  }, [strategiesData]);

  const isLoading = strategiesQuery.isLoading;
  const error = strategiesQuery.error;

  const deleteStrategyMutation = useDeleteStrategy();

  // Filtrar estrategias
  const filteredStrategies = useMemo(() => {
    return strategies.filter((strategy) => {
      const matchesSearch =
        strategy.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        strategy.tipo_eno_name?.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesFilter =
        filterStatus === "all" ||
        (filterStatus === "active" && strategy.active) ||
        (filterStatus === "inactive" && !strategy.active);

      return matchesSearch && matchesFilter;
    });
  }, [strategies, searchQuery, filterStatus]);

  // Estadísticas
  const stats = useMemo(() => {
    const totalStrategies = strategies.length;
    const activeStrategies = strategies.filter((s) => s.active).length;
    const eventsWithStrategy = new Set(strategies.map((s) => s.tipo_eno_id))
      .size;

    return {
      totalStrategies,
      activeStrategies,
      eventsWithStrategy,
    };
  }, [strategies]);

  // Handlers
  const handleView = (strategy: EventStrategy) => {
    setSelectedStrategy(strategy);
    setViewSheetOpen(true);
  };

  const handleEdit = (strategy: EventStrategy) => {
    if (isMobile) {
      router.push(`/dashboard/estrategias/${strategy.id}/edit`);
    } else {
      setSelectedStrategy(strategy);
      setEditSheetOpen(true);
    }
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

  return (
    <SidebarProvider>
      <AppSidebar variant="inset" />
      <SidebarInset>
        {/* Header */}
        <header className="flex h-14 shrink-0 items-center gap-4 border-b bg-background px-6">
          <SidebarTrigger className="-ml-2" />
          <Separator orientation="vertical" className="h-6" />
          <div className="flex flex-1 items-center justify-between">
            <h1 className="text-lg font-semibold">Estrategias de Clasificación</h1>
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

        {/* Main Content */}
        <main className="flex-1 p-6 space-y-6 overflow-y-auto">
          {/* Stats */}
          <div className="grid grid-cols-3 gap-4">
            <Card className="p-0">
              <CardContent className="p-4">
                <div className="text-2xl font-bold">{stats.eventsWithStrategy}</div>
                <p className="text-xs text-muted-foreground mt-1">Eventos con estrategia</p>
              </CardContent>
            </Card>
            <Card className="p-0">
              <CardContent className="p-4">
                <div className="text-2xl font-bold">{stats.totalStrategies}</div>
                <p className="text-xs text-muted-foreground mt-1">Total estrategias</p>
              </CardContent>
            </Card>
            <Card className="p-0">
              <CardContent className="p-4">
                <div className="text-2xl font-bold text-green-600">{stats.activeStrategies}</div>
                <p className="text-xs text-muted-foreground mt-1">Activas ahora</p>
              </CardContent>
            </Card>
          </div>

          {/* Filters */}
          <div className="flex gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Buscar estrategias..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>
            <Select
              value={filterStatus}
              onValueChange={(value) =>
                setFilterStatus(value as "all" | "active" | "inactive")
              }
            >
              <SelectTrigger className="w-[140px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todas</SelectItem>
                <SelectItem value="active">Activas</SelectItem>
                <SelectItem value="inactive">Inactivas</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Error State */}
          {error && (
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                Error al cargar estrategias. Intenta recargar la página.
              </AlertDescription>
            </Alert>
          )}

          {/* Strategies List */}
          {!error && (
            <div className="space-y-3">
              {isLoading ? (
                <div className="space-y-3">
                  {[1, 2, 3, 4].map((i) => (
                    <Card key={i} className="h-24 animate-pulse bg-muted" />
                  ))}
                </div>
              ) : filteredStrategies.length === 0 ? (
                <Card className="p-12">
                  <div className="flex flex-col items-center gap-3 text-center">
                    <div className="rounded-full bg-muted p-3">
                      <Sparkles className="h-6 w-6 text-muted-foreground" />
                    </div>
                    <div className="space-y-1">
                      <p className="font-medium">
                        {searchQuery || filterStatus !== "all"
                          ? "No se encontraron estrategias"
                          : "No hay estrategias configuradas"}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {searchQuery || filterStatus !== "all"
                          ? "Prueba con otros filtros"
                          : "Crea tu primera estrategia para automatizar clasificaciones"}
                      </p>
                    </div>
                    {!searchQuery && filterStatus === "all" && (
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
                </Card>
              ) : (
                filteredStrategies.map((strategy) => {
                  const now = new Date();
                  const from = new Date(strategy.valid_from || 0);
                  const until = strategy.valid_until
                    ? new Date(strategy.valid_until)
                    : null;
                  const isActive =
                    from <= now && (!until || until > now) && strategy.active;
                  const isPast = until && until < now;
                  const isFuture = from > now;

                  return (
                    <Card
                      key={strategy.id}
                      className={cn(
                        "group transition-all hover:shadow-md cursor-pointer",
                        isActive && "border-green-500/30 bg-green-50/30 dark:bg-green-950/10"
                      )}
                      onClick={() => handleView(strategy)}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between gap-4">
                          {/* Left: Main Info */}
                          <div className="flex-1 min-w-0 space-y-2">
                            <div className="flex items-center gap-2">
                              <h3 className="font-medium truncate">
                                {strategy.name}
                              </h3>
                              {isActive && (
                                <Badge className="bg-green-500 text-white shrink-0">
                                  <CheckCircle2 className="mr-1 h-3 w-3" />
                                  Activa
                                </Badge>
                              )}
                              {isPast && (
                                <Badge variant="secondary" className="shrink-0">
                                  Finalizada
                                </Badge>
                              )}
                              {isFuture && (
                                <Badge variant="outline" className="shrink-0">
                                  Programada
                                </Badge>
                              )}
                            </div>

                            <div className="flex items-center gap-4 text-xs text-muted-foreground">
                              <div className="flex items-center gap-1">
                                <span className="font-medium">
                                  {strategy.tipo_eno_name || `Evento ${strategy.tipo_eno_id}`}
                                </span>
                              </div>
                              <div className="flex items-center gap-1">
                                <Calendar className="h-3 w-3" />
                                <span>
                                  {formatDate(strategy.valid_from)} - {until && strategy.valid_until ? formatDate(strategy.valid_until) : "∞"}
                                </span>
                              </div>
                              <div>
                                {strategy.classification_rules_count || 0} reglas
                              </div>
                            </div>
                          </div>

                          {/* Right: Actions */}
                          <div className="flex items-center gap-1">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleView(strategy);
                              }}
                              className="opacity-0 group-hover:opacity-100 transition-opacity"
                            >
                              <Eye className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleEdit(strategy);
                              }}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                                <Button variant="ghost" size="sm">
                                  <MoreHorizontal className="h-4 w-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
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
                        </div>
                      </CardContent>
                    </Card>
                  );
                })
              )}
            </div>
          )}
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
                  : "Configura reglas para clasificar eventos automáticamente"}
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
                      Esta estrategia está activa. Los eventos dejarán de
                      clasificarse automáticamente.
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
              {deleteStrategyMutation.isPending
                ? "Eliminando..."
                : "Eliminar"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </SidebarProvider>
  );
}
