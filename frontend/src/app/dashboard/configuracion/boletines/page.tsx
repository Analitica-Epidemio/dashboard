"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { ChevronLeft } from "lucide-react";
import { CollapsibleSidebar } from "@/features/layout/components";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useBoletinTemplateConfig } from "@/features/boletines/api";
import { MetadataForm } from "@/features/boletines/components/config/metadata-form";
import { SectionsStructure } from "@/features/boletines/components/config/sections-structure";

const LazyUnifiedBoletinEditor = dynamic(
  () =>
    import(
      "@/features/boletines/components/config/unified-boletin-editor"
    ).then((mod) => mod.UnifiedBoletinEditor),
  {
    ssr: false,
    loading: () => <Skeleton className="h-[600px] w-full" />,
  }
);

export default function BoletinConfigPage() {
  const { data, isLoading, error } = useBoletinTemplateConfig();

  return (
    <div className="flex h-screen overflow-hidden">
      <CollapsibleSidebar />

      <div className="flex-1 flex flex-col overflow-hidden bg-background">
        {/* Header consistente con otras páginas de configuración */}
        <div className="shrink-0 border-b px-6 py-4">
          <Button variant="ghost" size="sm" asChild className="mb-3 -ml-2">
            <Link href="/dashboard/configuracion">
              <ChevronLeft className="h-4 w-4 mr-1" />
              Volver a Configuración
            </Link>
          </Button>
          <h1 className="text-3xl font-bold tracking-tight">
            Template de Boletines
          </h1>
          <p className="text-muted-foreground mt-1">
            Configurá los datos, la estructura y el contenido del boletín
            epidemiológico
          </p>
        </div>

        {error && (
          <Alert variant="destructive" className="mx-6 mt-4 shrink-0">
            <AlertDescription>
              Error al cargar la configuración:{" "}
              {error instanceof Error ? error.message : "Error desconocido"}
            </AlertDescription>
          </Alert>
        )}

        {isLoading && (
          <div className="flex-1 p-6">
            <Skeleton className="h-full w-full rounded-lg" />
          </div>
        )}

        {data?.data && (
          <Tabs
            defaultValue="datos"
            className="flex-1 flex flex-col min-h-0"
          >
            <TabsList className="mx-6 mt-4 w-fit shrink-0">
              <TabsTrigger value="datos">Datos del Boletín</TabsTrigger>
              <TabsTrigger value="estructura">Estructura</TabsTrigger>
              <TabsTrigger value="editor">Editor de Template</TabsTrigger>
            </TabsList>

            <TabsContent
              value="datos"
              className="flex-1 overflow-y-auto px-6 pb-6"
            >
              <MetadataForm config={data.data} />
            </TabsContent>

            <TabsContent
              value="estructura"
              className="flex-1 overflow-y-auto px-6 pb-6"
            >
              <SectionsStructure />
            </TabsContent>

            <TabsContent value="editor" className="flex-1 min-h-0">
              <LazyUnifiedBoletinEditor config={data.data} />
            </TabsContent>
          </Tabs>
        )}
      </div>
    </div>
  );
}
