"use client";

import { use, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  Calendar,
  FileText,
  MapPin,
  User,
  Activity,
  Share2,
  Printer,
  Download,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  Copy,
  Check,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/features/layout/components";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { toast } from "sonner";

import { usePersona, usePersonaTimeline } from "@/lib/api/personas";
import { PersonTimeline } from "../../_components/person-timeline";

export default function PersonaDetailPage({
  params,
}: {
  params: Promise<{ tipo_sujeto: "humano" | "animal"; id: string }>;
}) {
  const router = useRouter();
  const { tipo_sujeto, id } = use(params);
  const personaId = parseInt(id);
  const [copied, setCopied] = useState(false);

  const personaQuery = usePersona(tipo_sujeto, personaId);
  const timelineQuery = usePersonaTimeline(tipo_sujeto, personaId);

  const persona = personaQuery.data?.data;
  const timeline = timelineQuery.data?.data;
  const isLoading = personaQuery.isLoading || timelineQuery.isLoading;

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        router.back();
      }
      if ((e.metaKey || e.ctrlKey) && e.key === "p") {
        e.preventDefault();
        handlePrint();
      }
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        handleCopyURL();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [router]);

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: `${persona?.nombre_completo}`,
          text: `Ver perfil de ${persona?.nombre_completo}`,
          url: window.location.href,
        });
      } catch (err) {
        console.log("Error sharing:", err);
      }
    } else {
      handleCopyURL();
    }
  };

  const handleCopyURL = () => {
    navigator.clipboard.writeText(window.location.href);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    toast.success("URL copiada al portapapeles");
  };

  const handlePrint = () => {
    window.print();
  };

  const handleExport = () => {
    toast.success("Exportando perfil...");
  };

  if (isLoading) {
    return (
      <SidebarProvider>
        <AppSidebar variant="inset" />
        <SidebarInset>
          <div className="p-6">
            <Skeleton className="h-8 w-64 mb-6" />
            <Skeleton className="h-48 w-full mb-6" />
            <Skeleton className="h-96 w-full" />
          </div>
        </SidebarInset>
      </SidebarProvider>
    );
  }

  if (!persona) {
    return (
      <SidebarProvider>
        <AppSidebar variant="inset" />
        <SidebarInset>
          <div className="p-6">
            <p>Persona no encontrada</p>
          </div>
        </SidebarInset>
      </SidebarProvider>
    );
  }

  return (
    <SidebarProvider>
      <AppSidebar variant="inset" />
      <SidebarInset>
        {/* Header with breadcrumbs and actions (GitHub/Linear/Vercel style) */}
        <header className="sticky top-0 z-10 flex h-14 items-center gap-4 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 px-6">
          <SidebarTrigger className="-ml-2" />
          <Separator orientation="vertical" className="h-6" />

          {/* Breadcrumbs */}
          <Breadcrumb>
            <BreadcrumbList>
              <BreadcrumbItem>
                <BreadcrumbLink href="/dashboard">Dashboard</BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator />
              <BreadcrumbItem>
                <BreadcrumbLink href="/dashboard/personas">Personas</BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator />
              <BreadcrumbItem>
                <BreadcrumbPage>
                  {persona.nombre_completo}
                </BreadcrumbPage>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>

          <div className="ml-auto flex items-center gap-2">
            {/* Copy URL button */}
            <Button
              variant="ghost"
              size="sm"
              onClick={handleCopyURL}
              className="hidden sm:flex"
            >
              {copied ? (
                <>
                  <Check className="mr-2 h-4 w-4 text-green-600" />
                  Copiado
                </>
              ) : (
                <>
                  <Copy className="mr-2 h-4 w-4" />
                  Copiar URL
                </>
              )}
            </Button>

            {/* More actions dropdown */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm">
                  <Share2 className="mr-2 h-4 w-4" />
                  <span className="hidden sm:inline">Compartir</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                <DropdownMenuItem onClick={handleShare}>
                  <Share2 className="mr-2 h-4 w-4" />
                  Compartir
                </DropdownMenuItem>
                <DropdownMenuItem onClick={handleCopyURL}>
                  <Copy className="mr-2 h-4 w-4" />
                  Copiar URL
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handlePrint}>
                  <Printer className="mr-2 h-4 w-4" />
                  Imprimir
                </DropdownMenuItem>
                <DropdownMenuItem onClick={handleExport}>
                  <Download className="mr-2 h-4 w-4" />
                  Exportar PDF
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>

            <Button
              variant="ghost"
              size="sm"
              onClick={() => router.back()}
              className="hidden sm:flex"
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              Volver
            </Button>
          </div>
        </header>

        <main className="flex-1 p-6 overflow-y-auto print:p-0">
          {/* Print-only header */}
          <div className="hidden print:block mb-6">
            <h1 className="text-2xl font-bold">
              {persona.nombre_completo}
            </h1>
            <p className="text-sm text-muted-foreground">
              Generado el {new Date().toLocaleDateString("es-ES")}
            </p>
          </div>

          {/* Keyboard shortcuts hint */}
          <div className="hidden md:block mb-4 text-xs text-muted-foreground print:hidden">
            <kbd className="px-2 py-1 bg-muted rounded text-xs">ESC</kbd> para volver •{" "}
            <kbd className="px-2 py-1 bg-muted rounded text-xs">⌘K</kbd> copiar URL
          </div>

          {/* Header de persona */}
          <Card className="mb-6">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-4">
                  <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center">
                    <User className="h-8 w-8 text-primary" />
                  </div>
                  <div>
                    <CardTitle className="text-2xl">{persona.nombre_completo}</CardTitle>
                    <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                      {persona.documento_numero && (
                        <span className="flex items-center gap-1">
                          <FileText className="h-3 w-3" />
                          {persona.documento_tipo} {persona.documento_numero}
                        </span>
                      )}
                      {persona.edad_actual && <span>{persona.edad_actual} años</span>}
                      {persona.sexo_biologico && <span>{persona.sexo_biologico}</span>}
                    </div>
                  </div>
                </div>
                <Badge variant={persona.total_eventos > 3 ? "destructive" : "secondary"} className="text-lg px-4 py-2">
                  {persona.total_eventos} eventos
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {persona.provincia && (
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">Ubicación</p>
                    <p className="text-sm flex items-center gap-1 mt-1">
                      <MapPin className="h-3 w-3" />
                      {persona.localidad && `${persona.localidad}, `}{persona.provincia}
                    </p>
                  </div>
                )}
                {persona.primer_evento_fecha && (
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">Primer Evento</p>
                    <p className="text-sm flex items-center gap-1 mt-1">
                      <Calendar className="h-3 w-3" />
                      {new Date(persona.primer_evento_fecha).toLocaleDateString("es-ES")}
                    </p>
                  </div>
                )}
                {persona.ultimo_evento_fecha && (
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">Último Evento</p>
                    <p className="text-sm flex items-center gap-1 mt-1">
                      <Calendar className="h-3 w-3" />
                      {new Date(persona.ultimo_evento_fecha).toLocaleDateString("es-ES")}
                    </p>
                  </div>
                )}
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Tipos Únicos</p>
                  <p className="text-sm flex items-center gap-1 mt-1">
                    <Activity className="h-3 w-3" />
                    {persona.tipos_eventos_unicos || 0} tipos
                  </p>
                </div>
              </div>

              {/* Estadísticas de eventos */}
              <div className="grid grid-cols-3 gap-4 mt-6 pt-4 border-t">
                <div className="text-center p-4 rounded-lg bg-green-50 dark:bg-green-950/20">
                  <p className="text-3xl font-bold text-green-600">{persona.eventos_confirmados || 0}</p>
                  <p className="text-sm text-muted-foreground">Confirmados</p>
                </div>
                <div className="text-center p-4 rounded-lg bg-yellow-50 dark:bg-yellow-950/20">
                  <p className="text-3xl font-bold text-yellow-600">{persona.eventos_sospechosos || 0}</p>
                  <p className="text-sm text-muted-foreground">Sospechosos</p>
                </div>
                <div className="text-center p-4 rounded-lg bg-red-50 dark:bg-red-950/20">
                  <p className="text-3xl font-bold text-red-600">{persona.eventos_requieren_revision || 0}</p>
                  <p className="text-sm text-muted-foreground">Requiere Revisión</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Tabs de contenido */}
          <Tabs defaultValue="timeline" className="space-y-4">
            <TabsList>
              <TabsTrigger value="timeline">Timeline Completo</TabsTrigger>
              <TabsTrigger value="eventos">Eventos ({persona.total_eventos})</TabsTrigger>
              <TabsTrigger value="datos">Datos Personales</TabsTrigger>
            </TabsList>

            <TabsContent value="timeline" className="space-y-4">
              <PersonTimeline
                items={timeline?.items || []}
                isLoading={timelineQuery.isLoading}
              />
            </TabsContent>

            <TabsContent value="eventos" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Eventos de {persona.nombre_completo}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {persona.eventos && persona.eventos.length > 0 ? (
                      persona.eventos.map((evento: any) => (
                        <div key={evento.id} className="flex items-center justify-between p-3 border rounded-lg">
                          <div>
                            <p className="font-medium">{evento.tipo_eno}</p>
                            <p className="text-sm text-muted-foreground">
                              {new Date(evento.fecha).toLocaleDateString("es-ES")}
                            </p>
                          </div>
                          <Badge variant={evento.es_positivo ? "destructive" : "secondary"}>
                            {evento.clasificacion || "Sin clasificar"}
                          </Badge>
                        </div>
                      ))
                    ) : (
                      <p className="text-center py-8 text-muted-foreground">No hay eventos registrados</p>
                    )}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="datos" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Información Personal</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4">
                    {persona.nombre && (
                      <div>
                        <p className="text-sm font-medium text-muted-foreground">Nombre</p>
                        <p>{persona.nombre}</p>
                      </div>
                    )}
                    {persona.apellido && (
                      <div>
                        <p className="text-sm font-medium text-muted-foreground">Apellido</p>
                        <p>{persona.apellido}</p>
                      </div>
                    )}
                    {persona.fecha_nacimiento && (
                      <div>
                        <p className="text-sm font-medium text-muted-foreground">Fecha de Nacimiento</p>
                        <p>{new Date(persona.fecha_nacimiento).toLocaleDateString("es-ES")}</p>
                      </div>
                    )}
                    {persona.telefono && (
                      <div>
                        <p className="text-sm font-medium text-muted-foreground">Teléfono</p>
                        <p>{persona.telefono}</p>
                      </div>
                    )}
                    {persona.obra_social && (
                      <div>
                        <p className="text-sm font-medium text-muted-foreground">Obra Social</p>
                        <p>{persona.obra_social}</p>
                      </div>
                    )}
                    {tipo_sujeto === "animal" && (
                      <>
                        {persona.especie && (
                          <div>
                            <p className="text-sm font-medium text-muted-foreground">Especie</p>
                            <p>{persona.especie}</p>
                          </div>
                        )}
                        {persona.raza && (
                          <div>
                            <p className="text-sm font-medium text-muted-foreground">Raza</p>
                            <p>{persona.raza}</p>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </main>
      </SidebarInset>
    </SidebarProvider>
  );
}
