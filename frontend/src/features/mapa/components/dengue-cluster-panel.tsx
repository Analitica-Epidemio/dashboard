"use client";

import { format, differenceInDays } from "date-fns";
import { es } from "date-fns/locale";
import type { DengueCluster } from "../utils/dengue-cluster";
import { DENGUE_CLUSTER_CONFIG } from "../utils/dengue-cluster";

interface DengueClusterPanelProps {
  cluster: DengueCluster | null;
  onClose: () => void;
}

export function DengueClusterPanel({ cluster, onClose }: DengueClusterPanelProps) {
  if (!cluster) return null;

  const durationDays = differenceInDays(cluster.dateRange.end, cluster.dateRange.start) + 1;
  const casesPerDay = (cluster.totalCases / durationDays).toFixed(1);

  // Agrupar casos por tipo
  const casesByType: Record<string, number> = {};
  for (const c of cluster.cases) {
    casesByType[c.tipoNombre] = (casesByType[c.tipoNombre] || 0) + 1;
  }

  return (
    <div className="absolute bottom-4 left-4 z-[1000] bg-white rounded-lg shadow-xl border max-w-sm">
      {/* Header */}
      <div
        className={`px-4 py-3 rounded-t-lg flex items-center justify-between ${
          cluster.isActive ? "bg-red-50 border-b border-red-100" : "bg-orange-50 border-b border-orange-100"
        }`}
      >
        <div className="flex items-center gap-2">
          {cluster.isActive ? (
            <span className="inline-block w-3 h-3 rounded-full bg-red-500 animate-pulse" />
          ) : (
            <span className="inline-block w-3 h-3 rounded-full bg-orange-500" />
          )}
          <h3 className="font-bold text-gray-900">
            Cluster de Dengue #{cluster.id.split("-")[1]}
          </h3>
        </div>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 transition-colors"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="currentColor"
            className="w-5 h-5"
          >
            <path
              fillRule="evenodd"
              d="M5.47 5.47a.75.75 0 011.06 0L12 10.94l5.47-5.47a.75.75 0 111.06 1.06L13.06 12l5.47 5.47a.75.75 0 11-1.06 1.06L12 13.06l-5.47 5.47a.75.75 0 01-1.06-1.06L10.94 12 5.47 6.53a.75.75 0 010-1.06z"
              clipRule="evenodd"
            />
          </svg>
        </button>
      </div>

      {/* Body */}
      <div className="p-4 space-y-4">
        {/* Estado */}
        {cluster.isActive && (
          <div className="bg-red-50 border border-red-200 rounded-lg px-3 py-2 text-sm text-red-800">
            <strong>⚠️ Cluster activo:</strong> Se detectaron casos en los últimos 7
            días. Se recomienda intensificar vigilancia y control vectorial.
          </div>
        )}

        {/* Estadísticas principales */}
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-gray-50 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-gray-900">{cluster.totalCases}</div>
            <div className="text-xs text-gray-500">Casos totales</div>
          </div>
          <div className="bg-gray-50 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-gray-900">
              {cluster.uniqueDomicilios}
            </div>
            <div className="text-xs text-gray-500">Domicilios</div>
          </div>
        </div>

        {/* Detalles */}
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-500">Período:</span>
            <span className="font-medium">
              {format(cluster.dateRange.start, "d MMM", { locale: es })} -{" "}
              {format(cluster.dateRange.end, "d MMM yyyy", { locale: es })}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Duración:</span>
            <span className="font-medium">{durationDays} días</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Tasa:</span>
            <span className="font-medium">{casesPerDay} casos/día</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Radio del cluster:</span>
            <span className="font-medium">{Math.round(cluster.radiusMeters)}m</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Coordenadas:</span>
            <span className="font-mono text-xs">
              {cluster.centerLat.toFixed(5)}, {cluster.centerLng.toFixed(5)}
            </span>
          </div>
        </div>

        {/* Tipos de casos */}
        {Object.keys(casesByType).length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">
              Distribución por tipo
            </h4>
            <div className="space-y-1">
              {Object.entries(casesByType)
                .sort((a, b) => b[1] - a[1])
                .map(([tipo, count]) => (
                  <div key={tipo} className="flex items-center gap-2 text-sm">
                    <div className="flex-1 bg-gray-100 rounded-full h-2 overflow-hidden">
                      <div
                        className="h-full bg-red-500 rounded-full"
                        style={{
                          width: `${(count / cluster.totalCases) * 100}%`,
                        }}
                      />
                    </div>
                    <span className="text-gray-600 min-w-[60px] text-right">
                      {tipo}
                    </span>
                    <span className="font-medium min-w-[30px] text-right">{count}</span>
                  </div>
                ))}
            </div>
          </div>
        )}

        {/* Parámetros de clustering */}
        <div className="pt-3 border-t border-gray-200">
          <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">
            Parámetros de detección
          </h4>
          <div className="text-xs text-gray-500 space-y-1">
            <div>
              Radio de búsqueda: {DENGUE_CLUSTER_CONFIG.RADIUS_METERS}m (vuelo Aedes
              aegypti)
            </div>
            <div>
              Ventana temporal: {DENGUE_CLUSTER_CONFIG.WINDOW_DAYS} días (ciclo de
              transmisión)
            </div>
            <div>
              Mínimo para cluster: {DENGUE_CLUSTER_CONFIG.MIN_CASES_FOR_CLUSTER} casos
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
