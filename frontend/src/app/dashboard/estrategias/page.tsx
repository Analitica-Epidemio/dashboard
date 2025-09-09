"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Plus,
  MoreVertical,
  History,
  Search,
  AlertTriangle,
  CheckCircle2,
  Copy,
  Trash2,
  PlayCircle,
  Info,
  HelpCircle,
  Sparkles,
  ShieldCheck,
} from "lucide-react";
import { toast } from "sonner";

// UI Components
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
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
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AppSidebar } from "@/features/layout/components";

// API and types
import {
  useStrategies,
  useDeleteStrategy,
  useActivateStrategy,
  extractSuccessData,
  type EventStrategy,
} from "@/lib/api/strategies";

// Components
import { StrategyForm } from "./_components/strategy-form";
import { StrategyPreview } from "./_components/strategy-preview";
import { AuditLog } from "./_components/audit-log";

// Utils
import { useMediaQuery } from "@/hooks/use-mobile";

export default function ConfiguracionPage() {
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
  const [auditSheetOpen, setAuditSheetOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [strategyToDelete, setStrategyToDelete] =
    useState<EventStrategy | null>(null);

  // API
  const strategiesQuery = useStrategies();
  const strategiesData = extractSuccessData<EventStrategy[]>(
    strategiesQuery.data
  );
  const strategies = Array.isArray(strategiesData) ? strategiesData : [];
  const isLoading = strategiesQuery.isLoading;
  const error = strategiesQuery.error;

  const deleteStrategyMutation = useDeleteStrategy();
  const activateStrategyMutation = useActivateStrategy();

  // Filtering
  const filteredStrategies = strategies.filter((strategy: EventStrategy) => {
    const matchesSearch =
      strategy.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      strategy.tipo_eno_name?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFilter =
      filterStatus === "all" ||
      (filterStatus === "active" && strategy.active) ||
      (filterStatus === "inactive" && !strategy.active);
    return matchesSearch && matchesFilter;
  });

  // Handlers
  const handleView = (strategy: EventStrategy) => {
    if (isMobile) {
      router.push(`/configuracion/estrategias/${strategy.id}`);
    } else {
      setSelectedStrategy(strategy);
      setViewSheetOpen(true);
    }
  };

  const handleEdit = (strategy: EventStrategy) => {
    if (isMobile) {
      router.push(`/configuracion/estrategias/${strategy.id}/edit`);
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

      toast.success(
        <div className="flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4" />
          <div>
            <p className="font-semibold">Estrategia eliminada</p>
            <p className="text-sm">{strategyToDelete.name}</p>
          </div>
        </div>,
        {
          action: {
            label: "Deshacer",
            onClick: () => {
              toast.info("Función de deshacer en desarrollo");
            },
          },
        }
      );

      setDeleteDialogOpen(false);
      setStrategyToDelete(null);
    } catch {
      toast.error("Error al eliminar la estrategia");
    }
  };

  const handleToggleActive = async (strategy: EventStrategy) => {
    try {
      if (strategy.active) {
        // Deactivate
        toast.info("Función de desactivación en desarrollo");
      } else {
        // Activate
        await activateStrategyMutation.mutateAsync({
          params: {
            path: { strategy_id: strategy.id },
          },
        });
        toast.success("Estrategia activada correctamente");
      }
      strategiesQuery.refetch();
    } catch {
      toast.error("Error al cambiar el estado de la estrategia");
    }
  };

  const handleDuplicate = (_strategy: EventStrategy) => {
    toast.info("Función de duplicar en desarrollo");
  };

  const handleTest = (_strategy: EventStrategy) => {
    toast.info("Función de prueba en desarrollo");
  };

  const formatRelativeTime = (date: string | undefined) => {
    if (!date) return "Nunca";
    const now = new Date();
    const past = new Date(date);
    const diffInHours = Math.floor(
      (now.getTime() - past.getTime()) / (1000 * 60 * 60)
    );

    if (diffInHours < 1) return "Hace menos de 1 hora";
    if (diffInHours < 24) return `Hace ${diffInHours} horas`;
    if (diffInHours < 48) return "Ayer";
    if (diffInHours < 168) return `Hace ${Math.floor(diffInHours / 24)} días`;
    return past.toLocaleDateString("es-ES", { day: "numeric", month: "short" });
  };

  // Loading skeleton
  const StrategyRowSkeleton = () => (
    <TableRow>
      <TableCell>
        <div className="space-y-2">
          <Skeleton className="h-5 w-48" />
          <Skeleton className="h-4 w-32" />
        </div>
      </TableCell>
      <TableCell>
        <Skeleton className="h-10 w-24" />
      </TableCell>
      <TableCell>
        <Skeleton className="h-6 w-20" />
      </TableCell>
      <TableCell>
        <div className="space-y-1">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-3 w-20" />
        </div>
      </TableCell>
      <TableCell>
        <div className="flex gap-2">
          <Skeleton className="h-9 w-16" />
          <Skeleton className="h-9 w-16" />
        </div>
      </TableCell>
    </TableRow>
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
                  Estrategias de Clasificación
                </h1>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <HelpCircle className="h-4 w-4 text-muted-foreground cursor-help" />
                  </TooltipTrigger>
                  <TooltipContent className="max-w-xs">
                    <p>
                      Las estrategias definen cómo se clasifican automáticamente
                      los eventos epidemiológicos según reglas configurables
                    </p>
                  </TooltipContent>
                </Tooltip>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setAuditSheetOpen(true)}
                >
                  <History className="mr-2 h-4 w-4" />
                  <span className="hidden sm:inline">Historial</span>
                </Button>
                <Button
                  size="sm"
                  onClick={() => {
                    setSelectedStrategy(null);
                    setEditSheetOpen(true);
                  }}
                >
                  <Plus className="mr-2 h-4 w-4" />
                  Nueva Estrategia
                </Button>
              </div>
            </div>
          </header>

          {/* Main Content */}
          <main className="flex-1 p-6 space-y-6">
            {/* Info Banner */}
            <Alert className="border-blue-200 bg-blue-50/50 dark:border-blue-900 dark:bg-blue-950/20">
              <Info className="h-4 w-4 text-blue-600 dark:text-blue-400" />
              <AlertDescription className="text-sm">
                <strong>¿Qué son las estrategias?</strong> Las estrategias son
                conjuntos de reglas que clasifican automáticamente los eventos
                epidemiológicos (como dengue o rabia) en categorías como
                &quot;confirmado&quot;, &quot;sospechoso&quot; o
                &quot;descartado&quot; según los datos recibidos.
              </AlertDescription>
            </Alert>

            {/* Filters */}
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
              <div className="relative flex-1 max-w-sm">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Buscar por nombre o tipo de evento..."
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
                <SelectTrigger className="w-[200px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todas las estrategias</SelectItem>
                  <SelectItem value="active">Solo activas</SelectItem>
                  <SelectItem value="inactive">Solo inactivas</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Error State */}
            {error && (
              <Alert variant="destructive">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  <strong>Error al cargar estrategias.</strong> Por favor,
                  recarga la página o contacta soporte si el problema persiste.
                </AlertDescription>
              </Alert>
            )}

            {/* Table */}
            {!error && (
              <div className="rounded-lg border bg-card">
                <Table>
                  <TableHeader>
                    <TableRow className="hover:bg-transparent border-b">
                      <TableHead className="font-medium">Estrategia</TableHead>
                      <TableHead className="font-medium">
                        <div className="flex items-center gap-1">
                          Estado
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <HelpCircle className="h-3 w-3 text-muted-foreground" />
                            </TooltipTrigger>
                            <TooltipContent>
                              <p>
                                Solo puede haber una estrategia activa por tipo
                                de evento
                              </p>
                            </TooltipContent>
                          </Tooltip>
                        </div>
                      </TableHead>
                      <TableHead className="font-medium">Reglas</TableHead>
                      <TableHead className="font-medium">
                        Última modificación
                      </TableHead>
                      <TableHead className="text-right font-medium">
                        Acciones
                      </TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {isLoading ? (
                      <>
                        <StrategyRowSkeleton />
                        <StrategyRowSkeleton />
                        <StrategyRowSkeleton />
                      </>
                    ) : filteredStrategies.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={5} className="h-40 text-center">
                          <div className="flex flex-col items-center gap-3">
                            <div className="rounded-full bg-muted p-3">
                              <Sparkles className="h-6 w-6 text-muted-foreground" />
                            </div>
                            <div className="space-y-1">
                              <p className="font-medium text-base">
                                {searchQuery || filterStatus !== "all"
                                  ? "No se encontraron estrategias"
                                  : "No hay estrategias configuradas"}
                              </p>
                              <p className="text-sm text-muted-foreground max-w-sm mx-auto">
                                {searchQuery || filterStatus !== "all"
                                  ? "Prueba con otros filtros o términos de búsqueda"
                                  : "Las estrategias permiten clasificar automáticamente los eventos. Crea tu primera estrategia para comenzar."}
                              </p>
                            </div>
                            {!searchQuery && filterStatus === "all" && (
                              <Button
                                size="sm"
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
                        </TableCell>
                      </TableRow>
                    ) : (
                      filteredStrategies.map((strategy) => (
                        <TableRow
                          key={strategy.id}
                          className="group hover:bg-muted/30 transition-colors"
                        >
                          <TableCell>
                            <div className="space-y-1">
                              <div className="font-medium text-sm">
                                {strategy.name}
                              </div>
                              <div className="flex items-center gap-2">
                                <Badge
                                  variant="outline"
                                  className="text-xs font-normal"
                                >
                                  {strategy.tipo_eno_name ||
                                    `Evento ${strategy.tipo_eno_id}`}
                                </Badge>
                                {strategy.usa_provincia_carga && (
                                  <Tooltip>
                                    <TooltipTrigger asChild>
                                      <Badge
                                        variant="outline"
                                        className="text-xs font-normal"
                                      >
                                        <ShieldCheck className="mr-1 h-3 w-3" />
                                        Filtro provincia
                                      </Badge>
                                    </TooltipTrigger>
                                    <TooltipContent>
                                      <p>
                                        Esta estrategia solo procesa eventos de
                                        provincias específicas
                                      </p>
                                    </TooltipContent>
                                  </Tooltip>
                                )}
                              </div>
                            </div>
                          </TableCell>

                          <TableCell>
                            <div className="flex items-center gap-3">
                              <Switch
                                checked={strategy.active}
                                onCheckedChange={() =>
                                  handleToggleActive(strategy)
                                }
                                disabled={activateStrategyMutation.isPending}
                              />
                              <Badge
                                variant={
                                  strategy.active ? "default" : "secondary"
                                }
                                className="min-w-[80px] justify-center"
                              >
                                {strategy.active ? "Activa" : "Inactiva"}
                              </Badge>
                            </div>
                          </TableCell>

                          <TableCell>
                            <Badge variant="outline" className="font-normal">
                              {strategy.classification_rules?.length || 0}{" "}
                              {strategy.classification_rules?.length === 1
                                ? "regla"
                                : "reglas"}
                            </Badge>
                          </TableCell>

                          <TableCell>
                            <div className="space-y-0.5 text-sm">
                              <div className="text-foreground">
                                {formatRelativeTime(strategy.updated_at)}
                              </div>
                              <div className="text-xs text-muted-foreground">
                                por {strategy.created_by || "Sistema"}
                              </div>
                            </div>
                          </TableCell>

                          <TableCell className="text-right">
                            <div className="flex items-center justify-end gap-1">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleView(strategy)}
                                className="opacity-0 group-hover:opacity-100 transition-opacity"
                              >
                                Ver detalles
                              </Button>
                              <Button
                                variant="default"
                                size="sm"
                                onClick={() => handleEdit(strategy)}
                              >
                                Editar
                              </Button>
                              <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    className="opacity-0 group-hover:opacity-100 transition-opacity"
                                  >
                                    <MoreVertical className="h-4 w-4" />
                                    <span className="sr-only">
                                      Más opciones
                                    </span>
                                  </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent
                                  align="end"
                                  className="w-48"
                                >
                                  <DropdownMenuItem
                                    onClick={() => handleDuplicate(strategy)}
                                  >
                                    <Copy className="mr-2 h-4 w-4" />
                                    Duplicar estrategia
                                  </DropdownMenuItem>
                                  <DropdownMenuItem
                                    onClick={() => handleTest(strategy)}
                                  >
                                    <PlayCircle className="mr-2 h-4 w-4" />
                                    Probar con datos
                                  </DropdownMenuItem>
                                  <DropdownMenuSeparator />
                                  <DropdownMenuItem
                                    className="text-destructive focus:text-destructive"
                                    onClick={() => {
                                      setStrategyToDelete(strategy);
                                      setDeleteDialogOpen(true);
                                    }}
                                  >
                                    <Trash2 className="mr-2 h-4 w-4" />
                                    Eliminar
                                  </DropdownMenuItem>
                                </DropdownMenuContent>
                              </DropdownMenu>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </div>
            )}
          </main>
        </SidebarInset>

        {/* View Sheet - Wider */}
        <Sheet open={viewSheetOpen} onOpenChange={setViewSheetOpen}>
          <SheetContent className="w-full overflow-y-auto sm:max-w-3xl lg:max-w-4xl p-0">
            <div className="p-6">
              <StrategyPreview
                strategy={selectedStrategy}
                onClose={() => setViewSheetOpen(false)}
              />
            </div>
          </SheetContent>
        </Sheet>

        {/* Edit Sheet - Much Wider for forms */}
        <Sheet open={editSheetOpen} onOpenChange={setEditSheetOpen}>
          <SheetContent className="w-full overflow-y-auto sm:max-w-4xl lg:max-w-5xl p-0">
            <div className="p-6 space-y-6">
              <SheetHeader className="space-y-3">
                <div className="flex items-start justify-between">
                  <div className="space-y-2">
                    <SheetTitle className="text-xl">
                      {selectedStrategy
                        ? "Editar Estrategia"
                        : "Nueva Estrategia de Clasificación"}
                    </SheetTitle>
                    <SheetDescription>
                      {selectedStrategy
                        ? "Modifica las reglas que determinan cómo se clasifican los eventos"
                        : "Configura reglas para clasificar automáticamente eventos epidemiológicos"}
                    </SheetDescription>
                  </div>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button variant="ghost" size="icon">
                        <HelpCircle className="h-4 w-4" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent className="max-w-xs">
                      <div className="space-y-2 text-sm">
                        <p>
                          <strong>¿Qué es una estrategia?</strong>
                        </p>
                        <p>
                          Es un conjunto de reglas que evalúan los datos de cada
                          evento para clasificarlo automáticamente.
                        </p>
                        <p>
                          <strong>¿Qué es la prioridad?</strong>
                        </p>
                        <p>
                          Las reglas se evalúan en orden de prioridad (1 es la
                          más alta). La primera regla que coincida determina la
                          clasificación.
                        </p>
                      </div>
                    </TooltipContent>
                  </Tooltip>
                </div>
              </SheetHeader>
              <div className="px-2">
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
            </div>
          </SheetContent>
        </Sheet>

        {/* Audit Sheet - Wide for table */}
        <Sheet open={auditSheetOpen} onOpenChange={setAuditSheetOpen}>
          <SheetContent className="w-full overflow-y-auto sm:max-w-5xl lg:max-w-6xl p-0">
            <div className="p-6 space-y-6">
              <SheetHeader className="space-y-3">
                <SheetTitle className="text-xl">
                  Historial de Cambios
                </SheetTitle>
                <SheetDescription>
                  Registro completo de todas las modificaciones realizadas en
                  las estrategias
                </SheetDescription>
              </SheetHeader>
              <div className="px-2">
                <AuditLog />
              </div>
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
                  <p>
                    Esta acción no se puede deshacer. Se eliminará
                    permanentemente:
                  </p>
                  <div className="rounded-md border bg-muted/50 p-3 space-y-1">
                    <p className="font-medium text-foreground">
                      {strategyToDelete?.name}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      Contiene{" "}
                      {strategyToDelete?.classification_rules?.length || 0}{" "}
                      reglas de clasificación
                    </p>
                  </div>
                  {strategyToDelete?.active && (
                    <Alert className="border-amber-200 bg-amber-50/50 dark:border-amber-900 dark:bg-amber-950/20">
                      <AlertTriangle className="h-4 w-4 text-amber-600 dark:text-amber-400" />
                      <AlertDescription className="text-sm font-medium">
                        Esta estrategia está activa. Al eliminarla, los eventos
                        dejarán de clasificarse automáticamente.
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
                  : "Eliminar estrategia"}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </SidebarProvider>
    </TooltipProvider>
  );
}
