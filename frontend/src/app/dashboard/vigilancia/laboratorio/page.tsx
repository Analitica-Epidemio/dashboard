"use client";

import { useState, useMemo } from "react";
import {
    Activity,
    FlaskConical,
    Percent,
    Microscope,
    TrendingUp,
    TrendingDown,
    Minus,
    BarChart3,
    AreaChart as AreaChartIcon,
    LineChart as LineChartIcon,
    Table2,
} from "lucide-react";

import { AppSidebar } from "@/features/layout/components/app-sidebar";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";

import {
    ChartContainer,
    ChartTooltip,
    ChartTooltipContent,
    ChartConfig,
} from "@/components/ui/chart";
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    BarChart,
    Bar,
    Cell,
    ResponsiveContainer,
    AreaChart,
    Area,
} from "recharts";

import { $api } from "@/lib/api/client";
import { AgenteHeatmap, LaboratorioTable, AgrupacionesChart, AgrupacionDrillDown, ChartTypeSelector, ProvinceMap } from "@/components/charts";
import { ProvinciaSelect, EpidemiologicalPeriodPicker, ComparisonModeSelect, type PeriodoEpidemiologico, type ComparisonMode } from "@/components/filters";
import type { MetricDataRow } from "@/features/metricas";

// Helper: get current epidemiological week
function getCurrentWeek(): number {
    const now = new Date();
    const start = new Date(now.getFullYear(), 0, 1);
    const diff = now.getTime() - start.getTime();
    const oneWeek = 1000 * 60 * 60 * 24 * 7;
    return Math.min(52, Math.max(1, Math.ceil(diff / oneWeek)));
}

// --- Constants ---
const CURRENT_YEAR = new Date().getFullYear();

// Color palette for agentes (consistent, accessible)
const CHART_COLORS = [
    "hsl(217, 91%, 60%)",  // Blue
    "hsl(142, 76%, 36%)",  // Green
    "hsl(0, 84%, 60%)",    // Red
    "hsl(262, 83%, 58%)",  // Purple
    "hsl(38, 92%, 50%)",   // Orange
    "hsl(180, 70%, 45%)",  // Cyan
    "hsl(330, 81%, 60%)",  // Pink
    "hsl(45, 93%, 47%)",   // Yellow
];

const chartConfig = {
    positividad: { label: "% Positividad", color: "hsl(var(--primary))" },
    muestras: { label: "Muestras", color: "hsl(217, 91%, 60%)" },
    positivos: { label: "Positivos", color: "hsl(0, 84%, 60%)" },
} satisfies ChartConfig;

// --- Components ---
interface StatCardProps {
    title: string;
    value: number | string;
    icon: React.ElementType;
    subtitle?: string;
    trend?: { value: number; positive: boolean };
    className?: string;
}

function StatCard({ title, value, icon: Icon, subtitle, trend, className }: StatCardProps) {
    return (
        <Card className={cn("relative overflow-hidden", className)}>
            <CardContent className="p-4">
                <div className="flex items-center justify-between">
                    <div className="space-y-1">
                        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                            {title}
                        </p>
                        <div className="flex items-baseline gap-2">
                            <p className="text-2xl font-bold tabular-nums">
                                {typeof value === 'number' ? value.toLocaleString('es-AR') : value}
                            </p>
                            {trend && (
                                <span className={cn(
                                    "flex items-center text-xs font-medium",
                                    trend.positive ? "text-emerald-600" : "text-rose-600"
                                )}>
                                    {trend.value > 0 ? (
                                        <TrendingUp className="h-3 w-3 mr-0.5" />
                                    ) : trend.value < 0 ? (
                                        <TrendingDown className="h-3 w-3 mr-0.5" />
                                    ) : (
                                        <Minus className="h-3 w-3 mr-0.5" />
                                    )}
                                    {Math.abs(trend.value).toFixed(0)}%
                                </span>
                            )}
                        </div>
                        {subtitle && (
                            <p className="text-xs text-muted-foreground">{subtitle}</p>
                        )}
                    </div>
                    <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                        <Icon className="h-5 w-5 text-primary" />
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}

// ComparisonMode imported from @/components/filters

// --- Main Page ---
export default function VigilanciaLaboratorioPage() {
    // State
    const [periodo, setPeriodo] = useState<PeriodoEpidemiologico>({
        anio_desde: CURRENT_YEAR,
        semana_desde: 1,
        anio_hasta: CURRENT_YEAR,
        semana_hasta: getCurrentWeek(),
    });
    const [selectedProvincia, setSelectedProvincia] = useState("all");
    const [comparisonMode, setComparisonMode] = useState<ComparisonMode>("none");

    // Drill-down state for agrupaciones
    const [drillDownSlug, setDrillDownSlug] = useState<string | null>(null);
    const [drillDownNombre, setDrillDownNombre] = useState<string>("");
    const [drillDownColor, setDrillDownColor] = useState<string>("");

    // Tab state for Grupos de Patógenos
    const [grupoTab, setGrupoTab] = useState("respiratorio");

    // Chart type states
    const [trendChartType, setTrendChartType] = useState<"area" | "line" | "bar">("area");
    const [topAgentesView, setTopAgentesView] = useState<"bar" | "table">("bar");

    // Period filter - reactive to periodo state
    const periodoFilter = periodo;

    // Queries for lab data - connected to filters
    const { data: muestrasData, isLoading: loadingMuestras } = $api.useQuery(
        "post",
        "/api/v1/metricas/query",
        {
            body: {
                metric: "muestras_estudiadas",
                dimensions: ["SEMANA_EPIDEMIOLOGICA"],
                filters: { periodo: periodoFilter },
            },
        }
    );

    const { data: positivosData, isLoading: loadingPositivos } = $api.useQuery(
        "post",
        "/api/v1/metricas/query",
        {
            body: {
                metric: "muestras_positivas",
                dimensions: ["SEMANA_EPIDEMIOLOGICA"],
                filters: { periodo: periodoFilter },
            },
        }
    );

    // YoY comparison period (same weeks, previous year)
    const periodoYoY = useMemo(() => ({
        anio_desde: periodo.anio_desde - 1,
        semana_desde: periodo.semana_desde,
        anio_hasta: periodo.anio_hasta - 1,
        semana_hasta: periodo.semana_hasta,
    }), [periodo]);

    // YoY queries - only fetch if comparison is enabled
    const { data: muestrasYoYData } = $api.useQuery(
        "post",
        "/api/v1/metricas/query",
        {
            body: {
                metric: "muestras_estudiadas",
                dimensions: ["SEMANA_EPIDEMIOLOGICA"],
                filters: { periodo: periodoYoY },
            },
        },
        { enabled: comparisonMode === "yoy" }
    );

    const { data: positivosYoYData } = $api.useQuery(
        "post",
        "/api/v1/metricas/query",
        {
            body: {
                metric: "muestras_positivas",
                dimensions: ["SEMANA_EPIDEMIOLOGICA"],
                filters: { periodo: periodoYoY },
            },
        },
        { enabled: comparisonMode === "yoy" }
    );

    const { data: agenteData, isLoading: loadingAgente } = $api.useQuery(
        "post",
        "/api/v1/metricas/query",
        {
            body: {
                metric: "muestras_positivas",
                dimensions: ["AGENTE_ETIOLOGICO"],
                filters: { periodo: periodoFilter },
            },
        }
    );

    // YoY agente data - for comparison
    const { data: agenteYoYData } = $api.useQuery(
        "post",
        "/api/v1/metricas/query",
        {
            body: {
                metric: "muestras_positivas",
                dimensions: ["AGENTE_ETIOLOGICO"],
                filters: { periodo: periodoYoY },
            },
        },
        { enabled: comparisonMode === "yoy" }
    );

    // Query for heatmap: agente x semana
    const { data: heatmapData, isLoading: loadingHeatmap } = $api.useQuery(
        "post",
        "/api/v1/metricas/query",
        {
            body: {
                metric: "muestras_positivas",
                dimensions: ["AGENTE_ETIOLOGICO", "SEMANA_EPIDEMIOLOGICA"],
                filters: { periodo: periodoFilter },
            },
        }
    );

    // Query for geographic distribution by province
    const { data: provinciaData, isLoading: loadingProvincia } = $api.useQuery(
        "post",
        "/api/v1/metricas/query",
        {
            body: {
                metric: "muestras_positivas",
                dimensions: ["PROVINCIA"],
                filters: { periodo: periodoFilter },
            },
        }
    );

    // Data processing - combined chart data for area/line
    const trendChartData = useMemo(() => {
        if (!muestrasData?.data || !positivosData?.data) return [];

        const muestrasMap: Record<number, number> = {};
        muestrasData.data.forEach((row: MetricDataRow) => {
            if (row.semana_epidemiologica != null) {
                muestrasMap[row.semana_epidemiologica] = row.valor || 0;
            }
        });

        const positivosMap: Record<number, number> = {};
        positivosData.data.forEach((row: MetricDataRow) => {
            if (row.semana_epidemiologica != null) {
                positivosMap[row.semana_epidemiologica] = row.valor || 0;
            }
        });

        const semanas = new Set([
            ...Object.keys(muestrasMap).map(Number),
            ...Object.keys(positivosMap).map(Number),
        ]);

        return Array.from(semanas)
            .sort((a, b) => a - b)
            .map(semana => {
                const muestras = muestrasMap[semana] || 0;
                const positivos = positivosMap[semana] || 0;
                return {
                    semana: `SE ${semana}`,
                    semanaNum: semana,
                    muestras,
                    positivos,
                    positividad: muestras > 0 ? (positivos / muestras) * 100 : 0,
                };
            });
    }, [muestrasData, positivosData]);

    // YoY agente map for comparison
    const agenteYoYMap = useMemo(() => {
        if (!agenteYoYData?.data) return new Map<string, number>();
        const map = new Map<string, number>();
        agenteYoYData.data.forEach((row: MetricDataRow) => {
            const agente = row.agente_etiologico || "Otros";
            map.set(agente, row.valor || 0);
        });
        return map;
    }, [agenteYoYData]);

    // Agente bar chart data - top 8 agents with YoY comparison
    const agenteBarData = useMemo(() => {
        if (!agenteData?.data) return [];
        return agenteData.data
            .map((row: MetricDataRow, idx: number) => {
                const agente = row.agente_etiologico || "Otros";
                const positivos = row.valor || 0;
                const positivosYoY = agenteYoYMap.get(agente) || 0;
                const delta = positivosYoY > 0 ? ((positivos - positivosYoY) / positivosYoY) * 100 : null;
                return {
                    agente,
                    positivos,
                    positivosYoY,
                    delta,
                    fill: CHART_COLORS[idx % CHART_COLORS.length],
                };
            })
            .sort((a, b) => b.positivos - a.positivos)
            .slice(0, 8);
    }, [agenteData, agenteYoYMap]);

    // Table data - last 10 weeks
    const labTableData = useMemo(() => {
        return trendChartData
            .slice()
            .sort((a, b) => b.semanaNum - a.semanaNum)
            .slice(0, 10)
            .map(row => ({
                semana: row.semana,
                muestras: row.muestras,
                totalPositivos: row.positivos,
                positividad: row.positividad,
            }));
    }, [trendChartData]);

    // YoY table data (for comparison)
    const labTableDataYoY = useMemo(() => {
        if (!muestrasYoYData?.data || !positivosYoYData?.data) return [];

        const muestrasMap: Record<number, number> = {};
        muestrasYoYData.data.forEach((row: MetricDataRow) => {
            if (row.semana_epidemiologica != null) {
                muestrasMap[row.semana_epidemiologica] = row.valor || 0;
            }
        });

        const positivosMap: Record<number, number> = {};
        positivosYoYData.data.forEach((row: MetricDataRow) => {
            if (row.semana_epidemiologica != null) {
                positivosMap[row.semana_epidemiologica] = row.valor || 0;
            }
        });

        const semanas = new Set([
            ...Object.keys(muestrasMap).map(Number),
            ...Object.keys(positivosMap).map(Number),
        ]);

        return Array.from(semanas)
            .sort((a, b) => b - a)
            .map(semana => {
                const muestras = muestrasMap[semana] || 0;
                const positivos = positivosMap[semana] || 0;
                return {
                    semana: `SE ${semana}`,
                    muestras,
                    totalPositivos: positivos,
                    positividad: muestras > 0 ? (positivos / muestras) * 100 : 0,
                };
            });
    }, [muestrasYoYData, positivosYoYData]);

    // Heatmap data - top 8 agentes x semanas
    const heatmapChartData = useMemo(() => {
        if (!heatmapData?.data || !agenteBarData.length) return [];

        // Get top 8 agente names
        const topAgentes = new Set(agenteBarData.map(a => a.agente));

        // Filter and format heatmap data
        return (heatmapData.data as Array<{ agente_etiologico?: string; nombre_corto?: string; semana_epidemiologica: number; valor: number }>)
            .filter(row => {
                const agente = row.agente_etiologico || row.nombre_corto || "";
                return topAgentes.has(agente);
            })
            .map(row => ({
                row: row.agente_etiologico || row.nombre_corto || "Otros",
                col: `SE ${row.semana_epidemiologica}`,
                value: row.valor || 0,
            }));
    }, [heatmapData, agenteBarData]);

    // Geographic distribution data
    const provinciaMapData = useMemo(() => {
        if (!provinciaData?.data) return [];
        const rows = provinciaData.data;
        const total = rows.reduce((sum, row: MetricDataRow) => sum + (row.valor || 0), 0);
        return rows
            .map((row: MetricDataRow) => ({
                provincia: row.provincia || "Desconocido",
                valor: row.valor || 0,
                porcentaje: total > 0 ? ((row.valor || 0) / total) * 100 : 0,
            }))
            .sort((a, b) => b.valor - a.valor);
    }, [provinciaData]);

    // KPI calculations
    const totalMuestras = useMemo(() => {
        if (!muestrasData?.data) return 0;
        return muestrasData.data.reduce((sum, row: MetricDataRow) => sum + (row.valor || 0), 0);
    }, [muestrasData]);

    const totalPositivos = useMemo(() => {
        if (!positivosData?.data) return 0;
        return positivosData.data.reduce((sum, row: MetricDataRow) => sum + (row.valor || 0), 0);
    }, [positivosData]);

    const positividad = totalMuestras > 0 ? ((totalPositivos / totalMuestras) * 100).toFixed(1) : "0.0";

    // YoY totals (when comparison is enabled)
    const totalMuestrasYoY = useMemo(() => {
        if (!muestrasYoYData?.data) return 0;
        return muestrasYoYData.data.reduce((sum, row: MetricDataRow) => sum + (row.valor || 0), 0);
    }, [muestrasYoYData]);

    const totalPositivosYoY = useMemo(() => {
        if (!positivosYoYData?.data) return 0;
        return positivosYoYData.data.reduce((sum, row: MetricDataRow) => sum + (row.valor || 0), 0);
    }, [positivosYoYData]);

    const positividadYoY = totalMuestrasYoY > 0 ? (totalPositivosYoY / totalMuestrasYoY) * 100 : 0;

    // Calculate deltas (percentage change YoY)
    const calculateDelta = (current: number, previous: number): { value: number; positive: boolean } | undefined => {
        if (comparisonMode !== "yoy" || previous === 0) return undefined;
        const deltaPercent = ((current - previous) / previous) * 100;
        return { value: deltaPercent, positive: deltaPercent >= 0 }; // more samples = positive
    };

    // For positividad, LOWER is better, so we invert the logic
    const calculatePositividadDelta = (): { value: number; positive: boolean } | undefined => {
        if (comparisonMode !== "yoy" || positividadYoY === 0) return undefined;
        const currentPos = parseFloat(positividad);
        const deltaPercent = ((currentPos - positividadYoY) / positividadYoY) * 100;
        return { value: deltaPercent, positive: deltaPercent <= 0 }; // lower positividad = positive
    };

    const isLoading = loadingMuestras || loadingPositivos || loadingAgente;

    // Drill-down handler
    const handleDrillDown = (slug: string, nombre: string, color: string) => {
        setDrillDownSlug(slug);
        setDrillDownNombre(nombre);
        setDrillDownColor(color);
    };

    return (
        <SidebarProvider>
            <AppSidebar variant="inset" />
            <SidebarInset className="bg-muted/30 min-h-screen overflow-y-auto">
                {/* Header with always-visible filters */}
                <header className="sticky top-0 z-10 bg-background/95 backdrop-blur border-b">
                    <div className="px-6 py-3 flex items-center justify-between">
                        <div>
                            <h1 className="text-xl font-semibold">Vigilancia por Laboratorio</h1>
                            <p className="text-xs text-muted-foreground">
                                Muestras, positividad y agentes detectados
                            </p>
                        </div>
                        <Badge variant="outline" className="text-xs font-mono">
                            {periodo.anio_desde === periodo.anio_hasta
                                ? `SE ${periodo.semana_desde}-${periodo.semana_hasta}/${periodo.anio_desde}`
                                : `SE ${periodo.semana_desde}/${periodo.anio_desde} - ${periodo.semana_hasta}/${periodo.anio_hasta}`
                            }
                        </Badge>
                    </div>

                    {/* Filter bar */}
                    <div className="px-6 py-2 border-t bg-muted/30 flex items-center gap-3 flex-wrap">
                        <EpidemiologicalPeriodPicker
                            value={periodo}
                            onChange={setPeriodo}
                        />

                        <div className="h-6 w-px bg-border" />

                        <ProvinciaSelect
                            value={selectedProvincia}
                            onChange={setSelectedProvincia}
                        />

                        <div className="h-6 w-px bg-border" />

                        {/* Comparison Mode */}
                        <ComparisonModeSelect
                            value={comparisonMode}
                            onChange={setComparisonMode}
                            periodo={periodo}
                        />
                    </div>
                </header>

                {/* Main Content */}
                <div className="p-4 space-y-4 max-w-[1400px] mx-auto">
                    {/* KPI Row - Compact */}
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                        {isLoading ? (
                            <>
                                {[...Array(4)].map((_, i) => (
                                    <Skeleton key={i} className="h-20 rounded-lg" />
                                ))}
                            </>
                        ) : (
                            <>
                                <StatCard
                                    title="Muestras"
                                    value={totalMuestras}
                                    icon={FlaskConical}
                                    subtitle={comparisonMode === "yoy" ? `vs ${periodo.anio_hasta - 1}` : periodo.anio_desde === periodo.anio_hasta ? `Año ${periodo.anio_hasta}` : `${periodo.anio_desde}-${periodo.anio_hasta}`}
                                    trend={calculateDelta(totalMuestras, totalMuestrasYoY)}
                                />
                                <StatCard
                                    title="Positivos"
                                    value={totalPositivos}
                                    icon={Activity}
                                    subtitle={comparisonMode === "yoy" ? `vs ${periodo.anio_hasta - 1}` : "Total detectados"}
                                    trend={calculateDelta(totalPositivos, totalPositivosYoY)}
                                />
                                <StatCard
                                    title="Positividad"
                                    value={`${positividad}%`}
                                    icon={Percent}
                                    subtitle={comparisonMode === "yoy" ? `vs ${positividadYoY.toFixed(1)}% en ${periodo.anio_hasta - 1}` : "Tasa global"}
                                    trend={calculatePositividadDelta()}
                                />
                                <StatCard
                                    title="Agentes"
                                    value={agenteBarData.length}
                                    icon={Microscope}
                                    subtitle="Tipos identificados"
                                />
                            </>
                        )}
                    </div>

                    {/* Charts Grid - 2 columns on large screens */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                        {/* Trend Chart - Full width on mobile, half on desktop */}
                        <Card className="lg:col-span-2 shadow-none">
                            <CardHeader className="pb-2">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <CardTitle className="text-base">Tendencia Semanal</CardTitle>
                                        <CardDescription className="text-xs">
                                            Muestras procesadas y positividad
                                        </CardDescription>
                                    </div>
                                    <ChartTypeSelector
                                        types={[
                                            { type: "area", icon: AreaChartIcon, label: "Área" },
                                            { type: "line", icon: LineChartIcon, label: "Línea" },
                                            { type: "bar", icon: BarChart3, label: "Barras" },
                                        ]}
                                        value={trendChartType}
                                        onChange={(t) => setTrendChartType(t as "area" | "line" | "bar")}
                                    />
                                </div>
                            </CardHeader>
                            <CardContent className="pb-4">
                                {isLoading ? (
                                    <Skeleton className="h-[220px] w-full" />
                                ) : (
                                    <div className="h-[220px]">
                                        <ChartContainer config={chartConfig} className="h-full w-full">
                                            {trendChartType === "bar" ? (
                                                <BarChart data={trendChartData} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
                                                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                                                    <XAxis dataKey="semana" tickLine={false} axisLine={false} tickMargin={8} minTickGap={40} style={{ fontSize: '10px' }} />
                                                    <YAxis yAxisId="left" tickLine={false} axisLine={false} style={{ fontSize: '10px' }} width={45} />
                                                    <YAxis yAxisId="right" orientation="right" tickLine={false} axisLine={false} style={{ fontSize: '10px' }} width={40} domain={[0, 100]} tickFormatter={(v) => `${v}%`} />
                                                    <ChartTooltip content={<ChartTooltipContent />} />
                                                    <Bar yAxisId="left" dataKey="muestras" name="Muestras" fill="hsl(217, 91%, 60%)" radius={[4, 4, 0, 0]} />
                                                    <Line yAxisId="right" dataKey="positividad" name="% Positividad" type="monotone" stroke="hsl(0, 84%, 60%)" strokeWidth={2} dot={false} />
                                                </BarChart>
                                            ) : trendChartType === "line" ? (
                                                <LineChart data={trendChartData} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
                                                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                                                    <XAxis dataKey="semana" tickLine={false} axisLine={false} tickMargin={8} minTickGap={40} style={{ fontSize: '10px' }} />
                                                    <YAxis yAxisId="left" tickLine={false} axisLine={false} style={{ fontSize: '10px' }} width={45} />
                                                    <YAxis yAxisId="right" orientation="right" tickLine={false} axisLine={false} style={{ fontSize: '10px' }} width={40} domain={[0, 100]} tickFormatter={(v) => `${v}%`} />
                                                    <ChartTooltip content={<ChartTooltipContent />} />
                                                    <Line yAxisId="left" dataKey="muestras" name="Muestras" type="monotone" stroke="hsl(217, 91%, 60%)" strokeWidth={2} dot={false} />
                                                    <Line yAxisId="right" dataKey="positividad" name="% Positividad" type="monotone" stroke="hsl(0, 84%, 60%)" strokeWidth={2} dot={false} />
                                                </LineChart>
                                            ) : (
                                                <AreaChart data={trendChartData} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
                                                    <defs>
                                                        <linearGradient id="fillMuestras" x1="0" y1="0" x2="0" y2="1">
                                                            <stop offset="5%" stopColor="hsl(217, 91%, 60%)" stopOpacity={0.3} />
                                                            <stop offset="95%" stopColor="hsl(217, 91%, 60%)" stopOpacity={0} />
                                                        </linearGradient>
                                                    </defs>
                                                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                                                    <XAxis dataKey="semana" tickLine={false} axisLine={false} tickMargin={8} minTickGap={40} style={{ fontSize: '10px' }} />
                                                    <YAxis yAxisId="left" tickLine={false} axisLine={false} style={{ fontSize: '10px' }} width={45} />
                                                    <YAxis yAxisId="right" orientation="right" tickLine={false} axisLine={false} style={{ fontSize: '10px' }} width={40} domain={[0, 100]} tickFormatter={(v) => `${v}%`} />
                                                    <ChartTooltip content={<ChartTooltipContent />} />
                                                    <Area yAxisId="left" dataKey="muestras" name="Muestras" type="monotone" stroke="hsl(217, 91%, 60%)" fill="url(#fillMuestras)" strokeWidth={1.5} />
                                                    <Line yAxisId="right" dataKey="positividad" name="% Positividad" type="monotone" stroke="hsl(0, 84%, 60%)" strokeWidth={2} dot={false} />
                                                </AreaChart>
                                            )}
                                        </ChartContainer>
                                    </div>
                                )}
                            </CardContent>
                        </Card>

                        {/* Top Agentes Chart */}
                        <Card className="shadow-none">
                            <CardHeader className="pb-2">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <CardTitle className="text-base">Top 8 Patógenos Identificados</CardTitle>
                                        <CardDescription className="text-xs">
                                            Los agentes etiológicos con más muestras positivas
                                        </CardDescription>
                                    </div>
                                    <ChartTypeSelector
                                        types={[
                                            { type: "bar", icon: BarChart3, label: "Barras" },
                                            { type: "table", icon: Table2, label: "Tabla" },
                                        ]}
                                        value={topAgentesView}
                                        onChange={(t) => setTopAgentesView(t as "bar" | "table")}
                                    />
                                </div>
                            </CardHeader>
                            <CardContent className="pb-4">
                                {isLoading ? (
                                    <Skeleton className="h-[220px] w-full" />
                                ) : agenteBarData.length === 0 ? (
                                    <div className="h-[220px] flex items-center justify-center text-muted-foreground text-sm">
                                        Sin datos para el período
                                    </div>
                                ) : topAgentesView === "table" ? (
                                    <div className="h-[220px] overflow-auto">
                                        <table className="w-full text-sm">
                                            <thead className="sticky top-0 bg-background border-b">
                                                <tr>
                                                    <th className="text-left py-2 px-3 font-medium text-muted-foreground">Agente</th>
                                                    <th className="text-right py-2 px-3 font-medium text-muted-foreground">Positivos</th>
                                                    {comparisonMode === "yoy" && (
                                                        <th className="text-right py-2 px-3 font-medium text-muted-foreground">{periodo.anio_hasta - 1}</th>
                                                    )}
                                                    <th className="text-right py-2 px-3 font-medium text-muted-foreground">
                                                        {comparisonMode === "yoy" ? "Δ%" : "%"}
                                                    </th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {agenteBarData.map((ag, idx) => {
                                                    const total = agenteBarData.reduce((sum, a) => sum + a.positivos, 0);
                                                    const pct = total > 0 ? ((ag.positivos / total) * 100).toFixed(1) : "0";
                                                    return (
                                                        <tr key={idx} className="border-b border-border/50 hover:bg-muted/50">
                                                            <td className="py-2 px-3">
                                                                <div className="flex items-center gap-2">
                                                                    <div className="w-2 h-2 rounded-full" style={{ backgroundColor: ag.fill }} />
                                                                    <span className="truncate max-w-[140px]" title={ag.agente}>{ag.agente}</span>
                                                                </div>
                                                            </td>
                                                            <td className="text-right py-2 px-3 font-mono">{ag.positivos.toLocaleString()}</td>
                                                            {comparisonMode === "yoy" && (
                                                                <td className="text-right py-2 px-3 font-mono text-muted-foreground">
                                                                    {ag.positivosYoY.toLocaleString()}
                                                                </td>
                                                            )}
                                                            <td className="text-right py-2 px-3 font-mono">
                                                                {comparisonMode === "yoy" && ag.delta !== null ? (
                                                                    <span className={cn(
                                                                        ag.delta > 0 ? "text-rose-600" : ag.delta < 0 ? "text-emerald-600" : "text-muted-foreground"
                                                                    )}>
                                                                        {ag.delta > 0 ? "+" : ""}{ag.delta.toFixed(0)}%
                                                                    </span>
                                                                ) : comparisonMode === "yoy" ? (
                                                                    <span className="text-muted-foreground">—</span>
                                                                ) : (
                                                                    <span className="text-muted-foreground">{pct}%</span>
                                                                )}
                                                            </td>
                                                        </tr>
                                                    );
                                                })}
                                            </tbody>
                                        </table>
                                    </div>
                                ) : (
                                    <div className="h-[220px]">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <BarChart data={agenteBarData} layout="vertical" margin={{ left: 0, right: 10 }}>
                                                <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} />
                                                <XAxis type="number" tickLine={false} axisLine={false} style={{ fontSize: '10px' }} />
                                                <YAxis
                                                    type="category"
                                                    dataKey="agente"
                                                    tickLine={false}
                                                    axisLine={false}
                                                    width={120}
                                                    style={{ fontSize: '9px' }}
                                                    tick={{ fill: 'hsl(var(--foreground))' }}
                                                    tickFormatter={(value) => value.length > 18 ? value.slice(0, 16) + '...' : value}
                                                />
                                                <ChartTooltip />
                                                <Bar dataKey="positivos" radius={[0, 4, 4, 0]}>
                                                    {agenteBarData.map((entry, index) => (
                                                        <Cell key={`cell-${index}`} fill={entry.fill} />
                                                    ))}
                                                </Bar>
                                            </BarChart>
                                        </ResponsiveContainer>
                                    </div>
                                )}
                            </CardContent>
                        </Card>

                        {/* Weekly Table - Compact */}
                        <Card className="shadow-none">
                            <CardHeader className="pb-2">
                                <CardTitle className="text-base">Últimas Semanas</CardTitle>
                                <CardDescription className="text-xs">
                                    Detalle por semana epidemiológica
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="pb-4">
                                {isLoading ? (
                                    <Skeleton className="h-[220px] w-full" />
                                ) : (
                                    <div className="h-[220px] overflow-auto">
                                        <LaboratorioTable
                                            data={labTableData}
                                            compact
                                            showComparison={comparisonMode === "yoy"}
                                            comparisonData={labTableDataYoY}
                                            comparisonLabel={`${periodo.anio_hasta - 1}`}
                                        />
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    </div>

                    {/* Geographic Distribution */}
                    <Card className="shadow-none">
                        <CardHeader className="pb-2">
                            <CardTitle className="text-base">Distribución Geográfica</CardTitle>
                            <CardDescription className="text-xs">
                                Muestras positivas por provincia de residencia
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                                {/* Map */}
                                <div className="h-[350px]">
                                    {loadingProvincia ? (
                                        <Skeleton className="h-full w-full" />
                                    ) : provinciaMapData.length === 0 ? (
                                        <div className="h-full flex items-center justify-center text-sm text-muted-foreground">
                                            Sin datos geográficos disponibles
                                        </div>
                                    ) : (
                                        <ProvinceMap data={provinciaMapData} height={320} />
                                    )}
                                </div>
                                {/* Table */}
                                <div className="h-[350px] overflow-auto">
                                    {loadingProvincia ? (
                                        <Skeleton className="h-full w-full" />
                                    ) : provinciaMapData.length === 0 ? (
                                        <div className="h-full flex items-center justify-center text-sm text-muted-foreground">
                                            Sin datos disponibles
                                        </div>
                                    ) : (
                                        <table className="w-full text-sm">
                                            <thead className="sticky top-0 bg-background border-b">
                                                <tr>
                                                    <th className="text-left py-2 px-3 font-medium text-muted-foreground">Provincia</th>
                                                    <th className="text-right py-2 px-3 font-medium text-muted-foreground">Positivos</th>
                                                    <th className="text-right py-2 px-3 font-medium text-muted-foreground">%</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {provinciaMapData.slice(0, 15).map((prov, idx) => (
                                                    <tr key={idx} className="border-b border-border/50 hover:bg-muted/50">
                                                        <td className="py-2 px-3">{prov.provincia}</td>
                                                        <td className="text-right py-2 px-3 font-mono">{prov.valor.toLocaleString()}</td>
                                                        <td className="text-right py-2 px-3 font-mono text-muted-foreground">{prov.porcentaje.toFixed(1)}%</td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    )}
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Grupos de Patógenos - Card with divider, not nested card */}
                    <Card className="shadow-none">
                        <CardHeader className="pb-3">
                            <div className="flex items-center justify-between">
                                <div>
                                    <CardTitle className="text-base">Grupos de Patógenos</CardTitle>
                                    <CardDescription className="text-xs">
                                        Muestras positivas agrupadas • Clic para ver agentes individuales
                                    </CardDescription>
                                </div>
                                <Tabs value={grupoTab} onValueChange={setGrupoTab}>
                                    <TabsList>
                                        <TabsTrigger value="respiratorio">🫁 Respiratorios</TabsTrigger>
                                        <TabsTrigger value="enterico">🦠 Entéricos</TabsTrigger>
                                    </TabsList>
                                </Tabs>
                            </div>
                        </CardHeader>
                        <div className="border-t px-6 py-4">
                            {grupoTab === "respiratorio" ? (
                                <AgrupacionesChart
                                    categoria="respiratorio"
                                    periodoFilter={periodoFilter}
                                    title=""
                                    description=""
                                    defaultChartType="bar"
                                    height={240}
                                    onDrillDown={handleDrillDown}
                                    noCard
                                    showComparison={comparisonMode === "yoy"}
                                    comparisonPeriodoFilter={periodoYoY}
                                    comparisonLabel={`${periodo.anio_hasta - 1}`}
                                />
                            ) : (
                                <AgrupacionesChart
                                    categoria="enterico"
                                    periodoFilter={periodoFilter}
                                    title=""
                                    description=""
                                    defaultChartType="bar"
                                    height={240}
                                    onDrillDown={handleDrillDown}
                                    noCard
                                    showComparison={comparisonMode === "yoy"}
                                    comparisonPeriodoFilter={periodoYoY}
                                    comparisonLabel={`${periodo.anio_hasta - 1}`}
                                />
                            )}
                        </div>
                    </Card>

                    {/* Heatmap - at bottom */}
                    <Card className="shadow-none">
                        <CardHeader className="pb-2">
                            <CardTitle className="text-base">Mapa de Calor Semanal</CardTitle>
                            <CardDescription className="text-xs">
                                Muestra la intensidad de detección de cada agente por semana epidemiológica.
                                Colores más oscuros = mayor cantidad de positivos.
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            {loadingHeatmap || loadingAgente ? (
                                <Skeleton className="h-[200px] w-full" />
                            ) : heatmapChartData.length === 0 ? (
                                <div className="h-[200px] flex items-center justify-center text-muted-foreground text-sm">
                                    Sin datos para generar heatmap
                                </div>
                            ) : (
                                <AgenteHeatmap
                                    data={heatmapChartData}
                                    colorScale="blue"
                                />
                            )}
                        </CardContent>
                    </Card>
                </div>

                {/* Drill-down Sheet */}
                <AgrupacionDrillDown
                    slug={drillDownSlug}
                    nombre={drillDownNombre}
                    color={drillDownColor}
                    periodoFilter={periodoFilter}
                    open={!!drillDownSlug}
                    onClose={() => setDrillDownSlug(null)}
                />
            </SidebarInset>
        </SidebarProvider>
    );
}
