"use client";

import { Plus, FileText, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { AppSidebar } from "@/features/layout/components";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { $api } from "@/lib/api/client";

export default function BoletinesPage() {
  const router = useRouter();
  const { data: instancesResponse, isLoading } = $api.useQuery(
    "get",
    "/api/v1/boletines/instances",
    { params: { query: { limit: 50 } } }
  );

  const instances = instancesResponse?.data;

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
          <Link href="/dashboard/boletines/nuevo">
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
                        onClick={() =>
                          router.push(
                            `/dashboard/boletines/instances/${instance.id}`
                          )
                        }
                        className="group hover:bg-muted/50 cursor-pointer transition-colors"
                      >
                        <td className="px-4 py-3">
                          <span className="text-sm font-medium">
                            {instance.name}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm text-muted-foreground">
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
                        <td className="px-4 py-3">
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
                          <ChevronRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
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
                  <Link href="/dashboard/boletines/nuevo">
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
    </SidebarProvider>
  );
}
