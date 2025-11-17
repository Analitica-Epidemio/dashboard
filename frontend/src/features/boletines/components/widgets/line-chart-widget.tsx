"use client";

import { WidgetContainer } from "./widget-container";
import { WidgetProps } from "./types";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";

export function LineChartWidget({ widget, data, isLoading, onEdit, onDelete }: WidgetProps) {
  const config: Record<string, unknown> = widget.visual_config?.config || {};
  const showLegend = config.show_legend !== false;
  const showGrid = config.show_grid !== false;

  // Parse data
  let chartData: Record<string, unknown>[] = [];
  let lines: string[] = [];

  if (widget.data_config.source === "manual" && widget.data_config.manual_data) {
    const manualData = widget.data_config.manual_data as { data?: Record<string, unknown>[]; lines?: string[] };
    chartData = manualData.data || [];
    lines = manualData.lines || [];
  } else if (data) {
    if (Array.isArray(data)) {
      chartData = data as Record<string, unknown>[];
      // Detect numeric fields as lines (excluding x-axis field)
      if (data.length > 0) {
        const firstItem = data[0] as Record<string, unknown>;
        lines = Object.keys(firstItem).filter(
          (key) => typeof firstItem[key] === "number"
        );
      }
    } else if (typeof data === "object" && "data" in data && "lines" in data) {
      const typedData = data as { data: Record<string, unknown>[]; lines: string[] };
      chartData = typedData.data;
      lines = typedData.lines;
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
          <LineChart data={chartData}>
            {showGrid && <CartesianGrid strokeDasharray="3 3" />}
            <XAxis
              dataKey={(config.xAxis as string) || "name"}
              tick={{ fontSize: 12 }}
              tickLine={false}
            />
            <YAxis tick={{ fontSize: 12 }} tickLine={false} />
            <Tooltip
              contentStyle={{
                backgroundColor: "hsl(var(--background))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "6px",
              }}
            />
            {showLegend && <Legend />}
            {lines.map((line, idx) => (
              <Line
                key={line}
                type="monotone"
                dataKey={line}
                stroke={colors[idx % colors.length]}
                strokeWidth={2}
                dot={{ r: 3 }}
                activeDot={{ r: 5 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      )}
    </WidgetContainer>
  );
}
