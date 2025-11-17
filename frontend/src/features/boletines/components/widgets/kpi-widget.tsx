"use client";

import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { WidgetContainer } from "./widget-container";
import { WidgetProps } from "./types";
import { cn } from "@/lib/utils";

export function KPIWidget({ widget, data, isLoading, onEdit, onDelete }: WidgetProps) {
  const config = widget.visual_config?.config || {};
  const format = config.format || "number";
  const color = config.color || "blue";

  // Parse data from manual or query source
  let value = 0;
  let label = widget.title || "KPI";
  let comparison: { value: number; trend: "up" | "down" | "neutral" } | null = null;

  // Type narrowing: check if this is a KPI widget
  if (widget.type === "kpi") {
    const kpiConfig = widget.data_config;

    if (kpiConfig.source === "manual" && kpiConfig.manual_data) {
      value = kpiConfig.manual_data.value;
      label = kpiConfig.manual_data.label ?? label;
      if (kpiConfig.manual_data.comparison) {
        comparison = kpiConfig.manual_data.comparison;
      }
    }
  }

  // Fallback to data prop if provided (from query source)
  if (data && typeof data === "object" && !Array.isArray(data)) {
    const dataValue = (data as Record<string, unknown>).value;
    if (typeof dataValue === "number") {
      value = dataValue;
    }
    const dataComparison = (data as Record<string, unknown>).comparison;
    if (dataComparison && typeof dataComparison === "object") {
      comparison = dataComparison as { value: number; trend: "up" | "down" | "neutral" };
    }
  } else if (typeof data === "number") {
    value = data;
  }

  const formatValue = (val: number) => {
    switch (format) {
      case "number":
        return val.toLocaleString("es-AR");
      case "percentage":
        return `${val.toFixed(1)}%`;
      case "decimal":
        return val.toFixed(2);
      default:
        return val.toString();
    }
  };

  const colorClasses = {
    blue: "text-blue-600 dark:text-blue-400",
    red: "text-red-600 dark:text-red-400",
    green: "text-green-600 dark:text-green-400",
    yellow: "text-yellow-600 dark:text-yellow-400",
    purple: "text-purple-600 dark:text-purple-400",
  };

  return (
    <WidgetContainer
      title={widget.title}
      showTitle={widget.visual_config?.show_title}
      isLoading={isLoading}
      onEdit={onEdit}
      onDelete={onDelete}
    >
      <div className="flex flex-col items-center justify-center h-full">
        <div className={cn("text-4xl font-bold", colorClasses[color as keyof typeof colorClasses] || colorClasses.blue)}>
          {formatValue(value)}
        </div>
        {label && <div className="text-sm text-muted-foreground mt-2">{label}</div>}

        {comparison && (
          <div className="flex items-center gap-1 mt-2">
            {comparison.trend === "up" && (
              <>
                <TrendingUp className="w-4 h-4 text-green-600" />
                <span className="text-sm text-green-600">+{comparison.value}%</span>
              </>
            )}
            {comparison.trend === "down" && (
              <>
                <TrendingDown className="w-4 h-4 text-red-600" />
                <span className="text-sm text-red-600">{comparison.value}%</span>
              </>
            )}
            {comparison.trend === "neutral" && (
              <>
                <Minus className="w-4 h-4 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">{comparison.value}%</span>
              </>
            )}
          </div>
        )}
      </div>
    </WidgetContainer>
  );
}
