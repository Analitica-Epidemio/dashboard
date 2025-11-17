"use client";

import { useState, useMemo } from "react";
import { Search, TrendingUp, TrendingDown } from "lucide-react";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/features/layout/components";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { $api } from "@/lib/api/client";
import { DateRangePicker } from "@/features/analytics/components/date-range-picker";
import type { DateRange } from "react-day-picker";
import type { TopWinnerLoser } from "@/features/analytics/api";

type MetricType = "departamentos" | "tipo_eno" | "provincias";

export default function AnalyticsPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [metricType, setMetricType] = useState<MetricType>("departamentos");
  const [dateRange, setDateRange] = useState<DateRange | undefined>();

  const { data: dateRangeResponse } = $api.useQuery(
    'get',
    '/api/v1/analytics/date-range',
    {}
  );

  const maxDate = dateRangeResponse?.data?.fecha_maxima
    ? new Date(dateRangeResponse.data.fecha_maxima)
    : new Date();

  const { data: analyticsResponse, isLoading } = $api.useQuery(
    'get',
    '/api/v1/analytics/top-winners-losers',
    {
      params: {
        query: {
          metric_type: metricType,
          limit: 50,
          period_type: "personalizado",
          fecha_desde: dateRange?.from?.toISOString().split("T")[0],
          fecha_hasta: dateRange?.to?.toISOString().split("T")[0],
        }
      }
    },
    {
      enabled: !!dateRange?.from && !!dateRange?.to
    }
  );

  // Combinar winners y losers en una sola tabla
  const allData = useMemo(() => {
    const data = analyticsResponse?.data as { top_winners?: TopWinnerLoser[], top_losers?: TopWinnerLoser[] } | undefined;
    const winners = data?.top_winners || [];
    const losers = data?.top_losers || [];

    return [...winners, ...losers].sort(
      (a: TopWinnerLoser, b: TopWinnerLoser) =>
        Math.abs(b.diferencia_porcentual) - Math.abs(a.diferencia_porcentual)
    );
  }, [analyticsResponse]);

  // Filtrar por búsqueda
  const filteredData = useMemo(() => {
    if (!searchQuery) return allData;

    const query = searchQuery.toLowerCase();
    return allData.filter((item: TopWinnerLoser) =>
      item.entidad_nombre.toLowerCase().includes(query)
    );
  }, [allData, searchQuery]);

  const getChangeColor = (change: number) => {
    // Verde para disminución (bueno), Rojo para aumento (malo)
    if (change < 0) return "text-green-600 dark:text-green-500";
    if (change > 0) return "text-red-600 dark:text-red-500";
    return "text-muted-foreground";
  };

  const getChangeBgColor = (change: number) => {
    if (change < 0) return "bg-green-50 dark:bg-green-950/20";
    if (change > 0) return "bg-red-50 dark:bg-red-950/20";
    return "bg-muted/20";
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat("es-AR").format(Math.round(num));
  };

  const formatPercent = (num: number) => {
    const formatted = Math.abs(num).toFixed(2);
    return num > 0 ? `+${formatted}%` : num < 0 ? `${formatted}%` : "0.00%";
  };

  return (
    <SidebarProvider
      style={
        {
          "--sidebar-width": "calc(var(--spacing) * 72)",
          "--header-height": "calc(var(--spacing) * 12)",
        } as React.CSSProperties
      }
    >
      <AppSidebar variant="inset" />
      <SidebarInset>
        <div className="flex flex-col min-h-screen overflow-y-auto bg-muted">
          <div className="flex-1 w-full mx-auto px-6 py-8 max-w-7xl space-y-6">
            {/* Header */}
            <div className="mb-8">
              <div className="flex items-center gap-3 mb-2">
                <TrendingUp className="w-5 h-5 text-muted-foreground" />
                <h1 className="text-2xl font-semibold">
                  Análisis de Variaciones
                </h1>
              </div>
              <p className="text-sm text-muted-foreground">
                Monitoreo de cambios en casos epidemiológicos por región y tipo de evento
              </p>
            </div>

        {/* Filtros */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-col gap-4">
              <div className="flex flex-col lg:flex-row gap-4 lg:items-end">
                {/* Búsqueda */}
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Buscar por nombre..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-9"
                  />
                </div>

                {/* Tipo de métrica */}
                <Select
                  value={metricType}
                  onValueChange={(value) => setMetricType(value as MetricType)}
                >
                  <SelectTrigger className="w-full md:w-[200px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="departamentos">Departamentos</SelectItem>
                    <SelectItem value="provincias">Provincias</SelectItem>
                    <SelectItem value="tipo_eno">Tipo de Evento</SelectItem>
                  </SelectContent>
                </Select>

                {/* Date Range Picker */}
                <DateRangePicker
                  dateRange={dateRange}
                  onDateRangeChange={setDateRange}
                  maxDate={maxDate}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Stats Cards */}
        <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Registros
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{filteredData.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Con Aumento
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <div className="text-2xl font-bold text-red-600">
                {filteredData.filter((d) => d.diferencia_porcentual > 0).length}
              </div>
              <TrendingUp className="h-5 w-5 text-red-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Con Disminución
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <div className="text-2xl font-bold text-green-600">
                {filteredData.filter((d) => d.diferencia_porcentual < 0).length}
              </div>
              <TrendingDown className="h-5 w-5 text-green-600" />
            </div>
          </CardContent>
        </Card>
        </div>

        {/* Tabla Principal */}
        <Card>
          <CardHeader>
            <CardTitle>
              {metricType === "departamentos"
                ? "Departamentos"
                : metricType === "tipo_eno"
                ? "Tipos de Evento"
                : "Provincias"}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-3">
                {[...Array(10)].map((_, i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            ) : filteredData.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-muted-foreground">No hay datos disponibles</p>
              </div>
            ) : (
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-[50px]">#</TableHead>
                      <TableHead>Nombre</TableHead>
                      <TableHead className="text-right">Anterior</TableHead>
                      <TableHead className="text-right">Actual</TableHead>
                      <TableHead className="text-right">Diferencia</TableHead>
                      <TableHead className="text-right w-[140px]">
                        Cambio %
                      </TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredData.map((item, index) => {
                      const change = item.diferencia_porcentual;
                      const isIncrease = change > 0;
                      const isDecrease = change < 0;

                      return (
                        <TableRow
                          key={item.entidad_id}
                          className="hover:bg-muted/50 transition-colors"
                        >
                          <TableCell className="font-medium text-muted-foreground">
                            {index + 1}
                          </TableCell>
                          <TableCell className="font-medium">
                            {item.entidad_nombre}
                          </TableCell>
                          <TableCell className="text-right tabular-nums">
                            {formatNumber(item.valor_anterior)}
                          </TableCell>
                          <TableCell className="text-right tabular-nums font-semibold">
                            {formatNumber(item.valor_actual)}
                          </TableCell>
                          <TableCell
                            className={cn(
                              "text-right tabular-nums font-medium",
                              getChangeColor(change)
                            )}
                          >
                            {change > 0 ? "+" : ""}
                            {formatNumber(item.diferencia_absoluta)}
                          </TableCell>
                          <TableCell className="text-right">
                            <div className="flex items-center justify-end gap-2">
                              <Badge
                                variant="secondary"
                                className={cn(
                                  "tabular-nums font-semibold",
                                  getChangeBgColor(change),
                                  getChangeColor(change)
                                )}
                              >
                                {isIncrease && (
                                  <TrendingUp className="h-3 w-3 mr-1" />
                                )}
                                {isDecrease && (
                                  <TrendingDown className="h-3 w-3 mr-1" />
                                )}
                                {formatPercent(change)}
                              </Badge>
                            </div>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>
          </div>
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
