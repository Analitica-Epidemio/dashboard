"use client";

import { useEffect, useMemo, useState } from "react";
import dynamic from "next/dynamic";
import { format, startOfDay, startOfMonth, startOfWeek, endOfWeek, endOfMonth } from "date-fns";
import { es } from "date-fns/locale";
import { MapaLayout } from "@/features/mapa/components/mapa-layout";
import {
  MapaSidebar,
  type GrupoEventoResumen,
  type TimelineMode,
} from "@/features/mapa/components/mapa-sidebar-v2";
import { DomicilioDetalleDialog } from "@/features/mapa/components/domicilio-detalle-dialog";
import { EstablecimientoDetalleDialog } from "@/features/mapa/components/establecimiento-detalle-dialog";
import { useDomiciliosMapa, type DomicilioMapaItem } from "@/features/mapa/api";
import { type EstablecimientoMapaItem } from "@/features/establecimientos/api";
import { useTiposEno } from "@/features/eventos/api";
import { apiClient } from "@/lib/api/client";
import type { components } from "@/lib/api/types";

type EventoListItem = components["schemas"]["EventoListItem"];
type EventoListResponse = components["schemas"]["EventoListResponse"];

interface NormalizedTimelineEvent {
  id: number;
  domicilioId: number;
  fecha: Date;
  tipoNombre: string | null;
  grupoId: string;
}

interface TimelineBucket {
  key: string;
  start: Date;
  end: Date;
  label: string;
  events: NormalizedTimelineEvent[];
}

const MapaSimple = dynamic(
  () =>
    import("@/features/mapa/components/mapa-simple").then((mod) => ({
      default: mod.MapaSimple,
    })),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-full items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-b-2 border-blue-600"></div>
          <p className="font-medium text-gray-600">
            Cargando mapa de domicilios...
          </p>
          <p className="mt-1 text-sm text-gray-400">Por favor espere</p>
        </div>
      </div>
    ),
  }
);

const FALLBACK_GROUP_ID = "sin-categoria";
const FALLBACK_GROUP_NAME = "Sin categoría";
const FALLBACK_COLOR = "#94a3b8";
const CATEGORY_COLORS = [
  "#0ea5e9",
  "#f97316",
  "#10b981",
  "#a855f7",
  "#22d3ee",
  "#ef4444",
  "#facc15",
  "#6366f1",
  "#14b8a6",
  "#fb7185",
];
const TIMELINE_INTERVAL_MS = 1400;
const TIMELINE_SPEED_OPTIONS = [
  { label: "0.5×", value: 0.5 },
  { label: "1×", value: 1 },
  { label: "1.5×", value: 1.5 },
  { label: "2×", value: 2 },
  { label: "3×", value: 3 },
  { label: "4×", value: 4 },
];

const startOfBucket = (date: Date, mode: TimelineMode) => {
  if (mode === "month") return startOfMonth(date);
  if (mode === "week") return startOfWeek(date, { weekStartsOn: 1 });
  return startOfDay(date);
};

const endOfBucket = (start: Date, mode: TimelineMode) => {
  if (mode === "month") return endOfMonth(start);
  if (mode === "week") return endOfWeek(start, { weekStartsOn: 1 });
  return start;
};

const buildBucketLabel = (start: Date, end: Date, mode: TimelineMode) => {
  if (mode === "month") {
    return format(start, "MMMM yyyy", { locale: es });
  }
  if (mode === "week") {
    return `Semana del ${format(start, "d MMM", { locale: es })} al ${format(
      end,
      "d MMM",
      { locale: es }
    )}`;
  }
  return format(start, "d MMM yyyy", { locale: es });
};

export default function MapaPage() {
  const [selectedDomicilioId, setSelectedDomicilioId] = useState<number | null>(
    null
  );
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedEstablecimientoId, setSelectedEstablecimientoId] = useState<
    number | null
  >(null);
  const [establecimientoDialogOpen, setEstablecimientoDialogOpen] =
    useState(false);
  const [selectedGrupos, setSelectedGrupos] = useState<string[]>([]);

  const [eventosList, setEventosList] = useState<EventoListItem[]>([]);
  const [eventosLoading, setEventosLoading] = useState(false);
  const [eventosError, setEventosError] = useState<string | null>(null);
  const [timelineMode, setTimelineMode] = useState<TimelineMode>("day");
  const [timelineIndex, setTimelineIndex] = useState(0);
  const [timelinePlaying, setTimelinePlaying] = useState(false);
  const [timelineSpeed, setTimelineSpeed] = useState(1);

  const { data, isLoading } = useDomiciliosMapa({
    limit: 50000,
  });
  const { data: tiposEnoResponse, isLoading: tiposLoading } = useTiposEno({
    page: 1,
    per_page: 100,
  });

  const domicilios = data?.data?.items || [];
  const tiposEno = tiposEnoResponse?.data || [];

  useEffect(() => {
    let isMounted = true;

    async function fetchAllEvents() {
      setEventosLoading(true);
      setEventosError(null);
      try {
        const pageSize = 200;
        let page = 1;
        let totalPages = 1;
        const collected: EventoListItem[] = [];

        while (isMounted && page <= totalPages) {
          const response = await apiClient.GET("/api/v1/eventos/", {
            params: {
              query: {
                page,
                page_size: pageSize,
              },
            },
          });

          if (response.error) {
            throw response.error;
          }

          const payload = response.data?.data as EventoListResponse | undefined;
          if (!payload) break;

          collected.push(...(payload.data || []));
          totalPages = payload.pagination?.total_pages || totalPages;
          page += 1;
        }

        if (isMounted) {
          setEventosList(collected);
        }
      } catch (error) {
        console.error("Error cargando eventos para timeline", error);
        if (isMounted) {
          setEventosError(
            "No se pudieron cargar los eventos para la animación temporal."
          );
        }
      } finally {
        if (isMounted) {
          setEventosLoading(false);
        }
      }
    }

    fetchAllEvents();
    return () => {
      isMounted = false;
    };
  }, []);

  const tipoGrupoMapping = useMemo(() => {
    const mapping: Record<string, { grupoId: string; grupoNombre: string }> = {};
    tiposEno.forEach((tipo) => {
      const firstGrupo = tipo.grupos?.[0];
      if (firstGrupo) {
        mapping[tipo.nombre] = {
          grupoId: String(firstGrupo.id),
          grupoNombre: firstGrupo.nombre,
        };
      }
    });
    return mapping;
  }, [tiposEno]);

  const categoriasResumen: GrupoEventoResumen[] = useMemo(() => {
    if (!domicilios.length) return [];

    const gruposMap = new Map<
      string,
      {
        grupoId: string;
        grupoNombre: string;
        total: number;
        tipos: Map<string, number>;
      }
    >();

    domicilios.forEach((domicilio) => {
      const tiposEvento = domicilio.tipos_eventos || {};

      Object.entries(tiposEvento).forEach(([tipoNombre, total]) => {
        const totalCount = total as number;
        const grupo =
          tipoGrupoMapping[tipoNombre] || {
            grupoId: FALLBACK_GROUP_ID,
            grupoNombre: FALLBACK_GROUP_NAME,
          };

        if (!gruposMap.has(grupo.grupoId)) {
          gruposMap.set(grupo.grupoId, {
            grupoId: grupo.grupoId,
            grupoNombre: grupo.grupoNombre,
            total: 0,
            tipos: new Map(),
          });
        }

        const entry = gruposMap.get(grupo.grupoId)!;
        entry.total += totalCount;
        entry.tipos.set(
          tipoNombre,
          (entry.tipos.get(tipoNombre) || 0) + totalCount
        );
      });
    });

    return Array.from(gruposMap.values())
      .map((grupo) => ({
        grupoId: grupo.grupoId,
        grupoNombre: grupo.grupoNombre,
        totalEventos: grupo.total,
        tipos: Array.from(grupo.tipos.entries())
          .map(([nombre, total]) => ({ nombre, total }))
          .sort((a, b) => b.total - a.total),
      }))
      .sort((a, b) => b.totalEventos - a.totalEventos);
  }, [domicilios, tipoGrupoMapping]);

  const grupoColorMap = useMemo(() => {
    const map: Record<string, string> = {};

    categoriasResumen.forEach((grupo, index) => {
      map[grupo.grupoId] = CATEGORY_COLORS[index % CATEGORY_COLORS.length];
    });

    map[FALLBACK_GROUP_ID] = map[FALLBACK_GROUP_ID] || FALLBACK_COLOR;
    return map;
  }, [categoriasResumen]);

  const toggleGrupo = (grupoId: string) => {
    setSelectedGrupos((prev) => {
      const set = new Set(prev);
      if (set.has(grupoId)) {
        set.delete(grupoId);
      } else {
        set.add(grupoId);
      }
      return Array.from(set);
    });
  };

  const normalizedTimelineEvents = useMemo<NormalizedTimelineEvent[]>(() => {
    if (!eventosList.length) return [];

    return eventosList
      .filter(
        (evento) => evento.id_domicilio && evento.fecha_minima_evento !== null
      )
      .map((evento) => {
        const tipoNombre = evento.tipo_eno_nombre || null;
        const grupoInfo =
          (tipoNombre && tipoGrupoMapping[tipoNombre]) || undefined;
        return {
          id: evento.id,
          domicilioId: evento.id_domicilio!,
          fecha: new Date(evento.fecha_minima_evento as string),
          tipoNombre,
          grupoId: grupoInfo?.grupoId || FALLBACK_GROUP_ID,
        };
      })
      .sort((a, b) => a.fecha.getTime() - b.fecha.getTime());
  }, [eventosList, tipoGrupoMapping]);

  const timelineBuckets = useMemo<TimelineBucket[]>(() => {
    if (!normalizedTimelineEvents.length) return [];
    const bucketMap = new Map<string, TimelineBucket>();

    normalizedTimelineEvents.forEach((evento) => {
      const start = startOfBucket(evento.fecha, timelineMode);
      const end = endOfBucket(start, timelineMode);
      const key = `${timelineMode}-${start.toISOString()}`;

      if (!bucketMap.has(key)) {
        bucketMap.set(key, {
          key,
          start,
          end,
          label: buildBucketLabel(start, end, timelineMode),
          events: [],
        });
      }

      bucketMap.get(key)!.events.push(evento);
    });

    return Array.from(bucketMap.values()).sort(
      (a, b) => a.start.getTime() - b.start.getTime()
    );
  }, [normalizedTimelineEvents, timelineMode]);

  useEffect(() => {
    setTimelineIndex(0);
  }, [timelineMode, timelineBuckets.length]);

  const selectedGruposSet = useMemo(
    () => new Set(selectedGrupos),
    [selectedGrupos]
  );

  const timelineEnabled =
    selectedGrupos.length > 0 &&
    timelineBuckets.length > 0 &&
    !eventosLoading &&
    !eventosError;

  useEffect(() => {
    if (!timelineEnabled) {
      setTimelinePlaying(false);
    }
  }, [timelineEnabled]);

  useEffect(() => {
    if (!timelinePlaying || !timelineEnabled || !timelineBuckets.length) {
      return;
    }

    const speedFactor = timelineSpeed <= 0 ? 1 : timelineSpeed;
    const interval = Math.max(200, TIMELINE_INTERVAL_MS / speedFactor);

    const id = window.setInterval(() => {
      setTimelineIndex((prev) => {
        if (prev >= timelineBuckets.length - 1) {
          return 0;
        }
        return prev + 1;
      });
    }, interval);

    return () => window.clearInterval(id);
  }, [
    timelinePlaying,
    timelineEnabled,
    timelineBuckets.length,
    timelineSpeed,
  ]);

  const timelineActiveEvents = useMemo(() => {
    if (!timelineEnabled || !timelineBuckets.length) return [];
    const cappedIndex = Math.min(timelineIndex, timelineBuckets.length - 1);
    const bucketsToInclude = timelineBuckets.slice(0, cappedIndex + 1);

    return bucketsToInclude
      .flatMap((bucket) => bucket.events)
      .filter((event) => selectedGruposSet.has(event.grupoId));
  }, [
    timelineEnabled,
    timelineBuckets,
    timelineIndex,
    selectedGruposSet,
  ]);

  const domicilioById = useMemo(() => {
    const map = new Map<number, DomicilioMapaItem>();
    domicilios.forEach((domicilio) => {
      map.set(domicilio.id_domicilio, domicilio);
    });
    return map;
  }, [domicilios]);

  const timelineDomicilios = useMemo(() => {
    if (!timelineEnabled) return null;

    const map = new Map<
      number,
      { total: number; tipos: Record<string, number> }
    >();

    timelineActiveEvents.forEach((event) => {
      const current = map.get(event.domicilioId) || {
        total: 0,
        tipos: {},
      };
      current.total += 1;
      const tipoKey = event.tipoNombre || "Sin clasificar";
      current.tipos[tipoKey] = (current.tipos[tipoKey] || 0) + 1;
      map.set(event.domicilioId, current);
    });

    const list: DomicilioMapaItem[] = [];
    map.forEach((value, domicilioId) => {
      const base = domicilioById.get(domicilioId);
      if (!base) return;
      const tiposEntries = Object.entries(value.tipos);
      const tipoPredominante =
        tiposEntries.sort((a, b) => b[1] - a[1])[0]?.[0] ||
        base.tipo_evento_predominante;

      list.push({
        ...base,
        total_eventos: value.total,
        tipos_eventos: value.tipos,
        tipo_evento_predominante: tipoPredominante,
      });
    });

    return list;
  }, [timelineEnabled, timelineActiveEvents, domicilioById]);

  const baseFilteredDomicilios = useMemo(() => {
    if (selectedGrupos.length === 0) return domicilios;
    const selectedSet = new Set(selectedGrupos);

    return domicilios.filter((domicilio) => {
      const tiposKeys = Object.keys(domicilio.tipos_eventos || {});
      if (tiposKeys.length === 0) {
        const fallbackGrupo =
          (domicilio.tipo_evento_predominante &&
            tipoGrupoMapping[domicilio.tipo_evento_predominante]?.grupoId) ||
          FALLBACK_GROUP_ID;
        return selectedSet.has(fallbackGrupo);
      }

      return tiposKeys.some((tipo) => {
        const grupoId =
          tipoGrupoMapping[tipo]?.grupoId || FALLBACK_GROUP_ID;
        return selectedSet.has(grupoId);
      });
    });
  }, [domicilios, selectedGrupos, tipoGrupoMapping]);

  const finalDomicilios =
    timelineEnabled && timelineDomicilios !== null
      ? timelineDomicilios
      : baseFilteredDomicilios;

  const totalEventos = finalDomicilios.reduce(
    (sum: number, dom) => sum + dom.total_eventos,
    0
  );
  const totalDomicilios = finalDomicilios.length;
  const provinciasUnicas = new Set(
    finalDomicilios.map((dom) => dom.id_provincia_indec)
  ).size;

  const timelineRangeLabel =
    timelineBuckets.length > 0
      ? `${format(timelineBuckets[0].start, "d MMM yyyy", {
          locale: es,
        })} — ${format(
          timelineBuckets[timelineBuckets.length - 1].end,
          "d MMM yyyy",
          { locale: es }
        )}`
      : undefined;

  const timelineDisabledMessage = eventosLoading
    ? "Descargando eventos para la animación..."
    : eventosError
      ? eventosError
      : selectedGrupos.length === 0
        ? "Seleccioná al menos un grupo para habilitar la animación."
        : "No hay eventos con domicilio para la categoría elegida.";

  const timelineSidebarProps = {
    available: timelineBuckets.length > 0,
    enabled: timelineEnabled,
    loading: eventosLoading,
    playing: timelinePlaying,
    currentStep: Math.min(timelineIndex, Math.max(timelineBuckets.length - 1, 0)),
    totalSteps: timelineBuckets.length,
    currentLabel:
      timelineBuckets.length > 0
        ? timelineBuckets[
            Math.min(timelineIndex, timelineBuckets.length - 1)
          ]?.label
        : undefined,
    rangeLabel: timelineRangeLabel,
    mode: timelineMode,
    onModeChange: (mode: TimelineMode) => setTimelineMode(mode),
    onTogglePlay: () => {
      if (!timelineEnabled) return;
      setTimelinePlaying((prev) => !prev);
    },
    onStepChange: (value: number) => {
      setTimelineIndex(value);
      setTimelinePlaying(false);
    },
    onReset: () => {
      setTimelineIndex(0);
      setTimelinePlaying(false);
    },
    disabledMessage: timelineDisabledMessage,
    speed: timelineSpeed,
    onSpeedChange: (value: number) => setTimelineSpeed(value),
    speedOptions: TIMELINE_SPEED_OPTIONS,
  };

  const handleMarkerClick = (domicilio: DomicilioMapaItem) => {
    setSelectedDomicilioId(domicilio.id_domicilio);
    setDialogOpen(true);
  };

  const handleEstablecimientoClick = (
    establecimiento: EstablecimientoMapaItem
  ) => {
    setSelectedEstablecimientoId(establecimiento.id);
    setEstablecimientoDialogOpen(true);
  };

  return (
    <MapaLayout
      sidebar={
        <MapaSidebar
          totalEventosGlobal={totalEventos}
          totalEventosMapeados={totalEventos}
          poblacionTotal={0}
          provinciasAfectadas={provinciasUnicas}
          tasaIncidencia={0}
          categorias={categoriasResumen}
          grupoColorMap={grupoColorMap}
          categoriasLoading={tiposLoading}
          selectedGrupos={selectedGrupos}
          onToggleGrupo={toggleGrupo}
          onClearFiltros={() => setSelectedGrupos([])}
          timeline={timelineSidebarProps}
        />
      }
    >
      <div className="relative h-full">
        {isLoading && (
          <div className="absolute left-1/2 top-4 z-[999] -translate-x-1/2 rounded-lg border bg-white px-4 py-3 shadow-lg">
            <div className="flex items-center gap-3">
              <div className="h-5 w-5 animate-spin rounded-full border-b-2 border-blue-600"></div>
              <span className="text-sm font-medium text-gray-700">
                Cargando domicilios...
              </span>
            </div>
          </div>
        )}

        {!isLoading && (
          <div className="absolute left-4 top-4 z-[999] rounded-lg border bg-white p-4 shadow-lg">
            <div className="space-y-1 text-sm">
              <div>
                <span className="text-gray-600">Domicilios: </span>
                <span className="font-semibold">{totalDomicilios}</span>
              </div>
              <div>
                <span className="text-gray-600">Total eventos: </span>
                <span className="font-semibold">{totalEventos}</span>
              </div>
              <div>
                <span className="text-gray-600">Provincias: </span>
                <span className="font-semibold">{provinciasUnicas}</span>
              </div>
            </div>
          </div>
        )}

        <MapaSimple
          domicilios={finalDomicilios}
          isLoading={isLoading}
          onMarkerClick={handleMarkerClick}
          onEstablecimientoClick={handleEstablecimientoClick}
          grupoColorMap={grupoColorMap}
          tipoGrupoMapping={tipoGrupoMapping}
          fallbackGrupoId={FALLBACK_GROUP_ID}
        />

        <DomicilioDetalleDialog
          open={dialogOpen}
          onOpenChange={setDialogOpen}
          idDomicilio={selectedDomicilioId}
        />

        <EstablecimientoDetalleDialog
          open={establecimientoDialogOpen}
          onOpenChange={setEstablecimientoDialogOpen}
          idEstablecimiento={selectedEstablecimientoId}
        />
      </div>
    </MapaLayout>
  );
}
