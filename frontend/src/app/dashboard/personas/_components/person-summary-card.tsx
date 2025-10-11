"use client";

import React from "react";
import { User, FileText, Activity, AlertCircle, Calendar, MapPin } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

interface PersonSummaryCardProps {
  persona: any;
  onViewDetail?: () => void;
}

export function PersonSummaryCard({ persona, onViewDetail }: PersonSummaryCardProps) {
  return (
    <Card className="hover:bg-muted/30 transition-colors cursor-pointer" onClick={onViewDetail}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
              <User className="h-6 w-6 text-primary" />
            </div>
            <div>
              <CardTitle className="text-lg">{persona.nombre_completo}</CardTitle>
              <div className="flex items-center gap-2 text-sm text-muted-foreground mt-1">
                {persona.documento && (
                  <span className="flex items-center gap-1">
                    <FileText className="h-3 w-3" />
                    {persona.documento}
                  </span>
                )}
                {persona.edad_actual && <span>{persona.edad_actual} años</span>}
              </div>
            </div>
          </div>
          <Badge variant={persona.total_eventos > 3 ? "destructive" : "secondary"}>
            {persona.total_eventos} eventos
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Ubicación */}
        {persona.provincia && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <MapPin className="h-3 w-3" />
            {persona.localidad && `${persona.localidad}, `}{persona.provincia}
          </div>
        )}

        {/* Estadísticas */}
        <div className="grid grid-cols-3 gap-2 text-center">
          <div className="rounded-lg bg-green-50 dark:bg-green-950/20 p-2">
            <p className="text-2xl font-bold text-green-600">{persona.eventos_confirmados || 0}</p>
            <p className="text-xs text-muted-foreground">Confirmados</p>
          </div>
          <div className="rounded-lg bg-yellow-50 dark:bg-yellow-950/20 p-2">
            <p className="text-2xl font-bold text-yellow-600">{persona.eventos_sospechosos || 0}</p>
            <p className="text-xs text-muted-foreground">Sospechosos</p>
          </div>
          <div className="rounded-lg bg-red-50 dark:bg-red-950/20 p-2">
            <p className="text-2xl font-bold text-red-600">{persona.eventos_requieren_revision || 0}</p>
            <p className="text-xs text-muted-foreground">Revisión</p>
          </div>
        </div>

        {/* Fechas */}
        <div className="flex items-center justify-between text-xs text-muted-foreground pt-2 border-t">
          <div className="flex items-center gap-1">
            <Calendar className="h-3 w-3" />
            Último evento: {persona.ultimo_evento_fecha ? new Date(persona.ultimo_evento_fecha).toLocaleDateString("es-ES") : "N/A"}
          </div>
          {persona.tiene_eventos_activos && (
            <Badge variant="outline" className="text-xs">
              <Activity className="h-3 w-3 mr-1" />
              Activo
            </Badge>
          )}
        </div>

        {/* Último evento */}
        {persona.ultimo_evento_tipo && (
          <div className="text-sm">
            <span className="font-medium">Último evento:</span> {persona.ultimo_evento_tipo}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
