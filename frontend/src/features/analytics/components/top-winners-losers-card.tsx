"use client";

import { ArrowDown, ArrowUp, TrendingDown, TrendingUp } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { TopWinnerLoser } from "@/features/analytics/api";

interface TopWinnersLosersCardProps {
  winners: TopWinnerLoser[];
  losers: TopWinnerLoser[];
  metricType: string;
  className?: string;
}

export function TopWinnersLosersCard({
  winners,
  losers,
  metricType,
  className,
}: TopWinnersLosersCardProps) {
  const renderItem = (item: TopWinnerLoser, isWinner: boolean) => {
    const color = isWinner ? "text-red-600" : "text-green-600";
    const Icon = isWinner ? ArrowUp : ArrowDown;

    return (
      <div
        key={item.entidad_id}
        className="flex items-center justify-between py-2.5 border-b last:border-0"
      >
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium truncate">
            {item.entidad_nombre}
          </p>
          <p className="text-xs text-muted-foreground">
            {Math.round(item.valor_actual)} casos
          </p>
        </div>
        <div className={cn("flex items-center gap-1.5 font-semibold", color)}>
          <Icon className="h-4 w-4" />
          <span className="text-sm">
            {item.diferencia_porcentual > 0 ? "+" : ""}
            {item.diferencia_porcentual.toFixed(1)}%
          </span>
        </div>
      </div>
    );
  };

  return (
    <div className={cn("grid gap-4 md:grid-cols-2", className)}>
      {/* Top Winners */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-red-600" />
            <CardTitle className="text-base">Mayor Aumento</CardTitle>
          </div>
          <p className="text-xs text-muted-foreground">
            {metricType === "departamentos"
              ? "Departamentos"
              : metricType === "tipo_eno"
              ? "Tipos de evento"
              : "Provincias"}{" "}
            con más casos vs período anterior
          </p>
        </CardHeader>
        <CardContent>
          {winners.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-4">
              No hay datos disponibles
            </p>
          ) : (
            <div className="space-y-0">
              {winners.map((item) => renderItem(item, true))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Top Losers */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <TrendingDown className="h-5 w-5 text-green-600" />
            <CardTitle className="text-base">Mayor Disminución</CardTitle>
          </div>
          <p className="text-xs text-muted-foreground">
            {metricType === "departamentos"
              ? "Departamentos"
              : metricType === "tipo_eno"
              ? "Tipos de evento"
              : "Provincias"}{" "}
            con menos casos vs período anterior
          </p>
        </CardHeader>
        <CardContent>
          {losers.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-4">
              No hay datos disponibles
            </p>
          ) : (
            <div className="space-y-0">
              {losers.map((item) => renderItem(item, false))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
