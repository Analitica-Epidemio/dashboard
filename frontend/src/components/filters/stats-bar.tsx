"use client";

/**
 * Barra de estadísticas compartida
 * Muestra métricas clave con colores y separadores
 */

import React from "react";
import { Separator } from "@/components/ui/separator";

export interface StatItem {
  id: string;
  label: string;
  value: number | string;
  color?: string;
  icon?: React.ReactNode;
}

export interface StatsBarProps {
  stats: StatItem[];
  className?: string;
}

export function StatsBar({ stats, className = "" }: StatsBarProps) {
  if (stats.length === 0) return null;

  return (
    <div className={`flex items-center gap-4 text-sm flex-wrap ${className}`}>
      {stats.map((stat, index) => (
        <React.Fragment key={stat.id}>
          <div className="flex items-center gap-2">
            {stat.icon}
            <span className="text-muted-foreground">{stat.label}:</span>
            <span
              className={`font-semibold ${stat.color || "text-foreground"}`}
            >
              {typeof stat.value === "number"
                ? stat.value.toLocaleString("es-AR")
                : stat.value}
            </span>
          </div>
          {index < stats.length - 1 && (
            <Separator orientation="vertical" className="h-4" />
          )}
        </React.Fragment>
      ))}
    </div>
  );
}
