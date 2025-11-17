"use client";

import React from "react";
import Link from "next/link";
import { ChevronLeft } from "lucide-react";
import { CollapsibleSidebar } from "@/features/layout/components";
import { Button } from "@/components/ui/button";
import { MapeoEstablecimientosPanel } from "@/features/establecimientos/components/mapeo-establecimientos-panel";

export default function MapeoEstablecimientosPage() {
  return (
    <div className="flex h-screen overflow-hidden">
      <CollapsibleSidebar />

      <div className="flex-1 overflow-y-scroll bg-background">
        <div className="container mx-auto p-6 max-w-5xl">
          <div className="space-y-6">
            {/* Breadcrumb */}
            <div>
              <Button variant="ghost" size="sm" asChild>
                <Link href="/dashboard/configuracion">
                  <ChevronLeft className="h-4 w-4 mr-1" />
                  Volver a Configuración
                </Link>
              </Button>
            </div>

            {/* Header */}
            <div className="space-y-2">
              <h1 className="text-3xl font-bold tracking-tight">
                Mapeo de Establecimientos
              </h1>
              <p className="text-muted-foreground">
                Vincula establecimientos SNVS con el catálogo IGN para geolocalización
              </p>
            </div>

            {/* Panel de Mapeo */}
            <MapeoEstablecimientosPanel />
          </div>
        </div>
      </div>
    </div>
  );
}
