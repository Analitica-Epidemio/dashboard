"use client";

import { Plus, FileText } from "lucide-react";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/features/layout/components";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import Link from "next/link";
import { $api } from "@/lib/api/client";

export default function BoletinesPage() {
  const { data: templatesResponse, isLoading: templatesLoading } = $api.useQuery(
    'get',
    '/api/v1/boletines/templates',
    {}
  );
  const { data: instancesResponse, isLoading: instancesLoading } = $api.useQuery(
    'get',
    '/api/v1/boletines/instances',
    { params: { query: { limit: 5 } } }
  );

  const templates = templatesResponse?.data;
  const instances = instancesResponse?.data;

  return (
    <SidebarProvider
      style={
        {
          "--sidebar-width": "calc(var(--spacing) * 72)",
          "--header-height": "calc(var(--spacing) * 12)",
        } as React.CSSProperties
      }
    >
      <AppSidebar variant="inset" />
      <SidebarInset>
        <div className="flex flex-col min-h-screen overflow-y-auto bg-muted">
          <div className="flex-1 w-full mx-auto px-6 py-8 max-w-7xl space-y-6">
            {/* Header */}
            <div className="mb-8">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-3">
                  <FileText className="w-5 h-5 text-muted-foreground" />
                  <h1 className="text-2xl font-semibold">Boletines Epidemiológicos</h1>
                </div>
                <Link href="/dashboard/boletines/nuevo">
                  <Button>
                    <Plus className="w-4 h-4 mr-2" />
                    Nuevo Boletín
                  </Button>
                </Link>
              </div>
              <p className="text-sm text-muted-foreground">
                Crea y gestiona boletines epidemiológicos profesionales con plantillas reutilizables
              </p>
            </div>

            {/* Templates Grid */}
            <div>
              <h2 className="text-lg font-semibold mb-4">Plantillas Disponibles</h2>
              {templatesLoading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {[1, 2, 3].map((i) => (
                    <Card key={i}>
                      <CardHeader>
                        <Skeleton className="h-4 w-3/4 mb-2" />
                        <Skeleton className="h-3 w-full" />
                      </CardHeader>
                      <CardContent>
                        <Skeleton className="h-8 w-full" />
                      </CardContent>
                    </Card>
                  ))}
                </div>
              ) : templates && templates.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {templates.map((template) => (
                    <TemplateCard key={template.id} template={template} />
                  ))}
                </div>
              ) : (
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-center text-muted-foreground py-8">
                      <FileText className="w-12 h-12 mx-auto mb-4 text-muted-foreground/50" />
                      <p>No hay plantillas disponibles</p>
                      <p className="text-sm mt-2">
                        Crea tu primera plantilla para empezar
                      </p>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>

            {/* Recent Instances */}
            <div className="mt-8">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">Boletines Recientes</h2>
                <Link href="/dashboard/boletines/historial">
                  <Button variant="ghost" size="sm">
                    Ver todos
                  </Button>
                </Link>
              </div>
              {instancesLoading ? (
                <Card>
                  <CardContent className="pt-6">
                    <div className="space-y-4">
                      {[1, 2, 3].map((i) => (
                        <Skeleton key={i} className="h-16 w-full" />
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ) : instances && instances.length > 0 ? (
                <Card>
                  <CardContent className="pt-6">
                    <div className="space-y-4">
                      {instances.map((instance) => (
                        <div
                          key={instance.id}
                          className="flex items-center justify-between p-4 border rounded-lg hover:bg-accent/50 transition-colors"
                        >
                          <div>
                            <h3 className="font-medium">{instance.name}</h3>
                            <p className="text-sm text-muted-foreground">
                              {new Date(instance.created_at).toLocaleDateString("es-AR")}
                            </p>
                          </div>
                          <Badge
                            variant={
                              instance.status === "completed"
                                ? "default"
                                : instance.status === "failed"
                                ? "destructive"
                                : "secondary"
                            }
                          >
                            {instance.status}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ) : (
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-center text-muted-foreground py-8">
                      <FileText className="w-12 h-12 mx-auto mb-4 text-muted-foreground/50" />
                      <p>No hay boletines generados todavía</p>
                      <p className="text-sm mt-2">
                        Crea tu primer boletín usando una de las plantillas disponibles
                      </p>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}

interface TemplateCardProps {
  template: {
    id: number;
    name: string;
    description?: string | null;
    category: string;
    is_system?: boolean;
  };
}

function TemplateCard({ template }: TemplateCardProps) {
  const getCategoryColor = (cat: string) => {
    switch (cat) {
      case "semanal":
        return "bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400";
      case "brote":
        return "bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400";
      case "tendencias":
        return "bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-400";
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400";
    }
  };

  return (
    <Card className="hover:shadow-md transition-shadow cursor-pointer">
      <Link href={`/dashboard/boletines/editor/${template.id}`}>
        <CardHeader>
          <div className="flex items-start justify-between mb-2">
            <CardTitle className="text-base">{template.name}</CardTitle>
            {template.is_system && (
              <Badge variant="outline" className="text-xs">
                Sistema
              </Badge>
            )}
          </div>
          <CardDescription className="text-sm line-clamp-2">
            {template.description || "Sin descripción"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <Badge className={getCategoryColor(template.category)}>{template.category}</Badge>
            <Button variant="ghost" size="sm">
              Usar Plantilla
            </Button>
          </div>
        </CardContent>
      </Link>
    </Card>
  );
}
