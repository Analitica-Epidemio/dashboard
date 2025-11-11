"use client";

import React from "react";
import Link from "next/link";
import { CollapsibleSidebar } from "@/features/layout/components";
import {
  MapPin,
  Building2,
  Link as LinkIcon,
  ChevronRight,
  AlertTriangle,
  CheckCircle2,
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useEstablecimientosSinMapear } from "@/lib/api/establecimientos";

interface ConfigCard {
  title: string;
  description: string;
  href: string;
  icon: React.ElementType;
  status?: "active" | "warning" | "inactive";
  statusText?: string;
  showBadge?: boolean;
}

export default function ConfiguracionPage() {
  // Obtener datos para mostrar badge de alerta en Mapeo
  const { data: sinMapearData } = useEstablecimientosSinMapear({
    limit: 1,
    con_eventos_solo: true,
    incluir_sugerencias: false,
  });

  const sinMapearCount = sinMapearData?.sin_mapear_count || 0;

  const configCards: ConfigCard[] = [
    {
      title: "Geocodificación",
      description: "Configuración del servicio de geocodificación de domicilios",
      href: "/dashboard/configuracion/geocodificacion",
      icon: MapPin,
      status: "active",
      statusText: "Activo",
    },
    {
      title: "Mapeo de Establecimientos",
      description: "Vincular establecimientos SNVS con el catálogo IGN para geolocalización",
      href: "/dashboard/configuracion/establecimientos",
      icon: Building2,
      status: sinMapearCount > 0 ? "warning" : "active",
      statusText: sinMapearCount > 0
        ? `${sinMapearCount} sin mapear`
        : "Configurado",
      showBadge: sinMapearCount > 0,
    },
    {
      title: "Estrategias de Vinculación",
      description: "Configurar estrategias automáticas para vincular eventos entre sí",
      href: "/dashboard/configuracion/estrategias",
      icon: LinkIcon,
      status: "active",
      statusText: "Activo",
    },
  ];

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

            {/* Cards Grid */}
            <div className="grid gap-4 md:grid-cols-2">
              {configCards.map((card) => {
                const Icon = card.icon;
                const isClickable = card.status !== "inactive";

                return (
                  <Card
                    key={card.href}
                    className={`group ${
                      isClickable
                        ? "hover:border-primary cursor-pointer transition-all hover:shadow-md"
                        : "opacity-60 cursor-not-allowed"
                    }`}
                  >
                    {isClickable ? (
                      <Link href={card.href}>
                        <CardContent className="p-6">
                          <div className="flex items-start justify-between mb-4">
                            <div className="flex items-center gap-3">
                              <div className="p-2 rounded-lg bg-primary/10">
                                <Icon className="h-5 w-5 text-primary" />
                              </div>
                              <div>
                                <CardTitle className="text-lg group-hover:text-primary transition-colors">
                                  {card.title}
                                </CardTitle>
                              </div>
                            </div>
                            <ChevronRight className="h-5 w-5 text-muted-foreground group-hover:text-primary group-hover:translate-x-1 transition-all" />
                          </div>

                          <CardDescription className="mb-4">
                            {card.description}
                          </CardDescription>

                          {/* Status */}
                          <div className="flex items-center gap-2">
                            {card.status === "active" && (
                              <>
                                <CheckCircle2 className="h-4 w-4 text-green-600" />
                                <span className="text-sm text-green-700 font-medium">
                                  {card.statusText}
                                </span>
                              </>
                            )}
                            {card.status === "warning" && (
                              <>
                                <AlertTriangle className="h-4 w-4 text-orange-600" />
                                <span className="text-sm text-orange-700 font-medium">
                                  {card.statusText}
                                </span>
                                {card.showBadge && (
                                  <Badge variant="outline" className="ml-2 border-orange-200 bg-orange-50 text-orange-700">
                                    Requiere atención
                                  </Badge>
                                )}
                              </>
                            )}
                          </div>
                        </CardContent>
                      </Link>
                    ) : (
                      <CardContent className="p-6">
                        <div className="flex items-start justify-between mb-4">
                          <div className="flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-muted">
                              <Icon className="h-5 w-5 text-muted-foreground" />
                            </div>
                            <div>
                              <CardTitle className="text-lg">{card.title}</CardTitle>
                            </div>
                          </div>
                        </div>

                        <CardDescription className="mb-4">
                          {card.description}
                        </CardDescription>

                        <Badge variant="secondary">{card.statusText}</Badge>
                      </CardContent>
                    )}
                  </Card>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
