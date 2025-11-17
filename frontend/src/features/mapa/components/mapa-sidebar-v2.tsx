"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import {
  Activity,
  Users,
  TrendingUp,
  MapPin,
  Search,
  Layers,
  AlertCircle,
  CheckCircle2,
  Info
} from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface MapaSidebarProps {
  totalEventosGlobal: number;
  totalEventosMapeados: number;
  poblacionTotal: number;
  provinciasAfectadas: number;
  tasaIncidencia: number;
  onNivelChange: (nivel: "departamento" | "localidad" | null) => void;
  nivel: "departamento" | "localidad";
}

export function MapaSidebar({
  totalEventosGlobal,
  totalEventosMapeados,
  poblacionTotal,
  provinciasAfectadas,
  tasaIncidencia,
  onNivelChange,
  nivel,
}: MapaSidebarProps) {
  const [searchTerm, setSearchTerm] = useState("");

  const formatNumber = (num: number): string => {
    return num.toLocaleString('es-AR');
  };

  const formatCompact = (num: number): string => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  // Calcular domicilios no mapeados
  const domiciliosNoMapeados = totalEventosGlobal - totalEventosMapeados;
  const porcentajeCobertura = totalEventosGlobal > 0
    ? ((totalEventosMapeados / totalEventosGlobal) * 100).toFixed(1)
    : 0;

  return (
    <div className="space-y-4">
      {/* Métricas Principales - Diseño Limpio */}
      <Card className="border-gray-200">
        <CardHeader className="pb-3">
          <CardTitle className="text-base font-semibold text-gray-900">
            Vigilancia Epidemiológica
          </CardTitle>
          <p className="text-xs text-gray-500 mt-1">
            Datos actualizados en tiempo real
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Total Eventos Registrados */}
          <div className="bg-blue-50 border border-blue-100 rounded-lg p-4">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <Activity className="h-4 w-4 text-blue-600" />
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <div className="flex items-center gap-1">
                          <p className="text-xs font-medium text-blue-700 uppercase tracking-wide">
                            Total Registrado
                          </p>
                          <Info className="h-3 w-3 text-blue-500" />
                        </div>
                      </TooltipTrigger>
                      <TooltipContent>
                        <p className="max-w-xs text-xs">
                          Total de domicilios epidemiológicos registrados en el sistema de vigilancia
                        </p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </div>
                <p className="text-3xl font-bold text-blue-900">
                  {formatNumber(totalEventosGlobal)}
                </p>
                <p className="text-xs text-blue-600 mt-1">casos en base de datos</p>
              </div>
            </div>
          </div>

          {/* Calidad de Datos - CRÍTICO */}
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-3">
              <MapPin className="h-4 w-4 text-gray-600" />
              <p className="text-xs font-semibold text-gray-700 uppercase tracking-wide">
                Cobertura Geográfica
              </p>
            </div>

            {/* Mapeados */}
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                <span className="text-sm text-gray-700">Mapeados</span>
              </div>
              <div className="text-right">
                <p className="text-lg font-bold text-emerald-600">
                  {formatNumber(totalEventosMapeados)}
                </p>
                <Badge variant="secondary" className="text-xs">
                  {porcentajeCobertura}%
                </Badge>
              </div>
            </div>

            {/* No Mapeados - Mostrar solo si hay */}
            {domiciliosNoMapeados > 0 && (
              <>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <AlertCircle className="h-4 w-4 text-amber-600" />
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <div className="flex items-center gap-1">
                            <span className="text-sm text-gray-700">Sin mapear</span>
                            <Info className="h-3 w-3 text-gray-400" />
                          </div>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p className="max-w-xs text-xs">
                            Eventos sin coordenadas o con datos de ubicación incompletos
                          </p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  </div>
                  <p className="text-lg font-bold text-amber-600">
                    {formatNumber(domiciliosNoMapeados)}
                  </p>
                </div>
              </>
            )}

            {/* Barra de progreso */}
            <div className="w-full bg-gray-200 rounded-full h-2 mt-3">
              <div
                className="bg-emerald-600 h-2 rounded-full transition-all"
                style={{ width: `${porcentajeCobertura}%` }}
              />
            </div>
          </div>

          <Separator />

          {/* Población Afectada */}
          <div>
            <div className="flex items-center gap-2 mb-2">
              <div className="bg-emerald-50 p-1.5 rounded">
                <Users className="h-3.5 w-3.5 text-emerald-600" />
              </div>
              <p className="text-xs font-medium text-gray-600 uppercase tracking-wide">
                Población
              </p>
            </div>
            <p className="text-2xl font-bold text-gray-900">
              {formatCompact(poblacionTotal)}
            </p>
            <p className="text-xs text-gray-500 mt-0.5">habitantes afectados</p>
          </div>

          <Separator />

          {/* Tasa de Incidencia */}
          <div>
            <div className="flex items-center gap-2 mb-2">
              <div className="bg-sky-50 p-1.5 rounded">
                <TrendingUp className="h-3.5 w-3.5 text-sky-600" />
              </div>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <div className="flex items-center gap-1">
                      <p className="text-xs font-medium text-gray-600 uppercase tracking-wide">
                        Tasa × 100k
                      </p>
                      <Info className="h-3 w-3 text-gray-400" />
                    </div>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p className="max-w-xs text-xs">
                      Número de casos por cada 100,000 habitantes. Métrica estándar epidemiológica para comparar regiones.
                    </p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>
            <p className="text-2xl font-bold text-gray-900">
              {tasaIncidencia.toFixed(1)}
            </p>
            <p className="text-xs text-gray-500 mt-0.5">por 100,000 habitantes</p>
          </div>

          <Separator />

          {/* Provincias */}
          <div>
            <div className="flex items-center gap-2 mb-2">
              <div className="bg-purple-50 p-1.5 rounded">
                <MapPin className="h-3.5 w-3.5 text-purple-600" />
              </div>
              <p className="text-xs font-medium text-gray-600 uppercase tracking-wide">
                Provincias
              </p>
            </div>
            <p className="text-2xl font-bold text-gray-900">{provinciasAfectadas}</p>
            <p className="text-xs text-gray-500 mt-0.5">con casos registrados</p>
          </div>
        </CardContent>
      </Card>

      {/* Controles del Mapa */}
      <Card className="border-gray-200">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-semibold text-gray-900 flex items-center gap-2">
            <Layers className="h-4 w-4" />
            Controles de Visualización
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Nivel Geográfico */}
          <div className="space-y-2">
            <Label htmlFor="nivel" className="text-xs font-medium text-gray-700">
              Nivel de detalle
            </Label>
            <Select
              value={nivel}
              onValueChange={(value) => {
                if (value === "auto") {
                  onNivelChange(null);
                } else {
                  onNivelChange(value as "departamento" | "localidad");
                }
              }}
            >
              <SelectTrigger id="nivel" className="w-full">
                <SelectValue placeholder="Seleccionar nivel" />
              </SelectTrigger>
              <SelectContent className="z-[10000]">
                <SelectItem value="auto">
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary" className="text-xs">Auto</Badge>
                    Automático (por zoom)
                  </div>
                </SelectItem>
                <SelectItem value="departamento">Departamentos</SelectItem>
                <SelectItem value="localidad">Localidades/Municipios</SelectItem>
              </SelectContent>
            </Select>
            <p className="text-xs text-gray-500">
              {nivel === "departamento"
                ? "Mostrando divisiones administrativas"
                : "Mostrando municipios y comunas"}
            </p>
          </div>

          <Separator />

          {/* Búsqueda */}
          <div className="space-y-2">
            <Label htmlFor="search" className="text-xs font-medium text-gray-700 flex items-center gap-2">
              <Search className="h-3 w-3" />
              Buscar ubicación
            </Label>
            <Input
              id="search"
              type="text"
              placeholder="Nombre o código INDEC..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full"
            />
          </div>
        </CardContent>
      </Card>

      {/* Leyenda */}
      <Card className="border-gray-200">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-semibold text-gray-900">
            Leyenda
          </CardTitle>
          <p className="text-xs text-gray-500 mt-1">
            Colores según número de domicilios
          </p>
        </CardHeader>
        <CardContent>
          <div className="space-y-2.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded bg-gray-200 border border-gray-300"></div>
                <span className="text-xs text-gray-600">Sin datos</span>
              </div>
              <span className="text-xs font-mono text-gray-500">0</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded bg-green-500"></div>
                <span className="text-xs text-gray-600">Bajo</span>
              </div>
              <span className="text-xs font-mono text-gray-500">1-10</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded bg-yellow-500"></div>
                <span className="text-xs text-gray-600">Moderado</span>
              </div>
              <span className="text-xs font-mono text-gray-500">11-100</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded bg-orange-500"></div>
                <span className="text-xs text-gray-600">Alto</span>
              </div>
              <span className="text-xs font-mono text-gray-500">101-500</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded bg-red-600"></div>
                <span className="text-xs text-gray-600">Crítico</span>
              </div>
              <span className="text-xs font-mono text-gray-500">&gt;500</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Nota al pie */}
      <div className="text-xs text-gray-500 px-2 py-3 bg-gray-50 border border-gray-200 rounded-lg">
        <p className="font-medium text-gray-700 mb-1">Fuente de datos</p>
        <p>Sistema Nacional de Vigilancia Epidemiológica</p>
        <p className="mt-1 text-gray-400">Actualización en tiempo real</p>
      </div>
    </div>
  );
}
