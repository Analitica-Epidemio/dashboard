"use client";

import { useMemo, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import {
  Activity,
  Users,
  TrendingUp,
  MapPin,
  AlertCircle,
  Info,
  Search,
  Pause,
  Play,
  RotateCcw,
} from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

export type TimelineMode = "day" | "week" | "month";

/**
 * Modo de visualización temporal para el timeline
 * - cumulative: Acumulado histórico (todos los casos hasta la fecha)
 * - active: Casos activos dentro de una ventana temporal (ej: últimos 14 días)
 * - period: Solo casos nuevos del período actual
 */
export type TimelineDisplayMode = "cumulative" | "active" | "period";

export interface GrupoEventoResumen {
  grupoId: string;
  grupoNombre: string;
  totalEventos: number;
  tipos: { nombre: string; total: number }[];
}

interface TimelineSidebarProps {
  available: boolean;
  enabled: boolean;
  loading: boolean;
  playing: boolean;
  currentStep: number;
  totalSteps: number;
  currentLabel?: string;
  rangeLabel?: string;
  mode: TimelineMode;
  onModeChange: (mode: TimelineMode) => void;
  onTogglePlay: () => void;
  onStepChange: (value: number) => void;
  onReset: () => void;
  disabledMessage?: string;
  speed: number;
  onSpeedChange: (value: number) => void;
  speedOptions: { label: string; value: number }[];
  // Nuevas props para modo lazy
  modeEnabled: boolean; // Si el modo timeline está activado
  onToggleModeEnabled: () => void; // Callback para activar/desactivar
  dataLoaded: boolean; // Si los datos ya fueron cargados
  // Modo de visualización temporal
  displayMode: TimelineDisplayMode;
  onDisplayModeChange: (mode: TimelineDisplayMode) => void;
  // Ventana de días para modo "active" (casos activos)
  activeWindowDays: number;
  onActiveWindowDaysChange: (days: number) => void;
  // Ventana sugerida por el grupo ENO seleccionado (NULL = acumulado)
  suggestedWindowDays?: number | null;
}

interface MapaSidebarProps {
  totalEventosGlobal: number;
  totalEventosMapeados: number;
  poblacionTotal: number;
  provinciasAfectadas: number;
  tasaIncidencia: number;
  categorias: GrupoEventoResumen[];
  grupoColorMap: Record<string, string>;
  categoriasLoading?: boolean;
  selectedGrupos: string[];
  onToggleGrupo: (grupoId: string) => void;
  onClearFiltros: () => void;
  timeline: TimelineSidebarProps;
}

const TIMELINE_MODE_LABELS: Record<TimelineMode, string> = {
  day: "Días",
  week: "Semanas",
  month: "Meses",
};

const DISPLAY_MODE_LABELS: Record<TimelineDisplayMode, { label: string; description: string }> = {
  cumulative: {
    label: "Acumulado",
    description: "Todos los casos hasta la fecha (histórico total)",
  },
  active: {
    label: "Activos",
    description: "Casos dentro de la ventana temporal (brote activo)",
  },
  period: {
    label: "Del período",
    description: "Solo casos nuevos del período actual",
  },
};

const WINDOW_OPTIONS = [
  { label: "7 días", value: 7 },
  { label: "14 días", value: 14 },
  { label: "21 días", value: 21 },
  { label: "30 días", value: 30 },
  { label: "60 días", value: 60 },
  { label: "90 días", value: 90 },
];

export function MapaSidebar({
  totalEventosGlobal,
  totalEventosMapeados,
  poblacionTotal,
  provinciasAfectadas,
  tasaIncidencia,
  categorias,
  grupoColorMap,
  categoriasLoading = false,
  selectedGrupos,
  onToggleGrupo,
  onClearFiltros,
  timeline,
}: MapaSidebarProps) {
  const [categoriaSearch, setCategoriaSearch] = useState("");

  const formatNumber = (num: number): string => num.toLocaleString("es-AR");

  const formatCompact = (num: number): string => {
    if (num >= 1_000_000) return `${(num / 1_000_000).toFixed(1)}M`;
    if (num >= 1_000) return `${(num / 1_000).toFixed(1)}K`;
    return num.toString();
  };

  const domiciliosNoMapeados = Math.max(totalEventosGlobal - totalEventosMapeados, 0);
  const porcentajeCobertura =
    totalEventosGlobal > 0
      ? ((totalEventosMapeados / totalEventosGlobal) * 100).toFixed(1)
      : "0";

  const poblacionText = poblacionTotal > 0 ? formatCompact(poblacionTotal) : "N/D";
  const tasaText = tasaIncidencia > 0 ? tasaIncidencia.toFixed(1) : "N/D";

  const filteredCategorias = useMemo(() => {
    if (!categoriaSearch.trim()) return categorias;
    const term = categoriaSearch.toLowerCase();
    return categorias.filter(
      (grupo) =>
        grupo.grupoNombre.toLowerCase().includes(term) ||
        grupo.tipos.some((tipo) => tipo.nombre.toLowerCase().includes(term))
    );
  }, [categorias, categoriaSearch]);

  const timelineSliderMax = Math.max(timeline.totalSteps - 1, 0);
  const timelineSliderValue = Math.min(
    timeline.currentStep,
    timelineSliderMax
  );

  return (
    <div className="space-y-4">
      <section className="rounded-2xl border border-gray-200 bg-white/80 p-4 space-y-4">
        <div>
          <p className="text-sm font-semibold text-gray-900">
            Vigilancia epidemiológica
          </p>
          <p className="text-xs text-gray-500">
            Métricas de los domicilios visibles
          </p>
        </div>

        <div className="rounded-xl border border-blue-100 bg-blue-50 p-4">
          <div className="flex items-center gap-2 mb-2">
            <Activity className="h-4 w-4 text-blue-600" />
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <div className="flex items-center gap-1">
                    <span className="text-xs font-medium uppercase tracking-wide text-blue-700">
                      Total registrado
                    </span>
                    <Info className="h-3 w-3 text-blue-500" />
                  </div>
                </TooltipTrigger>
                <TooltipContent>
                  <p className="max-w-xs text-xs">
                    Total de eventos asociados a domicilios visibles en el mapa.
                  </p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
          <div className="text-3xl font-semibold text-blue-900">
            {formatNumber(totalEventosGlobal)}
          </div>
          <p className="text-xs text-blue-700">eventos geolocalizados</p>
        </div>

        <div className="rounded-xl border border-gray-200 bg-gray-50 p-4 space-y-2">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-gray-700">
            <MapPin className="h-4 w-4" />
            Cobertura
          </div>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Mapeados</p>
              <p className="text-lg font-semibold text-emerald-600">
                {formatNumber(totalEventosMapeados)}
              </p>
            </div>
            <Badge variant="secondary" className="text-xs">
              {porcentajeCobertura}%
            </Badge>
          </div>
          {domiciliosNoMapeados > 0 && (
            <div className="flex items-center justify-between text-sm text-gray-600">
              <div className="flex items-center gap-1">
                <AlertCircle className="h-4 w-4 text-amber-600" />
                <span>Sin geocodificar</span>
              </div>
              <span className="font-medium text-amber-600">
                {formatNumber(domiciliosNoMapeados)}
              </span>
            </div>
          )}
        </div>

        <Separator />

        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <div className="flex items-center gap-2 text-xs text-gray-500 uppercase tracking-wide">
              <Users className="h-3.5 w-3.5" />
              Población
            </div>
            <p className="text-xl font-semibold text-gray-900">{poblacionText}</p>
            <p className="text-xs text-gray-500">habitantes estimados</p>
          </div>
          <div>
            <div className="flex items-center gap-2 text-xs text-gray-500 uppercase tracking-wide">
              <TrendingUp className="h-3.5 w-3.5" />
              Tasa × 100k
            </div>
            <p className="text-xl font-semibold text-gray-900">{tasaText}</p>
            <p className="text-xs text-gray-500">incidencia acumulada</p>
          </div>
        </div>

        <Separator />

        <div>
          <div className="flex items-center gap-2 text-xs text-gray-500 uppercase tracking-wide">
            <MapPin className="h-3.5 w-3.5 text-purple-600" />
            Provincias
          </div>
          <p className="text-xl font-semibold text-gray-900">
            {provinciasAfectadas}
          </p>
          <p className="text-xs text-gray-500">con eventos visibles</p>
        </div>
      </section>

      <section className="rounded-2xl border border-gray-200 bg-white/80 p-4 space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-semibold text-gray-900">
              Categorías de eventos
            </p>
            <p className="text-xs text-gray-500">
              Colores sincronizados con los puntos del mapa
            </p>
          </div>
          {selectedGrupos.length > 0 && (
            <button
              onClick={onClearFiltros}
              className="text-xs font-medium text-blue-600 hover:underline"
            >
              Mostrar todos
            </button>
          )}
        </div>

        <div className="relative">
          <Input
            placeholder="Filtrar por grupo o evento..."
            value={categoriaSearch}
            onChange={(e) => setCategoriaSearch(e.target.value)}
            className="pl-9 text-sm"
          />
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
        </div>

        {categoriasLoading && (
          <p className="text-xs text-gray-500">Cargando categorías...</p>
        )}

        {!categoriasLoading && filteredCategorias.length === 0 && (
          <p className="text-xs text-gray-500">
            No hay coincidencias para “{categoriaSearch}”.
          </p>
        )}

        {!categoriasLoading && filteredCategorias.length > 0 && (
          <div className="max-h-[360px] space-y-3 overflow-y-auto pr-1">
            {filteredCategorias.map((grupo) => {
              const color = grupoColorMap[grupo.grupoId] || "#94a3b8";
              const isActive =
                selectedGrupos.length === 0 || selectedGrupos.includes(grupo.grupoId);

              return (
                <div
                  key={grupo.grupoId}
                  className={`rounded-xl border p-3 transition-colors ${
                    isActive
                      ? "border-gray-200 bg-white"
                      : "border-dashed border-gray-200 opacity-60"
                  }`}
                >
                  <button
                    onClick={() => onToggleGrupo(grupo.grupoId)}
                    className="flex w-full items-start justify-between text-left"
                  >
                    <div className="flex flex-1 items-start gap-3">
                      <span
                        className="mt-1.5 h-3 w-3 rounded-full border border-white shadow"
                        style={{ backgroundColor: color }}
                      />
                      <div className="space-y-0.5">
                        <p className="text-sm font-semibold text-gray-900">
                          {grupo.grupoNombre}
                        </p>
                        <p className="text-xs text-gray-500">
                          {grupo.totalEventos.toLocaleString("es-AR")} eventos
                        </p>
                      </div>
                    </div>
                    <Badge
                      variant={isActive ? "secondary" : "outline"}
                      className="text-[10px]"
                    >
                      {isActive ? "Visible" : "Oculto"}
                    </Badge>
                  </button>

                  {grupo.tipos.length > 0 && (
                    <div className="mt-3 border-t pt-2 text-[11px] text-gray-600">
                      <p className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-gray-500">
                        Eventos
                      </p>
                      <div className="space-y-1">
                        {grupo.tipos.map((tipo) => (
                          <div
                            key={tipo.nombre}
                            className="flex items-center justify-between gap-2"
                          >
                            <span className="truncate">{tipo.nombre}</span>
                            <span className="text-gray-400">
                              {tipo.total.toLocaleString("es-AR")}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </section>

      <section className="rounded-2xl border border-gray-200 bg-white/80 p-4 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-semibold text-gray-900">
              Timeline de aparición
            </p>
            <p className="text-xs text-gray-500">
              Reproducí la evolución acumulada por día, semana o mes
            </p>
          </div>
          <Button
            size="sm"
            variant={timeline.modeEnabled ? "default" : "outline"}
            onClick={timeline.onToggleModeEnabled}
            className="text-xs"
          >
            {timeline.modeEnabled ? "Desactivar" : "Activar"}
          </Button>
        </div>

        {/* Mostrar mensaje si el modo timeline no está activado */}
        {!timeline.modeEnabled && (
          <div className="rounded-lg border border-dashed border-gray-300 bg-gray-50 p-3">
            <p className="text-xs text-gray-500 text-center">
              Activá el modo timeline para cargar los datos de eventos y visualizar la evolución temporal.
            </p>
          </div>
        )}

        {/* Mostrar loading cuando se están cargando datos */}
        {timeline.modeEnabled && timeline.loading && (
          <div className="rounded-lg border border-blue-200 bg-blue-50 p-3">
            <div className="flex items-center gap-2">
              <div className="h-4 w-4 animate-spin rounded-full border-b-2 border-blue-600"></div>
              <p className="text-xs text-blue-700">
                Descargando eventos para el timeline...
              </p>
            </div>
          </div>
        )}

        {/* Controles del timeline (solo si está activado y tiene datos) */}
        {timeline.modeEnabled && !timeline.loading && (
          <>
            <div className="flex items-center justify-between gap-2">
              <Select
                value={timeline.mode}
                onValueChange={(value) => timeline.onModeChange(value as TimelineMode)}
                disabled={!timeline.available}
              >
                <SelectTrigger className="w-full text-sm">
                  <SelectValue placeholder="Agrupar" />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(TIMELINE_MODE_LABELS).map(([value, label]) => (
                    <SelectItem key={value} value={value}>
                      {label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select
                value={String(timeline.speed)}
                onValueChange={(value) => timeline.onSpeedChange(Number(value))}
                disabled={!timeline.available}
              >
                <SelectTrigger className="w-full text-sm">
                  <SelectValue placeholder="Velocidad" />
                </SelectTrigger>
                <SelectContent>
                  {timeline.speedOptions.map((option) => (
                    <SelectItem key={option.value} value={String(option.value)}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Selector de modo de visualización (Acumulado/Activos/Período) */}
            <div className="space-y-2">
              <div className="flex items-center gap-1 text-xs text-gray-500">
                <span>Modo de visualización</span>
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Info className="h-3 w-3 cursor-help" />
                    </TooltipTrigger>
                    <TooltipContent side="top" className="max-w-xs">
                      <div className="space-y-1 text-xs">
                        <p><strong>Acumulado:</strong> Total histórico hasta la fecha</p>
                        <p><strong>Activos:</strong> Casos dentro de la ventana temporal (brote activo)</p>
                        <p><strong>Del período:</strong> Solo casos nuevos del período</p>
                      </div>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>
              <div className="flex gap-1">
                {(Object.keys(DISPLAY_MODE_LABELS) as TimelineDisplayMode[]).map((mode) => (
                  <Button
                    key={mode}
                    size="sm"
                    variant={timeline.displayMode === mode ? "default" : "outline"}
                    onClick={() => timeline.onDisplayModeChange(mode)}
                    className="flex-1 text-xs px-2"
                    disabled={!timeline.available}
                  >
                    {DISPLAY_MODE_LABELS[mode].label}
                  </Button>
                ))}
              </div>

              {/* Selector de ventana para modo "active" */}
              {timeline.displayMode === "active" && (
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-500 whitespace-nowrap">Ventana:</span>
                  <Select
                    value={String(timeline.activeWindowDays)}
                    onValueChange={(value) => timeline.onActiveWindowDaysChange(Number(value))}
                    disabled={!timeline.available}
                  >
                    <SelectTrigger className="w-full text-xs h-8">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {WINDOW_OPTIONS.map((option) => (
                        <SelectItem key={option.value} value={String(option.value)}>
                          {option.label}
                          {timeline.suggestedWindowDays === option.value && " (sugerido)"}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}

              {/* Mensaje sobre ventana sugerida */}
              {timeline.suggestedWindowDays && timeline.displayMode === "cumulative" && (
                <p className="text-[10px] text-amber-600 bg-amber-50 px-2 py-1 rounded">
                  💡 Para esta enfermedad se sugiere usar modo &quot;Activos&quot; con ventana de {timeline.suggestedWindowDays} días
                </p>
              )}
            </div>

            <Separator />

            {!timeline.available && (
              <p className="text-xs text-gray-500">
                {timeline.disabledMessage ||
                  "Seleccioná una categoría para habilitar la animación."}
              </p>
            )}

            {timeline.available && (
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Button
                    size="sm"
                    variant={timeline.playing ? "secondary" : "default"}
                    onClick={timeline.onTogglePlay}
                    disabled={!timeline.enabled}
                    className="flex-1"
                  >
                    {timeline.playing ? (
                      <>
                        <Pause className="mr-2 h-4 w-4" />
                        Pausar
                      </>
                    ) : (
                      <>
                        <Play className="mr-2 h-4 w-4" />
                        Reproducir
                      </>
                    )}
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={timeline.onReset}
                    disabled={!timeline.enabled}
                  >
                    <RotateCcw className="mr-2 h-4 w-4" />
                    Reiniciar
                  </Button>
                </div>

                <div className="space-y-1">
                  <input
                    type="range"
                    min={0}
                    max={timelineSliderMax}
                    value={timelineSliderValue}
                    onChange={(e) => timeline.onStepChange(Number(e.target.value))}
                    disabled={!timeline.enabled}
                    className="w-full accent-blue-600"
                  />
                  <div className="flex items-center justify-between text-[10px] text-gray-500">
                    <span>{timeline.rangeLabel ?? "—"}</span>
                    <span className="font-semibold text-gray-800">
                      {timeline.currentLabel ?? "Seleccioná un punto"}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </section>
    </div>
  );
}
