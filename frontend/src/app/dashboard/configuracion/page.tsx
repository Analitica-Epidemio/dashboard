"use client";

import React from "react";
import { CollapsibleSidebar } from "@/features/layout/components";
import { GeocodingConfigPanel } from "./_components/geocoding-config-panel";

export default function ConfiguracionPage() {
  return (
    <div className="flex h-screen overflow-hidden">
      <CollapsibleSidebar />

      <div className="flex-1 overflow-y-scroll bg-background">
        <div className="container mx-auto p-6 max-w-5xl">
          <div className="space-y-6">
            {/* Header */}
            <div className="space-y-2">
              <h1 className="text-3xl font-bold tracking-tight">
                Configuración del Sistema
              </h1>
              <p className="text-muted-foreground">
                Administra la configuración y servicios del sistema de epidemiología
              </p>
            </div>

            {/* Geocoding Panel */}
            <GeocodingConfigPanel />

            {/* Más paneles de configuración pueden ir aquí */}
          </div>
        </div>
      </div>
    </div>
  );
}
