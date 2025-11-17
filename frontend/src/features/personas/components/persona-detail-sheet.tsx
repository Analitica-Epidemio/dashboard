"use client";

import { useState } from "react";
import { usePersona } from "@/features/personas/api";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  User,
  MapPin,
  Phone,
  Calendar,
  Activity,
  Heart,
  FileText,
  TestTube,
  Syringe,
  AlertCircle,
  ChevronRight,
} from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { getClasificacionColorClasses, getClasificacionLabel } from "@/features/eventos/api";

interface PersonaDetailSheetProps {
  tipoSujeto: 'humano' | 'animal';
  personaId: number;
  onClose?: () => void;
}

export function PersonaDetailSheet({
  tipoSujeto,
  personaId,
  onClose,
}: PersonaDetailSheetProps) {
  const [activeTab, setActiveTab] = useState("resumen");

  const { data: personaResponse, isLoading, error } = usePersona(tipoSujeto, personaId);
  const persona = personaResponse?.data;

  if (isLoading) {
    return (
      <div className="p-6 space-y-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-32 w-full" />
      </div>
    );
  }

  if (error || !persona) {
    return (
      <Alert variant="destructive" className="m-6">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          Error al cargar información de la persona. Por favor, intenta nuevamente.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="pb-6">
      {/* Header con info básica */}
      <div className="px-6 py-4 bg-muted/30 border-b">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 mb-2">
              <div className="flex-shrink-0 h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
                <User className="h-6 w-6 text-primary" />
              </div>
              <div className="flex-1 min-w-0">
                <h2 className="text-xl font-semibold truncate">{persona.nombre_completo}</h2>
                <p className="text-sm text-muted-foreground">
                  {persona.documento_numero ? `DNI ${persona.documento_numero}` : "Sin documento"}
                </p>
              </div>
            </div>

            {/* Badges */}
            <div className="flex flex-wrap gap-2 mt-3">
              <Badge variant="secondary">
                {persona.total_eventos} {persona.total_eventos === 1 ? "evento" : "eventos"}
              </Badge>
              {persona.sexo_biologico && (
                <Badge variant="outline">{persona.sexo_biologico}</Badge>
              )}
            </div>
          </div>

          {/* Stats rápidas */}
          <div className="flex flex-col gap-2 text-right">
            <div>
              <div className="text-2xl font-bold text-red-600">{persona.eventos_confirmados}</div>
              <div className="text-xs text-muted-foreground">Confirmados</div>
            </div>
            <div>
              <div className="text-xl font-semibold text-yellow-600">{persona.eventos_sospechosos}</div>
              <div className="text-xs text-muted-foreground">Sospechosos</div>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <div className="border-b px-6 bg-background sticky top-0 z-10">
          <TabsList className="w-full justify-start rounded-none border-0 bg-transparent p-0 h-auto">
            <TabsTrigger
              value="resumen"
              className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent px-4 py-3"
            >
              <FileText className="h-4 w-4 mr-2" />
              Resumen
            </TabsTrigger>
            <TabsTrigger
              value="eventos"
              className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent px-4 py-3"
            >
              <Activity className="h-4 w-4 mr-2" />
              Eventos ({persona.total_eventos})
            </TabsTrigger>
            <TabsTrigger
              value="datos"
              className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent px-4 py-3"
            >
              <User className="h-4 w-4 mr-2" />
              Datos Personales
            </TabsTrigger>
          </TabsList>
        </div>

        <div className="px-6 py-4">
          {/* RESUMEN TAB */}
          <TabsContent value="resumen" className="mt-0 space-y-4">
            {/* Estadísticas */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Resumen de Eventos</CardTitle>
              </CardHeader>
              <CardContent className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <div className="text-xs text-muted-foreground mb-1">Confirmados</div>
                  <div className="text-2xl font-bold text-red-600">{persona.eventos_confirmados}</div>
                </div>
                <div>
                  <div className="text-xs text-muted-foreground mb-1">Sospechosos</div>
                  <div className="text-2xl font-bold text-yellow-600">{persona.eventos_sospechosos}</div>
                </div>
                <div>
                  <div className="text-xs text-muted-foreground mb-1">Probables</div>
                  <div className="text-2xl font-bold text-orange-600">{persona.eventos_probables || 0}</div>
                </div>
                <div>
                  <div className="text-xs text-muted-foreground mb-1">Descartados</div>
                  <div className="text-2xl font-bold text-gray-600">{persona.eventos_descartados || 0}</div>
                </div>
              </CardContent>
            </Card>

            {/* Timeline de eventos */}
            {persona.eventos && persona.eventos.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Últimos Eventos</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {persona.eventos.slice(0, 5).map((evento, idx: number) => (
                      <div key={evento.id} className="flex items-start gap-3 pb-3 border-b last:border-0">
                        <div className="flex-shrink-0 w-2 h-2 mt-1.5 rounded-full bg-primary" />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between gap-2">
                            <span className="text-sm font-medium truncate">
                              {evento.tipo_eno_nombre || "ENO Desconocido"}
                            </span>
                            {evento.clasificacion_estrategia && (
                              <span
                                className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${getClasificacionColorClasses(evento.clasificacion_estrategia)}`}
                              >
                                {getClasificacionLabel(evento.clasificacion_estrategia)}
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-4 mt-1 text-xs text-muted-foreground">
                            <span>
                              {evento.fecha_minima_evento
                                ? new Date(evento.fecha_minima_evento).toLocaleDateString("es-ES", {
                                    day: "2-digit",
                                    month: "short",
                                    year: "numeric",
                                  })
                                : "Sin fecha"}
                            </span>
                            {evento.domicilio?.localidad && (
                              <span className="flex items-center gap-1">
                                <MapPin className="h-3 w-3" />
                                {evento.domicilio.localidad}
                              </span>
                            )}
                          </div>

                          {/* Síntomas */}
                          {evento.sintomas && evento.sintomas.length > 0 && (
                            <div className="mt-2 flex flex-wrap gap-1">
                              {evento.sintomas.slice(0, 3).map((sintoma) => (
                                <Badge key={sintoma.id} variant="outline" className="text-xs">
                                  {sintoma.nombre}
                                </Badge>
                              ))}
                              {evento.sintomas.length > 3 && (
                                <Badge variant="outline" className="text-xs">
                                  +{evento.sintomas.length - 3} más
                                </Badge>
                              )}
                            </div>
                          )}

                          {/* Muestras */}
                          {evento.muestras && evento.muestras.length > 0 && (
                            <div className="mt-2 text-xs text-muted-foreground flex items-center gap-1">
                              <TestTube className="h-3 w-3" />
                              {evento.muestras.length} {evento.muestras.length === 1 ? "muestra" : "muestras"}
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

          {/* EVENTOS TAB */}
          <TabsContent value="eventos" className="mt-0 space-y-3">
            {persona.eventos && persona.eventos.length > 0 ? (
              persona.eventos.map((evento) => (
                <Card key={evento.id}>
                  <CardContent className="pt-6">
                    <div className="space-y-3">
                      {/* Header del evento */}
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 min-w-0">
                          <h4 className="font-semibold">{evento.tipo_eno_nombre || "ENO Desconocido"}</h4>
                          <p className="text-sm text-muted-foreground">Evento #{evento.id_evento_caso}</p>
                        </div>
                        {evento.clasificacion_estrategia && (
                          <span
                            className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium border ${getClasificacionColorClasses(evento.clasificacion_estrategia)}`}
                          >
                            {getClasificacionLabel(evento.clasificacion_estrategia)}
                          </span>
                        )}
                      </div>

                      <Separator />

                      {/* Fechas */}
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        {evento.fecha_minima_evento && (
                          <div>
                            <div className="text-xs text-muted-foreground mb-1">Fecha del Evento</div>
                            <div className="flex items-center gap-1.5">
                              <Calendar className="h-3.5 w-3.5 text-muted-foreground" />
                              {new Date(evento.fecha_minima_evento).toLocaleDateString("es-ES", {
                                day: "2-digit",
                                month: "long",
                                year: "numeric",
                              })}
                            </div>
                          </div>
                        )}
                        {evento.fecha_inicio_sintomas && (
                          <div>
                            <div className="text-xs text-muted-foreground mb-1">Inicio Síntomas</div>
                            <div className="flex items-center gap-1.5">
                              <Calendar className="h-3.5 w-3.5 text-muted-foreground" />
                              {new Date(evento.fecha_inicio_sintomas).toLocaleDateString("es-ES")}
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Domicilio */}
                      {evento.domicilio && (
                        <div>
                          <div className="text-xs text-muted-foreground mb-1.5">Ubicación</div>
                          <div className="flex items-start gap-1.5 text-sm">
                            <MapPin className="h-3.5 w-3.5 text-muted-foreground mt-0.5" />
                            <div>
                              {evento.domicilio.calle && evento.domicilio.numero && (
                                <div>{evento.domicilio.calle} {evento.domicilio.numero}</div>
                              )}
                              <div className="text-muted-foreground">
                                {[evento.domicilio.localidad, evento.domicilio.provincia]
                                  .filter(Boolean)
                                  .join(", ") || "Sin ubicación"}
                              </div>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Síntomas */}
                      {evento.sintomas && evento.sintomas.length > 0 && (
                        <div>
                          <div className="text-xs text-muted-foreground mb-2">Síntomas ({evento.sintomas.length})</div>
                          <div className="flex flex-wrap gap-1.5">
                            {evento.sintomas.map((sintoma) => (
                              <Badge key={sintoma.id} variant="secondary" className="text-xs">
                                <Heart className="h-3 w-3 mr-1" />
                                {sintoma.nombre}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Muestras */}
                      {evento.muestras && evento.muestras.length > 0 && (
                        <div>
                          <div className="text-xs text-muted-foreground mb-2">Muestras ({evento.muestras.length})</div>
                          <div className="space-y-2">
                            {evento.muestras.map((muestra) => (
                              <div key={muestra.id} className="flex items-center gap-2 text-sm p-2 rounded bg-muted/50">
                                <TestTube className="h-4 w-4 text-muted-foreground" />
                                <div className="flex-1">
                                  <div className="font-medium">{muestra.tipo_muestra || "Muestra"}</div>
                                  {muestra.resultado && (
                                    <div className="text-xs text-muted-foreground">
                                      Resultado: {muestra.resultado}
                                    </div>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Vacunas */}
                      {evento.vacunas && evento.vacunas.length > 0 && (
                        <div>
                          <div className="text-xs text-muted-foreground mb-2">Vacunas ({evento.vacunas.length})</div>
                          <div className="flex flex-wrap gap-1.5">
                            {evento.vacunas.map((vacuna) => (
                              <Badge key={vacuna.id} variant="outline" className="text-xs">
                                <Syringe className="h-3 w-3 mr-1" />
                                {vacuna.vacuna} {vacuna.dosis && `(${vacuna.dosis}°)`}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))
            ) : (
              <div className="text-center py-12 text-muted-foreground">
                <Activity className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No hay eventos registrados</p>
              </div>
            )}
          </TabsContent>

          {/* DATOS PERSONALES TAB */}
          <TabsContent value="datos" className="mt-0">
            <Card>
              <CardContent className="pt-6 space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <div className="text-xs text-muted-foreground mb-1">Nombre Completo</div>
                    <div className="text-sm font-medium">{persona.nombre_completo}</div>
                  </div>

                  {persona.documento_numero && (
                    <div>
                      <div className="text-xs text-muted-foreground mb-1">Documento</div>
                      <div className="text-sm font-medium">
                        {persona.documento_tipo || "DNI"} {persona.documento_numero}
                      </div>
                    </div>
                  )}

                  {persona.fecha_nacimiento && (
                    <div>
                      <div className="text-xs text-muted-foreground mb-1">Fecha de Nacimiento</div>
                      <div className="text-sm font-medium">
                        {new Date(persona.fecha_nacimiento).toLocaleDateString("es-ES")}
                      </div>
                    </div>
                  )}

                  {persona.sexo_biologico && (
                    <div>
                      <div className="text-xs text-muted-foreground mb-1">Sexo</div>
                      <div className="text-sm font-medium">{persona.sexo_biologico}</div>
                    </div>
                  )}

                  {persona.telefono && (
                    <div>
                      <div className="text-xs text-muted-foreground mb-1">Teléfono</div>
                      <div className="text-sm font-medium flex items-center gap-1.5">
                        <Phone className="h-3.5 w-3.5 text-muted-foreground" />
                        {persona.telefono}
                      </div>
                    </div>
                  )}

                  {persona.obra_social && (
                    <div>
                      <div className="text-xs text-muted-foreground mb-1">Obra Social</div>
                      <div className="text-sm font-medium">{persona.obra_social}</div>
                    </div>
                  )}
                </div>

                {persona.domicilio && (
                  <>
                    <Separator />
                    <div>
                      <div className="text-xs text-muted-foreground mb-2">Domicilio</div>
                      <div className="flex items-start gap-1.5 text-sm">
                        <MapPin className="h-4 w-4 text-muted-foreground mt-0.5" />
                        <div>
                          {persona.domicilio.calle && persona.domicilio.numero && (
                            <div className="font-medium">
                              {persona.domicilio.calle} {persona.domicilio.numero}
                            </div>
                          )}
                          <div className="text-muted-foreground">
                            {[persona.domicilio.localidad, persona.domicilio.provincia]
                              .filter(Boolean)
                              .join(", ") || "Sin ubicación"}
                          </div>
                        </div>
                      </div>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </div>
      </Tabs>
    </div>
  );
}
