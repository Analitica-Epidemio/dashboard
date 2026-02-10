"use client";

/**
 * Mini Corredor Endémico Sparkline
 * Visualización compacta del corredor endémico (120x40px)
 */

import { useMemo } from "react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  Line,
  XAxis,
  YAxis,
  ReferenceLine,
} from "recharts";
import { cn } from "@/lib/utils";

export interface MiniCorredorData {
  semana: number;
  casos: number;
  exitoMax: number;
  seguridadMax: number;
  alertaMax: number;
}

interface MiniCorredorProps {
  data: MiniCorredorData[];
  currentWeek?: number;
  width?: number;
  height?: number;
  className?: string;
}

export function MiniCorredor({
  data,
  currentWeek,
  width = 120,
  height = 40,
  className,
}: MiniCorredorProps) {
  // Calculate max value for Y axis
  const maxY = useMemo(() => {
    if (!data.length) return 100;
    const maxCasos = Math.max(...data.map((d) => d.casos || 0));
    const maxAlerta = Math.max(...data.map((d) => d.alertaMax || 0));
    return Math.max(maxCasos, maxAlerta) * 1.1;
  }, [data]);

  if (!data.length) {
    return (
      <div
        className={cn("bg-muted/50 rounded flex items-center justify-center", className)}
        style={{ width, height }}
      >
        <span className="text-[10px] text-muted-foreground">Sin datos</span>
      </div>
    );
  }

  return (
    <div className={cn("rounded overflow-hidden", className)} style={{ width, height }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart
          data={data}
          margin={{ top: 2, right: 2, left: 2, bottom: 2 }}
        >
          <defs>
            {/* Zone gradients */}
            <linearGradient id="miniZonaExito" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#22c55e" stopOpacity={0.4} />
              <stop offset="100%" stopColor="#22c55e" stopOpacity={0.1} />
            </linearGradient>
            <linearGradient id="miniZonaSeguridad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#eab308" stopOpacity={0.4} />
              <stop offset="100%" stopColor="#eab308" stopOpacity={0.1} />
            </linearGradient>
            <linearGradient id="miniZonaAlerta" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#f97316" stopOpacity={0.4} />
              <stop offset="100%" stopColor="#f97316" stopOpacity={0.1} />
            </linearGradient>
            <linearGradient id="miniZonaBrote" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#ef4444" stopOpacity={0.4} />
              <stop offset="100%" stopColor="#ef4444" stopOpacity={0.1} />
            </linearGradient>
          </defs>

          <XAxis dataKey="semana" hide />
          <YAxis domain={[0, maxY]} hide />

          {/* Brote zone (above alerta) */}
          <Area
            dataKey="alertaMax"
            type="monotone"
            stackId="zones"
            fill="url(#miniZonaBrote)"
            stroke="none"
            baseValue={maxY}
          />

          {/* Alerta zone */}
          <Area
            dataKey="alertaMax"
            type="monotone"
            fill="url(#miniZonaAlerta)"
            stroke="none"
            baseValue={(d: MiniCorredorData) => d.seguridadMax}
          />

          {/* Seguridad zone */}
          <Area
            dataKey="seguridadMax"
            type="monotone"
            fill="url(#miniZonaSeguridad)"
            stroke="none"
            baseValue={(d: MiniCorredorData) => d.exitoMax}
          />

          {/* Éxito zone */}
          <Area
            dataKey="exitoMax"
            type="monotone"
            fill="url(#miniZonaExito)"
            stroke="none"
          />

          {/* Cases line */}
          <Line
            dataKey="casos"
            type="monotone"
            stroke="#1e40af"
            strokeWidth={1.5}
            dot={false}
            activeDot={false}
          />

          {/* Current week marker */}
          {currentWeek && (
            <ReferenceLine
              x={currentWeek}
              stroke="#6b7280"
              strokeDasharray="2 2"
              strokeWidth={1}
            />
          )}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

/**
 * Simplified version that just shows the trend with colored background
 */
interface MiniCorredorSimpleProps {
  zona: "exito" | "seguridad" | "alerta" | "brote";
  trend?: "up" | "down" | "stable";
  width?: number;
  height?: number;
  className?: string;
}

export function MiniCorredorSimple({
  zona,
  trend = "stable",
  width = 60,
  height = 24,
  className,
}: MiniCorredorSimpleProps) {
  const zonaColors: Record<string, string> = {
    exito: "bg-green-100",
    seguridad: "bg-yellow-100",
    alerta: "bg-orange-100",
    brote: "bg-red-100",
  };

  const trendColors: Record<string, string> = {
    up: "text-red-600",
    down: "text-green-600",
    stable: "text-gray-500",
  };

  const trendIcons: Record<string, string> = {
    up: "↑",
    down: "↓",
    stable: "→",
  };

  return (
    <div
      className={cn(
        "rounded flex items-center justify-center gap-1 px-2",
        zonaColors[zona],
        className
      )}
      style={{ width, height }}
    >
      <span className={cn("text-xs font-medium", trendColors[trend])}>
        {trendIcons[trend]}
      </span>
    </div>
  );
}
