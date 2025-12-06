"use client";

import React from "react";
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
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  useEvento,
  useEventoTimeline,
  getClasificacionLabel,
  getClasificacionVariant,
} from "@/features/eventos/api";

interface EventoDetailProps {
  eventoId: number;
  onClose?: () => void;
}

export function EventoDetail({ eventoId, onClose }: EventoDetailProps) {
  const eventoQuery = useEvento(eventoId);
  const timelineQuery = useEventoTimeline(eventoId);

  const evento = eventoQuery.data?.data;
  const timelineData = timelineQuery.data?.data;
  const timeline = timelineData?.items || [];
  const isLoading = eventoQuery.isLoading;
  const error = eventoQuery.error;

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="space-y-4">
          <Skeleton className="h-8 w-64" />
          <div className="flex gap-2">
            <Skeleton className="h-6 w-24" />
            <Skeleton className="h-6 w-32" />
          </div>
        </div>
        <Separator />
        <div className="space-y-3">
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-20 w-full" />
        </div>
      </div>
    );
  }

  if (error || !evento) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>
          Error al cargar el evento. Por favor, intenta nuevamente.
        </AlertDescription>
      </Alert>
    );
  }

  // Formatear fecha
  const formatDate = (date: string | null | undefined) => {
    if (!date) return "No especificada";
    return new Date(date).toLocaleDateString("es-ES", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  // Determinar icono de timeline
  const getTimelineIcon = (tipo: string) => {
    switch (tipo) {
      case "inicio_sintomas":
        return <Heart className="h-4 w-4 text-red-500" />;
      case "muestra":
        return <TestTube className="h-4 w-4 text-blue-500" />;
      case "diagnostico":
        return <Stethoscope className="h-4 w-4 text-green-500" />;
      case "vacuna":
        return <Syringe className="h-4 w-4 text-purple-500" />;
      case "consulta":
        return <Activity className="h-4 w-4 text-orange-500" />;
      default:
        return <Info className="h-4 w-4 text-gray-500" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header con información básica */}
      <div className="space-y-4 pb-4 border-b">
        <div className="flex items-start justify-between">
          <div className="space-y-2">
            <h2 className="text-xl font-semibold flex items-center gap-2">
              {evento.ciudadano
                ? `${evento.ciudadano.nombre} ${evento.ciudadano.apellido}`
                : evento.animal
                  ? evento.animal.identificacion || `Animal #${evento.animal.id}`
                  : "Sujeto no identificado"}
            </h2>
            <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
              <div className="flex items-center gap-1">
                <Hash className="h-4 w-4" />
                <span>Evento: {evento.id_evento_caso}</span>
              </div>
              <div className="flex items-center gap-1">
                <Activity className="h-4 w-4" />
                <span>
                  {evento.tipo_eno_nombre || `Tipo ${evento.tipo_eno_id}`}
                </span>
              </div>
              <div className="flex items-center gap-1">
                <Calendar className="h-4 w-4" />
                <span>{formatDate(evento.fecha_minima_caso)}</span>
              </div>
            </div>
          </div>
          <div className="flex flex-col gap-2">
            <Badge
              variant={getClasificacionVariant(evento.clasificacion_estrategia)}
              className="text-sm px-3 py-1"
            >
              {getClasificacionLabel(evento.clasificacion_estrategia)}
            </Badge>
          </div>
        </div>

        {/* Resumen de información del evento (EVENT-CENTERED) */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 text-sm">
          <div className="flex items-center gap-2">
            <Heart className="h-4 w-4 text-red-500" />
            <span>{evento.total_sintomas || 0} síntomas</span>
          </div>
          <div className="flex items-center gap-2">
            <TestTube className="h-4 w-4 text-blue-500" />
            <span>{evento.total_muestras || 0} muestras</span>
          </div>
          <div className="flex items-center gap-2">
            <Stethoscope className="h-4 w-4 text-green-500" />
            <span>{evento.total_diagnosticos || 0} diagnósticos</span>
          </div>
          <div className="flex items-center gap-2">
            <Activity className="h-4 w-4 text-purple-500" />
            <span>{evento.total_tratamientos || 0} tratamientos</span>
          </div>
          <div className="flex items-center gap-2">
            <Building className="h-4 w-4 text-orange-500" />
            <span>{evento.total_internaciones || 0} internaciones</span>
          </div>
          <div className="flex items-center gap-2">
            <Search className="h-4 w-4 text-indigo-500" />
            <span>{evento.total_investigaciones || 0} investigaciones</span>
          </div>
        </div>

        {/* Descripción si existe */}
        {evento.observaciones_texto && (
          <Alert>
            <Info className="h-4 w-4" />
            <AlertDescription>{evento.observaciones_texto}</AlertDescription>
          </Alert>
        )}

        {/* Metadata de clasificación */}
        {evento.confidence_score && (
          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-1.5">
              <Shield className="h-4 w-4 text-blue-600 dark:text-blue-400" />
              <span>
                Confianza: {(evento.confidence_score * 100).toFixed(0)}%
              </span>
            </div>
            {evento.requiere_revision_especie && (
              <Badge variant="destructive" className="text-xs">
                <AlertTriangle className="mr-1 h-3 w-3" />
                Requiere revisión de especie
              </Badge>
            )}
          </div>
        )}
      </div>

      {/* Tabs con diferentes vistas de información */}
      <Tabs defaultValue="informacion" className="space-y-4">
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="informacion">Información</TabsTrigger>
          <TabsTrigger value="clinico">Clínico</TabsTrigger>
          <TabsTrigger value="epidemiologia">Epidemiología</TabsTrigger>
          <TabsTrigger value="establecimientos">Establecimientos</TabsTrigger>
          <TabsTrigger value="timeline">Timeline</TabsTrigger>
          <TabsTrigger value="datos">Datos Raw</TabsTrigger>
        </TabsList>

        {/* Tab: Información General */}
        <TabsContent value="informacion" className="space-y-4">
          {/* Datos del sujeto */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Datos del Sujeto</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {evento.ciudadano ? (
                <div className="grid gap-3 md:grid-cols-2">
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-muted-foreground">
                      Nombre completo
                    </p>
                    <p className="text-sm">
                      {evento.ciudadano.nombre} {evento.ciudadano.apellido}
                    </p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-muted-foreground">
                      Documento
                    </p>
                    <p className="text-sm">
                      {evento.ciudadano.documento || "No especificado"}
                    </p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-muted-foreground">
                      Fecha de nacimiento
                    </p>
                    <p className="text-sm">
                      {formatDate(evento.ciudadano.fecha_nacimiento)}
                    </p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-muted-foreground">
                      Sexo
                    </p>
                    <p className="text-sm">
                      {evento.ciudadano.sexo || "No especificado"}
                    </p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-muted-foreground">
                      Provincia
                    </p>
                    <p className="text-sm">
                      {evento.ciudadano.provincia || "No especificada"}
                    </p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-muted-foreground">
                      Localidad
                    </p>
                    <p className="text-sm">
                      {evento.ciudadano.localidad || "No especificada"}
                    </p>
                  </div>
                  {evento.ciudadano.telefono && (
                    <div className="space-y-1">
                      <p className="text-sm font-medium text-muted-foreground">
                        Teléfono
                      </p>
                      <p className="text-sm">{evento.ciudadano.telefono}</p>
                    </div>
                  )}
                </div>
              ) : evento.animal ? (
                <div className="grid gap-3 md:grid-cols-2">
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-muted-foreground">
                      Nombre
                    </p>
                    <p className="text-sm">
                      {evento.animal.identificacion || "Sin nombre"}
                    </p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-muted-foreground">
                      Especie
                    </p>
                    <p className="text-sm">
                      {evento.animal.especie || "No especificada"}
                    </p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-muted-foreground">
                      Raza
                    </p>
                    <p className="text-sm">
                      {evento.animal.raza || "No especificada"}
                    </p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-muted-foreground">
                      Provincia
                    </p>
                    <p className="text-sm">
                      {evento.animal.provincia || "No especificada"}
                    </p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-muted-foreground">
                      Localidad
                    </p>
                    <p className="text-sm">
                      {evento.animal.localidad || "No especificada"}
                    </p>
                  </div>
                </div>
              ) : (
                <Alert>
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>
                    No hay información disponible del sujeto
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>

          {/* Fechas importantes */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Fechas Importantes</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid gap-3 md:grid-cols-2">
                <div className="space-y-1">
                  <p className="text-sm font-medium text-muted-foreground">
                    Fecha del evento
                  </p>
                  <p className="text-sm">
                    {formatDate(evento.fecha_minima_caso)}
                  </p>
                </div>
                {evento.fecha_inicio_sintomas && (
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-muted-foreground">
                      Inicio de síntomas
                    </p>
                    <p className="text-sm">
                      {formatDate(evento.fecha_inicio_sintomas)}
                    </p>
                  </div>
                )}
                {evento.fecha_apertura_caso && (
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-muted-foreground">
                      Apertura del caso
                    </p>
                    <p className="text-sm">
                      {formatDate(evento.fecha_apertura_caso)}
                    </p>
                  </div>
                )}
                {evento.fecha_primera_consulta && (
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-muted-foreground">
                      Primera consulta
                    </p>
                    <p className="text-sm">
                      {formatDate(evento.fecha_primera_consulta)}
                    </p>
                  </div>
                )}
              </div>
              {(evento.semana_epidemiologica_apertura ||
                evento.anio_epidemiologico_apertura) && (
                  <div className="pt-2 border-t">
                    <p className="text-sm text-muted-foreground">
                      Semana epidemiológica:{" "}
                      {evento.semana_epidemiologica_apertura}/
                      {evento.anio_epidemiologico_apertura}
                    </p>
                  </div>
                )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab: Información Clínica */}
        <TabsContent value="clinico" className="space-y-4">
          {/* Síntomas */}
          {evento.sintomas && evento.sintomas.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Heart className="h-4 w-4" />
                  Síntomas
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {evento.sintomas.map((sintoma) => (
                    <div
                      key={sintoma.id}
                      className="flex items-center justify-between py-2 border-b last:border-b-0"
                    >
                      <span className="text-sm">
                        {sintoma.nombre || "Síntoma no especificado"}
                      </span>
                      {sintoma.fecha_inicio && (
                        <span className="text-xs text-muted-foreground">
                          {formatDate(sintoma.fecha_inicio)}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Muestras */}
          {evento.muestras && evento.muestras.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <TestTube className="h-4 w-4" />
                  Muestras
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {evento.muestras.map((muestra) => (
                    <div
                      key={muestra.id}
                      className="space-y-1 py-2 border-b last:border-b-0"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">
                          {muestra.tipo || "Tipo no especificado"}
                        </span>
                        {muestra.valor && (
                          <Badge
                            variant={
                              muestra.valor === "Positivo"
                                ? "destructive"
                                : "outline"
                            }
                          >
                            {muestra.valor}
                          </Badge>
                        )}
                      </div>
                      {muestra.fecha_toma_muestra && (
                        <span className="text-xs text-muted-foreground">
                          Tomada el {formatDate(muestra.fecha_toma_muestra)}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Diagnósticos */}
          {evento.diagnosticos && evento.diagnosticos.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Stethoscope className="h-4 w-4" />
                  Diagnósticos
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {evento.diagnosticos.map((diagnostico) => (
                    <div
                      key={diagnostico.id}
                      className="space-y-1 py-2 border-b last:border-b-0"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-sm">
                          {diagnostico.diagnostico ||
                            "Diagnóstico no especificado"}
                        </span>
                        {diagnostico.es_principal && (
                          <Badge variant="default" className="text-xs">
                            Principal
                          </Badge>
                        )}
                      </div>
                      {diagnostico.fecha && (
                        <span className="text-xs text-muted-foreground">
                          {formatDate(diagnostico.fecha)}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Vacunas */}
          {evento.vacunas && evento.vacunas.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Syringe className="h-4 w-4" />
                  Vacunas
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {evento.vacunas.map((vacuna, idx: number) => (
                    <div
                      key={idx}
                      className="space-y-1 py-2 border-b last:border-b-0"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">
                          {vacuna.nombre_vacuna || "Vacuna no especificada"}
                        </span>
                        {vacuna.dosis_total && (
                          <Badge variant="outline" className="text-xs">
                            {vacuna.dosis_total} dosis
                          </Badge>
                        )}
                      </div>
                      {vacuna.fecha_ultima_dosis && (
                        <span className="text-xs text-muted-foreground">
                          Última dosis: {formatDate(vacuna.fecha_ultima_dosis)}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Tratamientos */}
          {evento.tratamientos && evento.tratamientos.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Heart className="h-4 w-4" />
                  Tratamientos
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {evento.tratamientos.map((tratamiento) => (
                    <div
                      key={tratamiento.id}
                      className="space-y-2 p-3 border rounded-lg"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          {tratamiento.recibio_tratamiento !== null && (
                            <Badge
                              variant={
                                tratamiento.recibio_tratamiento
                                  ? "default"
                                  : "secondary"
                              }
                            >
                              {tratamiento.recibio_tratamiento
                                ? "Recibió"
                                : "No recibió"}
                            </Badge>
                          )}
                        </div>
                        {tratamiento.fecha_inicio && (
                          <span className="text-xs text-muted-foreground">
                            Inicio: {formatDate(tratamiento.fecha_inicio)}
                          </span>
                        )}
                      </div>
                      {tratamiento.descripcion && (
                        <p className="text-sm text-muted-foreground">
                          {tratamiento.descripcion}
                        </p>
                      )}
                      {tratamiento.fecha_fin && (
                        <span className="text-xs text-muted-foreground">
                          Fin: {formatDate(tratamiento.fecha_fin)}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Internaciones */}
          {evento.internaciones && evento.internaciones.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Building className="h-4 w-4" />
                  Internaciones
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {evento.internaciones.map((internacion) => (
                    <div
                      key={internacion.id}
                      className="space-y-2 p-3 border rounded-lg"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          {internacion.requirio_uci && (
                            <Badge variant="destructive" className="text-xs">
                              UCI
                            </Badge>
                          )}
                          {(internacion as { condicion_egreso?: string })
                            .condicion_egreso && (
                              <Badge
                                variant={
                                  (
                                    (internacion as { condicion_egreso?: string })
                                      .condicion_egreso || ""
                                  )
                                    .toLowerCase()
                                    .includes("muerte")
                                    ? "destructive"
                                    : "default"
                                }
                                className="text-xs"
                              >
                                {
                                  (internacion as { condicion_egreso?: string })
                                    .condicion_egreso
                                }
                              </Badge>
                            )}
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        {internacion.fecha_internacion && (
                          <div>
                            <span className="font-medium">Ingreso:</span>
                            <span className="ml-2">
                              {formatDate(internacion.fecha_internacion)}
                            </span>
                          </div>
                        )}
                        {internacion.fecha_alta && (
                          <div>
                            <span className="font-medium">Alta:</span>
                            <span className="ml-2">
                              {formatDate(internacion.fecha_alta)}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Tab: Epidemiología (NEW - EVENT-CENTERED) */}
        <TabsContent value="epidemiologia" className="space-y-4">
          {/* Investigaciones */}
          {evento.investigaciones && evento.investigaciones.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Search className="h-4 w-4" />
                  Investigaciones Epidemiológicas
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {evento.investigaciones.map((inv) => (
                    <div
                      key={inv.id}
                      className="space-y-2 p-3 border rounded-lg"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          {inv.es_investigacion_terreno && (
                            <Badge variant="secondary" className="text-xs">
                              Terreno
                            </Badge>
                          )}
                          {inv.origen_financiamiento && (
                            <Badge variant="outline" className="text-xs">
                              {inv.origen_financiamiento}
                            </Badge>
                          )}
                        </div>
                        {inv.fecha_investigacion && (
                          <span className="text-xs text-muted-foreground">
                            {formatDate(inv.fecha_investigacion)}
                          </span>
                        )}
                      </div>
                      {inv.tipo_lugar_investigacion && (
                        <p className="text-sm text-muted-foreground">
                          {inv.tipo_lugar_investigacion}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Contactos */}
          {evento.contactos && evento.contactos.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <User className="h-4 w-4" />
                  Contactos y Notificaciones
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {evento.contactos.map((contacto) => (
                    <div
                      key={contacto.id}
                      className="space-y-2 p-3 border rounded-lg"
                    >
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        {contacto.contacto_caso_confirmado !== null && (
                          <div>
                            <span className="font-medium">
                              Caso confirmado:
                            </span>
                            <span
                              className={
                                contacto.contacto_caso_confirmado
                                  ? "ml-2 text-red-600"
                                  : "ml-2 text-green-600"
                              }
                            >
                              {contacto.contacto_caso_confirmado ? "Sí" : "No"}
                            </span>
                          </div>
                        )}
                        {contacto.contacto_caso_sospechoso !== null && (
                          <div>
                            <span className="font-medium">
                              Caso sospechoso:
                            </span>
                            <span
                              className={
                                contacto.contacto_caso_sospechoso
                                  ? "ml-2 text-yellow-600"
                                  : "ml-2 text-green-600"
                              }
                            >
                              {contacto.contacto_caso_sospechoso ? "Sí" : "No"}
                            </span>
                          </div>
                        )}
                        {(contacto.contactos_menores_un_ano ?? 0) > 0 && (
                          <div>
                            <span className="font-medium">Menores 1 año:</span>
                            <span className="ml-2">
                              {contacto.contactos_menores_un_ano}
                            </span>
                          </div>
                        )}
                        {(contacto.contactos_vacunados ?? 0) > 0 && (
                          <div>
                            <span className="font-medium">Vacunados:</span>
                            <span className="ml-2">
                              {contacto.contactos_vacunados}
                            </span>
                          </div>
                        )}
                        {(contacto.contactos_embarazadas ?? 0) > 0 && (
                          <div>
                            <span className="font-medium">Embarazadas:</span>
                            <span className="ml-2">
                              {contacto.contactos_embarazadas}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Ámbitos de Concurrencia */}
          {evento.ambitos_concurrencia &&
            evento.ambitos_concurrencia.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <MapPin className="h-4 w-4" />
                    Ámbitos de Concurrencia
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {evento.ambitos_concurrencia.map((ambito) => (
                      <div
                        key={ambito.id}
                        className="space-y-2 p-3 border rounded-lg"
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <h4 className="font-medium text-sm">
                              {ambito.nombre_lugar || "Lugar no especificado"}
                            </h4>
                            {ambito.tipo_lugar && (
                              <p className="text-xs text-muted-foreground">
                                {ambito.tipo_lugar}
                              </p>
                            )}
                          </div>
                          {ambito.fecha_ocurrencia && (
                            <span className="text-xs text-muted-foreground">
                              {formatDate(ambito.fecha_ocurrencia)}
                            </span>
                          )}
                        </div>
                        <div className="flex gap-2">
                          {ambito.localidad && (
                            <Badge variant="outline" className="text-xs">
                              <MapPin className="h-3 w-3 mr-1" />
                              {ambito.localidad}
                            </Badge>
                          )}
                          {ambito.frecuencia_concurrencia && (
                            <Badge variant="secondary" className="text-xs">
                              {ambito.frecuencia_concurrencia}
                            </Badge>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

          {/* Antecedentes Epidemiológicos */}
          {evento.antecedentes && evento.antecedentes.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Clock className="h-4 w-4" />
                  Antecedentes Epidemiológicos
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {evento.antecedentes.map((antecedente) => (
                    <div
                      key={antecedente.id}
                      className="flex items-center justify-between py-2 border-b last:border-b-0"
                    >
                      <span className="text-sm">
                        {antecedente.descripcion ||
                          "Antecedente no especificado"}
                      </span>
                      {antecedente.fecha_antecedente && (
                        <span className="text-xs text-muted-foreground">
                          {formatDate(antecedente.fecha_antecedente)}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Tab: Establecimientos (NEW - EVENT-CENTERED) */}
        <TabsContent value="establecimientos" className="space-y-4">
          {/* Establecimiento de Consulta */}
          {evento.establecimiento_consulta && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Stethoscope className="h-4 w-4" />
                  Establecimiento de Consulta
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div>
                    <p className="font-medium">
                      {evento.establecimiento_consulta.nombre}
                    </p>
                    {evento.establecimiento_consulta.tipo && (
                      <p className="text-sm text-muted-foreground">
                        {evento.establecimiento_consulta.tipo}
                      </p>
                    )}
                  </div>
                  {(evento.establecimiento_consulta.provincia ||
                    evento.establecimiento_consulta.localidad) && (
                      <div className="flex items-center gap-1 text-sm text-muted-foreground">
                        <MapPin className="h-3 w-3" />
                        <span>
                          {evento.establecimiento_consulta.localidad}
                          {evento.establecimiento_consulta.provincia &&
                            `, ${evento.establecimiento_consulta.provincia}`}
                        </span>
                      </div>
                    )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Establecimiento de Notificación */}
          {evento.establecimiento_notificacion && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4" />
                  Establecimiento de Notificación
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div>
                    <p className="font-medium">
                      {evento.establecimiento_notificacion.nombre}
                    </p>
                    {evento.establecimiento_notificacion.tipo && (
                      <p className="text-sm text-muted-foreground">
                        {evento.establecimiento_notificacion.tipo}
                      </p>
                    )}
                  </div>
                  {(evento.establecimiento_notificacion.provincia ||
                    evento.establecimiento_notificacion.localidad) && (
                      <div className="flex items-center gap-1 text-sm text-muted-foreground">
                        <MapPin className="h-3 w-3" />
                        <span>
                          {evento.establecimiento_notificacion.localidad}
                          {evento.establecimiento_notificacion.provincia &&
                            `, ${evento.establecimiento_notificacion.provincia}`}
                        </span>
                      </div>
                    )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Establecimiento de Carga */}
          {evento.establecimiento_carga && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  Establecimiento de Carga
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div>
                    <p className="font-medium">
                      {evento.establecimiento_carga.nombre}
                    </p>
                    {evento.establecimiento_carga.tipo && (
                      <p className="text-sm text-muted-foreground">
                        {evento.establecimiento_carga.tipo}
                      </p>
                    )}
                  </div>
                  {(evento.establecimiento_carga.provincia ||
                    evento.establecimiento_carga.localidad) && (
                      <div className="flex items-center gap-1 text-sm text-muted-foreground">
                        <MapPin className="h-3 w-3" />
                        <span>
                          {evento.establecimiento_carga.localidad}
                          {evento.establecimiento_carga.provincia &&
                            `, ${evento.establecimiento_carga.provincia}`}
                        </span>
                      </div>
                    )}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Tab: Timeline */}
        <TabsContent value="timeline" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Clock className="h-4 w-4" />
                Línea de Tiempo del Evento
              </CardTitle>
            </CardHeader>
            <CardContent>
              {timeline.length > 0 ? (
                <div className="space-y-4">
                  {timeline.map((item, index: number) => (
                    <div key={index} className="flex gap-3">
                      <div className="flex flex-col items-center">
                        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-muted">
                          {getTimelineIcon(item.tipo)}
                        </div>
                        {index < timeline.length - 1 && (
                          <div className="h-full w-px bg-border" />
                        )}
                      </div>
                      <div className="flex-1 pb-4">
                        <p className="text-sm font-medium">
                          {item.descripcion}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {formatDate(item.fecha)}
                        </p>
                        {item.detalles && (
                          <div className="mt-2">
                            <pre className="text-xs bg-muted p-2 rounded">
                              {JSON.stringify(item.detalles, null, 2)}
                            </pre>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground text-center py-8">
                  No hay eventos en el timeline
                </p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab: Datos Raw */}
        <TabsContent value="datos" className="space-y-4">
          {evento.datos_originales_csv && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">
                  Datos Originales del CSV
                </CardTitle>
              </CardHeader>
              <CardContent>
                <pre className="text-xs overflow-auto bg-muted p-3 rounded">
                  {JSON.stringify(evento.datos_originales_csv, null, 2)}
                </pre>
              </CardContent>
            </Card>
          )}

          {evento.metadata_clasificacion && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">
                  Metadata de Clasificación
                </CardTitle>
              </CardHeader>
              <CardContent>
                <pre className="text-xs overflow-auto bg-muted p-3 rounded">
                  {JSON.stringify(evento.metadata_clasificacion, null, 2)}
                </pre>
              </CardContent>
            </Card>
          )}

          {evento.metadata_extraida && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Metadata Extraída</CardTitle>
              </CardHeader>
              <CardContent>
                <pre className="text-xs overflow-auto bg-muted p-3 rounded">
                  {JSON.stringify(evento.metadata_extraida, null, 2)}
                </pre>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>

      {/* Footer con acciones */}
      {onClose && (
        <>
          <Separator />
          <div className="flex justify-end">
            <Button onClick={onClose}>Cerrar</Button>
          </div>
        </>
      )}
    </div>
  );
}
