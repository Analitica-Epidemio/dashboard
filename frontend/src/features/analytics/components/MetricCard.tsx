"use client";

import { ArrowDown, ArrowUp, Minus } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { MetricValue } from "@/lib/api/analytics";

interface MetricCardProps {
  title: string;
  metric: MetricValue;
  format?: "number" | "decimal" | "percentage";
  suffix?: string;
  description?: string;
  className?: string;
}

export function MetricCard({
  title,
  metric,
  format = "number",
  suffix,
  description,
  className,
}: MetricCardProps) {
  const formatValue = (value: number): string => {
    switch (format) {
      case "number":
        return Math.round(value).toLocaleString("es-AR");
      case "decimal":
        return value.toFixed(2).replace(".", ",");
      case "percentage":
        return `${value.toFixed(1)}%`;
      default:
        return value.toString();
    }
  };

  const getTrendColor = () => {
    if (!metric.tendencia) return "text-muted-foreground";

    switch (metric.tendencia) {
      case "up":
        return "text-red-600";
      case "down":
        return "text-green-600";
      case "stable":
        return "text-muted-foreground";
      default:
        return "text-muted-foreground";
    }
  };

  const getTrendIcon = () => {
    if (!metric.tendencia) return null;

    switch (metric.tendencia) {
      case "up":
        return <ArrowUp className="h-4 w-4" />;
      case "down":
        return <ArrowDown className="h-4 w-4" />;
      case "stable":
        return <Minus className="h-4 w-4" />;
      default:
        return null;
    }
  };

  const showComparison =
    metric.valor_anterior !== null &&
    metric.diferencia_porcentual !== null &&
    metric.diferencia_absoluta !== null;

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="flex items-baseline gap-2">
            <div className="text-3xl font-bold">
              {formatValue(metric.valor_actual)}
              {suffix && <span className="text-lg ml-1">{suffix}</span>}
            </div>
          </div>

          {showComparison && (
            <div
              className={cn(
                "flex items-center gap-1.5 text-sm font-medium",
                getTrendColor()
              )}
            >
              {getTrendIcon()}
              <span>
                {metric.diferencia_porcentual! > 0 ? "+" : ""}
                {metric.diferencia_porcentual!.toFixed(1)}%
              </span>
              <span className="text-xs text-muted-foreground font-normal">
                (
                {metric.diferencia_absoluta! > 0 ? "+" : ""}
                {formatValue(metric.diferencia_absoluta!)})
              </span>
            </div>
          )}

          {showComparison && (
            <div className="text-xs text-muted-foreground">
              vs. período anterior: {formatValue(metric.valor_anterior!)}
              {suffix}
            </div>
          )}

          {description && (
            <p className="text-xs text-muted-foreground pt-1">{description}</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
