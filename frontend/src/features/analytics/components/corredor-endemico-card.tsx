"use client";

/**
 * CorredorEndemicoCard Component
 *
 * Displays endemic corridor chart with zones:
 * - Zona Exito (green): below p25
 * - Zona Seguridad (yellow): p25-p50
 * - Zona Alerta (orange): p50-p75
 * - Zona Brote (red): above p75
 * - Valor Actual (line): current year values
 */

import {
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Line,
  ComposedChart,
} from "recharts";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, CheckCircle, AlertCircle, XCircle } from "lucide-react";
import type { CorredorEndemicoData } from "../api";

interface CorredorEndemicoCardProps {
  title: string;
  description?: string;
  data: CorredorEndemicoData[];
  anioActual: number;
  warnings?: string[] | null;
  className?: string;
}

// Zone colors matching typical endemic corridor visualizations
const ZONE_COLORS = {
  exito: "#22c55e",      // green-500
  seguridad: "#facc15",   // yellow-400
  alerta: "#fb923c",      // orange-400
  brote: "#ef4444",       // red-500
  actual: "#1d4ed8",      // blue-700
};

/**
 * Determines the current status based on the last value and zones
 */
function getStatus(data: CorredorEndemicoData[]): {
  label: string;
  icon: React.ReactNode;
  color: string;
} {
  if (data.length === 0) {
    return { label: "Sin datos", icon: <AlertCircle className="h-4 w-4" />, color: "gray" };
  }

  const lastPoint = data[data.length - 1];

  if (!lastPoint.corredor_valido) {
    return { label: "Corredor no válido", icon: <AlertCircle className="h-4 w-4" />, color: "gray" };
  }

  if (lastPoint.valor_actual <= lastPoint.zona_exito) {
    return { label: "Zona Éxito", icon: <CheckCircle className="h-4 w-4" />, color: "green" };
  } else if (lastPoint.valor_actual <= lastPoint.zona_seguridad) {
    return { label: "Zona Seguridad", icon: <CheckCircle className="h-4 w-4" />, color: "yellow" };
  } else if (lastPoint.valor_actual <= lastPoint.zona_alerta) {
    return { label: "Zona Alerta", icon: <AlertTriangle className="h-4 w-4" />, color: "orange" };
  } else {
    return { label: "Zona Brote", icon: <XCircle className="h-4 w-4" />, color: "red" };
  }
}

/**
 * Transform data for the stacked area chart
 * The zones are displayed as stacked areas where:
 * - exito: from 0 to zona_exito
 * - seguridad: from zona_exito to zona_seguridad
 * - alerta: from zona_seguridad to zona_alerta
 * - brote: from zona_alerta to zona_brote
 */
function transformDataForChart(data: CorredorEndemicoData[]) {
  return data.map((d) => ({
    semana: `SE ${d.semana_epidemiologica}`,
    semana_num: d.semana_epidemiologica,
    valor_actual: d.valor_actual,
    // For stacked areas, we need the height of each zone, not cumulative
    zona_exito: d.zona_exito,
    zona_seguridad: d.zona_seguridad - d.zona_exito,
    zona_alerta: d.zona_alerta - d.zona_seguridad,
    zona_brote: d.zona_brote - d.zona_alerta,
    corredor_valido: d.corredor_valido,
  }));
}

export function CorredorEndemicoCard({
  title,
  description,
  data,
  anioActual,
  warnings,
  className,
}: CorredorEndemicoCardProps) {
  const status = getStatus(data);
  const chartData = transformDataForChart(data);

  // Get the last value for display
  const lastValue = data.length > 0 ? data[data.length - 1] : null;

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg">{title}</CardTitle>
            {description && (
              <CardDescription>{description}</CardDescription>
            )}
          </div>
          <div className="flex items-center gap-2">
            {lastValue && (
              <Badge variant="outline" className="text-lg font-bold">
                {lastValue.valor_actual} casos
              </Badge>
            )}
            <Badge
              variant="outline"
              className={`flex items-center gap-1 ${
                status.color === "green" ? "border-green-500 text-green-700" :
                status.color === "yellow" ? "border-yellow-500 text-yellow-700" :
                status.color === "orange" ? "border-orange-500 text-orange-700" :
                status.color === "red" ? "border-red-500 text-red-700" :
                "border-gray-500 text-gray-700"
              }`}
            >
              {status.icon}
              {status.label}
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {warnings && warnings.length > 0 && (
          <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
            <p className="text-sm text-amber-800 flex items-center gap-2">
              <AlertTriangle className="h-4 w-4" />
              {warnings[0]}
            </p>
          </div>
        )}

        {data.length === 0 ? (
          <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg">
            <p className="text-muted-foreground">No hay datos disponibles</p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <ComposedChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
              <XAxis
                dataKey="semana"
                tick={{ fontSize: 11 }}
                interval="preserveStartEnd"
              />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip
                content={({ active, payload, label }) => {
                  if (active && payload && payload.length > 0) {
                    const originalData = data.find(
                      (d) => `SE ${d.semana_epidemiologica}` === label
                    );
                    if (!originalData) return null;

                    return (
                      <div className="bg-white p-3 border rounded-lg shadow-lg">
                        <p className="font-semibold mb-2">{label}</p>
                        <div className="space-y-1 text-sm">
                          <p className="text-blue-700 font-medium">
                            Valor actual: {originalData.valor_actual}
                          </p>
                          <hr className="my-2" />
                          <p style={{ color: ZONE_COLORS.exito }}>
                            Zona Éxito: ≤ {originalData.zona_exito.toFixed(0)}
                          </p>
                          <p style={{ color: ZONE_COLORS.seguridad }}>
                            Zona Seguridad: ≤ {originalData.zona_seguridad.toFixed(0)}
                          </p>
                          <p style={{ color: ZONE_COLORS.alerta }}>
                            Zona Alerta: ≤ {originalData.zona_alerta.toFixed(0)}
                          </p>
                          <p style={{ color: ZONE_COLORS.brote }}>
                            Zona Brote: {">"} {originalData.zona_alerta.toFixed(0)}
                          </p>
                        </div>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Legend
                wrapperStyle={{ fontSize: "12px" }}
                formatter={(value) => {
                  const labels: Record<string, string> = {
                    zona_exito: "Éxito (P25)",
                    zona_seguridad: "Seguridad (P50)",
                    zona_alerta: "Alerta (P75)",
                    zona_brote: "Brote (P90)",
                    valor_actual: `Actual ${anioActual}`,
                  };
                  return labels[value] || value;
                }}
              />
              {/* Stacked areas for zones */}
              <Area
                type="monotone"
                dataKey="zona_exito"
                stackId="1"
                stroke={ZONE_COLORS.exito}
                fill={ZONE_COLORS.exito}
                fillOpacity={0.4}
                name="zona_exito"
              />
              <Area
                type="monotone"
                dataKey="zona_seguridad"
                stackId="1"
                stroke={ZONE_COLORS.seguridad}
                fill={ZONE_COLORS.seguridad}
                fillOpacity={0.4}
                name="zona_seguridad"
              />
              <Area
                type="monotone"
                dataKey="zona_alerta"
                stackId="1"
                stroke={ZONE_COLORS.alerta}
                fill={ZONE_COLORS.alerta}
                fillOpacity={0.4}
                name="zona_alerta"
              />
              <Area
                type="monotone"
                dataKey="zona_brote"
                stackId="1"
                stroke={ZONE_COLORS.brote}
                fill={ZONE_COLORS.brote}
                fillOpacity={0.4}
                name="zona_brote"
              />
              {/* Line for current values */}
              <Line
                type="monotone"
                dataKey="valor_actual"
                stroke={ZONE_COLORS.actual}
                strokeWidth={3}
                dot={{ fill: ZONE_COLORS.actual, strokeWidth: 2 }}
                name="valor_actual"
              />
            </ComposedChart>
          </ResponsiveContainer>
        )}

        <div className="mt-4 flex items-center justify-center gap-6 text-xs text-muted-foreground">
          <span>Corredor endémico calculado con años: 2018, 2019, 2022, 2023, 2024</span>
        </div>
      </CardContent>
    </Card>
  );
}
