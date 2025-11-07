"use client";

import { MapContainer, TileLayer, CircleMarker, Tooltip } from "react-leaflet";
import { useDomiciliosMapa, type DomicilioMapaItem } from "@/lib/api/mapa";
import "leaflet/dist/leaflet.css";
import "./mapa-styles.css";
import L from "leaflet";

// Fix Leaflet default icon issue with Next.js
// eslint-disable-next-line @typescript-eslint/no-explicit-any
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png",
  iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
});

interface MapaSimpleProps {
  onMarkerClick?: (domicilio: DomicilioMapaItem) => void;
  domicilios?: DomicilioMapaItem[]; // Eventos filtrados desde el parent
  isLoading?: boolean;
}

// Pool de 20 colores visualmente distintos para categorías epidemiológicas
const COLOR_POOL = [
  "#ef4444", // rojo brillante - Respiratorias agudas
  "#10b981", // verde esmeralda - Vectoriales
  "#f59e0b", // amarillo/naranja - Transmisión alimentaria
  "#8b5cf6", // violeta - Transmisión sexual
  "#14b8a6", // teal - Zoonóticas
  "#ec4899", // rosa - Vacunables
  "#64748b", // gris azulado - Tuberculosis
  "#06b6d4", // cyan - Pediátricas/Congénitas
  "#f97316", // naranja - Intoxicaciones
  "#a855f7", // púrpura - Otras infecciones
  "#84cc16", // lima - Chagas y vectoriales secundarias
  "#fb923c", // naranja claro - Hepatitis
  "#22d3ee", // cyan claro - Eventos especiales
  "#fdba74", // melocotón - Brotes y clusters
  "#d946ef", // fucsia - Salud mental
  "#6366f1", // índigo - VIH
  "#22c55e", // verde claro - Hantavirus
  "#fbbf24", // amarillo dorado - Araneísmo/Ofidismo
  "#f43f5e", // rosa rojo - Rabia
  "#9ca3af", // gris - Sin clasificar
];

// Categorización inteligente por palabras clave
const categorizarEvento = (nombreEvento: string | null | undefined): number => {
  if (!nombreEvento) return 19; // Sin clasificar

  const nombre = nombreEvento.toLowerCase();

  // Respiratorias agudas (0)
  if (nombre.includes("covid") || nombre.includes("influenza") || nombre.includes("irag") ||
      nombre.includes("respiratoria") || nombre.includes("meningoencefalitis")) {
    return 0;
  }

  // Vectoriales principales (1)
  if (nombre.includes("dengue") || nombre.includes("zika") || nombre.includes("chikungunya") ||
      nombre.includes("paludismo") || nombre.includes("malaria")) {
    return 1;
  }

  // Transmisión alimentaria/fecal-oral (2)
  if (nombre.includes("diarrea") || nombre.includes("eta") || nombre.includes("brote") ||
      nombre.includes("suh") || nombre.includes("triquinelosis") || nombre.includes("fecal")) {
    return 2;
  }

  // Transmisión sexual (3)
  if (nombre.includes("vih") || nombre.includes("sífilis") || nombre.includes("gonorrea") ||
      (nombre.includes("hepatitis") && (nombre.includes("b") || nombre.includes("c")))) {
    return 3;
  }

  // Zoonóticas (4)
  if (nombre.includes("rabia") || nombre.includes("leptospirosis") || nombre.includes("hidatidosis") ||
      nombre.includes("brucelosis") || nombre.includes("araneísmo") || nombre.includes("ofidismo") ||
      nombre.includes("latrodectus") || nombre.includes("loxosceles")) {
    return 4;
  }

  // Vacunables (5)
  if (nombre.includes("coqueluche") || nombre.includes("parotiditis") || nombre.includes("sarampión") ||
      nombre.includes("rubéola") || nombre.includes("poliomielitis") || nombre.includes("varicela") ||
      nombre.includes("exantemática") || nombre.includes("paf")) {
    return 5;
  }

  // Tuberculosis (6)
  if (nombre.includes("tuberculosis")) {
    return 6;
  }

  // Pediátricas/Congénitas (7)
  if (nombre.includes("congénito") || nombre.includes("lactante") || nombre.includes("hipotiroidismo") ||
      nombre.includes("fibrosis") || nombre.includes("biotinidasa") || nombre.includes("expuesto perinatal") ||
      nombre.includes("rn expuesto")) {
    return 7;
  }

  // Intoxicaciones (8)
  if (nombre.includes("intoxicación") || nombre.includes("intento de suicidio") ||
      nombre.includes("monóxido") || nombre.includes("medicamentosa") || nombre.includes("tóxicos")) {
    return 8;
  }

  // Otras infecciones (9)
  if (nombre.includes("candidemia") || nombre.includes("candidiasis") || nombre.includes("bartonelosis") ||
      nombre.includes("tifoidea") || nombre.includes("paratifoidea") || nombre.includes("invasivas")) {
    return 9;
  }

  // Chagas y vectoriales secundarias (10)
  if (nombre.includes("chagas") || nombre.includes("hantavirus")) {
    return 10;
  }

  // Hepatitis (11)
  if (nombre.includes("hepatitis")) {
    return 11;
  }

  // Eventos especiales (12)
  if (nombre.includes("emergente") || nombre.includes("genómica") || nombre.includes("vigilancia") ||
      nombre.includes("centinela") || nombre.includes("seguimiento") || nombre.includes("especiales")) {
    return 12;
  }

  // Brotes (13)
  if (nombre.includes("brote")) {
    return 13;
  }

  // Salud mental (14)
  if (nombre.includes("suicidio")) {
    return 14;
  }

  // VIH específico (15)
  if (nombre.includes("vih")) {
    return 15;
  }

  // Hantavirus (16)
  if (nombre.includes("hantavirus")) {
    return 16;
  }

  // Araneísmo/Ofidismo (17)
  if (nombre.includes("araneísmo") || nombre.includes("ofidismo")) {
    return 17;
  }

  // Rabia (18)
  if (nombre.includes("rabia") || nombre.includes("rábico")) {
    return 18;
  }

  // Default: Sin clasificar (19)
  return 19;
};

// Obtener color según tipo de evento predominante
const getColorPorTipoEvento = (tipoEventoPredominante?: string | null): string => {
  const categoria = categorizarEvento(tipoEventoPredominante);
  return COLOR_POOL[categoria];
};

export function MapaSimple({
  onMarkerClick,
  domicilios: domiciliosProp,
  isLoading: isLoadingProp,
}: MapaSimpleProps) {
  // Usar datos del prop si están disponibles, si no, hacer query independiente
  const { data: dataFallback, isLoading: isLoadingFallback, error: errorFallback } = useDomiciliosMapa({
    limit: 50000, // Cargar todos los domicilios geocodificados
  });

  const domicilios = domiciliosProp || dataFallback?.data?.items || [];
  const loading = isLoadingProp !== undefined ? isLoadingProp : isLoadingFallback;
  const error = domiciliosProp ? undefined : errorFallback;

  // Todos los domicilios retornados ya tienen coordenadas válidas (filtrado en backend)
  const domiciliosConCoordenadas = domicilios;

  return (
    <div className="relative w-full h-full">
      {error && (
        <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-[1000] text-red-500 text-center py-3 px-6 bg-red-50 rounded-lg border border-red-200 shadow-lg">
          <strong>Error:</strong> No se pudieron cargar los domicilios del mapa
        </div>
      )}

      {loading && (
        <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-[1000] bg-white shadow-lg rounded-lg px-4 py-3 flex items-center gap-3 border">
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
          <span className="text-sm font-medium">Cargando domicilios...</span>
        </div>
      )}

      {!loading && domiciliosConCoordenadas.length === 0 && (
        <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-[1000] bg-yellow-50 shadow-lg rounded-lg px-4 py-3 flex items-center gap-3 border border-yellow-200">
          <span className="text-sm font-medium text-yellow-800">
            No hay domicilios geocodificados para mostrar
          </span>
        </div>
      )}

      <MapContainer
        center={[-38.416097, -63.616671]} // Centro de Argentina
        zoom={6}
        minZoom={4}
        maxZoom={18}
        style={{ height: "100%", width: "100%" }}
        scrollWheelZoom={true}
        preferCanvas={true}
        zoomAnimation={true}
        markerZoomAnimation={true}
      >
        {/* Usar CartoDB Positron que tiene colores más suaves */}
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
          subdomains="abcd"
        />

        {/* Mostrar puntos de domicilios geocodificados */}
        {domiciliosConCoordenadas.map((domicilio: DomicilioMapaItem) => {
          const color = getColorPorTipoEvento(domicilio.tipo_evento_predominante);
          const lat = domicilio.latitud!;
          const lng = domicilio.longitud!;

          // Tamaño según cantidad de eventos
          const radius = Math.min(4 + (domicilio.total_eventos * 0.5), 12);

          return (
            <CircleMarker
              key={domicilio.id}
              center={[lat, lng]}
              radius={radius}
              pathOptions={{
                fillColor: color,
                color: "#fff",
                weight: 1.5,
                opacity: 1,
                fillOpacity: 0.75,
              }}
              eventHandlers={{
                click: () => {
                  if (onMarkerClick) {
                    onMarkerClick(domicilio);
                  }
                },
                mouseover: (e) => {
                  const layer = e.target;
                  layer.setStyle({
                    radius: 8,
                    weight: 2,
                    fillOpacity: 0.9,
                  });
                },
                mouseout: (e) => {
                  const layer = e.target;
                  layer.setStyle({
                    radius: 6,
                    weight: 1,
                    fillOpacity: 0.7,
                  });
                },
              }}
            >
              <Tooltip direction="top" opacity={0.9} permanent={false}>
                <div className="text-sm">
                  <div className="font-semibold">{domicilio.nombre}</div>
                  <div className="text-xs text-gray-600">{domicilio.total_eventos} evento{domicilio.total_eventos !== 1 ? 's' : ''}</div>
                </div>
              </Tooltip>
            </CircleMarker>
          );
        })}
      </MapContainer>

      {/* Leyenda de colores por categoría de evento */}
      {!loading && domiciliosConCoordenadas.length > 0 && (
        <div className="absolute bottom-6 right-6 z-[1000] bg-white shadow-lg rounded-lg p-4 max-h-[500px] overflow-y-auto">
          <div className="font-semibold text-sm mb-3">Categorías de Eventos</div>
          <div className="space-y-1.5 text-xs">
            {(() => {
              // Agrupar eventos por categoría
              const categorias = new Map<number, Set<string>>();
              domiciliosConCoordenadas.forEach((d) => {
                if (d.tipo_evento_predominante) {
                  const cat = categorizarEvento(d.tipo_evento_predominante);
                  if (!categorias.has(cat)) {
                    categorias.set(cat, new Set());
                  }
                  categorias.get(cat)!.add(d.tipo_evento_predominante);
                }
              });

              const nombresCategorias = [
                "Respiratorias",
                "Vectoriales",
                "Alimentarias",
                "Transmisión Sexual",
                "Zoonóticas",
                "Vacunables",
                "Tuberculosis",
                "Congénitas",
                "Intoxicaciones",
                "Otras Infecciones",
                "Chagas/Hantavirus",
                "Hepatitis",
                "Vigilancia",
                "Brotes",
                "Salud Mental",
                "VIH",
                "Hantavirus",
                "Araneísmo/Ofidismo",
                "Rabia",
                "Sin Clasificar",
              ];

              return Array.from(categorias.entries())
                .sort((a, b) => a[0] - b[0])
                .map(([catIndex, eventos]) => (
                  <div key={catIndex} className="mb-2">
                    <div className="flex items-center gap-2 mb-1">
                      <div
                        className="w-3 h-3 rounded-full border border-white shadow-sm flex-shrink-0"
                        style={{ backgroundColor: COLOR_POOL[catIndex] }}
                      />
                      <span className="text-gray-900 font-medium">
                        {nombresCategorias[catIndex]}
                      </span>
                      <span className="text-gray-500">({eventos.size})</span>
                    </div>
                    <div className="ml-5 text-gray-600 space-y-0.5">
                      {Array.from(eventos)
                        .sort()
                        .slice(0, 3)
                        .map((evento) => (
                          <div key={evento} className="truncate text-[10px]">
                            • {evento}
                          </div>
                        ))}
                      {eventos.size > 3 && (
                        <div className="text-[10px] text-gray-400">
                          +{eventos.size - 3} más...
                        </div>
                      )}
                    </div>
                  </div>
                ));
            })()}
          </div>
        </div>
      )}
    </div>
  );
}
