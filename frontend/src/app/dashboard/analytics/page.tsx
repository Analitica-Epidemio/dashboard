"use client";

/**
 * Analytics Page - Generación automática de boletines
 *
 * Muestra top eventos con mayor crecimiento/decrecimiento por grupo epidemiológico.
 * Permite seleccionar eventos y generar borradores de boletines automáticamente.
 */

import { useState } from "react";
import { useRouter } from "next/navigation";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/features/layout/components";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { Loader2, TrendingUp, TrendingDown, FileText, Info } from "lucide-react";
import { toast } from "sonner";
import { useTopChangesByGroup, useGenerateDraft, type EventoCambio } from "@/features/analytics/api";

export default function AnalyticsPage() {
  const router = useRouter();

  // State
  const [semanaActual, setSemanaActual] = useState(40);
  const [anioActual, setAnioActual] = useState(2025);
  const [numSemanas, setNumSemanas] = useState(4);
  const [eventosSeleccionados, setEventosSeleccionados] = useState<Set<number>>(new Set());

  // Data fetching
  const { data, isLoading } = useTopChangesByGroup({
    semana_actual: semanaActual,
    anio_actual: anioActual,
    num_semanas: numSemanas,
    limit: 10,
  });

  const generateBoletin = useGenerateDraft();

  // Handlers
  const toggleEvento = (id: number) => {
    const newSet = new Set(eventosSeleccionados);
    if (newSet.has(id)) {
      newSet.delete(id);
    } else {
      newSet.add(id);
    }
    setEventosSeleccionados(newSet);
  };

  const handleGenerar = async () => {
    if (eventosSeleccionados.size === 0) {
      toast.error("Debes seleccionar al menos un evento");
      return;
    }

    try {
      const result = await generateBoletin.mutateAsync({
        semana: semanaActual,
        anio: anioActual,
        num_semanas: numSemanas,
        eventos_seleccionados: Array.from(eventosSeleccionados).map((id) => ({
          tipo_eno_id: id,
          incluir_charts: true,
        })),
      });

      console.log("Generate result:", result);

      if (!result?.data?.boletin_instance_id) {
        console.error("No boletin_instance_id in response:", result);
        toast.error("Error: No se recibió ID del boletín");
        return;
      }

      toast.success("Boletín generado exitosamente");
      router.push(`/dashboard/boletines/instances/${result.data.boletin_instance_id}`);
    } catch (error) {
      console.error("Error generando boletín:", error);
      toast.error("Error al generar boletín");
    }
  };

  const topCrecimiento = data?.data?.top_crecimiento || [];
  const topDecrecimiento = data?.data?.top_decrecimiento || [];
  const periodoAnalisis = data?.data?.periodo_actual;

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
              <div className="flex items-center gap-3 mb-2">
                <FileText className="w-5 h-5 text-muted-foreground" />
                <h1 className="text-2xl font-semibold">
                  Generador de Boletines
                </h1>
              </div>
              <p className="text-sm text-muted-foreground">
                Analiza los eventos con mayores cambios y genera boletines automáticamente
              </p>
            </div>

            {/* Filtros */}
            <Card>
              <CardHeader>
                <CardTitle>Configuración del Análisis</CardTitle>
                <CardDescription>
                  Selecciona el período de análisis para identificar eventos relevantes
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="semana">Semana Epidemiológica</Label>
                    <Input
                      id="semana"
                      type="number"
                      min={1}
                      max={53}
                      value={semanaActual}
                      onChange={(e) => setSemanaActual(Number(e.target.value))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="anio">Año</Label>
                    <Input
                      id="anio"
                      type="number"
                      min={2020}
                      max={2030}
                      value={anioActual}
                      onChange={(e) => setAnioActual(Number(e.target.value))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="numSemanas">Número de Semanas</Label>
                    <Select
                      value={numSemanas.toString()}
                      onValueChange={(value) => setNumSemanas(Number(value))}
                    >
                      <SelectTrigger id="numSemanas">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="4">4 semanas</SelectItem>
                        <SelectItem value="8">8 semanas</SelectItem>
                        <SelectItem value="12">12 semanas</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                {periodoAnalisis && (
                  <div className="text-sm text-muted-foreground">
                    Período de análisis: Semanas {periodoAnalisis.semana_inicio} - {periodoAnalisis.semana_fin} del {periodoAnalisis.anio}
                    <br />
                    ({periodoAnalisis.fecha_inicio} - {periodoAnalisis.fecha_fin})
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Selected Events Summary */}
            {eventosSeleccionados.size > 0 && (
              <Card className="border-primary">
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span>Eventos Seleccionados ({eventosSeleccionados.size})</span>
                    <Button
                      onClick={handleGenerar}
                      disabled={generateBoletin.isPending}
                    >
                      {generateBoletin.isPending && (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      )}
                      Generar Boletín
                    </Button>
                  </CardTitle>
                </CardHeader>
              </Card>
            )}

            {/* Loading State */}
            {isLoading && (
              <div className="space-y-4">
                {[...Array(3)].map((_, i) => (
                  <Card key={i}>
                    <CardHeader>
                      <Skeleton className="h-6 w-48" />
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        {[...Array(5)].map((_, j) => (
                          <Skeleton key={j} className="h-12 w-full" />
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}

            {/* Empty State */}
            {!isLoading && topCrecimiento.length === 0 && topDecrecimiento.length === 0 && (
              <Card>
                <CardContent className="py-12">
                  <div className="text-center text-muted-foreground">
                    No se encontraron cambios significativos en el período seleccionado
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Top Crecimiento - Tabla Global */}
            {!isLoading && topCrecimiento.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5 text-red-600" />
                    Top 10 - Mayor Crecimiento
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Info className="h-4 w-4 text-muted-foreground cursor-help" />
                        </TooltipTrigger>
                        <TooltipContent className="max-w-xs">
                          <p className="font-semibold mb-1">¿Cómo se calculan los rankings?</p>
                          <p className="text-sm">
                            Se compara el número de casos del período actual con el período anterior del mismo tamaño.
                            Los eventos se ordenan por el porcentaje de cambio, mostrando aquellos con mayor incremento relativo.
                          </p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  </CardTitle>
                  <CardDescription>
                    Eventos con mayor incremento de casos en el período analizado
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="rounded-md border">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead className="w-[50px]"></TableHead>
                          <TableHead>Evento</TableHead>
                          <TableHead>Grupo</TableHead>
                          <TableHead className="text-right">
                            <TooltipProvider>
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <span className="cursor-help">Anterior</span>
                                </TooltipTrigger>
                                <TooltipContent>
                                  <p className="text-sm">Casos en el período anterior de igual duración</p>
                                </TooltipContent>
                              </Tooltip>
                            </TooltipProvider>
                          </TableHead>
                          <TableHead className="text-right">
                            <TooltipProvider>
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <span className="cursor-help">Actual</span>
                                </TooltipTrigger>
                                <TooltipContent>
                                  <p className="text-sm">Casos en el período seleccionado</p>
                                </TooltipContent>
                              </Tooltip>
                            </TooltipProvider>
                          </TableHead>
                          <TableHead className="text-right">
                            <TooltipProvider>
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <span className="cursor-help">Cambio</span>
                                </TooltipTrigger>
                                <TooltipContent>
                                  <p className="text-sm">Variación porcentual: ((Actual - Anterior) / Anterior) × 100%</p>
                                </TooltipContent>
                              </Tooltip>
                            </TooltipProvider>
                          </TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {topCrecimiento.map((evento: EventoCambio) => (
                          <TableRow key={evento.tipo_eno_id}>
                            <TableCell>
                              <Checkbox
                                checked={eventosSeleccionados.has(evento.tipo_eno_id)}
                                onCheckedChange={() => toggleEvento(evento.tipo_eno_id)}
                              />
                            </TableCell>
                            <TableCell className="font-medium">
                              {evento.tipo_eno_nombre}
                            </TableCell>
                            <TableCell>
                              <Badge variant="outline">{evento.grupo_eno_nombre}</Badge>
                            </TableCell>
                            <TableCell className="text-right tabular-nums">
                              {evento.casos_anteriores}
                            </TableCell>
                            <TableCell className="text-right tabular-nums font-semibold">
                              {evento.casos_actuales}
                            </TableCell>
                            <TableCell className="text-right">
                              <Badge variant="secondary" className="bg-red-50 text-red-700">
                                <TrendingUp className="h-3 w-3 mr-1" />
                                +{evento.diferencia_porcentual.toFixed(1)}%
                              </Badge>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Top Decrecimiento - Tabla Global */}
            {!isLoading && topDecrecimiento.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingDown className="h-5 w-5 text-green-600" />
                    Top 10 - Mayor Decrecimiento
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Info className="h-4 w-4 text-muted-foreground cursor-help" />
                        </TooltipTrigger>
                        <TooltipContent className="max-w-xs">
                          <p className="font-semibold mb-1">¿Cómo se calculan los rankings?</p>
                          <p className="text-sm">
                            Se compara el número de casos del período actual con el período anterior del mismo tamaño.
                            Los eventos se ordenan por el porcentaje de cambio negativo, mostrando aquellos con mayor disminución relativa.
                          </p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  </CardTitle>
                  <CardDescription>
                    Eventos con mayor disminución de casos en el período analizado
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="rounded-md border">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead className="w-[50px]"></TableHead>
                          <TableHead>Evento</TableHead>
                          <TableHead>Grupo</TableHead>
                          <TableHead className="text-right">
                            <TooltipProvider>
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <span className="cursor-help">Anterior</span>
                                </TooltipTrigger>
                                <TooltipContent>
                                  <p className="text-sm">Casos en el período anterior de igual duración</p>
                                </TooltipContent>
                              </Tooltip>
                            </TooltipProvider>
                          </TableHead>
                          <TableHead className="text-right">
                            <TooltipProvider>
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <span className="cursor-help">Actual</span>
                                </TooltipTrigger>
                                <TooltipContent>
                                  <p className="text-sm">Casos en el período seleccionado</p>
                                </TooltipContent>
                              </Tooltip>
                            </TooltipProvider>
                          </TableHead>
                          <TableHead className="text-right">
                            <TooltipProvider>
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <span className="cursor-help">Cambio</span>
                                </TooltipTrigger>
                                <TooltipContent>
                                  <p className="text-sm">Variación porcentual: ((Actual - Anterior) / Anterior) × 100%</p>
                                </TooltipContent>
                              </Tooltip>
                            </TooltipProvider>
                          </TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {topDecrecimiento.map((evento: EventoCambio) => (
                          <TableRow key={evento.tipo_eno_id}>
                            <TableCell>
                              <Checkbox
                                checked={eventosSeleccionados.has(evento.tipo_eno_id)}
                                onCheckedChange={() => toggleEvento(evento.tipo_eno_id)}
                              />
                            </TableCell>
                            <TableCell className="font-medium">
                              {evento.tipo_eno_nombre}
                            </TableCell>
                            <TableCell>
                              <Badge variant="outline">{evento.grupo_eno_nombre}</Badge>
                            </TableCell>
                            <TableCell className="text-right tabular-nums">
                              {evento.casos_anteriores}
                            </TableCell>
                            <TableCell className="text-right tabular-nums font-semibold">
                              {evento.casos_actuales}
                            </TableCell>
                            <TableCell className="text-right">
                              <Badge variant="secondary" className="bg-green-50 text-green-700">
                                <TrendingDown className="h-3 w-3 mr-1" />
                                {evento.diferencia_porcentual.toFixed(1)}%
                              </Badge>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
