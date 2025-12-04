"use client";

import { WidgetContainer } from "./widget-container";
import { WidgetProps } from "./types";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";

export function BarChartWidget({ widget, data, isLoading, onEdit, onDelete }: WidgetProps) {
  const config: Record<string, unknown> = widget.visual_config?.config || {};
  const showLegend = config.show_legend !== false;
  const showGrid = config.show_grid !== false;
  const orientation = (config.orientation as "vertical" | "horizontal") || "vertical";

  // Parse data
  let chartData: Record<string, unknown>[] = [];
  let bars: string[] = [];

  if (widget.data_config.source === "manual" && widget.data_config.manual_data) {
    const manualData = widget.data_config.manual_data as { data?: Record<string, unknown>[]; bars?: string[] };
    chartData = manualData.data || [];
    bars = manualData.bars || [];
  } else if (data) {
    if (Array.isArray(data)) {
      chartData = data as Record<string, unknown>[];
      // Detect numeric fields as bars (excluding x-axis field)
      if (data.length > 0) {
        const firstItem = data[0] as Record<string, unknown>;
        bars = Object.keys(firstItem).filter(
          (key) => typeof firstItem[key] === "number"
        );
      }
    } else if (typeof data === "object" && "data" in data && "bars" in data) {
      const typedData = data as { data: Record<string, unknown>[]; bars: string[] };
      chartData = typedData.data;
      bars = typedData.bars;
    }
  }

  const colors = [
    "#3b82f6", // blue
    "#ef4444", // red
    "#10b981", // green
    "#f59e0b", // yellow
    "#8b5cf6", // purple
    "#ec4899", // pink
  ];

  return (
    <WidgetContainer
      title={widget.title}
      showTitle={widget.visual_config?.show_title}
      isLoading={isLoading}
      onEdit={onEdit}
      onDelete={onDelete}
    >
      {chartData.length === 0 ? (
        <div className="flex items-center justify-center h-full text-muted-foreground">
          No hay datos disponibles
        </div>
      ) : (
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            layout={orientation === "horizontal" ? "horizontal" : "vertical"}
          >
            {showGrid && <CartesianGrid strokeDasharray="3 3" />}
            <XAxis
              dataKey={(config.xAxis as string) || "name"}
              type={orientation === "horizontal" ? "number" : "category"}
              tick={{ fontSize: 12 }}
              tickLine={false}
            />
            <YAxis
              type={orientation === "horizontal" ? "category" : "number"}
              tick={{ fontSize: 12 }}
              tickLine={false}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "hsl(var(--background))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "6px",
                color: "hsl(var(--foreground))",
              }}
            />
            {showLegend && <Legend />}
            {bars.map((bar, idx) => (
              <Bar
                key={bar}
                dataKey={bar}
                fill={colors[idx % colors.length]}
                radius={[4, 4, 0, 0]}
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      )}
    </WidgetContainer>
  );
}
