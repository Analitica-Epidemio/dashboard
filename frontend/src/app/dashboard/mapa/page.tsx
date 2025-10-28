"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { MapaLayout } from "./_components/mapa-layout";
import { MapaSidebar } from "./_components/mapa-sidebar-v2";
import { useDomiciliosMapa, type DomicilioMapaItem } from "@/lib/api/mapa";

// Cargar el mapa solo en el cliente (no SSR) porque Leaflet usa window
const MapaSimple = dynamic(
  () => import("./_components/mapa-simple").then((mod) => ({ default: mod.MapaSimple })),
  {
    ssr: false,
    loading: () => (
      <div className="flex items-center justify-center h-full bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 font-medium">Cargando mapa de domicilios...</p>
          <p className="text-sm text-gray-400 mt-1">Por favor espere</p>
        </div>
      </div>
    ),
  }
);

export default function MapaPage() {
  // Cargar domicilios geocodificados
  const { data, isLoading } = useDomiciliosMapa({
    limit: 1000,
  });

  const domicilios = data?.data?.items || [];

  // Calcular estadísticas
  const totalDomicilios = domicilios.length;
  const totalEventos = domicilios.reduce((sum, d) => sum + d.total_eventos, 0);
  const provinciasUnicas = new Set(domicilios.map(d => d.id_provincia_indec)).size;

  return (
    <MapaLayout
      sidebar={
        <MapaSidebar
          totalEventosGlobal={totalEventos}
          totalEventosMapeados={totalEventos}
          poblacionTotal={0}
          provinciasAfectadas={provinciasUnicas}
          tasaIncidencia={0}
          onNivelChange={() => {}}
          nivel="localidad"
        />
      }
    >
      <div className="h-full relative">
        {/* Indicador de carga */}
        {isLoading && (
          <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-[999] bg-white shadow-lg rounded-lg px-4 py-3 flex items-center gap-3 border">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
            <span className="text-sm font-medium">Cargando {totalDomicilios} domicilios...</span>
          </div>
        )}

        {/* Info rápida */}
        {!isLoading && domicilios.length > 0 && (
          <div className="absolute top-4 left-4 z-[999] bg-white shadow-lg rounded-lg p-4 border">
            <div className="text-sm space-y-1">
              <div>
                <span className="text-gray-600">Domicilios: </span>
                <span className="font-semibold">{totalDomicilios}</span>
              </div>
              <div>
                <span className="text-gray-600">Total Eventos: </span>
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
          domicilios={domicilios}
          isLoading={isLoading}
        />
      </div>
    </MapaLayout>
  );
}
