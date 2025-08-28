"use client";

import React from "react";
import { Activity, Users, Stethoscope, Loader2 } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";

interface Grupo {
  id: number;
  nombre: string;
  tipo: string;
  descripcion?: string | null;
  clasificaciones_disponibles: string[];
  graficos_especiales?: string[];
  orden: number;
  activo: boolean;
}

interface GrupoSelectorProps {
  grupos: Grupo[];
  grupoSeleccionado: number | null;
  onSeleccionar: (grupoId: number | null) => void;
  isLoading?: boolean;
}

export function GrupoSelector({
  grupos,
  grupoSeleccionado,
  onSeleccionar,
  isLoading = false
}: GrupoSelectorProps) {
  
  const getGrupoIcon = (tipo: string) => {
    switch (tipo) {
      case "grupo":
        return <Users className="h-3 w-3" />;
      case "simple":
        return <Stethoscope className="h-3 w-3" />;
      default:
        return <Activity className="h-3 w-3" />;
    }
  };

  const getGrupoVariant = (tipo: string): "default" | "secondary" => {
    return tipo === "grupo" ? "default" : "secondary";
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-4">
        <Loader2 className="h-4 w-4 animate-spin mr-2" />
        <span className="text-sm text-muted-foreground">Cargando grupos...</span>
      </div>
    );
  }

  if (grupos.length === 0) {
    return (
      <div className="text-center p-4">
        <Activity className="h-8 w-8 mx-auto text-muted-foreground opacity-50 mb-2" />
        <p className="text-sm text-muted-foreground">
          No hay grupos disponibles
        </p>
      </div>
    );
  }

  const grupoActual = grupos.find(g => g.id === grupoSeleccionado);

  return (
    <div className="space-y-3">
      <Select
        value={grupoSeleccionado?.toString() || ""}
        onValueChange={(value) => onSeleccionar(value ? parseInt(value) : null)}
      >
        <SelectTrigger>
          <SelectValue placeholder="Selecciona un grupo..." />
        </SelectTrigger>
        <SelectContent>
          {grupos.map((grupo) => (
            <SelectItem key={grupo.id} value={grupo.id.toString()}>
              <div className="flex items-center gap-2">
                {getGrupoIcon(grupo.tipo)}
                <span>{grupo.nombre}</span>
                <Badge variant={getGrupoVariant(grupo.tipo)} className="text-xs">
                  {grupo.tipo === "grupo" ? "Grupo" : "Simple"}
                </Badge>
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Información del grupo seleccionado */}
      {grupoActual && (
        <div className="p-3 bg-muted/30 rounded-md space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">{grupoActual.nombre}</span>
            <Badge variant={getGrupoVariant(grupoActual.tipo)} className="text-xs">
              {grupoActual.tipo === "grupo" ? "Grupo" : "Evento Simple"}
            </Badge>
          </div>
          
          <div className="text-xs text-muted-foreground">
            <p className="mb-1">
              <strong>Clasificaciones:</strong> {grupoActual.clasificaciones_disponibles.join(", ")}
            </p>
            
            {grupoActual.graficos_especiales && grupoActual.graficos_especiales.length > 0 && (
              <p>
                <strong>Gráficos especiales:</strong> {grupoActual.graficos_especiales.length}
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}