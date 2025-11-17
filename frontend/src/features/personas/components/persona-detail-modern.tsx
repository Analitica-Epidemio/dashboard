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
  Building,
  ChevronDown,
  ChevronRight,
  Users,
  Pill,
  Bed,
  Phone,
  CreditCard,
  Baby,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import {
  usePersona,
  usePersonaTimeline,
} from "@/features/personas/api";
import {
  getClasificacionLabel,
  getClasificacionColorClasses,
} from "@/lib/utils/clasificacion";
import { cn } from "@/lib/utils";

interface PersonaDetailModernProps {
  tipoSujeto: "humano" | "animal";
  personaId: number;
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
        <div className={cn("px-4 pb-4", isEmpty && "pb-3")}>
          {children}
        </div>
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
function DataRow({ label, value, icon: Icon }: { label: string; value: string | React.ReactNode; icon?: React.ComponentType<{ className?: string }> }) {
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

export function PersonaDetailModern({ tipoSujeto, personaId, onClose }: PersonaDetailModernProps) {
  const personaQuery = usePersona(tipoSujeto, personaId);
  const timelineQuery = usePersonaTimeline(tipoSujeto, personaId);

  const persona = personaQuery.data?.data;
  const timelineData = timelineQuery.data?.data;
  const timeline = timelineData?.items || [];
  const isLoading = personaQuery.isLoading;
  const error = personaQuery.error;

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
    if (sexoLower === 'm' || sexoLower === 'masculino') return 'Masculino';
    if (sexoLower === 'f' || sexoLower === 'femenino') return 'Femenino';
    return sexo;
  };

  // Loading State
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
        <div className="grid grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
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
  if (error || !persona) {
    return (
      <div className="px-6 py-12 flex flex-col items-center justify-center">
        <div className="rounded-full bg-destructive/10 p-3 mb-4">
          <AlertTriangle className="h-8 w-8 text-destructive" />
        </div>
        <h3 className="text-lg font-semibold mb-2">Error al cargar persona</h3>
        <p className="text-sm text-muted-foreground mb-4">
          No pudimos cargar la información de la persona. Por favor, intenta nuevamente.
        </p>
        {onClose && (
          <Button variant="outline" onClick={onClose}>
            Cerrar
          </Button>
        )}
      </div>
    );
  }

  return (
    <div className="px-6 py-6 space-y-6">
      {/* Hero Header - Key Information */}
      <div className="space-y-4">
        {/* Title & ID */}
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1 flex-1">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Hash className="h-3 w-3" />
              <span>Persona {personaId}</span>
              <span>•</span>
              <span>{tipoSujeto === "humano" ? "Humano" : "Animal"}</span>
            </div>
            <h1 className="text-2xl font-semibold tracking-tight">{persona.nombre_completo}</h1>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <User className="h-4 w-4" />
              <span>
                {persona.documento_numero
                  ? `${persona.documento_tipo || "DNI"} ${persona.documento_numero}`
                  : "Sin documento"}
              </span>
            </div>
          </div>

          {/* Stats Badge */}
          <div className="text-right">
            <div className="text-3xl font-bold text-primary">{persona.total_eventos}</div>
            <div className="text-xs text-muted-foreground">
              {persona.total_eventos === 1 ? "Evento" : "Eventos"}
            </div>
          </div>
        </div>

        {/* Quick Stats Grid */}
        <div className="grid grid-cols-4 gap-3">
          <div className="rounded-lg border bg-red-50 dark:bg-red-950/20 p-3 text-center">
            <div className="text-2xl font-bold text-red-600 dark:text-red-400">
              {persona.eventos_confirmados}
            </div>
            <div className="text-xs text-muted-foreground mt-1">Confirmados</div>
          </div>
          <div className="rounded-lg border bg-yellow-50 dark:bg-yellow-950/20 p-3 text-center">
            <div className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">
              {persona.eventos_sospechosos}
            </div>
            <div className="text-xs text-muted-foreground mt-1">Sospechosos</div>
          </div>
          <div className="rounded-lg border bg-orange-50 dark:bg-orange-950/20 p-3 text-center">
            <div className="text-2xl font-bold text-orange-600 dark:text-orange-400">
              {persona.eventos_probables || 0}
            </div>
            <div className="text-xs text-muted-foreground mt-1">Probables</div>
          </div>
          <div className="rounded-lg border bg-gray-50 dark:bg-gray-950/20 p-3 text-center">
            <div className="text-2xl font-bold text-gray-600 dark:text-gray-400">
              {persona.eventos_descartados || 0}
            </div>
            <div className="text-xs text-muted-foreground mt-1">Descartados</div>
          </div>
        </div>

        {/* Metadata */}
        <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
          {persona.fecha_nacimiento && (
            <div className="flex items-center gap-1.5">
              <Calendar className="h-4 w-4" />
              <span>
                {formatDate(persona.fecha_nacimiento)}
                {calcularEdad(persona.fecha_nacimiento) !== null && (
                  <span className="ml-1">({calcularEdad(persona.fecha_nacimiento)} años)</span>
                )}
              </span>
            </div>
          )}
          {persona.sexo_biologico && (
            <Badge variant="outline" className="text-xs">
              {getSexoCompleto(persona.sexo_biologico)}
            </Badge>
          )}
          {persona.tipos_eventos_unicos > 0 && (
            <div className="flex items-center gap-1.5">
              <Activity className="h-4 w-4" />
              <span>{persona.tipos_eventos_unicos} tipos de eventos diferentes</span>
            </div>
          )}
        </div>
      </div>

      <Separator />

      {/* Collapsible Sections */}
      <div className="space-y-0">
        {/* Datos Personales */}
        {tipoSujeto === "humano" && (
          <CollapsibleSection title="Datos Personales" icon={User}>
            <div className="space-y-4">
              <div className="grid gap-x-8 gap-y-3 md:grid-cols-2">
                <DataRow label="Nombre" value={persona.nombre || "No especificado"} />
                <DataRow label="Apellido" value={persona.apellido || "No especificado"} />
                {persona.documento_numero && (
                  <DataRow
                    label="Documento"
                    icon={CreditCard}
                    value={`${persona.documento_tipo || "DNI"} ${persona.documento_numero}`}
                  />
                )}
                {persona.fecha_nacimiento && (
                  <DataRow
                    label="Fecha de nacimiento"
                    icon={Calendar}
                    value={
                      <>
                        {formatDate(persona.fecha_nacimiento)}
                        {calcularEdad(persona.fecha_nacimiento) !== null && (
                          <span className="text-muted-foreground ml-2">
                            ({calcularEdad(persona.fecha_nacimiento)} años)
                          </span>
                        )}
                      </>
                    }
                  />
                )}
                {persona.sexo_biologico && (
                  <DataRow label="Sexo" value={getSexoCompleto(persona.sexo_biologico)} />
                )}
                {persona.genero_autopercibido && (
                  <DataRow label="Género autopercibido" value={persona.genero_autopercibido} />
                )}
                {persona.telefono && (
                  <DataRow label="Teléfono" icon={Phone} value={persona.telefono} />
                )}
                {persona.obra_social && (
                  <DataRow label="Obra Social" value={persona.obra_social} />
                )}
              </div>

              {/* Domicilio */}
              {persona.domicilio && (
                <div className="pt-4 border-t">
                  <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-3 flex items-center gap-2">
                    <MapPin className="h-3 w-3" />
                    Domicilio
                  </p>
                  <div className="space-y-2">
                    {persona.domicilio.calle && (
                      <DataRow label="Calle" value={persona.domicilio.calle} />
                    )}
                    {persona.domicilio.numero && (
                      <DataRow label="Número" value={persona.domicilio.numero} />
                    )}
                    {persona.domicilio.barrio && (
                      <DataRow label="Barrio" value={persona.domicilio.barrio} />
                    )}
                    {persona.domicilio.localidad && (
                      <DataRow label="Localidad" value={persona.domicilio.localidad} />
                    )}
                    {persona.domicilio.provincia && (
                      <DataRow label="Provincia" value={persona.domicilio.provincia} />
                    )}
                  </div>
                </div>
              )}
            </div>
          </CollapsibleSection>
        )}

        {/* Datos de Animal */}
        {tipoSujeto === "animal" && (
          <CollapsibleSection title="Datos del Animal" icon={User}>
            <div className="grid gap-x-8 gap-y-3 md:grid-cols-2">
              {persona.identificacion_animal && (
                <DataRow label="Identificación" value={persona.identificacion_animal} />
              )}
              {persona.especie && <DataRow label="Especie" value={persona.especie} />}
              {persona.raza && <DataRow label="Raza" value={persona.raza} />}
              {persona.provincia && (
                <DataRow label="Provincia" icon={MapPin} value={persona.provincia} />
              )}
              {persona.localidad && <DataRow label="Localidad" value={persona.localidad} />}
            </div>
          </CollapsibleSection>
        )}

        {/* Resumen de Eventos */}
        {(persona.primer_evento_fecha || persona.ultimo_evento_fecha) && (
          <CollapsibleSection title="Resumen de Eventos" icon={Activity}>
            <div className="space-y-4">
              <div className="grid gap-x-8 gap-y-3 md:grid-cols-2">
                {persona.primer_evento_fecha && (
                  <DataRow
                    label="Primer evento"
                    icon={Calendar}
                    value={formatDateLong(persona.primer_evento_fecha)}
                  />
                )}
                {persona.ultimo_evento_fecha && (
                  <DataRow
                    label="Último evento"
                    icon={Calendar}
                    value={formatDateLong(persona.ultimo_evento_fecha)}
                  />
                )}
                <DataRow label="Total de eventos" value={persona.total_eventos.toString()} />
                <DataRow
                  label="Tipos diferentes"
                  value={persona.tipos_eventos_unicos.toString()}
                />
              </div>
            </div>
          </CollapsibleSection>
        )}

        {/* Eventos Completos */}
        <CollapsibleSection
          title="Eventos Detallados"
          icon={Activity}
          count={persona.eventos?.length}
          isEmpty={!persona.eventos || persona.eventos.length === 0}
        >
          {persona.eventos && persona.eventos.length > 0 ? (
            <div className="space-y-4">
              {persona.eventos.map((evento) => (
                <div
                  key={evento.id}
                  className="border rounded-lg p-4 space-y-4 hover:bg-muted/30 transition-colors"
                >
                  {/* Evento Header */}
                  <div className="flex items-start justify-between gap-4">
                    <div className="space-y-1 flex-1">
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <Hash className="h-3 w-3" />
                        <span>Evento {evento.id_evento_caso}</span>
                      </div>
                      <h4 className="text-base font-semibold">
                        {evento.tipo_eno_nombre || `Tipo ${evento.tipo_eno_id}`}
                      </h4>
                      {evento.grupos_eno_nombres && evento.grupos_eno_nombres.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {evento.grupos_eno_nombres.map((grupo, idx: number) => (
                            <Badge key={idx} variant="secondary" className="text-xs">
                              {grupo}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </div>
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

                  <Separator />

                  {/* Fechas */}
                  <div className="grid gap-x-6 gap-y-2 md:grid-cols-3 text-sm">
                    {evento.fecha_minima_evento && (
                      <div className="space-y-1">
                        <p className="text-xs text-muted-foreground">Fecha del evento</p>
                        <p className="font-medium">{formatDate(evento.fecha_minima_evento)}</p>
                      </div>
                    )}
                    {evento.fecha_inicio_sintomas && (
                      <div className="space-y-1">
                        <p className="text-xs text-muted-foreground">Inicio de síntomas</p>
                        <p className="font-medium">{formatDate(evento.fecha_inicio_sintomas)}</p>
                      </div>
                    )}
                    {evento.fecha_apertura && (
                      <div className="space-y-1">
                        <p className="text-xs text-muted-foreground">Apertura del caso</p>
                        <p className="font-medium">{formatDate(evento.fecha_apertura)}</p>
                      </div>
                    )}
                  </div>

                  {/* Flags */}
                  {(evento.es_sintomatico || evento.requiere_revision) && (
                    <div className="flex gap-2">
                      {evento.es_sintomatico && (
                        <Badge variant="outline" className="text-xs">
                          Sintomático
                        </Badge>
                      )}
                      {evento.requiere_revision && (
                        <Badge variant="destructive" className="text-xs">
                          <AlertTriangle className="mr-1 h-3 w-3" />
                          Requiere revisión
                        </Badge>
                      )}
                    </div>
                  )}

                  {/* Domicilio del evento */}
                  {evento.domicilio && (
                    <div className="pt-3 border-t">
                      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">
                        Ubicación del Evento
                      </p>
                      <div className="flex items-start gap-2 text-sm">
                        <MapPin className="h-4 w-4 text-muted-foreground mt-0.5" />
                        <div>
                          {evento.domicilio.calle && evento.domicilio.numero && (
                            <div>{evento.domicilio.calle} {evento.domicilio.numero}</div>
                          )}
                          <div className="text-muted-foreground">
                            {[
                              evento.domicilio.localidad,
                              evento.domicilio.departamento,
                              evento.domicilio.provincia,
                            ]
                              .filter(Boolean)
                              .join(", ") || "Sin ubicación"}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Síntomas */}
                  {evento.sintomas && evento.sintomas.length > 0 && (
                    <div className="pt-3 border-t">
                      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">
                        Síntomas ({evento.sintomas.length})
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {evento.sintomas.map((sintoma) => (
                          <Badge key={sintoma.id} variant="secondary" className="text-xs">
                            <Heart className="h-3 w-3 mr-1" />
                            {sintoma.nombre}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Muestras y Estudios */}
                  {evento.muestras && evento.muestras.length > 0 && (
                    <div className="pt-3 border-t">
                      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-3">
                        Muestras y Estudios ({evento.muestras.length})
                      </p>
                      <div className="space-y-3">
                        {evento.muestras.map((muestra) => (
                          <div
                            key={muestra.id}
                            className="bg-muted/50 p-3 rounded-lg space-y-2"
                          >
                            <div className="flex items-start justify-between">
                              <div className="flex items-center gap-2">
                                <TestTube className="h-4 w-4 text-muted-foreground" />
                                <span className="text-sm font-medium">
                                  {muestra.tipo_muestra || "Muestra"}
                                </span>
                              </div>
                              {muestra.fecha_toma && (
                                <span className="text-xs text-muted-foreground">
                                  {formatDate(muestra.fecha_toma)}
                                </span>
                              )}
                            </div>
                            {muestra.resultado && (
                              <p className="text-xs text-muted-foreground">
                                Resultado: <span className="font-medium">{muestra.resultado}</span>
                              </p>
                            )}

                            {/* Estudios nested in muestra */}
                            {evento.estudios && evento.estudios.length > 0 && (
                              <div className="space-y-2 border-t pt-2 mt-2">
                                <p className="text-xs font-medium text-muted-foreground">
                                  Estudios Realizados
                                </p>
                                {evento.estudios
                                  .filter((estudio) => {
                                    // Show all estudios for now (ideally filter by muestra_id)
                                    return true;
                                  })
                                  .map((estudio) => (
                                    <div
                                      key={estudio.id}
                                      className="bg-background p-2 rounded space-y-1"
                                    >
                                      <div className="flex justify-between items-start gap-2">
                                        <span className="text-xs font-medium">
                                          {estudio.determinacion || "Estudio no especificado"}
                                        </span>
                                        {estudio.resultado && (
                                          <Badge
                                            variant={
                                              estudio.resultado.toLowerCase().includes("positivo")
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
                                      {estudio.fecha_estudio && (
                                        <p className="text-xs text-muted-foreground">
                                          {formatDate(estudio.fecha_estudio)}
                                        </p>
                                      )}
                                    </div>
                                  ))}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Diagnósticos */}
                  {evento.diagnosticos && evento.diagnosticos.length > 0 && (
                    <div className="pt-3 border-t">
                      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">
                        Diagnósticos ({evento.diagnosticos.length})
                      </p>
                      <div className="space-y-2">
                        {evento.diagnosticos.map((diagnostico) => (
                          <div
                            key={diagnostico.id}
                            className="flex items-center gap-2 text-sm"
                          >
                            <Stethoscope className="h-3 w-3 text-muted-foreground" />
                            <span>{diagnostico.diagnostico}</span>
                            {diagnostico.fecha && (
                              <span className="text-xs text-muted-foreground">
                                ({formatDate(diagnostico.fecha)})
                              </span>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Tratamientos */}
                  {evento.tratamientos && evento.tratamientos.length > 0 && (
                    <div className="pt-3 border-t">
                      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">
                        Tratamientos ({evento.tratamientos.length})
                      </p>
                      <div className="space-y-2">
                        {evento.tratamientos.map((tratamiento) => (
                          <div
                            key={tratamiento.id}
                            className="flex items-start gap-2 text-sm"
                          >
                            <Pill className="h-3 w-3 text-muted-foreground mt-0.5" />
                            <div className="flex-1">
                              <div>{tratamiento.tratamiento || "Tratamiento no especificado"}</div>
                              {(tratamiento.fecha_inicio || tratamiento.fecha_fin) && (
                                <div className="text-xs text-muted-foreground mt-1">
                                  {tratamiento.fecha_inicio && `Inicio: ${formatDate(tratamiento.fecha_inicio)}`}
                                  {tratamiento.fecha_inicio && tratamiento.fecha_fin && " • "}
                                  {tratamiento.fecha_fin && `Fin: ${formatDate(tratamiento.fecha_fin)}`}
                                </div>
                              )}
                            </div>
                            {tratamiento.resultado && (
                              <Badge variant="outline" className="text-xs">
                                {tratamiento.resultado}
                              </Badge>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Internaciones */}
                  {evento.internaciones && evento.internaciones.length > 0 && (
                    <div className="pt-3 border-t">
                      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">
                        Internaciones ({evento.internaciones.length})
                      </p>
                      <div className="space-y-2">
                        {evento.internaciones.map((internacion) => (
                          <div
                            key={internacion.id}
                            className="flex items-start gap-2 text-sm"
                          >
                            <Bed className="h-3 w-3 text-muted-foreground mt-0.5" />
                            <div className="flex-1">
                              {internacion.establecimiento && (
                                <div className="font-medium">{internacion.establecimiento}</div>
                              )}
                              <div className="text-xs text-muted-foreground mt-1">
                                {internacion.fecha_internacion &&
                                  `Ingreso: ${formatDate(internacion.fecha_internacion)}`}
                                {internacion.fecha_internacion && internacion.fecha_alta && " • "}
                                {internacion.fecha_alta && `Alta: ${formatDate(internacion.fecha_alta)}`}
                              </div>
                            </div>
                            {internacion.cuidados_intensivos && (
                              <Badge variant="destructive" className="text-xs">
                                UCI
                              </Badge>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Vacunas */}
                  {evento.vacunas && evento.vacunas.length > 0 && (
                    <div className="pt-3 border-t">
                      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">
                        Vacunas ({evento.vacunas.length})
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {evento.vacunas.map((vacuna) => (
                          <Badge key={vacuna.id} variant="outline" className="text-xs">
                            <Syringe className="h-3 w-3 mr-1" />
                            {vacuna.vacuna}
                            {vacuna.dosis && ` (${vacuna.dosis}°)`}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              icon={Activity}
              title="Sin eventos registrados"
              description="Esta persona no tiene eventos registrados en el sistema"
            />
          )}
        </CollapsibleSection>

        {/* Timeline */}
        {timeline && timeline.length > 0 && (
          <CollapsibleSection
            title="Línea de Tiempo"
            icon={Clock}
            count={timeline.length}
            defaultOpen={false}
          >
            <div className="space-y-4">
              {timeline.map((item, index: number) => (
                <div key={index} className="flex gap-4">
                  <div className="flex flex-col items-center">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-muted flex-shrink-0">
                      <div className="h-2 w-2 rounded-full bg-primary" />
                    </div>
                    {index < timeline.length - 1 && <div className="w-px flex-1 bg-border mt-2" />}
                  </div>
                  <div className="flex-1 pb-4">
                    <p className="text-sm font-medium">{item.descripcion}</p>
                    <p className="text-xs text-muted-foreground mt-1">{formatDate(item.fecha)}</p>
                  </div>
                </div>
              ))}
            </div>
          </CollapsibleSection>
        )}
      </div>
    </div>
  );
}
