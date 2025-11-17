"use client";

import React, { useState } from "react";
import {
  Calendar,
  MapPin,
  User,
  Activity,
  FileText,
  Hash,
  Clock,
  Shield,
  AlertTriangle,
  Info,
  Heart,
  Syringe,
  TestTube,
  Stethoscope,
  Search,
  Building,
  ChevronDown,
  ChevronRight,
  ExternalLink,
  Users,
  UserCheck,
  Pill,
  Bed,
  FlaskConical,
  MapPinned,
  BadgeCheck,
  Baby,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import {
  useEvento,
  useEventoTimeline,
  getClasificacionLabel,
  getClasificacionColorClasses,
} from "@/features/eventos/api";
import { cn } from "@/lib/utils";
import type { components } from "@/lib/api/types";

// Trazabilidad types - using generic object since specific schemas are not in OpenAPI
type TrazabilidadClasificacion = {
  razon: string;
  mensaje?: string;
  regla_nombre?: string;
  regla_prioridad?: number;
  clasificacion_aplicada?: string;
  condiciones_evaluadas?: Array<{
    campo: string;
    operador: string;
    valor_esperado: unknown;
    valor_real: unknown;
    cumple: boolean;
    resultado?: boolean;
    tipo_filtro?: string;
    config?: {
      value?: unknown;
      values?: unknown;
    };
    valor_campo?: string;
  }>;
  reglas_evaluadas?: Array<{
    regla_nombre: string;
    regla_prioridad: number;
    condiciones_cumplidas: number;
    condiciones_totales: number;
    condiciones: Array<{
      campo: string;
      operador: string;
      valor_esperado: unknown;
      valor_real: unknown;
      cumple: boolean;
      resultado?: boolean;
      tipo_filtro?: string;
      config?: {
        value?: unknown;
        values?: unknown;
      };
      valor_campo?: string;
    }>;
  }>;
  [key: string]: unknown;
};

type TrazabilidadReglaAplicada = TrazabilidadClasificacion & {
  razon: "regla_aplicada";
  regla_nombre: string;
  clasificacion_aplicada: string;
};

type TrazabilidadEvaluando = TrazabilidadClasificacion & {
  razon: "evaluando";
};

type TrazabilidadRequiereRevision = TrazabilidadClasificacion & {
  razon: "requiere_revision";
};

type TrazabilidadSinEstrategia = TrazabilidadClasificacion & {
  razon: "sin_estrategia";
};

type TrazabilidadError = TrazabilidadClasificacion & {
  razon: "error";
};

function isReglaAplicada(
  traz: TrazabilidadClasificacion
): traz is TrazabilidadReglaAplicada {
  return traz.razon === "regla_aplicada";
}

function isEvaluando(
  traz: TrazabilidadClasificacion
): traz is TrazabilidadEvaluando {
  return traz.razon === "evaluando";
}

function isRequiereRevision(
  traz: TrazabilidadClasificacion
): traz is TrazabilidadRequiereRevision {
  return traz.razon === "requiere_revision";
}

function isSinEstrategia(
  traz: TrazabilidadClasificacion
): traz is TrazabilidadSinEstrategia {
  return traz.razon === "sin_estrategia";
}

function isError(
  traz: TrazabilidadClasificacion
): traz is TrazabilidadError {
  return traz.razon === "error";
}

interface EventoDetailProps {
  eventoId: number;
  onClose?: () => void;
}

// Collapsible Section Component
function CollapsibleSection({
  title,
  icon: Icon,
  children,
  defaultOpen = true,
  count,
  isEmpty = false,
}: {
  title: string;
  icon: React.ComponentType<{ className?: string }>;
  children: React.ReactNode;
  defaultOpen?: boolean;
  count?: number;
  isEmpty?: boolean;
}) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className="rounded-lg border border-border bg-card mb-3">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex w-full items-center justify-between py-3 px-4 text-left hover:bg-muted/50 transition-colors rounded-t-lg"
      >
        <div className="flex items-center gap-3">
          <Icon className="h-4 w-4 text-muted-foreground" />
          <h3 className="text-sm font-semibold">{title}</h3>
          {count !== undefined && count > 0 && (
            <span className="text-xs text-muted-foreground">({count})</span>
          )}
        </div>
        {isOpen ? (
          <ChevronDown className="h-4 w-4 text-muted-foreground" />
        ) : (
          <ChevronRight className="h-4 w-4 text-muted-foreground" />
        )}
      </button>
      {isOpen && (
        <div className={cn("px-4 pb-4", isEmpty && "pb-3")}>{children}</div>
      )}
    </div>
  );
}

// Empty State Component
function EmptyState({
  icon: Icon,
  title,
  description,
}: {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  description: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-8 text-center">
      <div className="rounded-full bg-muted p-3 mb-3">
        <Icon className="h-6 w-6 text-muted-foreground" />
      </div>
      <h4 className="text-sm font-medium mb-1">{title}</h4>
      <p className="text-xs text-muted-foreground max-w-sm">{description}</p>
    </div>
  );
}

// Data Row Component (key-value pairs)
function DataRow({
  label,
  value,
  icon: Icon,
}: {
  label: string;
  value: string | React.ReactNode;
  icon?: React.ComponentType<{ className?: string }>;
}) {
  return (
    <div className="flex items-start justify-between py-2 text-sm">
      <div className="flex items-center gap-2 text-muted-foreground">
        {Icon && <Icon className="h-3.5 w-3.5" />}
        <span>{label}</span>
      </div>
      <span className="font-medium text-right">{value}</span>
    </div>
  );
}

export function EventoDetailModern({ eventoId, onClose }: EventoDetailProps) {
  const eventoQuery = useEvento(eventoId);
  const timelineQuery = useEventoTimeline(eventoId);

  const evento = eventoQuery.data?.data;
  const timelineData = timelineQuery.data?.data;
  const timeline = timelineData?.items || [];
  const isLoading = eventoQuery.isLoading;
  const error = eventoQuery.error;

  // Cast trazabilidad_clasificacion to our defined type
  const trazabilidad = evento?.trazabilidad_clasificacion as TrazabilidadClasificacion | null;

  // Formatear fecha
  const formatDate = (date: string | null | undefined) => {
    if (!date) return "No especificada";
    return new Date(date).toLocaleDateString("es-ES", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  const formatDateLong = (date: string | null | undefined) => {
    if (!date) return "No especificada";
    return new Date(date).toLocaleDateString("es-ES", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  // Calcular edad desde fecha de nacimiento
  const calcularEdad = (fechaNacimiento: string | null | undefined) => {
    if (!fechaNacimiento) return null;
    const hoy = new Date();
    const nacimiento = new Date(fechaNacimiento);
    let edad = hoy.getFullYear() - nacimiento.getFullYear();
    const mes = hoy.getMonth() - nacimiento.getMonth();
    if (mes < 0 || (mes === 0 && hoy.getDate() < nacimiento.getDate())) {
      edad--;
    }
    return edad;
  };

  // Expandir sexo a texto completo
  const getSexoCompleto = (sexo: string | null | undefined) => {
    if (!sexo) return "No especificado";
    const sexoLower = sexo.toLowerCase();
    if (sexoLower === "m" || sexoLower === "masculino") return "Masculino";
    if (sexoLower === "f" || sexoLower === "femenino") return "Femenino";
    return sexo;
  };

  // Loading State - More specific skeletons
  if (isLoading) {
    return (
      <div className="px-6 py-6 space-y-6">
        {/* Header skeleton */}
        <div className="space-y-3">
          <Skeleton className="h-6 w-48" />
          <div className="flex gap-2">
            <Skeleton className="h-5 w-24" />
            <Skeleton className="h-5 w-32" />
          </div>
          <Skeleton className="h-4 w-64" />
        </div>

        {/* Stats skeleton */}
        <div className="grid grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="space-y-2">
              <Skeleton className="h-4 w-16" />
              <Skeleton className="h-8 w-12" />
            </div>
          ))}
        </div>

        <Separator />

        {/* Content skeleton */}
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="space-y-2">
              <Skeleton className="h-5 w-32" />
              <Skeleton className="h-16 w-full" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Error State
  if (error || !evento) {
    return (
      <div className="px-6 py-12 flex flex-col items-center justify-center">
        <div className="rounded-full bg-destructive/10 p-3 mb-4">
          <AlertTriangle className="h-8 w-8 text-destructive" />
        </div>
        <h3 className="text-lg font-semibold mb-2">Error al cargar evento</h3>
        <p className="text-sm text-muted-foreground mb-4">
          No pudimos cargar la información del evento. Por favor, intenta
          nuevamente.
        </p>
        {onClose && (
          <Button variant="outline" onClick={onClose}>
            Cerrar
          </Button>
        )}
      </div>
    );
  }

  // Determine subject info
  const subjectName = evento.ciudadano
    ? `${evento.ciudadano.nombre} ${evento.ciudadano.apellido}`
    : evento.animal
    ? evento.animal.identificacion || `Animal #${evento.animal.id}`
    : "Sujeto no identificado";

  const subjectType = evento.ciudadano
    ? "Humano"
    : evento.animal
    ? "Animal"
    : "Desconocido";

  return (
    <div className="px-6 py-6 space-y-6">
      {/* Hero Header - Key Information */}
      <div className="space-y-4">
        {/* Title & ID */}
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1 flex-1">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Hash className="h-3 w-3" />
              <span>Evento {evento.id_evento_caso}</span>
              <span>•</span>
              <span>{subjectType}</span>
            </div>
            <h1 className="text-2xl font-semibold tracking-tight">
              {subjectName}
            </h1>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Activity className="h-4 w-4" />
              <span>
                {evento.tipo_eno_nombre || `Tipo ${evento.tipo_eno_id}`}
              </span>
            </div>
          </div>

          {/* Classification Badge */}
          {evento.clasificacion_estrategia && (
            <Badge
              className={cn(
                "px-3 py-1.5 text-sm font-medium",
                getClasificacionColorClasses(evento.clasificacion_estrategia)
              )}
            >
              {getClasificacionLabel(evento.clasificacion_estrategia)}
            </Badge>
          )}
        </div>

        {/* Metadata */}
        <div className="flex flex-wrap items-center gap-4 text-sm">
          <div className="flex items-center gap-1.5 text-muted-foreground">
            <Calendar className="h-4 w-4" />
            <span>{formatDateLong(evento.fecha_minima_evento)}</span>
          </div>
          {evento.confidence_score && (
            <div className="flex items-center gap-1.5 text-muted-foreground">
              <Shield className="h-4 w-4" />
              <span>
                Confianza: {(evento.confidence_score * 100).toFixed(0)}%
              </span>
            </div>
          )}
          {evento.requiere_revision_especie && (
            <Badge variant="destructive" className="text-xs">
              <AlertTriangle className="mr-1 h-3 w-3" />
              Requiere revisión
            </Badge>
          )}
        </div>

        {/* Observation Alert */}
        {evento.observaciones_texto && (
          <Alert className="bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-900">
            <Info className="h-4 w-4 text-blue-600 dark:text-blue-400" />
            <AlertDescription className="text-blue-900 dark:text-blue-100">
              {evento.observaciones_texto}
            </AlertDescription>
          </Alert>
        )}
      </div>

      <Separator />

      {/* Collapsible Sections */}
      <div className="space-y-0">
        {/* Información del Sujeto */}
        <CollapsibleSection
          title="Información del Sujeto"
          icon={User}
          isEmpty={!evento.ciudadano && !evento.animal}
        >
          {evento.ciudadano ? (
            <div className="space-y-4">
              <div className="grid gap-x-8 gap-y-3 md:grid-cols-2">
                <DataRow
                  label="Documento"
                  value={evento.ciudadano.documento || "No especificado"}
                />
                <DataRow
                  label="Fecha de nacimiento"
                  value={
                    <>
                      {formatDate(evento.ciudadano.fecha_nacimiento)}
                      {evento.ciudadano.fecha_nacimiento &&
                        calcularEdad(evento.ciudadano.fecha_nacimiento) !==
                          null && (
                          <span className="text-muted-foreground ml-2">
                            ({calcularEdad(evento.ciudadano.fecha_nacimiento)}{" "}
                            años)
                          </span>
                        )}
                    </>
                  }
                />
                <DataRow
                  label="Sexo"
                  value={getSexoCompleto(evento.ciudadano.sexo)}
                />
                {evento.ciudadano.telefono && (
                  <DataRow label="Teléfono" value={evento.ciudadano.telefono} />
                )}
              </div>

              {/* Domicilio */}
              {(evento.ciudadano.calle ||
                evento.ciudadano.numero ||
                evento.ciudadano.barrio ||
                evento.ciudadano.localidad ||
                evento.ciudadano.provincia) && (
                <div className="pt-4 border-t">
                  <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-3 flex items-center gap-2">
                    <MapPin className="h-3 w-3" />
                    Domicilio
                  </p>
                  <div className="space-y-2">
                    {evento.ciudadano.calle && (
                      <div className="flex items-baseline justify-between text-sm">
                        <span className="text-muted-foreground">Calle:</span>
                        <span className="font-medium text-right">
                          {evento.ciudadano.calle}
                        </span>
                      </div>
                    )}
                    {evento.ciudadano.numero && (
                      <div className="flex items-baseline justify-between text-sm">
                        <span className="text-muted-foreground">Número:</span>
                        <span className="font-medium text-right">
                          {evento.ciudadano.numero}
                        </span>
                      </div>
                    )}
                    {evento.ciudadano.barrio && (
                      <div className="flex items-baseline justify-between text-sm">
                        <span className="text-muted-foreground">Barrio:</span>
                        <span className="font-medium text-right">
                          {evento.ciudadano.barrio}
                        </span>
                      </div>
                    )}
                    {evento.ciudadano.localidad && (
                      <div className="flex items-baseline justify-between text-sm">
                        <span className="text-muted-foreground">
                          Localidad:
                        </span>
                        <span className="font-medium text-right">
                          {evento.ciudadano.localidad}
                        </span>
                      </div>
                    )}
                    {evento.ciudadano.provincia && (
                      <div className="flex items-baseline justify-between text-sm">
                        <span className="text-muted-foreground">
                          Provincia:
                        </span>
                        <span className="font-medium text-right">
                          {evento.ciudadano.provincia}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Datos adicionales si existen */}
              {(evento.ciudadano.es_embarazada !== null ||
                evento.ciudadano.cobertura_social ||
                evento.ciudadano.ocupacion_laboral) && (
                <div className="pt-4 border-t">
                  <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-3">
                    Información Adicional
                  </p>
                  <div className="grid gap-x-8 gap-y-3 md:grid-cols-2">
                    {evento.ciudadano.es_embarazada !== null && (
                      <DataRow
                        label="Embarazo"
                        icon={Baby}
                        value={
                          <Badge
                            variant={
                              evento.ciudadano.es_embarazada
                                ? "default"
                                : "outline"
                            }
                            className="text-xs"
                          >
                            {evento.ciudadano.es_embarazada ? "Sí" : "No"}
                          </Badge>
                        }
                      />
                    )}
                    {evento.ciudadano.cobertura_social && (
                      <DataRow
                        label="Cobertura social"
                        value={evento.ciudadano.cobertura_social}
                      />
                    )}
                    {evento.ciudadano.ocupacion_laboral && (
                      <DataRow
                        label="Ocupación"
                        value={evento.ciudadano.ocupacion_laboral}
                      />
                    )}
                  </div>
                </div>
              )}
            </div>
          ) : evento.animal ? (
            <div className="grid gap-x-8 gap-y-3 md:grid-cols-2">
              <DataRow
                label="Identificación"
                value={evento.animal.identificacion || "Sin nombre"}
              />
              <DataRow
                label="Especie"
                value={evento.animal.especie || "No especificada"}
              />
              <DataRow
                label="Raza"
                value={evento.animal.raza || "No especificada"}
              />
              <DataRow
                label="Provincia"
                value={evento.animal.provincia || "No especificada"}
                icon={MapPin}
              />
              <DataRow
                label="Localidad"
                value={evento.animal.localidad || "No especificada"}
              />
            </div>
          ) : (
            <EmptyState
              icon={User}
              title="Sin información del sujeto"
              description="No hay datos disponibles sobre el sujeto asociado a este evento"
            />
          )}
        </CollapsibleSection>

        {/* Fechas */}
        <CollapsibleSection title="Cronología" icon={Calendar}>
          {/* Semana epidemiológica destacada */}
          {evento.semana_epidemiologica_apertura &&
            evento.anio_epidemiologico_apertura && (
              <div className="mb-4 p-3 rounded-lg bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-900">
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                  <span className="text-sm font-medium text-blue-900 dark:text-blue-100">
                    Semana Epidemiológica{" "}
                    {evento.semana_epidemiologica_apertura}/
                    {evento.anio_epidemiologico_apertura}
                  </span>
                </div>
              </div>
            )}

          <div className="grid gap-x-8 gap-y-3 md:grid-cols-2">
            <DataRow
              label="Fecha del evento"
              value={formatDate(evento.fecha_minima_evento)}
            />
            {evento.fecha_inicio_sintomas && (
              <DataRow
                label="Inicio de síntomas"
                value={formatDate(evento.fecha_inicio_sintomas)}
              />
            )}
            {evento.fecha_apertura_caso && (
              <DataRow
                label="Apertura del caso"
                value={formatDate(evento.fecha_apertura_caso)}
              />
            )}
            {evento.fecha_primera_consulta && (
              <DataRow
                label="Primera consulta"
                value={formatDate(evento.fecha_primera_consulta)}
              />
            )}
          </div>

          {/* Información epidemiológica adicional */}
          {evento.semana_epidemiologica_sintomas && (
            <div className="mt-4 pt-4 border-t space-y-2">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">
                Información Epidemiológica Adicional
              </p>
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">
                  Semana epi. síntomas
                </span>
                <span className="font-medium">
                  {evento.semana_epidemiologica_sintomas}
                </span>
              </div>
            </div>
          )}
        </CollapsibleSection>

        {/* Trazabilidad de Clasificación */}
        {trazabilidad && (
          <CollapsibleSection
            title="Trazabilidad de Clasificación"
            icon={Search}
            defaultOpen={false}
          >
            <div className="space-y-4">
              {/* Estrategia aplicada */}
              {evento.estrategia_nombre && (
                <div className="p-3 rounded-lg bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-900">
                  <div className="flex items-center gap-2 mb-1">
                    <Shield className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                    <span className="text-sm font-medium text-blue-900 dark:text-blue-100">
                      Estrategia: {evento.estrategia_nombre}
                    </span>
                  </div>
                  <p className="text-xs text-blue-700 dark:text-blue-300 ml-6">
                    ID: {evento.id_estrategia_aplicada}
                  </p>
                </div>
              )}

              {/* Razón de la clasificación */}
              {trazabilidad.razon && (
                <div
                  className={cn(
                    "p-3 rounded-lg border",
                    trazabilidad.razon === "regla_aplicada"
                      ? "bg-green-50 dark:bg-green-950/20 border-green-200 dark:border-green-900"
                      : trazabilidad.razon ===
                        "requiere_revision"
                      ? "bg-yellow-50 dark:bg-yellow-950/20 border-yellow-200 dark:border-yellow-900"
                      : "bg-gray-50 dark:bg-gray-950/20 border-gray-200 dark:border-gray-900"
                  )}
                >
                  <p className="text-sm font-medium mb-1">
                    {isReglaAplicada(trazabilidad) && "✓ Regla Aplicada"}
                    {isEvaluando(trazabilidad) && "⚠ Evaluando"}
                    {isRequiereRevision(trazabilidad) && "⚠ Requiere Revisión"}
                    {isSinEstrategia(trazabilidad) && "ℹ Sin Estrategia"}
                    {isError(trazabilidad) && "✗ Error"}
                  </p>
                  {(isSinEstrategia(trazabilidad) ||
                    isError(trazabilidad) ||
                    isRequiereRevision(trazabilidad)) && (
                    <p className="text-xs text-muted-foreground">
                      {trazabilidad.mensaje}
                    </p>
                  )}

                  {/* Regla aplicada con éxito */}
                  {isReglaAplicada(trazabilidad) && (
                    <div className="mt-3 pt-3 border-t space-y-2">
                      <div className="text-xs">
                        <span className="font-medium">Regla:</span>{" "}
                        {trazabilidad.regla_nombre || "Sin nombre"}
                      </div>
                      <div className="text-xs">
                        <span className="font-medium">Clasificación:</span>{" "}
                        <Badge
                          className={cn(
                            "text-xs",
                            getClasificacionColorClasses(
                              trazabilidad
                                .clasificacion_aplicada || ""
                            )
                          )}
                        >
                          {getClasificacionLabel(
                            trazabilidad
                              .clasificacion_aplicada || ""
                          )}
                        </Badge>
                      </div>
                      <div className="text-xs">
                        <span className="font-medium">Prioridad:</span>{" "}
                        {trazabilidad.regla_prioridad}
                      </div>

                      {/* Condiciones evaluadas */}
                      {trazabilidad.condiciones_evaluadas &&
                        trazabilidad.condiciones_evaluadas
                          .length > 0 && (
                          <div className="mt-3">
                            <p className="text-xs font-medium mb-2">
                              Condiciones Evaluadas:
                            </p>
                            <div className="space-y-2">
                              {trazabilidad.condiciones_evaluadas.map(
                                (cond, idx) => (
                                <div
                                  key={idx}
                                  className={cn(
                                    "p-3 rounded-lg border",
                                    cond.resultado
                                      ? "bg-green-50 dark:bg-green-950/20 border-green-200 dark:border-green-900"
                                      : "bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-900"
                                  )}
                                >
                                  <div className="flex items-start gap-3">
                                    <div
                                      className={cn(
                                        "flex h-5 w-5 items-center justify-center rounded-full flex-shrink-0",
                                        cond.resultado
                                          ? "bg-green-500 text-white"
                                          : "bg-red-500 text-white"
                                      )}
                                    >
                                      <span className="text-xs font-bold">
                                        {cond.resultado ? "✓" : "✗"}
                                      </span>
                                    </div>
                                    <div className="flex-1 min-w-0">
                                      <div className="flex items-baseline gap-2 mb-1">
                                        <span className="font-medium text-sm">
                                          {cond.campo}
                                        </span>
                                        <Badge
                                          variant="outline"
                                          className="text-xs"
                                        >
                                          {cond.tipo_filtro
                                            ?.replace("CAMPO_", "")
                                            ?.toLowerCase()}
                                        </Badge>
                                      </div>

                                      {/* Valor esperado */}
                                      {(() => {
                                        if (!cond.config) return null;
                                        const val = cond.config.value;
                                        const vals = cond.config.values;
                                        if (!val && !vals) return null;

                                        return (
                                          <p className="text-xs text-muted-foreground mb-1">
                                            Esperado:{" "}
                                            <span className="font-medium text-foreground">
                                              {String(val) ||
                                                (Array.isArray(vals)
                                                  ? vals.map(String).join(", ")
                                                  : String(vals))}
                                            </span>
                                          </p>
                                        );
                                      })()}

                                      {/* Valor encontrado */}
                                      {cond.valor_campo && (
                                        <p className="text-xs text-muted-foreground">
                                          Encontrado:{" "}
                                          <span className="font-medium text-foreground">
                                            {cond.valor_campo}
                                          </span>
                                        </p>
                                      )}
                                    </div>
                                  </div>
                                </div>
                              )
                            )}
                            </div>
                          </div>
                        )}
                    </div>
                  )}

                  {/* Reglas evaluadas que no cumplieron */}
                  {isEvaluando(trazabilidad) &&
                  trazabilidad.reglas_evaluadas &&
                  trazabilidad.reglas_evaluadas.length >
                    0 && (
                    <div className="mt-3 pt-3 border-t">
                      <p className="text-xs font-medium mb-3">
                        Reglas evaluadas sin coincidencias (
                        {trazabilidad.reglas_evaluadas.length}
                        ):
                      </p>
                      <div className="space-y-3">
                        {trazabilidad.reglas_evaluadas.map(
                          (regla, idx) => (
                          <div
                            key={idx}
                            className="p-3 rounded-lg bg-gray-50 dark:bg-gray-900/50 border border-gray-200 dark:border-gray-800"
                          >
                            <div className="flex items-start justify-between mb-3">
                              <span className="text-sm font-medium">
                                {regla.regla_nombre}
                              </span>
                              <Badge variant="outline" className="text-xs">
                                Prioridad {regla.regla_prioridad}
                              </Badge>
                            </div>

                            {regla.condiciones &&
                              regla.condiciones.length > 0 && (
                                <div className="space-y-2">
                                  {regla.condiciones.map(
                                    (cond, condIdx) => (
                                      <div
                                        key={condIdx}
                                        className={cn(
                                          "p-2 rounded border flex items-start gap-2",
                                          cond.resultado
                                            ? "bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800"
                                            : "bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800"
                                        )}
                                      >
                                        <div
                                          className={cn(
                                            "flex h-4 w-4 items-center justify-center rounded-full flex-shrink-0 mt-0.5",
                                            cond.resultado
                                              ? "bg-green-500 text-white"
                                              : "bg-red-500 text-white"
                                          )}
                                        >
                                          <span className="text-[10px] font-bold">
                                            {cond.resultado ? "✓" : "✗"}
                                          </span>
                                        </div>
                                        <div className="flex-1 min-w-0">
                                          <div className="flex items-baseline gap-2 mb-1">
                                            <p className="text-xs font-medium">
                                              {cond.campo}
                                            </p>
                                            <Badge
                                              variant="outline"
                                              className="text-[10px] px-1 py-0"
                                            >
                                              {cond.tipo_filtro
                                                ?.replace("CAMPO_", "")
                                                ?.toLowerCase()}
                                            </Badge>
                                          </div>

                                          {/* Valor esperado */}
                                          {(() => {
                                            if (!cond.config) return null;
                                            const val = cond.config.value;
                                            const vals = cond.config.values;
                                            if (!val && !vals) return null;

                                            return (
                                              <p className="text-xs text-muted-foreground">
                                                Esperado:{" "}
                                                <span className="font-medium">
                                                  {String(val) ||
                                                    (Array.isArray(vals)
                                                      ? vals.map(String).join(", ")
                                                      : String(vals))}
                                                </span>
                                              </p>
                                            );
                                          })()}

                                          {/* Valor encontrado */}
                                          {cond.valor_campo && (
                                            <p className="text-xs text-muted-foreground mt-0.5">
                                              Encontrado:{" "}
                                              <span className="font-medium">
                                                {cond.valor_campo}
                                              </span>
                                            </p>
                                          )}
                                        </div>
                                      </div>
                                    )
                                  )}
                                </div>
                              )}
                          </div>
                        )
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </CollapsibleSection>
        )}

        {/* Síntomas */}
        <CollapsibleSection
          title="Síntomas"
          icon={Heart}
          count={evento.sintomas?.length}
          isEmpty={!evento.sintomas || evento.sintomas.length === 0}
        >
          {evento.sintomas && evento.sintomas.length > 0 ? (
            <div className="space-y-3">
              {evento.sintomas.map((sintoma) => (
                <div
                  key={sintoma.id}
                  className="py-3 px-3 rounded-md border border-border hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-start justify-between mb-2">
                    <span className="text-sm font-medium">
                      {sintoma.nombre || "Síntoma no especificado"}
                    </span>
                    {sintoma.fecha_inicio && (
                      <span className="text-xs text-muted-foreground">
                        {formatDate(sintoma.fecha_inicio)}
                      </span>
                    )}
                  </div>
                  {(sintoma.semana_epidemiologica ||
                    sintoma.anio_epidemiologico) && (
                    <div className="text-xs text-muted-foreground">
                      Semana epi: {sintoma.semana_epidemiologica || "?"}/
                      {sintoma.anio_epidemiologico || "?"}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              icon={Heart}
              title="Sin síntomas registrados"
              description="No se han registrado síntomas para este evento"
            />
          )}
        </CollapsibleSection>

        {/* Muestras */}
        <CollapsibleSection
          title="Muestras y Estudios"
          icon={TestTube}
          count={evento.muestras?.length}
          isEmpty={!evento.muestras || evento.muestras.length === 0}
        >
          {evento.muestras && evento.muestras.length > 0 ? (
            <div className="space-y-4">
              {evento.muestras.map((muestra) => (
                <div
                  key={muestra.id}
                  className="border rounded-lg p-4 space-y-3 hover:bg-muted/30 transition-colors"
                >
                  {/* Muestra header */}
                  <div className="flex justify-between items-start gap-4">
                    <div className="space-y-1 flex-1">
                      <p className="font-medium text-sm">
                        {muestra.tipo || "Tipo no especificado"}
                      </p>
                      {muestra.fecha_toma_muestra && (
                        <p className="text-xs text-muted-foreground">
                          Tomada el {formatDate(muestra.fecha_toma_muestra)}
                        </p>
                      )}
                      {muestra.establecimiento && (
                        <div className="flex items-center gap-1 text-xs text-muted-foreground">
                          <Building className="h-3 w-3" />
                          <span>{muestra.establecimiento}</span>
                        </div>
                      )}
                    </div>
                    {muestra.semana_epidemiologica &&
                      muestra.anio_epidemiologico && (
                        <Badge variant="outline" className="text-xs">
                          Semana {muestra.semana_epidemiologica}/
                          {muestra.anio_epidemiologico}
                        </Badge>
                      )}
                  </div>

                  {/* Estudios nested */}
                  {muestra.estudios && muestra.estudios.length > 0 && (
                    <div className="space-y-2 border-t pt-3">
                      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                        Estudios Realizados
                      </p>
                      {muestra.estudios.map((estudio) => (
                        <div
                          key={estudio.id}
                          className="bg-muted/50 p-3 rounded space-y-2"
                        >
                          <div className="flex justify-between items-start gap-2">
                            <span className="text-sm font-medium">
                              {estudio.determinacion ||
                                "Estudio no especificado"}
                            </span>
                            {estudio.resultado && (
                              <Badge
                                variant={
                                  estudio.resultado
                                    .toLowerCase()
                                    .includes("positivo")
                                    ? "destructive"
                                    : "outline"
                                }
                                className="text-xs"
                              >
                                {estudio.resultado}
                              </Badge>
                            )}
                          </div>
                          {estudio.tecnica && (
                            <p className="text-xs text-muted-foreground">
                              Técnica: {estudio.tecnica}
                            </p>
                          )}
                          <div className="flex gap-4 text-xs text-muted-foreground">
                            {estudio.fecha_estudio && (
                              <span>
                                Estudio: {formatDate(estudio.fecha_estudio)}
                              </span>
                            )}
                            {estudio.fecha_recepcion && (
                              <span>
                                Recepción: {formatDate(estudio.fecha_recepcion)}
                              </span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              icon={TestTube}
              title="Sin muestras registradas"
              description="No se han tomado muestras para este evento"
            />
          )}
        </CollapsibleSection>

        {/* Diagnósticos */}
        <CollapsibleSection
          title="Diagnósticos"
          icon={Stethoscope}
          count={evento.diagnosticos?.length}
          isEmpty={!evento.diagnosticos || evento.diagnosticos.length === 0}
        >
          {evento.diagnosticos && evento.diagnosticos.length > 0 ? (
            <div className="space-y-2">
              {evento.diagnosticos.map((diagnostico) => (
                <div
                  key={diagnostico.id}
                  className="flex items-start justify-between py-2 px-3 rounded-md hover:bg-muted/50 transition-colors"
                >
                  <div className="space-y-1 flex-1">
                    <p className="text-sm">
                      {diagnostico.diagnostico || "Diagnóstico no especificado"}
                    </p>
                    {diagnostico.fecha && (
                      <p className="text-xs text-muted-foreground">
                        {formatDate(diagnostico.fecha)}
                      </p>
                    )}
                  </div>
                  {diagnostico.es_principal && (
                    <Badge variant="default" className="text-xs ml-2">
                      Principal
                    </Badge>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              icon={Stethoscope}
              title="Sin diagnósticos registrados"
              description="No se han registrado diagnósticos para este evento"
            />
          )}
        </CollapsibleSection>

        {/* Establecimientos */}
        <CollapsibleSection
          title="Establecimientos"
          icon={Building}
          isEmpty={
            !evento.establecimiento_consulta &&
            !evento.establecimiento_notificacion &&
            !evento.establecimiento_carga
          }
        >
          {evento.establecimiento_consulta ||
          evento.establecimiento_notificacion ||
          evento.establecimiento_carga ? (
            <div className="space-y-4">
              {evento.establecimiento_consulta && (
                <div className="space-y-2">
                  <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    Consulta
                  </p>
                  <div className="pl-3 border-l-2 border-blue-200 dark:border-blue-900">
                    <p className="text-sm font-medium">
                      {evento.establecimiento_consulta.nombre}
                    </p>
                    {evento.establecimiento_consulta.tipo && (
                      <p className="text-xs text-muted-foreground">
                        {evento.establecimiento_consulta.tipo}
                      </p>
                    )}
                    {(evento.establecimiento_consulta.provincia ||
                      evento.establecimiento_consulta.localidad) && (
                      <div className="flex items-center gap-1 text-xs text-muted-foreground mt-1">
                        <MapPin className="h-3 w-3" />
                        <span>
                          {evento.establecimiento_consulta.localidad}
                          {evento.establecimiento_consulta.provincia &&
                            `, ${evento.establecimiento_consulta.provincia}`}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {evento.establecimiento_notificacion && (
                <div className="space-y-2">
                  <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    Notificación
                  </p>
                  <div className="pl-3 border-l-2 border-yellow-200 dark:border-yellow-900">
                    <p className="text-sm font-medium">
                      {evento.establecimiento_notificacion.nombre}
                    </p>
                    {evento.establecimiento_notificacion.tipo && (
                      <p className="text-xs text-muted-foreground">
                        {evento.establecimiento_notificacion.tipo}
                      </p>
                    )}
                    {(evento.establecimiento_notificacion.provincia ||
                      evento.establecimiento_notificacion.localidad) && (
                      <div className="flex items-center gap-1 text-xs text-muted-foreground mt-1">
                        <MapPin className="h-3 w-3" />
                        <span>
                          {evento.establecimiento_notificacion.localidad}
                          {evento.establecimiento_notificacion.provincia &&
                            `, ${evento.establecimiento_notificacion.provincia}`}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {evento.establecimiento_carga && (
                <div className="space-y-2">
                  <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    Carga
                  </p>
                  <div className="pl-3 border-l-2 border-gray-200 dark:border-gray-800">
                    <p className="text-sm font-medium">
                      {evento.establecimiento_carga.nombre}
                    </p>
                    {evento.establecimiento_carga.tipo && (
                      <p className="text-xs text-muted-foreground">
                        {evento.establecimiento_carga.tipo}
                      </p>
                    )}
                    {(evento.establecimiento_carga.provincia ||
                      evento.establecimiento_carga.localidad) && (
                      <div className="flex items-center gap-1 text-xs text-muted-foreground mt-1">
                        <MapPin className="h-3 w-3" />
                        <span>
                          {evento.establecimiento_carga.localidad}
                          {evento.establecimiento_carga.provincia &&
                            `, ${evento.establecimiento_carga.provincia}`}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <EmptyState
              icon={Building}
              title="Sin establecimientos registrados"
              description="No hay información de establecimientos para este evento"
            />
          )}
        </CollapsibleSection>

        {/* Investigaciones */}
        <CollapsibleSection
          title="Investigaciones Epidemiológicas"
          icon={Search}
          count={evento.investigaciones?.length}
          isEmpty={
            !evento.investigaciones || evento.investigaciones.length === 0
          }
          defaultOpen={false}
        >
          {evento.investigaciones && evento.investigaciones.length > 0 ? (
            <div className="space-y-4">
              {evento.investigaciones.map((inv) => (
                <div key={inv.id} className="p-4 rounded-lg border space-y-3">
                  {/* Badges de estado */}
                  <div className="flex flex-wrap gap-2">
                    {inv.es_usuario_centinela && (
                      <Badge variant="default" className="text-xs">
                        <UserCheck className="h-3 w-3 mr-1" />
                        Usuario Centinela
                      </Badge>
                    )}
                    {inv.es_evento_centinela && (
                      <Badge variant="default" className="text-xs">
                        <BadgeCheck className="h-3 w-3 mr-1" />
                        Evento Centinela
                      </Badge>
                    )}
                    {inv.es_investigacion_terreno && (
                      <Badge variant="outline" className="text-xs">
                        Investigación de Terreno
                      </Badge>
                    )}
                  </div>

                  {/* Datos de la investigación */}
                  <div className="grid gap-x-8 gap-y-2 md:grid-cols-2 text-sm">
                    {inv.fecha_investigacion && (
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">Fecha:</span>
                        <span className="font-medium">
                          {formatDate(inv.fecha_investigacion)}
                        </span>
                      </div>
                    )}
                    {inv.tipo_lugar_investigacion && (
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">Lugar:</span>
                        <span className="font-medium text-right">
                          {inv.tipo_lugar_investigacion}
                        </span>
                      </div>
                    )}
                    {inv.origen_financiamiento && (
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">
                          Financiamiento:
                        </span>
                        <span className="font-medium">
                          {inv.origen_financiamiento}
                        </span>
                      </div>
                    )}
                    {inv.participo_usuario_centinela && (
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">
                          Participó centinela:
                        </span>
                        <Badge variant="outline" className="text-xs">
                          Sí
                        </Badge>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              icon={Search}
              title="Sin investigaciones"
              description="No se han registrado investigaciones epidemiológicas para este evento"
            />
          )}
        </CollapsibleSection>

        {/* Contactos */}
        <CollapsibleSection
          title="Contactos Relevados"
          icon={Users}
          count={evento.contactos?.length}
          isEmpty={!evento.contactos || evento.contactos.length === 0}
          defaultOpen={false}
        >
          {evento.contactos && evento.contactos.length > 0 ? (
            <div className="space-y-4">
              {evento.contactos.map((contacto) => (
                <div
                  key={contacto.id}
                  className="p-4 rounded-lg border space-y-3"
                >
                  {/* Tipo de contacto */}
                  <div className="flex flex-wrap gap-2">
                    {contacto.contacto_caso_confirmado && (
                      <Badge variant="destructive" className="text-xs">
                        Contacto con caso confirmado
                      </Badge>
                    )}
                    {contacto.contacto_caso_sospechoso && (
                      <Badge variant="secondary" className="text-xs">
                        Contacto con caso sospechoso
                      </Badge>
                    )}
                  </div>

                  {/* Estadísticas de contactos */}
                  {(contacto.contactos_menores_un_ano !== null ||
                    contacto.contactos_vacunados !== null ||
                    contacto.contactos_embarazadas !== null) && (
                    <div className="grid gap-4 md:grid-cols-3 text-center">
                      {contacto.contactos_menores_un_ano !== null && (
                        <div className="p-3 rounded-lg bg-blue-50 dark:bg-blue-950/20">
                          <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                            {contacto.contactos_menores_un_ano}
                          </p>
                          <p className="text-xs text-muted-foreground mt-1">
                            Menores de 1 año
                          </p>
                        </div>
                      )}
                      {contacto.contactos_vacunados !== null && (
                        <div className="p-3 rounded-lg bg-green-50 dark:bg-green-950/20">
                          <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                            {contacto.contactos_vacunados}
                          </p>
                          <p className="text-xs text-muted-foreground mt-1">
                            Vacunados
                          </p>
                        </div>
                      )}
                      {contacto.contactos_embarazadas !== null && (
                        <div className="p-3 rounded-lg bg-purple-50 dark:bg-purple-950/20">
                          <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                            {contacto.contactos_embarazadas}
                          </p>
                          <p className="text-xs text-muted-foreground mt-1">
                            Embarazadas
                          </p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              icon={Users}
              title="Sin contactos"
              description="No se han registrado contactos para este evento"
            />
          )}
        </CollapsibleSection>

        {/* Tratamientos */}
        {evento.tratamientos && evento.tratamientos.length > 0 && (
          <CollapsibleSection
            title="Tratamientos"
            icon={Pill}
            count={evento.tratamientos.length}
            defaultOpen={false}
          >
            <div className="space-y-3">
              {evento.tratamientos.map((trat, idx: number) => (
                <div
                  key={`${trat.id}-${idx}`}
                  className="p-4 rounded-lg border space-y-2"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <p className="text-sm font-medium mb-1">
                        {trat.descripcion || "Tratamiento no especificado"}
                      </p>
                      {trat.establecimiento && (
                        <div className="flex items-center gap-1 text-xs text-muted-foreground mb-1">
                          <Building className="h-3 w-3" />
                          <span>{trat.establecimiento}</span>
                        </div>
                      )}
                    </div>
                    {trat.resultado && (
                      <Badge variant="outline" className="text-xs ml-2">
                        {trat.resultado}
                      </Badge>
                    )}
                  </div>
                  {(trat.fecha_inicio || trat.fecha_fin) && (
                    <div className="flex gap-4 text-xs text-muted-foreground pt-2 border-t">
                      {trat.fecha_inicio && (
                        <span>Inicio: {formatDate(trat.fecha_inicio)}</span>
                      )}
                      {trat.fecha_fin && (
                        <span>Fin: {formatDate(trat.fecha_fin)}</span>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CollapsibleSection>
        )}

        {/* Internaciones */}
        {evento.internaciones && evento.internaciones.length > 0 && (
          <CollapsibleSection
            title="Internaciones"
            icon={Bed}
            count={evento.internaciones.length}
            defaultOpen={false}
          >
            <div className="space-y-3">
              {evento.internaciones.map((int) => (
                <div key={int.id} className="p-3 rounded-lg border">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex gap-2 items-center">
                      <Bed className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm font-medium">Internación</span>
                    </div>
                    {int.requirio_uci && (
                      <Badge variant="destructive" className="text-xs">
                        UCI
                      </Badge>
                    )}
                  </div>
                  <div className="grid gap-2 md:grid-cols-2 text-sm">
                    {int.fecha_internacion && (
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">Ingreso:</span>
                        <span className="font-medium">
                          {formatDate(int.fecha_internacion)}
                        </span>
                      </div>
                    )}
                    {int.fecha_alta && (
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">Alta:</span>
                        <span className="font-medium">
                          {formatDate(int.fecha_alta)}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CollapsibleSection>
        )}

        {/* Vacunas */}
        {evento.vacunas && evento.vacunas.length > 0 && (
          <CollapsibleSection
            title="Vacunas"
            icon={Syringe}
            count={evento.vacunas.length}
            defaultOpen={false}
          >
            <div className="space-y-3">
              {evento.vacunas.map((vac) => (
                <div key={vac.id} className="p-3 rounded-lg border">
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <p className="text-sm font-medium">
                        {vac.nombre_vacuna || "Vacuna no especificada"}
                      </p>
                      {vac.fecha_ultima_dosis && (
                        <p className="text-xs text-muted-foreground">
                          Última dosis: {formatDate(vac.fecha_ultima_dosis)}
                        </p>
                      )}
                    </div>
                    {vac.dosis_total && (
                      <Badge variant="outline" className="text-xs">
                        {vac.dosis_total}{" "}
                        {vac.dosis_total === 1 ? "dosis" : "dosis"}
                      </Badge>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CollapsibleSection>
        )}

        {/* Antecedentes */}
        {evento.antecedentes && evento.antecedentes.length > 0 && (
          <CollapsibleSection
            title="Antecedentes Epidemiológicos"
            icon={FileText}
            count={evento.antecedentes.length}
            defaultOpen={false}
          >
            <div className="space-y-2">
              {evento.antecedentes.map((ant) => (
                <div key={ant.id} className="p-3 rounded-lg border">
                  <p className="text-sm">
                    {ant.descripcion || "Antecedente no especificado"}
                  </p>
                  {ant.fecha_antecedente && (
                    <p className="text-xs text-muted-foreground mt-1">
                      {formatDate(ant.fecha_antecedente)}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </CollapsibleSection>
        )}

        {/* Ámbitos de concurrencia */}
        {evento.ambitos_concurrencia &&
          evento.ambitos_concurrencia.length > 0 && (
            <CollapsibleSection
              title="Ámbitos de Concurrencia"
              icon={MapPinned}
              count={evento.ambitos_concurrencia.length}
              defaultOpen={false}
            >
              <div className="space-y-3">
                {evento.ambitos_concurrencia.map((amb) => (
                  <div key={amb.id} className="p-3 rounded-lg border">
                    <div className="flex items-start justify-between mb-2">
                      <div className="space-y-1">
                        <p className="text-sm font-medium">
                          {amb.nombre_lugar || "Lugar no especificado"}
                        </p>
                        {amb.tipo_lugar && (
                          <p className="text-xs text-muted-foreground">
                            {amb.tipo_lugar}
                          </p>
                        )}
                      </div>
                      {amb.frecuencia_concurrencia && (
                        <Badge variant="outline" className="text-xs">
                          {amb.frecuencia_concurrencia}
                        </Badge>
                      )}
                    </div>
                    <div className="flex gap-4 text-xs text-muted-foreground">
                      {amb.localidad && (
                        <span>
                          <MapPin className="inline h-3 w-3 mr-1" />
                          {amb.localidad}
                        </span>
                      )}
                      {amb.fecha_ocurrencia && (
                        <span>{formatDate(amb.fecha_ocurrencia)}</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CollapsibleSection>
          )}

        {/* Timeline */}
        <CollapsibleSection
          title="Línea de Tiempo"
          icon={Clock}
          count={timeline.length}
          isEmpty={timeline.length === 0}
          defaultOpen={false}
        >
          {timeline.length > 0 ? (
            <div className="space-y-4">
              {timeline.map((item, index: number) => (
                <div key={index} className="flex gap-4">
                  <div className="flex flex-col items-center">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-muted flex-shrink-0">
                      <div className="h-2 w-2 rounded-full bg-primary" />
                    </div>
                    {index < timeline.length - 1 && (
                      <div className="w-px flex-1 bg-border mt-2" />
                    )}
                  </div>
                  <div className="flex-1 pb-4">
                    <p className="text-sm font-medium">{item.descripcion}</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {formatDate(item.fecha)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              icon={Clock}
              title="Sin eventos en la línea de tiempo"
              description="No hay eventos registrados en la cronología de este caso"
            />
          )}
        </CollapsibleSection>
      </div>
    </div>
  );
}
