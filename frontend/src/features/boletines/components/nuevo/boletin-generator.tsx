"use client";

/**
 * Generador de Boletines Epidemiológicos
 * Flujo dinámico basado en eventos disponibles del backend
 */

import { useState, useCallback, useMemo } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Loader2,
  FileText,
  Calendar,
  CheckCircle2,
  Info,
  Plus,
  Search,
  X,
  GripVertical,
} from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { $api } from "@/lib/api/client";
import {
  useEventosDisponibles,
  useEventoPreview,
} from "@/features/boletines/api";
import {
  getIconForEvento,
  getColorForEvento,
  getZonaLabel,
  type ZonaEpidemica,
} from "./section-definitions";

// ============================================================================
// TYPES
// ============================================================================

interface EventoSeleccionado {
  id: number;
  codigo: string;
  nombre: string;
  tipo: "tipo_eno" | "grupo_eno" | "grupo_de_enfermedades";
  order: number;
}

// ============================================================================
// HELPERS
// ============================================================================

function getCurrentEpiWeek(): { semana: number; anio: number } {
  const now = new Date();
  const startOfYear = new Date(now.getFullYear(), 0, 1);
  const days = Math.floor((now.getTime() - startOfYear.getTime()) / 86400000);
  const weekNumber = Math.ceil((days + startOfYear.getDay() + 1) / 7);
  return {
    semana: Math.min(weekNumber, 52),
    anio: now.getFullYear(),
  };
}

// ============================================================================
// EVENTO PREVIEW CARD
// ============================================================================

interface EventoPreviewCardProps {
  evento: EventoSeleccionado;
  semana: number;
  anio: number;
  numSemanas: number;
  onRemove: () => void;
}

function EventoPreviewCard({
  evento,
  semana,
  anio,
  numSemanas,
  onRemove,
}: EventoPreviewCardProps) {
  const { data, isLoading, error } = useEventoPreview({
    codigo: evento.codigo,
    semana,
    anio,
    numSemanas,
  });

  const Icon = getIconForEvento(evento.nombre);
  const color = getColorForEvento(evento.nombre);

  const colorClasses: Record<string, { bg: string; border: string; icon: string }> = {
    slate: { bg: "bg-slate-50", border: "border-slate-200", icon: "text-slate-600" },
    blue: { bg: "bg-blue-50", border: "border-blue-200", icon: "text-blue-600" },
    orange: { bg: "bg-orange-50", border: "border-orange-200", icon: "text-orange-600" },
    cyan: { bg: "bg-cyan-50", border: "border-cyan-200", icon: "text-cyan-600" },
    red: { bg: "bg-red-50", border: "border-red-200", icon: "text-red-600" },
    purple: { bg: "bg-purple-50", border: "border-purple-200", icon: "text-purple-600" },
    amber: { bg: "bg-amber-50", border: "border-amber-200", icon: "text-amber-600" },
    rose: { bg: "bg-rose-50", border: "border-rose-200", icon: "text-rose-600" },
  };

  const colors = colorClasses[color] || colorClasses.slate;
  const preview = data?.data;

  return (
    <Card className={cn("transition-all", colors.border)}>
      <CardHeader className="pb-2">
        <div className="flex items-start gap-3">
          {/* Drag handle */}
          <GripVertical className="h-5 w-5 text-muted-foreground/50 cursor-grab mt-1" />

          {/* Icon */}
          <div className={cn("p-2 rounded-lg", colors.bg)}>
            <Icon className={cn("h-5 w-5", colors.icon)} />
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-medium text-sm">{evento.nombre}</h3>
                <Badge variant="outline" className="text-xs mt-1">
                  {evento.tipo === "tipo_eno" ? "Tipo ENO" : "Grupo ENO"}
                </Badge>
              </div>
              <Button
                variant="ghost"
                size="sm"
                className="h-7 w-7 p-0 text-muted-foreground hover:text-destructive"
                onClick={onRemove}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>

            {/* Preview data */}
            <div className="mt-3 pt-3 border-t">
              {isLoading ? (
                <div className="space-y-2">
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-4 w-1/2" />
                </div>
              ) : error ? (
                <p className="text-sm text-red-600">Error al cargar datos</p>
              ) : preview ? (
                <div className="space-y-2">
                  {/* Corredor zone */}
                  {preview.corredor && (
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-muted-foreground">Zona:</span>
                      <ZonaBadge zona={preview.corredor.zona_actual as ZonaEpidemica} />
                      {preview.corredor.porcentaje_cambio !== undefined && (
                        <span className={cn(
                          "text-xs",
                          preview.corredor.tendencia === "up" ? "text-red-600" :
                            preview.corredor.tendencia === "down" ? "text-green-600" :
                              "text-gray-500"
                        )}>
                          {preview.corredor.tendencia === "up" ? "↑" :
                            preview.corredor.tendencia === "down" ? "↓" : "→"}
                          {Math.abs(preview.corredor.porcentaje_cambio ?? 0).toFixed(1)}%
                        </span>
                      )}
                    </div>
                  )}

                  {/* Metrics */}
                  {preview.metrics && preview.metrics.length > 0 && (
                    <div className="grid grid-cols-2 gap-2">
                      {preview.metrics.slice(0, 4).map((metric, i) => (
                        <div key={i} className="text-xs">
                          <span className="text-muted-foreground">{metric.label}:</span>{" "}
                          <span className="font-medium">{metric.value}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Summary */}
                  {preview.summary && (
                    <p className="text-xs text-muted-foreground italic mt-1">
                      {preview.summary}
                    </p>
                  )}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">Sin datos disponibles</p>
              )}
            </div>
          </div>
        </div>
      </CardHeader>
    </Card>
  );
}

function ZonaBadge({ zona }: { zona: ZonaEpidemica }) {
  const colorMap: Record<ZonaEpidemica, string> = {
    exito: "bg-green-100 text-green-800 border-green-300",
    seguridad: "bg-yellow-100 text-yellow-800 border-yellow-300",
    alerta: "bg-orange-100 text-orange-800 border-orange-300",
    brote: "bg-red-100 text-red-800 border-red-300",
  };

  return (
    <Badge variant="outline" className={cn("text-xs font-medium", colorMap[zona])}>
      {getZonaLabel(zona)}
    </Badge>
  );
}

// ============================================================================
// EVENTO SELECTOR
// ============================================================================

interface EventoSelectorProps {
  onSelect: (evento: { id: number; codigo: string; nombre: string; tipo: "tipo_eno" | "grupo_eno" | "grupo_de_enfermedades" }) => void;
  selectedCodigos: string[];
}

function EventoSelector({ onSelect, selectedCodigos }: EventoSelectorProps) {
  const { data, isLoading } = useEventosDisponibles();
  const [search, setSearch] = useState("");
  const [isOpen, setIsOpen] = useState(false);

  const filteredEventos = useMemo(() => {
    const eventos = data?.data || [];
    if (!search) return eventos;
    const searchLower = search.toLowerCase();
    return eventos.filter(
      (e) =>
        e.nombre.toLowerCase().includes(searchLower) ||
        e.codigo.toLowerCase().includes(searchLower)
    );
  }, [data?.data, search]);

  // Group by tipo
  const grupoEnos = filteredEventos.filter((e) => e.tipo === "grupo_de_enfermedades");
  const tipoEnos = filteredEventos.filter((e) => e.tipo === "tipo_eno");

  return (
    <div className="space-y-2">
      <Button
        variant="outline"
        className="w-full justify-start"
        onClick={() => setIsOpen(!isOpen)}
      >
        <Plus className="h-4 w-4 mr-2" />
        Agregar evento al boletín
      </Button>

      {isOpen && (
        <Card>
          <CardContent className="pt-4">
            {/* Search */}
            <div className="relative mb-4">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Buscar evento..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>

            {isLoading ? (
              <div className="space-y-2">
                <Skeleton className="h-8 w-full" />
                <Skeleton className="h-8 w-full" />
                <Skeleton className="h-8 w-full" />
              </div>
            ) : (
              <div className="max-h-64 overflow-y-auto space-y-4">
                {/* Grupos ENO */}
                {grupoEnos.length > 0 && (
                  <div>
                    <h4 className="text-xs font-semibold text-muted-foreground mb-2">
                      GRUPOS DE EVENTOS
                    </h4>
                    <div className="space-y-1">
                      {grupoEnos.map((evento) => {
                        const isSelected = selectedCodigos.includes(evento.codigo);
                        return (
                          <button
                            key={evento.codigo}
                            onClick={() => {
                              if (!isSelected) {
                                onSelect({
                                  id: evento.id,
                                  codigo: evento.codigo,
                                  nombre: evento.nombre,
                                  tipo: evento.tipo,
                                });
                              }
                            }}
                            disabled={isSelected}
                            className={cn(
                              "w-full text-left px-3 py-2 rounded-md text-sm transition-colors",
                              isSelected
                                ? "bg-muted text-muted-foreground cursor-not-allowed"
                                : "hover:bg-accent"
                            )}
                          >
                            <div className="flex items-center justify-between">
                              <span>{evento.nombre}</span>
                              {isSelected && (
                                <CheckCircle2 className="h-4 w-4 text-green-600" />
                              )}
                            </div>
                            <span className="text-xs text-muted-foreground">
                              {evento.codigo}
                            </span>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Tipos ENO */}
                {tipoEnos.length > 0 && (
                  <div>
                    <h4 className="text-xs font-semibold text-muted-foreground mb-2">
                      TIPOS DE EVENTOS
                    </h4>
                    <div className="space-y-1">
                      {tipoEnos.map((evento) => {
                        const isSelected = selectedCodigos.includes(evento.codigo);
                        return (
                          <button
                            key={evento.codigo}
                            onClick={() => {
                              if (!isSelected) {
                                onSelect({
                                  id: evento.id,
                                  codigo: evento.codigo,
                                  nombre: evento.nombre,
                                  tipo: evento.tipo,
                                });
                              }
                            }}
                            disabled={isSelected}
                            className={cn(
                              "w-full text-left px-3 py-2 rounded-md text-sm transition-colors",
                              isSelected
                                ? "bg-muted text-muted-foreground cursor-not-allowed"
                                : "hover:bg-accent"
                            )}
                          >
                            <div className="flex items-center justify-between">
                              <span>{evento.nombre}</span>
                              {isSelected && (
                                <CheckCircle2 className="h-4 w-4 text-green-600" />
                              )}
                            </div>
                            <span className="text-xs text-muted-foreground">
                              {evento.codigo}
                            </span>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}

                {filteredEventos.length === 0 && (
                  <p className="text-sm text-muted-foreground text-center py-4">
                    No se encontraron eventos
                  </p>
                )}
              </div>
            )}

            <div className="mt-4 pt-4 border-t">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsOpen(false)}
                className="w-full"
              >
                Cerrar
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export function BoletinGenerator() {
  const router = useRouter();
  const currentWeek = getCurrentEpiWeek();

  // Form state
  const [semana, setSemana] = useState(currentWeek.semana);
  const [anio, setAnio] = useState(currentWeek.anio);
  const [numSemanas, setNumSemanas] = useState(4);
  const [tituloCustom, setTituloCustom] = useState("");

  // Selected eventos
  const [eventosSeleccionados, setEventosSeleccionados] = useState<EventoSeleccionado[]>([]);

  // Loading state
  const [isGenerating, setIsGenerating] = useState(false);

  // Generate mutation
  const generateMutation = $api.useMutation("post", "/api/v1/boletines/generate-draft");

  // Add evento
  const handleAddEvento = useCallback(
    (evento: { id: number; codigo: string; nombre: string; tipo: "tipo_eno" | "grupo_eno" | "grupo_de_enfermedades" }) => {
      setEventosSeleccionados((prev) => [
        ...prev,
        {
          ...evento,
          order: prev.length,
        },
      ]);
    },
    []
  );

  // Remove evento
  const handleRemoveEvento = useCallback((codigo: string) => {
    setEventosSeleccionados((prev) =>
      prev.filter((e) => e.codigo !== codigo).map((e, i) => ({ ...e, order: i }))
    );
  }, []);

  // Selected codigos for the selector
  const selectedCodigos = useMemo(
    () => eventosSeleccionados.map((e) => e.codigo),
    [eventosSeleccionados]
  );

  // Calculate date range
  const periodoInfo = useMemo(() => {
    const semanaInicio = Math.max(1, semana - numSemanas + 1);
    return {
      semanaInicio,
      semanaFin: semana,
    };
  }, [semana, numSemanas]);

  // Handle generate
  const handleGenerate = async () => {
    if (eventosSeleccionados.length === 0) {
      toast.error("Debes seleccionar al menos un evento");
      return;
    }

    setIsGenerating(true);

    try {
      const result = await generateMutation.mutateAsync({
        body: {
          semana,
          anio,
          num_semanas: numSemanas,
          eventos_seleccionados: eventosSeleccionados.map((e) => ({
            tipo_eno_id: e.id,
            incluir_charts: true,
          })),
          titulo_custom: tituloCustom || undefined,
        },
      });

      if (result?.data?.boletin_instance_id) {
        toast.success("Boletín generado exitosamente");
        router.push(`/dashboard/boletines/instances/${result.data.boletin_instance_id}`);
      }
    } catch (error) {
      console.error("Error generando boletín:", error);
      toast.error("Error al generar el boletín");
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Period Configuration */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Calendar className="h-5 w-5 text-muted-foreground" />
            <CardTitle className="text-lg">Período del Boletín</CardTitle>
          </div>
          <CardDescription>
            Selecciona la semana epidemiológica y el rango de análisis
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="space-y-2">
              <Label htmlFor="semana">Semana Epidemiológica</Label>
              <Input
                id="semana"
                type="number"
                min={1}
                max={53}
                value={semana}
                onChange={(e) => setSemana(parseInt(e.target.value) || 1)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="anio">Año</Label>
              <Input
                id="anio"
                type="number"
                min={2020}
                max={2030}
                value={anio}
                onChange={(e) => setAnio(parseInt(e.target.value) || 2025)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="numSemanas">Semanas a analizar</Label>
              <Select
                value={numSemanas.toString()}
                onValueChange={(v) => setNumSemanas(parseInt(v))}
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

            <div className="space-y-2">
              <Label htmlFor="titulo">Título (opcional)</Label>
              <Input
                id="titulo"
                placeholder={`Boletín SE ${semana}/${anio}`}
                value={tituloCustom}
                onChange={(e) => setTituloCustom(e.target.value)}
              />
            </div>
          </div>

          <div className="mt-4 p-3 bg-muted/50 rounded-md">
            <p className="text-sm text-muted-foreground">
              <strong>Período de análisis:</strong> SE {periodoInfo.semanaInicio} a SE{" "}
              {periodoInfo.semanaFin} del {anio}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Eventos Selection */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-muted-foreground" />
              <CardTitle className="text-lg">Eventos a Incluir</CardTitle>
            </div>
            <Badge variant="secondary">
              {eventosSeleccionados.length} evento{eventosSeleccionados.length !== 1 ? "s" : ""}
            </Badge>
          </div>
          <CardDescription>
            Selecciona los eventos epidemiológicos que deseas incluir en el boletín.
            Los datos se cargarán automáticamente del período seleccionado.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Evento Selector */}
          <EventoSelector
            onSelect={handleAddEvento}
            selectedCodigos={selectedCodigos}
          />

          {/* Selected eventos */}
          {eventosSeleccionados.length > 0 ? (
            <div className="space-y-3">
              {eventosSeleccionados.map((evento) => (
                <EventoPreviewCard
                  key={evento.codigo}
                  evento={evento}
                  semana={semana}
                  anio={anio}
                  numSemanas={numSemanas}
                  onRemove={() => handleRemoveEvento(evento.codigo)}
                />
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No hay eventos seleccionados</p>
              <p className="text-sm mt-1">
                Usa el botón de arriba para agregar eventos al boletín
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Fixed Content Info */}
      <Alert>
        <Info className="h-4 w-4" />
        <AlertDescription>
          <strong>Contenido fijo incluido automáticamente:</strong> Portada, Introducción,
          Autoridades, Autoría, Índice, Metodología, Material de consulta, Anexos y Footer
          institucional.
        </AlertDescription>
      </Alert>

      {/* Actions */}
      <div className="flex items-center justify-between pt-4 border-t">
        <div className="text-sm text-muted-foreground">
          {eventosSeleccionados.length > 0 ? (
            <span className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-green-600" />
              {eventosSeleccionados.length} evento{eventosSeleccionados.length !== 1 ? "s" : ""}{" "}
              seleccionado{eventosSeleccionados.length !== 1 ? "s" : ""}
            </span>
          ) : (
            <span className="text-amber-600">Selecciona al menos un evento</span>
          )}
        </div>

        <div className="flex gap-3">
          <Button
            variant="outline"
            onClick={() => router.push("/dashboard/boletines")}
          >
            Cancelar
          </Button>
          <Button
            onClick={handleGenerate}
            disabled={isGenerating || eventosSeleccionados.length === 0}
            className="min-w-[160px]"
          >
            {isGenerating ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Generando...
              </>
            ) : (
              <>
                <FileText className="mr-2 h-4 w-4" />
                Generar Boletín
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
