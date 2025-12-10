"use client";

import { WidgetContainer } from "./widget-container";
import { WidgetProps } from "./types";
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from "recharts";

export function PieChartWidget({ widget, data, isLoading, onEdit, onDelete }: WidgetProps) {
  const config = widget.visual_config?.config || {};
  const showLegend = config.show_legend !== false;
  const showLabels = config.show_labels !== false;

  // Parse data
  let chartData: Array<{ name: string; value: number }> = [];

  if (widget.data_config?.source === "manual" && widget.data_config?.manual_data) {
    const manualData = widget.data_config.manual_data as { data?: Array<{ name: string; value: number }> };
    chartData = manualData.data || [];
  } else if (data) {
    if (Array.isArray(data)) {
      // Convert array to pie data format
      chartData = (data as Array<Record<string, unknown>>).map((item) => ({
        name: String(item.name || item.label || "Sin nombre"),
        value: Number(item.value || item.count || item.casos || 0),
      }));
    } else if (typeof data === "object" && "data" in data) {
      const typedData = data as { data: Array<{ name: string; value: number }> };
      chartData = typedData.data;
    }
  }

  const COLORS = [
    "#3b82f6", // blue
    "#ef4444", // red
    "#10b981", // green
    "#f59e0b", // yellow
    "#8b5cf6", // purple
    "#ec4899", // pink
    "#06b6d4", // cyan
    "#f97316", // orange
  ];

  const renderLabel = (entry: { name: string; percent: number }) => {
    return showLabels ? `${entry.name}: ${(entry.percent * 100).toFixed(0)}%` : "";
  };

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
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              labelLine={showLabels}
              label={renderLabel}
              outerRadius="80%"
              fill="#8884d8"
              dataKey="value"
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: "hsl(var(--background))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "6px",
                color: "hsl(var(--foreground))",
              }}
            />
            {showLegend && <Legend />}
          </PieChart>
        </ResponsiveContainer>
      )}
    </WidgetContainer>
  );
}
