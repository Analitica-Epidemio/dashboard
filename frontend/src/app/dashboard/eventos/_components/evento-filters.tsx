"use client";

import React from "react";
import { X, Calendar, MapPin, Activity, Filter } from "lucide-react";
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
import { Badge } from "@/components/ui/badge";
import type { EventoFilters } from "@/lib/api/eventos";

interface EventoFiltersPanelProps {
  filters: EventoFilters;
  onFilterChange: (key: string, value: unknown) => void;
  onClose: () => void;
}

export function EventoFiltersPanel({
  filters,
  onFilterChange,
  onClose,
}: EventoFiltersPanelProps) {
  // Contador de filtros activos
  const activeFiltersCount = Object.entries(filters).filter(
    ([key, value]) => value && !["page", "page_size", "sort_by"].includes(key)
  ).length;

  const handleClearFilters = () => {
    // Reset todos los filtros excepto paginación
    const clearedFilters: EventoFilters = {
      page: 1,
      page_size: filters.page_size || 50,
      sort_by: filters.sort_by || "fecha_desc",
    };

    Object.keys(clearedFilters).forEach((key) => {
      if (key !== "page" && key !== "page_size" && key !== "sort_by") {
        onFilterChange(key, undefined);
      }
    });
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Filter className="h-5 w-5 text-muted-foreground" />
          <h3 className="text-lg font-semibold">Filtros</h3>
          {activeFiltersCount > 0 && (
            <Badge variant="secondary">{activeFiltersCount} activos</Badge>
          )}
        </div>
        <div className="flex items-center gap-2">
          {activeFiltersCount > 0 && (
            <Button variant="ghost" size="sm" onClick={handleClearFilters}>
              Limpiar filtros
            </Button>
          )}
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <Separator />

      {/* Filtros en grid */}
      <div className="grid gap-4 md:grid-cols-3">
        {/* Tipo de Evento */}
        <div className="space-y-2">
          <Label htmlFor="tipo_eno">
            <Activity className="inline-block h-3 w-3 mr-1" />
            Tipo de Evento
          </Label>
          <Select
            value={filters.tipo_eno_id?.toString() || ""}
            onValueChange={(value) =>
              onFilterChange("tipo_eno_id", value ? parseInt(value) : undefined)
            }
          >
            <SelectTrigger id="tipo_eno">
              <SelectValue placeholder="Todos los eventos" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">Todos los eventos</SelectItem>
              <SelectItem value="1">Dengue</SelectItem>
              <SelectItem value="2">COVID-19</SelectItem>
              <SelectItem value="3">Rabia</SelectItem>
              <SelectItem value="4">Sífilis</SelectItem>
              <SelectItem value="5">Chagas</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Clasificación */}
        <div className="space-y-2">
          <Label htmlFor="clasificacion">Clasificación</Label>
          <Select
            value={filters.clasificacion || ""}
            onValueChange={(value) =>
              onFilterChange("clasificacion", value || undefined)
            }
          >
            <SelectTrigger id="clasificacion">
              <SelectValue placeholder="Todas las clasificaciones" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">Todas</SelectItem>
              <SelectItem value="confirmados">Confirmados</SelectItem>
              <SelectItem value="sospechosos">Sospechosos</SelectItem>
              <SelectItem value="probables">Probables</SelectItem>
              <SelectItem value="en_estudio">En Estudio</SelectItem>
              <SelectItem value="negativos">Negativos</SelectItem>
              <SelectItem value="descartados">Descartados</SelectItem>
              <SelectItem value="requiere_revision">
                Requiere Revisión
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Tipo de Sujeto */}
        <div className="space-y-2">
          <Label htmlFor="tipo_sujeto">Tipo de Sujeto</Label>
          <Select
            value={filters.tipo_sujeto || ""}
            onValueChange={(value) =>
              onFilterChange("tipo_sujeto", value || undefined)
            }
          >
            <SelectTrigger id="tipo_sujeto">
              <SelectValue placeholder="Todos los sujetos" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">Todos</SelectItem>
              <SelectItem value="humano">👤 Humanos</SelectItem>
              <SelectItem value="animal">🐾 Animales</SelectItem>
              <SelectItem value="desconocido">❓ Desconocido</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Fecha Desde */}
        <div className="space-y-2">
          <Label htmlFor="fecha_desde">
            <Calendar className="inline-block h-3 w-3 mr-1" />
            Fecha Desde
          </Label>
          <Input
            id="fecha_desde"
            type="date"
            value={filters.fecha_desde || ""}
            onChange={(e) =>
              onFilterChange("fecha_desde", e.target.value || undefined)
            }
          />
        </div>

        {/* Fecha Hasta */}
        <div className="space-y-2">
          <Label htmlFor="fecha_hasta">
            <Calendar className="inline-block h-3 w-3 mr-1" />
            Fecha Hasta
          </Label>
          <Input
            id="fecha_hasta"
            type="date"
            value={filters.fecha_hasta || ""}
            onChange={(e) =>
              onFilterChange("fecha_hasta", e.target.value || undefined)
            }
          />
        </div>

        {/* Provincia */}
        <div className="space-y-2">
          <Label htmlFor="provincia">
            <MapPin className="inline-block h-3 w-3 mr-1" />
            Provincia
          </Label>
          <Select
            value={filters.provincia || ""}
            onValueChange={(value) =>
              onFilterChange("provincia", value || undefined)
            }
          >
            <SelectTrigger id="provincia">
              <SelectValue placeholder="Todas las provincias" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">Todas</SelectItem>
              <SelectItem value="Buenos Aires">Buenos Aires</SelectItem>
              <SelectItem value="CABA">CABA</SelectItem>
              <SelectItem value="Catamarca">Catamarca</SelectItem>
              <SelectItem value="Chaco">Chaco</SelectItem>
              <SelectItem value="Chubut">Chubut</SelectItem>
              <SelectItem value="Córdoba">Córdoba</SelectItem>
              <SelectItem value="Corrientes">Corrientes</SelectItem>
              <SelectItem value="Entre Ríos">Entre Ríos</SelectItem>
              <SelectItem value="Formosa">Formosa</SelectItem>
              <SelectItem value="Jujuy">Jujuy</SelectItem>
              <SelectItem value="La Pampa">La Pampa</SelectItem>
              <SelectItem value="La Rioja">La Rioja</SelectItem>
              <SelectItem value="Mendoza">Mendoza</SelectItem>
              <SelectItem value="Misiones">Misiones</SelectItem>
              <SelectItem value="Neuquén">Neuquén</SelectItem>
              <SelectItem value="Río Negro">Río Negro</SelectItem>
              <SelectItem value="Salta">Salta</SelectItem>
              <SelectItem value="San Juan">San Juan</SelectItem>
              <SelectItem value="San Luis">San Luis</SelectItem>
              <SelectItem value="Santa Cruz">Santa Cruz</SelectItem>
              <SelectItem value="Santa Fe">Santa Fe</SelectItem>
              <SelectItem value="Santiago del Estero">
                Santiago del Estero
              </SelectItem>
              <SelectItem value="Tierra del Fuego">Tierra del Fuego</SelectItem>
              <SelectItem value="Tucumán">Tucumán</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Es Positivo */}
        <div className="space-y-2">
          <Label htmlFor="es_positivo">Estado del Caso</Label>
          <Select
            value={
              filters.es_positivo === undefined
                ? ""
                : filters.es_positivo.toString()
            }
            onValueChange={(value) =>
              onFilterChange(
                "es_positivo",
                value === "" ? undefined : value === "true"
              )
            }
          >
            <SelectTrigger id="es_positivo">
              <SelectValue placeholder="Todos los estados" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">Todos</SelectItem>
              <SelectItem value="true">✅ Positivos</SelectItem>
              <SelectItem value="false">❌ Negativos</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Requiere Revisión */}
        <div className="space-y-2">
          <Label htmlFor="requiere_revision">Revisión</Label>
          <Select
            value={
              filters.requiere_revision === undefined
                ? ""
                : filters.requiere_revision.toString()
            }
            onValueChange={(value) =>
              onFilterChange(
                "requiere_revision",
                value === "" ? undefined : value === "true"
              )
            }
          >
            <SelectTrigger id="requiere_revision">
              <SelectValue placeholder="Todos" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">Todos</SelectItem>
              <SelectItem value="true">⚠️ Requiere Revisión</SelectItem>
              <SelectItem value="false">✓ No Requiere Revisión</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Ordenamiento */}
        <div className="space-y-2">
          <Label htmlFor="sort_by">Ordenar por</Label>
          <Select
            value={filters.sort_by || "fecha_desc"}
            onValueChange={(value) => onFilterChange("sort_by", value)}
          >
            <SelectTrigger id="sort_by">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="fecha_desc">Fecha (más reciente)</SelectItem>
              <SelectItem value="fecha_asc">Fecha (más antiguo)</SelectItem>
              <SelectItem value="id_desc">ID (mayor a menor)</SelectItem>
              <SelectItem value="id_asc">ID (menor a mayor)</SelectItem>
              <SelectItem value="tipo_eno">Tipo de Evento</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Filtros activos como badges */}
      {activeFiltersCount > 0 && (
        <div className="space-y-2">
          <Separator />
          <div className="flex flex-wrap gap-2">
            <span className="text-sm text-muted-foreground">
              Filtros activos:
            </span>
            {filters.tipo_eno_id && (
              <Badge variant="secondary">
                Tipo evento: {filters.tipo_eno_id}
                <X
                  className="ml-1 h-3 w-3 cursor-pointer"
                  onClick={() => onFilterChange("tipo_eno_id", undefined)}
                />
              </Badge>
            )}
            {filters.clasificacion && (
              <Badge variant="secondary">
                {filters.clasificacion}
                <X
                  className="ml-1 h-3 w-3 cursor-pointer"
                  onClick={() => onFilterChange("clasificacion", undefined)}
                />
              </Badge>
            )}
            {filters.provincia && (
              <Badge variant="secondary">
                {filters.provincia}
                <X
                  className="ml-1 h-3 w-3 cursor-pointer"
                  onClick={() => onFilterChange("provincia", undefined)}
                />
              </Badge>
            )}
            {filters.tipo_sujeto && (
              <Badge variant="secondary">
                Sujeto: {filters.tipo_sujeto}
                <X
                  className="ml-1 h-3 w-3 cursor-pointer"
                  onClick={() => onFilterChange("tipo_sujeto", undefined)}
                />
              </Badge>
            )}
            {filters.fecha_desde && (
              <Badge variant="secondary">
                Desde: {filters.fecha_desde}
                <X
                  className="ml-1 h-3 w-3 cursor-pointer"
                  onClick={() => onFilterChange("fecha_desde", undefined)}
                />
              </Badge>
            )}
            {filters.fecha_hasta && (
              <Badge variant="secondary">
                Hasta: {filters.fecha_hasta}
                <X
                  className="ml-1 h-3 w-3 cursor-pointer"
                  onClick={() => onFilterChange("fecha_hasta", undefined)}
                />
              </Badge>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
