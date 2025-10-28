"use client";

import { useMemo } from "react";
import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
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
  onFeatureClick?: (feature: DomicilioMapaItem) => void;
  domicilios?: DomicilioMapaItem[]; // Domicilios filtrados desde el parent
  isLoading?: boolean;
}

// Colores por provincia (paleta distintiva)
const COLORES_PROVINCIA: Record<number, string> = {
  2: "#ef4444",   // Ciudad de Buenos Aires - rojo
  6: "#3b82f6",   // Buenos Aires - azul
  10: "#10b981",  // Catamarca - verde
  14: "#f59e0b",  // Córdoba - naranja
  18: "#8b5cf6",  // Corrientes - violeta
  22: "#ec4899",  // Chaco - rosa
  26: "#06b6d4",  // Chubut - cyan
  30: "#84cc16",  // Entre Ríos - lima
  34: "#f97316",  // Formosa - naranja oscuro
  38: "#14b8a6",  // Jujuy - teal
  42: "#a855f7",  // La Pampa - púrpura
  46: "#0ea5e9",  // La Rioja - celeste
  50: "#f43f5e",  // Mendoza - rojo rosado
  54: "#22c55e",  // Misiones - verde claro
  58: "#eab308",  // Neuquén - amarillo
  62: "#6366f1",  // Río Negro - índigo
  66: "#64748b",  // Salta - gris azulado
  70: "#d946ef",  // San Juan - fucsia
  74: "#10b981",  // San Luis - esmeralda
  78: "#059669",  // Santa Cruz - verde azulado
  82: "#0891b2",  // Santa Fe - azul verdoso
  86: "#7c3aed",  // Santiago del Estero - violeta oscuro
  90: "#fb923c",  // Tucumán - naranja medio
  94: "#dc2626",  // Tierra del Fuego - rojo oscuro
};

// Color por defecto para provincias sin mapeo
const COLOR_DEFAULT = "#9ca3af"; // gris

export function MapaSimple({
  onFeatureClick,
  domicilios: domiciliosProp,
  isLoading: isLoadingProp,
}: MapaSimpleProps) {
  // Usar datos del prop si están disponibles, si no, hacer query independiente
  const { data: dataFallback, isLoading: isLoadingFallback, error: errorFallback } = useDomiciliosMapa({
    limit: 1000, // Máximo de puntos a mostrar
  });

  const domicilios = domiciliosProp || dataFallback?.data?.items || [];
  const loading = isLoadingProp !== undefined ? isLoadingProp : isLoadingFallback;
  const error = domiciliosProp ? undefined : errorFallback;

  // Todos los domicilios retornados ya tienen coordenadas válidas (filtrado en backend)
  const domiciliosConCoordenadas = domicilios;

  // Obtener color según provincia
  const getColorPorProvincia = (idProvinciaIndec?: number | null): string => {
    if (!idProvinciaIndec) return COLOR_DEFAULT;
    return COLORES_PROVINCIA[idProvinciaIndec] || COLOR_DEFAULT;
  };

  return (
    <div className="relative w-full h-full">
      {error && (
        <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-[1000] text-red-500 text-center py-3 px-6 bg-red-50 rounded-lg border border-red-200 shadow-lg">
          <strong>Error:</strong> No se pudieron cargar los eventos del mapa
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
          const color = getColorPorProvincia(domicilio.id_provincia_indec);
          const lat = domicilio.latitud;
          const lng = domicilio.longitud;

          return (
            <CircleMarker
              key={domicilio.id}
              center={[lat, lng]}
              radius={6}
              pathOptions={{
                fillColor: color,
                color: "#fff",
                weight: 1,
                opacity: 1,
                fillOpacity: 0.7,
              }}
              eventHandlers={{
                click: () => {
                  if (onFeatureClick) {
                    onFeatureClick(domicilio);
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
              <Popup>
                <div className="p-2 min-w-[200px]">
                  <div className="font-semibold text-sm mb-1">{domicilio.nombre}</div>
                  <div className="text-xs text-gray-600 mb-2">
                    {domicilio.provincia_nombre}
                    {domicilio.departamento_nombre && ` - ${domicilio.departamento_nombre}`}
                  </div>
                  <div className="text-sm">
                    <span className="text-gray-600">Eventos: </span>
                    <span className="font-semibold">{domicilio.total_eventos}</span>
                  </div>
                  <div className="text-xs text-gray-500 mt-2">
                    📍 {lat.toFixed(6)}, {lng.toFixed(6)}
                  </div>
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>

      {/* Leyenda de colores por provincia */}
      {!loading && domiciliosConCoordenadas.length > 0 && (
        <div className="absolute bottom-6 right-6 z-[1000] bg-white shadow-lg rounded-lg p-4 max-h-[400px] overflow-y-auto">
          <div className="font-semibold text-sm mb-3">Provincias</div>
          <div className="space-y-1 text-xs">
            {Array.from(new Set(domiciliosConCoordenadas.map(d => d.id_provincia_indec))).map(
              (idProvincia) => {
                const domicilio = domiciliosConCoordenadas.find(d => d.id_provincia_indec === idProvincia);
                const color = getColorPorProvincia(idProvincia);
                return (
                  <div key={idProvincia} className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full border border-white"
                      style={{ backgroundColor: color }}
                    />
                    <span className="text-gray-700">{domicilio?.provincia_nombre || `Provincia ${idProvincia}`}</span>
                  </div>
                );
              }
            )}
          </div>
        </div>
      )}
    </div>
  );
}
