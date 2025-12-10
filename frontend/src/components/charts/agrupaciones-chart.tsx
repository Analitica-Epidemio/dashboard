/**
 * AgrupacionesChart - Chart dinámico para agrupaciones de agentes.
 * 
 * Soporta múltiples tipos de visualización:
 * - bar: Barras horizontales por agrupación
 * - stacked_bar: Barras apiladas por semana epidemiológica
 * - line: Líneas temporales por agrupación
 * - table: Tabla con totales y porcentajes
 * 
 * @example
 * <AgrupacionesChart
 *   categoria="respiratorio"
 *   periodoFilter={{ anio: 2025, semana_desde: 1, semana_hasta: 52 }}
 *   onDrillDown={(slug) => setSelectedAgrupacion(slug)}
 * />
 */

"use client";

import { useState, useMemo, useEffect } from "react";
import {
    BarChart,
    Bar,
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    Cell,
} from "recharts";
import {
    BarChart3,
    LineChartIcon,
    Table2,
    Layers,
    ChevronRight,
    Loader2,
} from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { apiClient } from "@/lib/api/client";
import { useAgrupaciones } from "@/features/metricas/hooks/useAgrupaciones";
import type { PeriodoFilter, MetricDataRow, MetricQueryResponse } from "@/features/metricas";

// Types
type ChartType = "bar" | "stacked_bar" | "line" | "table";

interface AgrupacionesChartProps {
    /** Categoría de agrupaciones: "respiratorio", "enterico", etc. */
    categoria: string;
    /** Filtro de período temporal */
    periodoFilter: PeriodoFilter;
    /** Tipo de chart inicial */
    defaultChartType?: ChartType;
    /** Callback al hacer click en una agrupación para drill-down */
    onDrillDown?: (slug: string, nombre: string, color: string) => void;
    /** Título del chart */
    title?: string;
    /** Descripción */
    description?: string;
    /** Altura del chart */
    height?: number;
    /** Metric a consultar */
    metric?: string;
    /** Skip Card wrapper (for embedding in parent Card) */
    noCard?: boolean;
    /** Show YoY comparison (only in table mode) */
    showComparison?: boolean;
    /** Comparison period filter */
    comparisonPeriodoFilter?: PeriodoFilter;
    /** Label for comparison column */
    comparisonLabel?: string;
}

// Chart type selector buttons
const CHART_TYPES: { type: ChartType; icon: React.ElementType; label: string }[] = [
    { type: "bar", icon: BarChart3, label: "Barras" },
    { type: "stacked_bar", icon: Layers, label: "Apiladas" },
    { type: "line", icon: LineChartIcon, label: "Líneas" },
    { type: "table", icon: Table2, label: "Tabla" },
];

interface AgrupacionDataItem {
    slug: string;
    nombre: string;
    color: string;
    valor: number;
    valorYoY?: number;
    delta?: number | null;
}

interface TimeSeriesRow {
    semana: string;
    semanaNum: number;
    [key: string]: string | number;
}

export function AgrupacionesChart({
    categoria,
    periodoFilter,
    defaultChartType = "bar",
    onDrillDown,
    title,
    description,
    height = 350,
    metric = "muestras_positivas",
    noCard = false,
    showComparison = false,
    comparisonPeriodoFilter,
    comparisonLabel = "Anterior",
}: AgrupacionesChartProps) {
    const [chartType, setChartType] = useState<ChartType>(defaultChartType);
    const [agrupacionData, setAgrupacionData] = useState<AgrupacionDataItem[]>([]);
    const [timeSeriesData, setTimeSeriesData] = useState<TimeSeriesRow[]>([]);
    const [isLoadingMetrics, setIsLoadingMetrics] = useState(false);

    // Fetch agrupaciones for this category
    const { data: agrupacionesData, isLoading: loadingAgrupaciones } = useAgrupaciones({
        categoria,
    });

    // Get agrupaciones from response
    const agrupaciones = useMemo(() =>
        agrupacionesData?.items || []
        , [agrupacionesData]);

    // Fetch real metrics for each agrupacion using agrupacion_slug
    useEffect(() => {
        if (!agrupaciones.length || loadingAgrupaciones) return;

        const fetchMetrics = async () => {
            setIsLoadingMetrics(true);

            try {
                // For bar/table view: fetch total per agrupacion
                if (chartType === "bar" || chartType === "table") {
                    // Fetch current period data
                    const currentResults = await Promise.all(
                        agrupaciones.map(async (agrup) => {
                            try {
                                const { data, error } = await apiClient.POST("/api/v1/metricas/query", {
                                    body: {
                                        metric,
                                        dimensions: [],
                                        filters: {
                                            periodo: periodoFilter,
                                            agrupacion_slug: agrup.slug,
                                        },
                                    },
                                });

                                if (error || !data) {
                                    console.warn(`Failed to fetch metrics for ${agrup.slug}`);
                                    return { slug: agrup.slug, nombre: agrup.nombre_corto, color: agrup.color, valor: 0 };
                                }

                                const response = data as MetricQueryResponse;
                                const valor = response.data?.[0]?.valor || 0;

                                return {
                                    slug: agrup.slug,
                                    nombre: agrup.nombre_corto,
                                    color: agrup.color,
                                    valor: typeof valor === 'number' ? valor : 0,
                                };
                            } catch (error) {
                                console.warn(`Error fetching metrics for ${agrup.slug}:`, error);
                                return { slug: agrup.slug, nombre: agrup.nombre_corto, color: agrup.color, valor: 0 };
                            }
                        })
                    );

                    // Fetch comparison data if enabled
                    const comparisonMap = new Map<string, number>();
                    if (showComparison && comparisonPeriodoFilter) {
                        const compResults = await Promise.all(
                            agrupaciones.map(async (agrup) => {
                                try {
                                    const { data, error } = await apiClient.POST("/api/v1/metricas/query", {
                                        body: {
                                            metric,
                                            dimensions: [],
                                            filters: {
                                                periodo: comparisonPeriodoFilter,
                                                agrupacion_slug: agrup.slug,
                                            },
                                        },
                                    });
                                    if (error || !data) return { slug: agrup.slug, valor: 0 };
                                    const response = data as MetricQueryResponse;
                                    const valor = response.data?.[0]?.valor || 0;
                                    return { slug: agrup.slug, valor: typeof valor === 'number' ? valor : 0 };
                                } catch {
                                    return { slug: agrup.slug, valor: 0 };
                                }
                            })
                        );
                        compResults.forEach(r => comparisonMap.set(r.slug, r.valor));
                    }

                    // Merge current and comparison data
                    const results = currentResults.map(item => {
                        const valorYoY = comparisonMap.get(item.slug);
                        const delta = valorYoY && valorYoY > 0 ? ((item.valor - valorYoY) / valorYoY) * 100 : null;
                        return { ...item, valorYoY, delta };
                    });

                    setAgrupacionData(results.sort((a, b) => b.valor - a.valor));
                }

                // For stacked_bar/line view: fetch time series per agrupacion
                if (chartType === "stacked_bar" || chartType === "line") {
                    const semanaDesde = periodoFilter.semana_desde || 1;
                    const semanaHasta = periodoFilter.semana_hasta || 52;

                    // Initialize time series structure
                    const timeSeriesMap: Record<number, TimeSeriesRow> = {};
                    for (let s = semanaDesde; s <= semanaHasta; s++) {
                        timeSeriesMap[s] = { semana: `SE ${s}`, semanaNum: s };
                        agrupaciones.forEach(a => {
                            timeSeriesMap[s][a.slug] = 0;
                        });
                    }

                    // Fetch data for each agrupacion
                    await Promise.all(
                        agrupaciones.map(async (agrup) => {
                            try {
                                const { data, error } = await apiClient.POST("/api/v1/metricas/query", {
                                    body: {
                                        metric,
                                        dimensions: ["SEMANA_EPIDEMIOLOGICA"],
                                        filters: {
                                            periodo: periodoFilter,
                                            agrupacion_slug: agrup.slug,
                                        },
                                    },
                                });

                                if (error || !data) return;

                                const response = data as MetricQueryResponse;
                                (response.data || []).forEach((row: MetricDataRow) => {
                                    const semana = row.semana_epidemiologica;
                                    if (semana != null && timeSeriesMap[semana]) {
                                        timeSeriesMap[semana][agrup.slug] = row.valor || 0;
                                    }
                                });
                            } catch (error) {
                                console.warn(`Error fetching time series for ${agrup.slug}:`, error);
                            }
                        })
                    );

                    const sortedData = Object.values(timeSeriesMap).sort((a, b) => a.semanaNum - b.semanaNum);
                    setTimeSeriesData(sortedData);
                }
            } finally {
                setIsLoadingMetrics(false);
            }
        };

        fetchMetrics();
    }, [agrupaciones, chartType, periodoFilter, metric, loadingAgrupaciones, showComparison, comparisonPeriodoFilter]);

    // isLoading kept for potential future use
    const _ = loadingAgrupaciones || isLoadingMetrics;
    void _;

    // Handle click on bar/line for drill-down
    const handleClick = (data: { slug?: string; nombre?: string; color?: string } | null) => {
        if (onDrillDown && data?.slug) {
            onDrillDown(data.slug, data.nombre || "", data.color || "#666");
        }
    };

    // Render loading state
    if (loadingAgrupaciones) {
        return (
            <Card>
                <CardHeader>
                    <Skeleton className="h-6 w-48" />
                    <Skeleton className="h-4 w-72 mt-2" />
                </CardHeader>
                <CardContent>
                    <Skeleton className="h-[300px] w-full" />
                </CardContent>
            </Card>
        );
    }

    // Render empty state
    if (agrupaciones.length === 0) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle>{title || `Agentes ${categoria}`}</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="flex items-center justify-center h-[200px] text-muted-foreground">
                        No hay agrupaciones configuradas para {categoria}
                    </div>
                </CardContent>
            </Card>
        );
    }

    // Chart content - reused in both modes
    const chartContent = (
        <>
            {/* Loading indicator for metrics */}
            {isLoadingMetrics && (
                <div className="flex items-center justify-center h-[300px]">
                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
            )}

            {/* Bar Chart */}
            {!isLoadingMetrics && chartType === "bar" && (
                <ResponsiveContainer width="100%" height={height}>
                    <BarChart
                        data={agrupacionData}
                        layout="vertical"
                        margin={{ top: 5, right: 30, left: 80, bottom: 5 }}
                    >
                        <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} />
                        <XAxis type="number" />
                        <YAxis
                            type="category"
                            dataKey="nombre"
                            tick={{ fontSize: 12 }}
                            width={70}
                        />
                        <Tooltip
                            formatter={(value: number) => [value.toLocaleString(), "Positivos"]}
                            cursor={{ fill: "hsl(var(--muted))" }}
                        />
                        <Bar
                            dataKey="valor"
                            radius={[0, 4, 4, 0]}
                            cursor="pointer"
                            onClick={handleClick}
                        >
                            {agrupacionData.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            )}

            {/* Stacked Bar Chart */}
            {!isLoadingMetrics && chartType === "stacked_bar" && (
                <ResponsiveContainer width="100%" height={height}>
                    <BarChart
                        data={timeSeriesData}
                        margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                    >
                        <CartesianGrid strokeDasharray="3 3" vertical={false} />
                        <XAxis dataKey="semana" tick={{ fontSize: 11 }} />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        {agrupaciones.map((agrup) => (
                            <Bar
                                key={agrup.slug}
                                dataKey={agrup.slug}
                                name={agrup.nombre_corto}
                                stackId="a"
                                fill={agrup.color}
                                cursor="pointer"
                            />
                        ))}
                    </BarChart>
                </ResponsiveContainer>
            )}

            {/* Line Chart */}
            {!isLoadingMetrics && chartType === "line" && (
                <ResponsiveContainer width="100%" height={height}>
                    <LineChart
                        data={timeSeriesData}
                        margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                    >
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="semana" tick={{ fontSize: 11 }} />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        {agrupaciones.map((agrup) => (
                            <Line
                                key={agrup.slug}
                                type="monotone"
                                dataKey={agrup.slug}
                                name={agrup.nombre_corto}
                                stroke={agrup.color}
                                strokeWidth={2}
                                dot={{ r: 3 }}
                                activeDot={{ r: 5 }}
                            />
                        ))}
                    </LineChart>
                </ResponsiveContainer>
            )}

            {/* Table View */}
            {!isLoadingMetrics && chartType === "table" && (
                <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="border-b">
                                <th className="text-left py-3 px-4 font-medium">Agrupación</th>
                                <th className="text-right py-3 px-4 font-medium">Positivos</th>
                                {showComparison && (
                                    <th className="text-right py-3 px-4 font-medium">{comparisonLabel}</th>
                                )}
                                <th className="text-right py-3 px-4 font-medium">
                                    {showComparison ? "Δ%" : "% del Total"}
                                </th>
                                <th className="w-10"></th>
                            </tr>
                        </thead>
                        <tbody>
                            {agrupacionData.map((row) => {
                                const total = agrupacionData.reduce((sum, r) => sum + r.valor, 0);
                                const pct = total > 0 ? ((row.valor / total) * 100).toFixed(1) : "0.0";
                                return (
                                    <tr
                                        key={row.slug}
                                        className="border-b hover:bg-muted/50 cursor-pointer transition-colors"
                                        onClick={() => onDrillDown?.(row.slug, row.nombre, row.color)}
                                    >
                                        <td className="py-3 px-4">
                                            <div className="flex items-center gap-2">
                                                <div
                                                    className="w-3 h-3 rounded-full"
                                                    style={{ backgroundColor: row.color }}
                                                />
                                                <span className="font-medium">{row.nombre}</span>
                                            </div>
                                        </td>
                                        <td className="text-right py-3 px-4 font-mono">
                                            {row.valor.toLocaleString()}
                                        </td>
                                        {showComparison && (
                                            <td className="text-right py-3 px-4 font-mono text-muted-foreground">
                                                {row.valorYoY?.toLocaleString() ?? "—"}
                                            </td>
                                        )}
                                        <td className="text-right py-3 px-4 font-mono">
                                            {showComparison && row.delta !== null && row.delta !== undefined ? (
                                                <span className={cn(
                                                    row.delta > 0 ? "text-rose-600" :
                                                        row.delta < 0 ? "text-emerald-600" :
                                                            "text-muted-foreground"
                                                )}>
                                                    {row.delta > 0 ? "+" : ""}{row.delta.toFixed(0)}%
                                                </span>
                                            ) : showComparison ? (
                                                <span className="text-muted-foreground">—</span>
                                            ) : (
                                                <span className="text-muted-foreground">{pct}%</span>
                                            )}
                                        </td>
                                        <td className="py-3 px-4">
                                            <ChevronRight className="h-4 w-4 text-muted-foreground" />
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                        <tfoot>
                            <tr className="bg-muted/30 font-medium">
                                <td className="py-3 px-4">Total</td>
                                <td className="text-right py-3 px-4 font-mono">
                                    {agrupacionData.reduce((sum, r) => sum + r.valor, 0).toLocaleString()}
                                </td>
                                {showComparison && (
                                    <td className="text-right py-3 px-4 font-mono text-muted-foreground">
                                        {agrupacionData.reduce((sum, r) => sum + (r.valorYoY || 0), 0).toLocaleString()}
                                    </td>
                                )}
                                <td className="text-right py-3 px-4">
                                    {showComparison ? "—" : "100%"}
                                </td>
                                <td></td>
                            </tr>
                        </tfoot>
                    </table>
                </div>
            )}

            {/* Empty data state */}
            {!isLoadingMetrics && agrupacionData.length === 0 && (chartType === "bar" || chartType === "table") && (
                <div className="flex items-center justify-center h-[200px] text-muted-foreground">
                    No hay datos para el período seleccionado
                </div>
            )}
        </>
    );

    // noCard mode - just render content with optional chart type selector
    if (noCard) {
        return (
            <div>
                {/* Chart type selector when no card */}
                <div className="flex items-center justify-end gap-1 mb-3">
                    {CHART_TYPES.map(({ type, icon: Icon, label }) => (
                        <Button
                            key={type}
                            variant={chartType === type ? "secondary" : "ghost"}
                            size="sm"
                            className={cn(
                                "h-7 px-2",
                                chartType === type && "bg-background shadow-sm"
                            )}
                            onClick={() => setChartType(type)}
                            title={label}
                        >
                            <Icon className="h-4 w-4" />
                        </Button>
                    ))}
                </div>
                {chartContent}
            </div>
        );
    }

    return (
        <Card>
            <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                    <div>
                        <CardTitle className="text-lg flex items-center gap-2">
                            {title || `Agentes ${categoria === "respiratorio" ? "Respiratorios" : "Entéricos"}`}
                            {isLoadingMetrics && <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />}
                        </CardTitle>
                        {description && (
                            <CardDescription className="mt-1">{description}</CardDescription>
                        )}
                    </div>
                    {/* Chart type selector */}
                    <div className="flex items-center gap-1 bg-muted rounded-lg p-1">
                        {CHART_TYPES.map(({ type, icon: Icon, label }) => (
                            <Button
                                key={type}
                                variant={chartType === type ? "secondary" : "ghost"}
                                size="sm"
                                className={cn(
                                    "h-8 px-3",
                                    chartType === type && "bg-background shadow-sm"
                                )}
                                onClick={() => setChartType(type)}
                                title={label}
                            >
                                <Icon className="h-4 w-4" />
                            </Button>
                        ))}
                    </div>
                </div>
            </CardHeader>
            <CardContent>
                {chartContent}
            </CardContent>
        </Card>
    );
}

export default AgrupacionesChart;
