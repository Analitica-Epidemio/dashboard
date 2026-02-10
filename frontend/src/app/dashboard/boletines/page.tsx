"use client";

import { useState } from "react";
import { Plus, FileText, ChevronRight, Copy, MoreVertical, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
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
import { AppSidebar } from "@/features/layout/components";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { $api, apiClient } from "@/lib/api/client";
import { toast } from "sonner";

export default function BoletinesPage() {
  const router = useRouter();
  const [duplicatingId, setDuplicatingId] = useState<number | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deletingInstance, setDeletingInstance] = useState<{ id: number; name: string } | null>(null);

  const { data: instancesResponse, isLoading, refetch } = $api.useQuery(
    "get",
    "/api/v1/boletines/instances",
    { params: { query: { limit: 50 } } }
  );

  const instances = instancesResponse?.data;

  // Handle duplicate
  const handleDuplicate = async (instanceId: number, instanceName: string) => {
    setDuplicatingId(instanceId);
    try {
      const response = await apiClient.POST("/api/v1/boletines/instances/{instance_id}/duplicate", {
        params: { path: { instance_id: instanceId } },
      });

      if (response.data?.data?.id) {
        toast.success(`Boletín "${instanceName}" duplicado exitosamente`);
        refetch();
        router.push(`/dashboard/boletines/instances/${response.data.data.id}`);
      }
    } catch (error) {
      console.error("Error duplicating:", error);
      toast.error("Error al duplicar el boletín");
    } finally {
      setDuplicatingId(null);
    }
  };

  // Handle delete
  const handleDelete = async () => {
    if (!deletingInstance) return;

    try {
      await apiClient.DELETE("/api/v1/boletines/instances/{instance_id}", {
        params: { path: { instance_id: deletingInstance.id } },
      });

      toast.success(`Boletín "${deletingInstance.name}" eliminado`);
      refetch();
    } catch (error) {
      console.error("Error deleting:", error);
      toast.error("Error al eliminar el boletín");
    } finally {
      setDeleteDialogOpen(false);
      setDeletingInstance(null);
    }
  };

  const RowSkeleton = () => (
    <div className="px-4 py-3 flex items-center gap-4">
      <Skeleton className="h-4 w-48" />
      <Skeleton className="h-4 w-32" />
      <Skeleton className="h-4 w-20" />
    </div>
  );

  return (
    <SidebarProvider>
      <AppSidebar variant="inset" />
      <SidebarInset>
        {/* Header */}
        <header className="flex h-14 items-center justify-between gap-4 border-b bg-background px-6">
          <div className="flex items-center gap-4">
            <SidebarTrigger className="-ml-2" />
            <Separator orientation="vertical" className="h-6" />
            <h1 className="text-lg font-semibold">Boletines</h1>
          </div>
          <Link href="/dashboard/analytics">
            <Button size="sm">
              <Plus className="w-4 h-4 mr-2" />
              Nuevo Boletín
            </Button>
          </Link>
        </header>

        {/* Main Content */}
        <main className="flex-1 p-6 overflow-y-scroll bg-muted/40">
          <div className="border border-border bg-background rounded-lg overflow-hidden">
            {isLoading ? (
              <div className="divide-y divide-border">
                {[...Array(5)].map((_, i) => (
                  <RowSkeleton key={i} />
                ))}
              </div>
            ) : instances && instances.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="border-b border-border bg-muted/50">
                    <tr>
                      <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">
                        Nombre
                      </th>
                      <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">
                        Período
                      </th>
                      <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">
                        Fecha de creación
                      </th>
                      <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">
                        PDF
                      </th>
                      <th className="w-[40px]"></th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {instances.map((instance) => (
                      <tr
                        key={instance.id}
                        className="group hover:bg-muted/50 transition-colors"
                      >
                        <td
                          className="px-4 py-3 cursor-pointer"
                          onClick={() =>
                            router.push(
                              `/dashboard/boletines/instances/${instance.id}`
                            )
                          }
                        >
                          <span className="text-sm font-medium">
                            {instance.name}
                          </span>
                        </td>
                        <td
                          className="px-4 py-3 text-sm text-muted-foreground cursor-pointer"
                          onClick={() =>
                            router.push(
                              `/dashboard/boletines/instances/${instance.id}`
                            )
                          }
                        >
                          {instance.semana_epidemiologica && instance.anio_epidemiologico ? (
                            <span className="text-sm">
                              SE {instance.semana_epidemiologica}/{instance.anio_epidemiologico}
                              {instance.num_semanas ? ` (${instance.num_semanas} sem)` : ""}
                            </span>
                          ) : (
                            <span className="text-xs text-muted-foreground">-</span>
                          )}
                        </td>
                        <td
                          className="px-4 py-3 text-sm text-muted-foreground cursor-pointer"
                          onClick={() =>
                            router.push(
                              `/dashboard/boletines/instances/${instance.id}`
                            )
                          }
                        >
                          {new Date(instance.created_at).toLocaleDateString(
                            "es-AR",
                            {
                              day: "2-digit",
                              month: "short",
                              year: "numeric",
                              hour: "2-digit",
                              minute: "2-digit",
                            }
                          )}
                        </td>
                        <td
                          className="px-4 py-3 cursor-pointer"
                          onClick={() =>
                            router.push(
                              `/dashboard/boletines/instances/${instance.id}`
                            )
                          }
                        >
                          {instance.pdf_path ? (
                            <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-green-50 text-green-700 border border-green-200">
                              Generado
                            </span>
                          ) : (
                            <span className="text-xs text-muted-foreground">
                              -
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-3">
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                                onClick={(e) => e.stopPropagation()}
                              >
                                <MoreVertical className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleDuplicate(instance.id, instance.name);
                                }}
                                disabled={duplicatingId === instance.id}
                              >
                                <Copy className="h-4 w-4 mr-2" />
                                {duplicatingId === instance.id
                                  ? "Duplicando..."
                                  : "Duplicar"}
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setDeletingInstance({
                                    id: instance.id,
                                    name: instance.name,
                                  });
                                  setDeleteDialogOpen(true);
                                }}
                                className="text-destructive focus:text-destructive"
                              >
                                <Trash2 className="h-4 w-4 mr-2" />
                                Eliminar
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="p-12">
                <div className="text-center">
                  <FileText className="mx-auto h-12 w-12 text-muted-foreground opacity-50 mb-4" />
                  <h3 className="text-lg font-medium mb-2">
                    No hay boletines generados
                  </h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    Crea tu primer boletín haciendo click en &quot;Nuevo
                    Boletín&quot;
                  </p>
                  <Link href="/dashboard/analytics">
                    <Button>
                      <Plus className="w-4 h-4 mr-2" />
                      Nuevo Boletín
                    </Button>
                  </Link>
                </div>
              </div>
            )}
          </div>
        </main>
      </SidebarInset>

      {/* Delete confirmation dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Eliminar boletín</AlertDialogTitle>
            <AlertDialogDescription>
              ¿Estás seguro de que deseas eliminar el boletín &quot;{deletingInstance?.name}&quot;?
              Esta acción no se puede deshacer.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Eliminar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </SidebarProvider>
  );
}
