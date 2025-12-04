"use client";

import { Circle, Tooltip, useMap } from "react-leaflet";
import { useEffect } from "react";
import type { DengueCluster } from "../utils/dengue-cluster";
import { DENGUE_CLUSTER_CONFIG } from "../utils/dengue-cluster";
import { format } from "date-fns";
import { es } from "date-fns/locale";

interface DengueClusterLayerProps {
  clusters: DengueCluster[];
  onClusterClick?: (cluster: DengueCluster) => void;
  selectedClusterId?: string | null;
}

// Colores para clusters
const CLUSTER_COLORS = {
  active: {
    fill: "#ef4444", // red-500
    stroke: "#dc2626", // red-600
  },
  inactive: {
    fill: "#f97316", // orange-500
    stroke: "#ea580c", // orange-600
  },
  selected: {
    fill: "#3b82f6", // blue-500
    stroke: "#2563eb", // blue-600
  },
};

export function DengueClusterLayer({
  clusters,
  onClusterClick,
  selectedClusterId,
}: DengueClusterLayerProps) {
  const map = useMap();

  // Auto-fit bounds cuando hay clusters
  useEffect(() => {
    if (clusters.length > 0 && map) {
      const bounds = clusters.map((c) => [c.centerLat, c.centerLng] as [number, number]);
      if (bounds.length > 0) {
        // No hacer auto-fit, puede ser molesto
        // map.fitBounds(bounds, { padding: [50, 50] });
      }
    }
  }, [clusters, map]);

  if (clusters.length === 0) return null;

  return (
    <>
      {clusters.map((cluster) => {
        const isSelected = cluster.id === selectedClusterId;
        const colors = isSelected
          ? CLUSTER_COLORS.selected
          : cluster.isActive
          ? CLUSTER_COLORS.active
          : CLUSTER_COLORS.inactive;

        // Convertir metros a grados aproximados para Leaflet
        // 1 grado de latitud ≈ 111,320 metros
        const radiusInDegrees = cluster.radiusMeters / 111320;

        return (
          <Circle
            key={cluster.id}
            center={[cluster.centerLat, cluster.centerLng]}
            radius={cluster.radiusMeters}
            pathOptions={{
              fillColor: colors.fill,
              fillOpacity: isSelected ? 0.35 : 0.2,
              color: colors.stroke,
              weight: isSelected ? 3 : 2,
              dashArray: cluster.isActive ? undefined : "5, 5",
            }}
            eventHandlers={{
              click: () => onClusterClick?.(cluster),
            }}
          >
            <Tooltip direction="top" sticky>
              <div className="text-sm min-w-[180px]">
                <div className="font-bold text-base mb-1 flex items-center gap-2">
                  {cluster.isActive ? (
                    <span className="inline-block w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                  ) : (
                    <span className="inline-block w-2 h-2 rounded-full bg-orange-500" />
                  )}
                  Cluster de Dengue
                </div>
                <div className="space-y-0.5 text-gray-700">
                  <div>
                    <span className="font-medium">{cluster.totalCases}</span> casos
                  </div>
                  <div>
                    <span className="font-medium">{cluster.uniqueDomicilios}</span> domicilios
                  </div>
                  <div className="text-xs text-gray-500">
                    {format(cluster.dateRange.start, "d MMM", { locale: es })} -{" "}
                    {format(cluster.dateRange.end, "d MMM yyyy", { locale: es })}
                  </div>
                  <div className="text-xs mt-1">
                    Radio: {Math.round(cluster.radiusMeters)}m
                  </div>
                </div>
                {cluster.isActive && (
                  <div className="mt-1 text-xs font-medium text-red-600">
                    ⚠️ Cluster activo (casos recientes)
                  </div>
                )}
              </div>
            </Tooltip>
          </Circle>
        );
      })}

      {/* Indicador de parámetros del clustering */}
      <ClusterLegend clustersCount={clusters.length} />
    </>
  );
}

function ClusterLegend({ clustersCount }: { clustersCount: number }) {
  return (
    <div className="leaflet-bottom leaflet-left" style={{ pointerEvents: "auto" }}>
      <div className="leaflet-control bg-white rounded-lg shadow-lg p-3 m-3 text-xs">
        <div className="font-semibold mb-2 flex items-center gap-2">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="currentColor"
            className="w-4 h-4 text-red-500"
          >
            <path
              fillRule="evenodd"
              d="M11.54 22.351l.07.04.028.016a.76.76 0 00.723 0l.028-.015.071-.041a16.975 16.975 0 001.144-.742 19.58 19.58 0 002.683-2.282c1.944-1.99 3.963-4.98 3.963-8.827a8.25 8.25 0 00-16.5 0c0 3.846 2.02 6.837 3.963 8.827a19.58 19.58 0 002.682 2.282 16.975 16.975 0 001.145.742z"
              clipRule="evenodd"
            />
          </svg>
          Clusters de Dengue
        </div>
        <div className="space-y-1 text-gray-600">
          <div className="flex items-center gap-2">
            <span
              className="inline-block w-3 h-3 rounded-full"
              style={{ backgroundColor: CLUSTER_COLORS.active.fill }}
            />
            Activo (casos &lt;7 días)
          </div>
          <div className="flex items-center gap-2">
            <span
              className="inline-block w-3 h-3 rounded-full border border-dashed"
              style={{
                backgroundColor: CLUSTER_COLORS.inactive.fill,
                borderColor: CLUSTER_COLORS.inactive.stroke,
              }}
            />
            Histórico
          </div>
        </div>
        <div className="mt-2 pt-2 border-t border-gray-200 text-gray-500">
          <div>Radio: {DENGUE_CLUSTER_CONFIG.RADIUS_METERS}m</div>
          <div>Ventana: {DENGUE_CLUSTER_CONFIG.WINDOW_DAYS} días</div>
          <div className="mt-1 font-medium text-gray-700">
            {clustersCount} cluster{clustersCount !== 1 ? "s" : ""} detectado
            {clustersCount !== 1 ? "s" : ""}
          </div>
        </div>
      </div>
    </div>
  );
}
