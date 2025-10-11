"use client";

import React from "react";
import {
  Calendar, Heart, TestTube, Stethoscope, Syringe,
  Activity, Building, Search, Clock, AlertTriangle, Info
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

interface TimelineItem {
  tipo: string;
  fecha: string;
  titulo: string;
  descripcion?: string;
  detalles?: Record<string, any>;
  evento_id?: number;
  evento_tipo?: string;
  clasificacion?: string;
  es_critico: boolean;
  icono: string;
  color: string;
}

interface PersonTimelineProps {
  items: TimelineItem[];
  isLoading?: boolean;
}

export function PersonTimeline({ items, isLoading }: PersonTimelineProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-48" />
        </CardHeader>
        <CardContent className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex gap-4">
              <Skeleton className="h-12 w-12 rounded-full" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-3 w-1/2" />
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    );
  }

  const getIcon = (iconName: string) => {
    const icons: Record<string, any> = {
      'activity': Activity,
      'heart': Heart,
      'test-tube': TestTube,
      'stethoscope': Stethoscope,
      'syringe': Syringe,
      'building': Building,
      'search': Search,
      'clock': Clock,
      'alert-circle': AlertTriangle,
      'info': Info,
    };
    const IconComponent = icons[iconName] || Info;
    return <IconComponent className="h-4 w-4" />;
  };

  const getColorClass = (color: string) => {
    const colors: Record<string, string> = {
      'blue': 'bg-blue-500',
      'red': 'bg-red-500',
      'green': 'bg-green-500',
      'yellow': 'bg-yellow-500',
      'purple': 'bg-purple-500',
      'orange': 'bg-orange-500',
      'indigo': 'bg-indigo-500',
      'teal': 'bg-teal-500',
    };
    return colors[color] || 'bg-gray-500';
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Clock className="h-5 w-5" />
          Timeline Completo
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {items.map((item, index) => (
            <div key={index} className="flex gap-4">
              {/* Icon */}
              <div className="flex flex-col items-center">
                <div
                  className={`flex h-10 w-10 items-center justify-center rounded-full ${getColorClass(item.color)} text-white`}
                >
                  {getIcon(item.icono)}
                </div>
                {index < items.length - 1 && (
                  <div className="w-px flex-1 bg-border mt-2" />
                )}
              </div>

              {/* Content */}
              <div className="flex-1 pb-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="font-medium flex items-center gap-2">
                      {item.titulo}
                      {item.es_critico && (
                        <Badge variant="destructive" className="text-xs">
                          Crítico
                        </Badge>
                      )}
                    </p>
                    <p className="text-sm text-muted-foreground mt-1">
                      {item.descripcion}
                    </p>
                    {item.evento_tipo && (
                      <p className="text-xs text-muted-foreground mt-1">
                        {item.evento_tipo}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-1 text-sm text-muted-foreground">
                    <Calendar className="h-3 w-3" />
                    {new Date(item.fecha).toLocaleDateString("es-ES")}
                  </div>
                </div>

                {/* Detalles adicionales */}
                {item.detalles && Object.keys(item.detalles).length > 0 && (
                  <div className="mt-2 rounded-md bg-muted p-2 text-xs">
                    <pre className="overflow-auto">
                      {JSON.stringify(item.detalles, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          ))}

          {items.length === 0 && (
            <div className="text-center py-12 text-muted-foreground">
              <Clock className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No hay items en el timeline</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
