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

/**
 * Pre-compute stacked zone deltas so each Area represents only its band height.
 * Recharts stacks them bottom-up: exito → seguridad → alerta → brote.
 */
interface StackedData {
  semana: number;
  casos: number;
  exitoBand: number;
  seguridadBand: number;
  alertaBand: number;
  broteBand: number;
}

export function MiniCorredor({
  data,
  currentWeek,
  width = 120,
  height = 40,
  className,
}: MiniCorredorProps) {
  const { stackedData, maxY } = useMemo(() => {
    if (!data.length) return { stackedData: [] as StackedData[], maxY: 100 };

    let computedMaxY = 0;
    const stacked = data.map((d) => {
      const exitoBand = Math.max(0, d.exitoMax);
      const seguridadBand = Math.max(0, d.seguridadMax - d.exitoMax);
      const alertaBand = Math.max(0, d.alertaMax - d.seguridadMax);
      // Brote band extends from alertaMax to the chart ceiling
      const top = Math.max(d.casos || 0, d.alertaMax || 0);
      if (top > computedMaxY) computedMaxY = top;

      return {
        semana: d.semana,
        casos: d.casos,
        exitoBand,
        seguridadBand,
        alertaBand,
        broteBand: 0, // will be set after we know maxY
      };
    });

    computedMaxY = computedMaxY * 1.1;

    // Set brote band now that we know the ceiling
    for (const row of stacked) {
      const alertaTop = row.exitoBand + row.seguridadBand + row.alertaBand;
      row.broteBand = Math.max(0, computedMaxY - alertaTop);
    }

    return { stackedData: stacked, maxY: computedMaxY };
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
          data={stackedData}
          margin={{ top: 2, right: 2, left: 2, bottom: 2 }}
        >
          <defs>
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

          {/* Stacked zones bottom-up: éxito → seguridad → alerta → brote */}
          <Area
            dataKey="exitoBand"
            type="monotone"
            stackId="zones"
            fill="url(#miniZonaExito)"
            stroke="none"
          />
          <Area
            dataKey="seguridadBand"
            type="monotone"
            stackId="zones"
            fill="url(#miniZonaSeguridad)"
            stroke="none"
          />
          <Area
            dataKey="alertaBand"
            type="monotone"
            stackId="zones"
            fill="url(#miniZonaAlerta)"
            stroke="none"
          />
          <Area
            dataKey="broteBand"
            type="monotone"
            stackId="zones"
            fill="url(#miniZonaBrote)"
            stroke="none"
          />

          {/* Cases line (not stacked) */}
          <Line
            dataKey="casos"
            type="monotone"
            stroke="#1e40af"
            strokeWidth={1.5}
            dot={false}
            activeDot={false}
          />

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
