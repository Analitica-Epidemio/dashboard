"use client";

import React, { useState } from "react";
import {
  BarChart3,
  PieChart,
  Activity,
  Filter,
  Download,
  Settings2,
  Info,
  Play,
  Loader2,
} from "lucide-react";

// UI Components
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Separator } from "@/components/ui/separator";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { AppSidebar } from "@/components/app-sidebar";

// Analytics Components
import { GrupoSelector } from "./_components/grupo-selector";
import { EventoSelector } from "./_components/evento-selector";
import { FiltrosPanel } from "./_components/filtros-panel";
import { VisualizacionContainer } from "./_components/visualizacion-container";

// API hooks
import { useGrupos } from "@/lib/api/analytics";

export default function AnalyticsPage() {
  // Estados principales
  const [grupoSeleccionado, setGrupoSeleccionado] = useState<number | null>(null);
  const [eventosSeleccionados, setEventosSeleccionados] = useState<number[]>([]);
  const [tipoGrafico, setTipoGrafico] = useState<string>("casos_por_edad");
  const [clasificacion, setClasificacion] = useState<string>("todos");
  
  // Estados de UI
  const [filtrosOpen, setFiltrosOpen] = useState(false);
  const [configOpen, setConfigOpen] = useState(false);
  const [generandoGrafico, setGenerandoGrafico] = useState(false);
  
  // Filtros adicionales
  const [fechaDesde, setFechaDesde] = useState<string>("");
  const [fechaHasta, setFechaHasta] = useState<string>("");
  
  // Data using real API
  const gruposQuery = useGrupos();
  const grupos = gruposQuery.data?.data?.grupos || [];

  const handleGenerarVisualizacion = async () => {
    if (!grupoSeleccionado) return;
    
    setGenerandoGrafico(true);
    try {
      // La visualización se maneja en el componente VisualizacionContainer
      setTimeout(() => {
        setGenerandoGrafico(false);
      }, 1000);
    } catch (error) {
      setGenerandoGrafico(false);
      console.error("Error generando visualización:", error);
    }
  };

  const grupoActual = grupos.find(g => g.id === grupoSeleccionado);
  const tieneConfiguracionCompleta = grupoSeleccionado && tipoGrafico;

  return (
    <SidebarProvider>
      <AppSidebar variant="inset" />
      <SidebarInset>
        {/* Header */}
        <header className="flex h-14 items-center gap-4 border-b bg-background px-6">
          <SidebarTrigger className="-ml-2" />
          <Separator orientation="vertical" className="h-6" />
          <div className="flex flex-1 items-center justify-between">
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-semibold">Analytics Epidemiológicos</h1>
              {grupoActual && (
                <Badge variant="outline" className="ml-2">
                  {grupoActual.nombre}
                </Badge>
              )}
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setFiltrosOpen(true)}
              >
                <Filter className="mr-2 h-4 w-4" />
                Filtros
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setConfigOpen(true)}
              >
                <Settings2 className="mr-2 h-4 w-4" />
                Configurar
              </Button>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1 p-6">
          {/* Info Banner */}
          <Alert className="mb-6 border-blue-200 bg-blue-50/50 dark:border-blue-900 dark:bg-blue-950/20">
            <Info className="h-4 w-4 text-blue-600 dark:text-blue-400" />
            <AlertDescription className="text-sm">
              <strong>Analytics Epidemiológicos</strong> - Selecciona un grupo de eventos,
              configura los filtros y genera visualizaciones interactivas para análisis
              epidemiológico profundo.
            </AlertDescription>
          </Alert>

          <div className="grid gap-6">
            {/* Configuración Section */}
            <div className="grid gap-4 md:grid-cols-3">
              {/* Selector de Grupo */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <Activity className="h-4 w-4" />
                    Grupo de Eventos
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <GrupoSelector
                    grupos={grupos}
                    grupoSeleccionado={grupoSeleccionado}
                    onSeleccionar={setGrupoSeleccionado}
                    isLoading={gruposQuery.isLoading}
                  />
                </CardContent>
              </Card>

              {/* Selector de Eventos */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <BarChart3 className="h-4 w-4" />
                    Eventos Específicos
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <EventoSelector
                    grupoId={grupoSeleccionado}
                    eventosSeleccionados={eventosSeleccionados}
                    onSeleccionar={setEventosSeleccionados}
                  />
                </CardContent>
              </Card>

              {/* Tipo de Visualización */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <PieChart className="h-4 w-4" />
                    Tipo de Gráfico
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <Select value={tipoGrafico} onValueChange={setTipoGrafico}>
                    <SelectTrigger>
                      <SelectValue placeholder="Selecciona tipo de gráfico" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="casos_por_edad">📊 Casos por Edad</SelectItem>
                      <SelectItem value="torta_sexo">🥧 Distribución por Sexo</SelectItem>
                      <SelectItem value="casos_mensual">📈 Evolución Mensual</SelectItem>
                      <SelectItem value="tabla">📋 Tabla de Datos</SelectItem>
                      <SelectItem value="historicos">📊 Históricos</SelectItem>
                      <SelectItem value="corredor_endemico">📈 Corredor Endémico</SelectItem>
                    </SelectContent>
                  </Select>
                </CardContent>
              </Card>
            </div>

            {/* Filtros Rápidos */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                  <Filter className="h-4 w-4" />
                  Filtros Rápidos
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 md:grid-cols-4">
                  {/* Clasificación */}
                  <div>
                    <label className="text-xs font-medium text-muted-foreground mb-2 block">
                      Clasificación
                    </label>
                    <Select value={clasificacion} onValueChange={setClasificacion}>
                      <SelectTrigger className="h-8">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="todos">Todos</SelectItem>
                        <SelectItem value="confirmados">✅ Confirmados</SelectItem>
                        <SelectItem value="sospechosos">⚠️ Sospechosos</SelectItem>
                        <SelectItem value="probables">🔍 Probables</SelectItem>
                        <SelectItem value="negativos">❌ Negativos</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Fecha Desde */}
                  <div>
                    <label className="text-xs font-medium text-muted-foreground mb-2 block">
                      Desde
                    </label>
                    <input
                      type="date"
                      value={fechaDesde}
                      onChange={(e) => setFechaDesde(e.target.value)}
                      className="h-8 w-full px-3 rounded-md border border-input bg-background text-sm"
                    />
                  </div>

                  {/* Fecha Hasta */}
                  <div>
                    <label className="text-xs font-medium text-muted-foreground mb-2 block">
                      Hasta
                    </label>
                    <input
                      type="date"
                      value={fechaHasta}
                      onChange={(e) => setFechaHasta(e.target.value)}
                      className="h-8 w-full px-3 rounded-md border border-input bg-background text-sm"
                    />
                  </div>

                  {/* Botón Generar */}
                  <div className="flex items-end">
                    <Button
                      onClick={handleGenerarVisualizacion}
                      disabled={!tieneConfiguracionCompleta || generandoGrafico}
                      size="sm"
                      className="w-full h-8"
                    >
                      {generandoGrafico ? (
                        <Loader2 className="mr-2 h-3 w-3 animate-spin" />
                      ) : (
                        <Play className="mr-2 h-3 w-3" />
                      )}
                      Generar
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Visualización */}
            {tieneConfiguracionCompleta && (
              <VisualizacionContainer
                grupoId={grupoSeleccionado!}
                eventosSeleccionados={eventosSeleccionados}
                tipoGrafico={tipoGrafico}
                clasificacion={clasificacion}
                fechaDesde={fechaDesde}
                fechaHasta={fechaHasta}
                generando={generandoGrafico}
              />
            )}

            {/* Empty State */}
            {!grupoSeleccionado && (
              <Card className="p-12">
                <div className="text-center">
                  <Activity className="mx-auto h-12 w-12 text-muted-foreground opacity-50 mb-4" />
                  <h3 className="text-lg font-medium mb-2">
                    Selecciona un Grupo de Eventos
                  </h3>
                  <p className="text-sm text-muted-foreground max-w-md mx-auto">
                    Elige un grupo de eventos epidemiológicos para comenzar a generar
                    visualizaciones y análisis detallados.
                  </p>
                </div>
              </Card>
            )}
          </div>
        </main>

        {/* Sheet de Filtros Avanzados */}
        <Sheet open={filtrosOpen} onOpenChange={setFiltrosOpen}>
          <SheetContent className="w-full sm:max-w-md">
            <SheetHeader>
              <SheetTitle>Filtros Avanzados</SheetTitle>
            </SheetHeader>
            <div className="mt-6">
              <FiltrosPanel
                onClose={() => setFiltrosOpen(false)}
                // Aquí irían más filtros avanzados
              />
            </div>
          </SheetContent>
        </Sheet>

        {/* Sheet de Configuración */}
        <Sheet open={configOpen} onOpenChange={setConfigOpen}>
          <SheetContent className="w-full sm:max-w-md">
            <SheetHeader>
              <SheetTitle>Configuración</SheetTitle>
            </SheetHeader>
            <div className="mt-6">
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium mb-2">Exportar Datos</h4>
                  <Button variant="outline" size="sm" className="w-full">
                    <Download className="mr-2 h-4 w-4" />
                    Exportar CSV
                  </Button>
                </div>
                
                <div>
                  <h4 className="font-medium mb-2">Configuración de Gráfico</h4>
                  <p className="text-sm text-muted-foreground">
                    Personaliza colores, etiquetas y formato de visualización.
                  </p>
                  <Button variant="outline" size="sm" className="w-full mt-2" disabled>
                    Próximamente
                  </Button>
                </div>
              </div>
            </div>
          </SheetContent>
        </Sheet>
      </SidebarInset>
    </SidebarProvider>
  );
}