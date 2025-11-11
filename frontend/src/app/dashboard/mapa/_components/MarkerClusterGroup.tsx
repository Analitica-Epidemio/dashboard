"use client";

import { useEffect, memo } from "react";
import { useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet.markercluster";
import type { EstablecimientoMapaItem } from "@/lib/api/establecimientos";

interface MarkerClusterGroupProps {
  establecimientos: EstablecimientoMapaItem[];
  onEstablecimientoClick?: (establecimiento: EstablecimientoMapaItem) => void;
  icon: L.Icon;
}

// OPTIMIZACIÓN: Componente memoizado para evitar re-renders innecesarios
export const MarkerClusterGroup = memo(function MarkerClusterGroup({
  establecimientos,
  onEstablecimientoClick,
  icon,
}: MarkerClusterGroupProps) {
  const map = useMap();

  useEffect(() => {
    // OPTIMIZACIÓN: Configuración de clustering optimizada
    const markerClusterGroup = L.markerClusterGroup({
      // Agrupar hasta zoom 15 para mejor rendimiento
      disableClusteringAtZoom: 15,
      // Limitar los íconos por cluster para mejor UX
      maxClusterRadius: 80,
      // Animaciones más rápidas
      spiderfyOnMaxZoom: true,
      showCoverageOnHover: true,
      zoomToBoundsOnClick: true,
      // CRÍTICO: Usar canvas para mejor rendimiento con muchos markers
      chunkedLoading: true,
      chunkInterval: 200,
      chunkDelay: 50,
      // Personalizar el ícono del cluster
      iconCreateFunction: (cluster) => {
        const count = cluster.getChildCount();
        let sizeClass = "marker-cluster-small";

        if (count > 100) {
          sizeClass = "marker-cluster-large";
        } else if (count > 10) {
          sizeClass = "marker-cluster-medium";
        }

        return L.divIcon({
          html: `<div><span>${count}</span></div>`,
          className: `marker-cluster ${sizeClass}`,
          iconSize: L.point(40, 40),
        });
      },
    });

    // OPTIMIZACIÓN: Crear markers en lotes para no bloquear el UI
    const markers: L.Marker[] = [];

    establecimientos.forEach((establecimiento) => {
      const marker = L.marker([establecimiento.latitud, establecimiento.longitud], {
        icon,
        // CRÍTICO: Usar riseOnHover para mejor UX sin afectar performance
        riseOnHover: true,
      });

      // Crear tooltip con información básica
      const tooltipContent = `
        <div class="text-sm">
          <div class="font-semibold">${establecimiento.nombre}</div>
          ${establecimiento.localidad_nombre ? `<div class="text-xs text-gray-600">${establecimiento.localidad_nombre}</div>` : ''}
          <div class="text-xs text-blue-600 mt-1 cursor-pointer">Click para ver detalles</div>
        </div>
      `;

      marker.bindTooltip(tooltipContent, {
        direction: "top",
        opacity: 0.9,
        permanent: false,
      });

      // Crear popup con información completa
      const popupContent = `
        <div class="p-2 min-w-[200px]">
          <div class="font-semibold text-sm mb-1">${establecimiento.nombre}</div>
          ${establecimiento.codigo_refes ? `<div class="text-xs text-gray-500 mb-2">Código: ${establecimiento.codigo_refes}</div>` : ''}
          ${establecimiento.localidad_nombre ? `
            <div class="text-xs text-gray-600 mb-1">
              ${establecimiento.localidad_nombre}${establecimiento.departamento_nombre ? `, ${establecimiento.departamento_nombre}` : ''}
            </div>
          ` : ''}
          ${establecimiento.provincia_nombre ? `<div class="text-xs text-gray-600 mb-2">${establecimiento.provincia_nombre}</div>` : ''}
          <div class="text-xs text-gray-500 mt-2">📍 ${establecimiento.latitud.toFixed(6)}, ${establecimiento.longitud.toFixed(6)}</div>
        </div>
      `;

      marker.bindPopup(popupContent);

      // Event handler para click
      marker.on("click", () => {
        if (onEstablecimientoClick) {
          onEstablecimientoClick(establecimiento);
        }
      });

      markers.push(marker);
    });

    // OPTIMIZACIÓN: Añadir todos los markers de una vez
    markerClusterGroup.addLayers(markers);
    map.addLayer(markerClusterGroup);

    // Cleanup al desmontar
    return () => {
      map.removeLayer(markerClusterGroup);
    };
  }, [establecimientos, map, onEstablecimientoClick, icon]);

  return null;
});
