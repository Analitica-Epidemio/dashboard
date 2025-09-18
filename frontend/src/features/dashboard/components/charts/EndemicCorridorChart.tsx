/**
 * Componente de Corredor Endémico
 * Replica funcionalidad del original con Recharts
 */

import React, { useMemo } from "react";
import {
  AreaChart,
  Area,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import { AlertTriangle, TrendingUp, CheckCircle } from "lucide-react";
import {
  EndemicCorridorConfig,
  EpidemiologicalFilters,
  ChartConfig,
} from "../../types";
import { useEndemicCorridor } from "../../hooks/useEpidemiologicalData";
import type { TooltipProps, EndemicCorridorPayload } from "../../types/recharts";

// Configuración de colores (replicando el original)
const ZONE_COLORS = {
  success: "rgb(195, 214, 155)", // Verde - Zona de éxito
  security: "rgb(255, 255, 153)", // Amarillo - Zona de seguridad
  alert: "rgb(247, 153, 75)", // Naranja - Zona de alerta
  currentYear: "rgb(0, 0, 0)", // Negro - Año actual
} as const;

interface EndemicCorridorChartProps {
  config: EndemicCorridorConfig;
  filters?: EpidemiologicalFilters;
  chartConfig?: ChartConfig;
  onWeekSelect?: (week: number) => void;
  showCurrentWeekIndicator?: boolean;
}

// Tooltip personalizado
const CustomTooltip: React.FC<TooltipProps<EndemicCorridorPayload>> = ({ active, payload, label }) => {
  if (!active || !payload || !payload.length) return null;

  const week = label;
  const data = payload[0]?.payload;

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3">
      <p className="font-semibold text-gray-800">Semana {week}</p>

      <div className="space-y-1 mt-2">
        <div className="flex items-center gap-2">
          <div
            className="w-3 h-3 rounded"
            style={{ backgroundColor: ZONE_COLORS.success }}
          />
          <span className="text-sm">
            Éxito: {data?.success?.toFixed(1)} casos
          </span>
        </div>

        <div className="flex items-center gap-2">
          <div
            className="w-3 h-3 rounded"
            style={{ backgroundColor: ZONE_COLORS.security }}
          />
          <span className="text-sm">
            Seguridad: {data?.security?.toFixed(1)} casos
          </span>
        </div>

        <div className="flex items-center gap-2">
          <div
            className="w-3 h-3 rounded"
            style={{ backgroundColor: ZONE_COLORS.alert }}
          />
          <span className="text-sm">
            Alerta: {data?.alert?.toFixed(1)} casos
          </span>
        </div>

        {data?.currentCases !== null && (
          <div className="flex items-center gap-2 mt-2 pt-2 border-t border-gray-200">
            <div
              className="w-3 h-3 rounded"
              style={{ backgroundColor: ZONE_COLORS.currentYear }}
            />
            <span className="text-sm font-semibold">
              Año actual: {data?.currentCases || 0} casos
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

// Indicador de zona actual
const ZoneIndicator: React.FC<{
  currentWeek: number;
  currentCases: number;
  zoneData: any;
}> = ({ currentWeek, currentCases, zoneData }) => {
  const getCurrentZone = () => {
    if (currentCases <= zoneData.success) {
      return {
        zone: "success",
        label: "Éxito",
        icon: CheckCircle,
        color: "text-green-600",
      };
    } else if (currentCases <= zoneData.success + zoneData.security) {
      return {
        zone: "security",
        label: "Seguridad",
        icon: TrendingUp,
        color: "text-yellow-600",
      };
    } else {
      return {
        zone: "alert",
        label: "Alerta",
        icon: AlertTriangle,
        color: "text-orange-600",
      };
    }
  };

  const { zone, label, icon: Icon, color } = getCurrentZone();

  return (
    <div className="flex items-center gap-2">
      <Icon className={`h-4 w-4 ${color}`} />
      <span className={`text-sm font-medium ${color}`}>
        Zona {label} - Semana {currentWeek}
      </span>
    </div>
  );
};

export const EndemicCorridorChart: React.FC<EndemicCorridorChartProps> = ({
  config,
  filters,
  chartConfig = {},
  onWeekSelect,
  showCurrentWeekIndicator = true,
}) => {
  const { processedData, loading, error, refetch } = useEndemicCorridor(
    config,
    filters
  );

  // Datos para el gráfico
  const { chartData, currentWeekData, title } = useMemo(() => {
    if (!processedData)
      return { chartData: [], currentWeekData: null, title: "" };

    const { chartData: data, metadata } = processedData;

    // Encontrar la última semana con datos del año actual
    const lastCurrentWeek = data
      .filter((d) => d.currentCases !== null)
      .reduce((max, d) => Math.max(max, d.week), 0);

    const currentData =
      lastCurrentWeek > 0 ? data.find((d) => d.week === lastCurrentWeek) : null;

    const chartTitle = `Corredor epidemiológico semanal - Año ${
      metadata.currentYear
    } (${
      metadata.historicalYears
    } años históricos) - valor t ${metadata.tValue.toFixed(2)}`;

    return {
      chartData: data,
      currentWeekData: currentData,
      title: chartTitle,
    };
  }, [processedData]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="flex items-center gap-2">
          <div className="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full" />
          <span>Cargando corredor endémico...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-4">
        <AlertTriangle className="h-12 w-12 text-red-500" />
        <div className="text-center">
          <p className="text-lg font-semibold text-gray-800">
            Error al cargar datos
          </p>
          <p className="text-sm text-gray-600">{error}</p>
          <button
            onClick={refetch}
            className="mt-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
          >
            Reintentar
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full">
      <div className="mb-4">
        <div className="flex justify-between items-start">
          <div>
            {currentWeekData && showCurrentWeekIndicator && (
              <div className="mt-2">
                <ZoneIndicator
                  currentWeek={currentWeekData.week}
                  currentCases={currentWeekData?.currentCases || 0}
                  zoneData={currentWeekData}
                />
              </div>
            )}
          </div>
        </div>
      </div>

      <div>
        <div
          className="w-full"
          style={{
            height: chartConfig.height || 400,
            backgroundColor: "rgb(238, 188, 172)", // Background original
          }}
        >
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart
              data={chartData}
              margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
              onClick={(data) => {
                if (data?.activeLabel && onWeekSelect) {
                  const weekNum = typeof data.activeLabel === 'string' ? parseInt(data.activeLabel) : data.activeLabel;
                  onWeekSelect(weekNum);
                }
              }}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="rgba(128, 128, 128, 0.2)"
              />

              <XAxis
                dataKey="week"
                domain={[1, 52]}
                type="number"
                scale="linear"
                tick={{ fontSize: 12 }}
                tickLine={{ stroke: "#666" }}
                axisLine={{ stroke: "#666" }}
                label={{
                  value: "Semana Epidemiológica",
                  position: "insideBottom",
                  offset: -40,
                }}
              />

              <YAxis
                domain={[0, "dataMax"]}
                tick={{ fontSize: 12 }}
                tickLine={{ stroke: "#666" }}
                axisLine={{ stroke: "#666" }}
                label={{ value: "Casos", angle: -90, position: "insideLeft" }}
              />

              {/* Zonas apiladas */}
              <Area
                type="monotone"
                dataKey="success"
                stackId="1"
                stroke="rgb(128, 128, 128)"
                fill={ZONE_COLORS.success}
                strokeWidth={1}
              />

              <Area
                type="monotone"
                dataKey="security"
                stackId="1"
                stroke="rgb(128, 128, 128)"
                fill={ZONE_COLORS.security}
                strokeWidth={1}
              />

              <Area
                type="monotone"
                dataKey="alert"
                stackId="1"
                stroke="rgb(128, 128, 128)"
                fill={ZONE_COLORS.alert}
                strokeWidth={1}
              />

              {/* Línea del año actual */}
              <Line
                type="monotone"
                dataKey="currentCases"
                stroke={ZONE_COLORS.currentYear}
                strokeWidth={2}
                dot={{ fill: ZONE_COLORS.currentYear, strokeWidth: 2, r: 3 }}
                connectNulls={false}
              />

              {/* Línea vertical para semana actual */}
              {currentWeekData && config?.lastWeek && config.lastWeek < 52 && (
                <ReferenceLine
                  x={config?.lastWeek}
                  stroke="rgba(0, 0, 255, 0.5)"
                  strokeWidth={1.5}
                  strokeDasharray="5 5"
                />
              )}

              <Tooltip content={<CustomTooltip />} />

              <Legend
                layout="horizontal"
                verticalAlign="top"
                align="right"
                wrapperStyle={{ paddingBottom: "20px" }}
                payload={[
                  { value: "Éxito", type: "rect", color: ZONE_COLORS.success },
                  {
                    value: "Seguridad",
                    type: "rect",
                    color: ZONE_COLORS.security,
                  },
                  { value: "Alerta", type: "rect", color: ZONE_COLORS.alert },
                  {
                    value: "Año actual",
                    type: "line",
                    color: ZONE_COLORS.currentYear,
                  },
                ]}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Indicador de semana actual */}
        {currentWeekData && config?.lastWeek && config.lastWeek < 52 && (
          <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-blue-500 rounded-full" />
              <span className="text-sm font-medium text-blue-800">
                Semana actual ({config?.lastWeek}) - Próximas semanas en
                proyección
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default EndemicCorridorChart;
