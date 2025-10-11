"use client";

import { useState } from "react";
import dynamic from "next/dynamic";

// Cargar el mapa solo en el cliente (no SSR) porque Leaflet usa window
const MapaInteractivo = dynamic(
  () => import("./_components/mapa-interactivo").then((mod) => ({ default: mod.MapaInteractivo })),
  {
    ssr: false,
    loading: () => (
      <div className="flex items-center justify-center h-[600px] bg-gray-50 rounded-lg">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto mb-4"></div>
          <p className="text-muted-foreground">Cargando mapa...</p>
        </div>
      </div>
    ),
  }
);

export default function MapaPage() {
  const [nivel, setNivel] = useState<"provincia" | "departamento" | "localidad">("provincia");
  const [selectedProvinciaId, setSelectedProvinciaId] = useState<number | null>(null);
  const [selectedDepartamentoId, setSelectedDepartamentoId] = useState<number | null>(null);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Mapa Epidemiologico</h1>
        <p className="text-muted-foreground">
          Visualizacion geografica de eventos epidemiologicos
        </p>
      </div>

      <MapaInteractivo
        nivel={nivel}
        onNivelChange={setNivel}
        selectedProvinciaId={selectedProvinciaId}
        selectedDepartamentoId={selectedDepartamentoId}
        onProvinciaSelect={setSelectedProvinciaId}
        onDepartamentoSelect={setSelectedDepartamentoId}
      />
    </div>
  );
}
