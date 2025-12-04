"use client";

import { Separator } from "@/components/ui/separator";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { useBoletinTemplateConfig } from "@/features/boletines/api";
import { UnifiedBoletinEditor } from "@/features/boletines/components/config/unified-boletin-editor";

export default function BoletinConfigPage() {
  const { data, isLoading, error } = useBoletinTemplateConfig();

  return (
    <div className="h-screen flex flex-col">
      {/* Compact header with breadcrumbs */}
      <header className="flex h-12 shrink-0 items-center gap-2 border-b px-4 bg-background">
        <Separator orientation="vertical" className="mr-2 h-4" />
        <Breadcrumb>
          <BreadcrumbList>
            <BreadcrumbItem className="hidden md:block">
              <BreadcrumbLink href="/dashboard/configuracion">
                Configuración
              </BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator className="hidden md:block" />
            <BreadcrumbItem>
              <BreadcrumbPage>Plantilla de Boletines</BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>
      </header>

      {error && (
        <Alert variant="destructive" className="m-2 shrink-0">
          <AlertDescription>
            Error al cargar la configuración:{" "}
            {error instanceof Error ? error.message : "Error desconocido"}
          </AlertDescription>
        </Alert>
      )}

      {isLoading && (
        <div className="flex-1 p-2">
          <Skeleton className="h-full w-full" />
        </div>
      )}

      {data?.data && (
        <div className="flex-1 min-h-0">
          <UnifiedBoletinEditor config={data.data} />
        </div>
      )}
    </div>
  );
}
