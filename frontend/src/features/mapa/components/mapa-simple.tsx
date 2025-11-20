"use client";

import { useState } from "react";
import { MapContainer, TileLayer, CircleMarker, Tooltip } from "react-leaflet";
import { useDomiciliosMapa, type DomicilioMapaItem } from "@/features/mapa/api";
import { useEstablecimientosMapa, type EstablecimientoMapaItem } from "@/features/establecimientos/api";
import "leaflet/dist/leaflet.css";
import "leaflet.markercluster/dist/MarkerCluster.css";
import "leaflet.markercluster/dist/MarkerCluster.Default.css";
import "./mapa-styles.css";
import L from "leaflet";
import { MarkerClusterGroup } from "./marker-cluster-group";

// Fix Leaflet default icon issue with Next.js
// eslint-disable-next-line @typescript-eslint/no-explicit-any
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png",
  iconUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png",
  shadowUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
});

// OPTIMIZACIÓN: Ícono creado una sola vez fuera del componente (singleton)
const HOSPITAL_ICON = new L.Icon({
  iconUrl: "data:image/svg+xml;base64," + btoa(`
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#dc2626" width="32" height="32">
      <path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5zm0 18c-4.52 0-8-3.48-8-8V8.3l8-4.44 8 4.44V12c0 4.52-3.48 8-8 8zm1-13h-2v3H8v2h3v3h2v-3h3v-2h-3V7z"/>
    </svg>
  `),
  iconSize: [32, 32],
  iconAnchor: [16, 32],
  popupAnchor: [0, -32],
  tooltipAnchor: [16, -16],
});

interface MapaSimpleProps {
  onMarkerClick?: (domicilio: DomicilioMapaItem) => void;
  onEstablecimientoClick?: (establecimiento: EstablecimientoMapaItem) => void;
  domicilios?: DomicilioMapaItem[]; // Eventos filtrados desde el parent
  isLoading?: boolean;
  grupoColorMap: Record<string, string>;
  tipoGrupoMapping: Record<string, { grupoId: string; grupoNombre: string }>;
  fallbackGrupoId?: string;
}

export function MapaSimple({
  onMarkerClick,
  onEstablecimientoClick,
  domicilios: domiciliosProp,
  isLoading: isLoadingProp,
  grupoColorMap,
  tipoGrupoMapping,
  fallbackGrupoId,
}: MapaSimpleProps) {
  // Estado para mostrar/ocultar establecimientos
  const [mostrarEstablecimientos, setMostrarEstablecimientos] = useState(false);

  // Usar datos del prop si están disponibles, si no, hacer query independiente
  const {
    data: dataFallback,
    isLoading: isLoadingFallback,
    error: errorFallback,
  } = useDomiciliosMapa({
    limit: 50000, // Cargar todos los domicilios geocodificados
  });

  // OPTIMIZACIÓN: Solo cargar establecimientos cuando el toggle está activado
  const {
    data: establecimientosData,
    isLoading: isLoadingEstablecimientos,
  } = useEstablecimientosMapa(
    {
      limit: 10000,
    },
    {
      enabled: mostrarEstablecimientos, // Solo hacer query cuando sea necesario
    }
  );

  const domicilios = domiciliosProp || dataFallback?.data?.items || [];
  const establecimientos = establecimientosData?.data?.items || [];
  const loading =
    isLoadingProp !== undefined ? isLoadingProp : isLoadingFallback;
  const error = domiciliosProp ? undefined : errorFallback;

  const fallbackGrupo = fallbackGrupoId || "sin-categoria";
  const fallbackColor = grupoColorMap[fallbackGrupo] || "#94a3b8";

  const getColorForDomicilio = (domicilio: DomicilioMapaItem): string => {
    const tipo = domicilio.tipo_evento_predominante;
    const grupoId = tipo ? tipoGrupoMapping[tipo]?.grupoId : undefined;
    const resolvedGrupoId = grupoId || fallbackGrupo;
    return grupoColorMap[resolvedGrupoId] || fallbackColor;
  };

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
          const color = getColorForDomicilio(domicilio);
          const lat = domicilio.latitud!;
          const lng = domicilio.longitud!;

          // Tamaño según cantidad de eventos
          const radius = Math.min(4 + domicilio.total_eventos * 0.5, 12);

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
                  <div className="text-xs text-gray-600">
                    {domicilio.total_eventos} evento
                    {domicilio.total_eventos !== 1 ? "s" : ""}
                  </div>
                </div>
              </Tooltip>
            </CircleMarker>
          );
        })}

        {/* OPTIMIZACIÓN: Usar clustering para establecimientos */}
        {mostrarEstablecimientos && establecimientos.length > 0 && (
          <MarkerClusterGroup
            establecimientos={establecimientos}
            onEstablecimientoClick={onEstablecimientoClick}
            icon={HOSPITAL_ICON}
          />
        )}
      </MapContainer>

      {/* Toggle para mostrar/ocultar establecimientos */}
      <div className="absolute top-4 right-4 z-[1000]">
        <button
          onClick={() => setMostrarEstablecimientos(!mostrarEstablecimientos)}
          className={`px-4 py-2 rounded-lg shadow-lg font-medium text-sm transition-colors flex items-center gap-2 ${
            mostrarEstablecimientos
              ? "bg-red-600 text-white hover:bg-red-700"
              : "bg-white text-gray-700 border border-gray-300 hover:bg-gray-50"
          }`}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="currentColor"
            className="w-5 h-5"
          >
            <path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5zm0 18c-4.52 0-8-3.48-8-8V8.3l8-4.44 8 4.44V12c0 4.52-3.48 8-8 8zm1-13h-2v3H8v2h3v3h2v-3h3v-2h-3V7z" />
          </svg>
          {mostrarEstablecimientos ? "Ocultar" : "Mostrar"} Establecimientos
          {mostrarEstablecimientos && ` (${establecimientos.length})`}
          {isLoadingEstablecimientos && mostrarEstablecimientos && (
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
          )}
        </button>
      </div>

    </div>
  );
}
