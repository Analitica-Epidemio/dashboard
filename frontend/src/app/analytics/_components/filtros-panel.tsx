"use client";

import React from "react";
import { X, Filter, Calendar, MapPin } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";

interface FiltrosPanelProps {
  onClose: () => void;
}

export function FiltrosPanel({ onClose }: FiltrosPanelProps) {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Filter className="h-5 w-5 text-muted-foreground" />
          <h3 className="text-lg font-semibold">Filtros Avanzados</h3>
        </div>
        <Button variant="ghost" size="icon" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </div>

      <Separator />

      {/* Filtros temporales */}
      <div className="space-y-4">
        <h4 className="text-sm font-semibold flex items-center gap-2">
          <Calendar className="h-4 w-4" />
          Rango Temporal
        </h4>
        
        <div className="grid gap-3">
          <div>
            <Label htmlFor="fecha_desde">Fecha desde</Label>
            <Input
              id="fecha_desde"
              type="date"
              className="mt-1"
            />
          </div>
          
          <div>
            <Label htmlFor="fecha_hasta">Fecha hasta</Label>
            <Input
              id="fecha_hasta"
              type="date"
              className="mt-1"
            />
          </div>
          
          <div>
            <Label htmlFor="periodo">Período predefinido</Label>
            <Select>
              <SelectTrigger className="mt-1">
                <SelectValue placeholder="Seleccionar período" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ultima_semana">Última semana</SelectItem>
                <SelectItem value="ultimo_mes">Último mes</SelectItem>
                <SelectItem value="ultimos_3_meses">Últimos 3 meses</SelectItem>
                <SelectItem value="ultimo_anio">Último año</SelectItem>
                <SelectItem value="anio_actual">Año actual</SelectItem>
                <SelectItem value="anio_anterior">Año anterior</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      <Separator />

      {/* Filtros geográficos */}
      <div className="space-y-4">
        <h4 className="text-sm font-semibold flex items-center gap-2">
          <MapPin className="h-4 w-4" />
          Ubicación Geográfica
        </h4>
        
        <div className="grid gap-3">
          <div>
            <Label htmlFor="provincia">Provincia</Label>
            <Select>
              <SelectTrigger className="mt-1">
                <SelectValue placeholder="Todas las provincias" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="todas">Todas</SelectItem>
                <SelectItem value="chubut">Chubut</SelectItem>
                <SelectItem value="buenos_aires">Buenos Aires</SelectItem>
                <SelectItem value="caba">CABA</SelectItem>
                {/* Más provincias */}
              </SelectContent>
            </Select>
          </div>
          
          <div>
            <Label htmlFor="departamento">Departamento</Label>
            <Select>
              <SelectTrigger className="mt-1">
                <SelectValue placeholder="Todos los departamentos" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="todos">Todos</SelectItem>
                {/* Departamentos dinámicos según provincia */}
              </SelectContent>
            </Select>
          </div>
          
          <div>
            <Label htmlFor="region_sanitaria">Región Sanitaria</Label>
            <Select>
              <SelectTrigger className="mt-1">
                <SelectValue placeholder="Todas las regiones" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="todas">Todas</SelectItem>
                <SelectItem value="region_1">Región I</SelectItem>
                <SelectItem value="region_2">Región II</SelectItem>
                <SelectItem value="region_3">Región III</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      <Separator />

      {/* Filtros demográficos */}
      <div className="space-y-4">
        <h4 className="text-sm font-semibold">Datos Demográficos</h4>
        
        <div className="grid gap-3">
          <div>
            <Label htmlFor="grupo_edad">Grupo de Edad</Label>
            <Select>
              <SelectTrigger className="mt-1">
                <SelectValue placeholder="Todos los grupos" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="todos">Todos</SelectItem>
                <SelectItem value="0-4">0-4 años</SelectItem>
                <SelectItem value="5-14">5-14 años</SelectItem>
                <SelectItem value="15-24">15-24 años</SelectItem>
                <SelectItem value="25-34">25-34 años</SelectItem>
                <SelectItem value="35-44">35-44 años</SelectItem>
                <SelectItem value="45-54">45-54 años</SelectItem>
                <SelectItem value="55-64">55-64 años</SelectItem>
                <SelectItem value="65+">65+ años</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <div>
            <Label htmlFor="sexo">Sexo</Label>
            <Select>
              <SelectTrigger className="mt-1">
                <SelectValue placeholder="Todos" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="todos">Todos</SelectItem>
                <SelectItem value="masculino">Masculino</SelectItem>
                <SelectItem value="femenino">Femenino</SelectItem>
                <SelectItem value="otro">Otro</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      <Separator />

      {/* Botones de acción */}
      <div className="flex gap-2">
        <Button onClick={onClose} className="flex-1">
          Aplicar Filtros
        </Button>
        <Button variant="outline" className="flex-1">
          Limpiar Todo
        </Button>
      </div>
    </div>
  );
}