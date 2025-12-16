"use client";

import { useState, useMemo } from "react";
import {
    Activity,
    AlertTriangle,
    BarChart3,
    AreaChart as AreaChartIcon,
    LineChart as LineChartIcon,
    TrendingUp,
    ArrowUpRight,
    ArrowDownRight,
} from "lucide-react";

import { AppSidebar } from "@/features/layout/components/app-sidebar";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

import {
    ChartContainer,
    ChartTooltip,
    ChartTooltipContent,
    ChartLegendContent,
    ChartConfig,
} from "@/components/ui/chart";
import {
    ComposedChart,
    Line,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Legend,
    PieChart,
    Pie,
    Cell,
    Bar,
    ResponsiveContainer,
} from "recharts";

import { $api } from "@/lib/api/client";
import { ProvinceMap, TopEventosTable, PyramidChart, ChartTypeSelector } from "@/components/charts";
import { ProvinciaSelect, EpidemiologicalPeriodPicker, ComparisonModeSelect, type PeriodoEpidemiologico, type ComparisonMode } from "@/components/filters";
import type { MetricDataRow, MetricQueryResponse } from "@/features/metricas";

// Helper: get current epidemiological week
function getCurrentWeek(): number {
    const now = new Date();
    const start = new Date(now.getFullYear(), 0, 1);
    const diff = now.getTime() - start.getTime();
    const oneWeek = 1000 * 60 * 60 * 24 * 7;
    return Math.ceil(diff / oneWeek);
}

// --- Constants ---
const CURRENT_YEAR = new Date().getFullYear();

// ComparisonMode imported from @/components/filters

const CHART_COLORS = {
    exito: "hsl(142 76% 36%)",      // Green
    seguridad: "hsl(47 96% 53%)",   // Yellow
    alerta: "hsl(24 95% 53%)",      // Orange
    brote: "hsl(0 84% 60%)",        // Red
};

const corredorConfig = {
    exito: { label: "Zona Éxito (P25)", color: CHART_COLORS.exito },
    seguridad: { label: "Zona Seguridad (P50)", color: CHART_COLORS.seguridad },
    alerta: { label: "Zona Alerta (P75)", color: CHART_COLORS.alerta },
    brote: { label: "Zona Brote", color: CHART_COLORS.brote },
    casos_actual: { label: "Casos Actuales", color: "hsl(var(--foreground))" },
} satisfies ChartConfig;

const PIE_COLORS = [
    "hsl(217 91% 60%)",
    "hsl(142 76% 36%)",
    "hsl(47 96% 53%)",
    "hsl(24 95% 53%)",
    "hsl(0 84% 60%)",
    "hsl(262 83% 58%)",
];

// --- Types ---
interface KpiProps {
    title: string;
    value: number | string;
    icon: React.ElementType;
    trend?: { value: number; isPositive: boolean };
    trendLabel?: string;
    variant?: "default" | "warning" | "danger" | "success";
    description?: string;
}

// --- Components ---
function KpiCard({ title, value, icon: Icon, trend, trendLabel, variant = "default", description }: KpiProps) {
    const colorMap = {
        default: "bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400",
        success: "bg-emerald-50 text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-400",
        warning: "bg-amber-50 text-amber-700 dark:bg-amber-900/20 dark:text-amber-400",
        danger: "bg-rose-50 text-rose-700 dark:bg-rose-900/20 dark:text-rose-400",
    };

    return (
        <Card className="shadow-sm border-l-4" style={{
            borderLeftColor: variant === 'danger' ? '#e11d48' :
                variant === 'warning' ? '#f59e0b' :
                    variant === 'success' ? '#10b981' : '#3b82f6'
        }}>
            <CardContent className="p-4 flex items-start justify-between">
                <div>
                    <p className="text-sm font-medium text-muted-foreground">{title}</p>
                    <div className="mt-2 flex items-baseline gap-2">
                        <span className="text-3xl font-bold tracking-tight">
                            {typeof value === 'number' ? value.toLocaleString() : value}
                        </span>
                    </div>
                    {trend && (
                        <div className={cn("mt-1 flex items-center text-xs font-medium",
                            trend.isPositive ? "text-rose-600" : "text-emerald-600"
                        )}>
                            {trend.isPositive ? <ArrowUpRight className="h-3 w-3 mr-1" /> : <ArrowDownRight className="h-3 w-3 mr-1" />}
                            {Math.abs(trend.value)}% {trendLabel || "vs año anterior"}
                        </div>
                    )}
                    {description && <p className="mt-1 text-xs text-muted-foreground">{description}</p>}
                </div>
                <div className={cn("p-2 rounded-lg", colorMap[variant])}>
                    <Icon className="h-5 w-5" />
                </div>
            </CardContent>
        </Card>
    );
}

// --- Main Page ---
export default function VigilanciaClinicaPage() {
    // State
    const [periodo, setPeriodo] = useState<PeriodoEpidemiologico>({
        anio_desde: CURRENT_YEAR,
        semana_desde: 1,
        anio_hasta: CURRENT_YEAR,
        semana_hasta: getCurrentWeek(),
    });
    const [selectedProvincia, setSelectedProvincia] = useState("all");
    const [comparisonMode, setComparisonMode] = useState<ComparisonMode>("none");
    const [chartType, setChartType] = useState<string>("area");

    // Period filter
    const periodoFilter = useMemo(() => ({
        anio_desde: periodo.anio_desde,
        semana_desde: periodo.semana_desde,
        anio_hasta: periodo.anio_hasta,
        semana_hasta: periodo.semana_hasta,
        ...(selectedProvincia !== "all" && { provincia_nombre: selectedProvincia }),
    }), [periodo, selectedProvincia]);

    // YoY period for comparison (same weeks, previous year)
    const yoyPeriodoFilter = useMemo(() => ({
        anio_desde: periodo.anio_desde - 1,
        semana_desde: periodo.semana_desde,
        anio_hasta: periodo.anio_hasta - 1,
        semana_hasta: periodo.semana_hasta,
        ...(selectedProvincia !== "all" && { provincia_nombre: selectedProvincia }),
    }), [periodo, selectedProvincia]);

    // Build filters object
    const buildFilters = (extras: Record<string, unknown> = {}) => ({
        periodo: periodoFilter,
        ...extras,
    });

    // Queries - all now respect selectedEventIds filter
    const { data: corredorData, isLoading: loadingCorredor } = $api.useQuery("post", "/api/v1/metricas/query", {
        body: {
            metric: "casos_clinicos",
            dimensions: ["SEMANA_EPIDEMIOLOGICA", "ANIO_EPIDEMIOLOGICO"],
            filters: buildFilters({ comparar_con: "yoy" }),
            compute: "corredor_endemico",
        },
    });

    // Query de grupo etario - actualmente no usado pero disponible para futura expansión
    $api.useQuery("post", "/api/v1/metricas/query", {
        body: {
            metric: "casos_clinicos",
            dimensions: ["GRUPO_ETARIO"],
            filters: buildFilters(),
        },
    });

    const { data: eventosData, isLoading: loadingEventos } = $api.useQuery("post", "/api/v1/metricas/query", {
        body: {
            metric: "casos_clinicos",
            dimensions: ["TIPO_EVENTO"],
            filters: buildFilters(),
        },
    });

    // Query for Pyramid (SEXO + GRUPO_ETARIO)
    const { data: pyramidData, isLoading: loadingPyramid } = $api.useQuery("post", "/api/v1/metricas/query", {
        body: {
            metric: "casos_clinicos",
            dimensions: ["SEXO", "GRUPO_ETARIO"],
            filters: buildFilters(),
        },
    });

    // Query for Province Map
    const { data: provinciaData, isLoading: loadingProvincia } = $api.useQuery("post", "/api/v1/metricas/query", {
        body: {
            metric: "casos_clinicos",
            dimensions: ["PROVINCIA"],
            filters: buildFilters(),
        },
    });

    // Query for Events with Comparison (for table with variation)
    const { data: eventosCompData, isLoading: loadingEventosComp } = $api.useQuery("post", "/api/v1/metricas/query", {
        body: {
            metric: "casos_clinicos",
            dimensions: ["TIPO_EVENTO"],
            filters: buildFilters({ comparar_con: "yoy" }),
        },
    });

    // YoY Query - fetch previous year data when comparison is on
    const { data: yoyData } = $api.useQuery("post", "/api/v1/metricas/query", {
        body: {
            metric: "casos_clinicos",
            dimensions: ["SEMANA_EPIDEMIOLOGICA"],
            filters: { periodo: yoyPeriodoFilter },
        },
    }, {
        enabled: comparisonMode === "yoy",
    });

    // Delta calculation helper
    const calculateDelta = (current: number, previous: number): number | null => {
        if (previous === 0 || !previous) return null;
        return Math.round(((current - previous) / previous) * 100);
    };

    // Data processing
    const corredorWarnings = useMemo(() => {
        const data = corredorData as MetricQueryResponse | undefined;
        return data?.metadata?.warnings || [];
    }, [corredorData]);

    const corredorChartData = useMemo(() => {
        if (!corredorData?.data || !Array.isArray(corredorData.data)) return [];

        return corredorData.data.map((row: MetricDataRow) => {
            const p25 = row.zona_exito ?? 0;
            const p50 = row.zona_seguridad ?? 0;
            const p75 = row.zona_alerta ?? 0;

            return {
                semana: row.semana_epidemiologica ?? 0,
                label: `SE ${row.semana_epidemiologica}`,
                p25,
                p50,
                p75,
                casos_actual: row.valor_actual ?? 0,
                exito: p25,
                seguridad: Math.max(0, p50 - p25),
                alerta: Math.max(0, p75 - p50),
                brote: 0,
                corredor_valido: row.corredor_valido,
            };
        }).sort((a, b) => a.semana - b.semana);
    }, [corredorData]);

    const eventoPieData = useMemo(() => {
        if (!eventosData?.data) return [];
        return eventosData.data
            .map((row: MetricDataRow, index: number) => ({
                name: row.tipo_evento || "Otros",
                value: row.valor || 0,
                fill: PIE_COLORS[index % PIE_COLORS.length],
            }))
            .sort((a, b) => b.value - a.value)
            .slice(0, 6);
    }, [eventosData]);

    // Pyramid data processing (SEXO + GRUPO_ETARIO)
    const pyramidChartData = useMemo(() => {
        if (!pyramidData?.data) return [];
        const grouped: Record<string, { masculino: number; femenino: number }> = {};

        pyramidData.data.forEach((row: MetricDataRow) => {
            const grupo = row.grupo_etario || "Desconocido";
            const sexo = (row.sexo || "").toUpperCase();
            const valor = row.valor || 0;

            if (!grouped[grupo]) {
                grouped[grupo] = { masculino: 0, femenino: 0 };
            }
            if (sexo === "M" || sexo === "MASCULINO") {
                grouped[grupo].masculino += valor;
            } else if (sexo === "F" || sexo === "FEMENINO") {
                grouped[grupo].femenino += valor;
            }
        });

        return Object.entries(grouped).map(([grupo, vals]) => ({
            grupo,
            masculino: vals.masculino,
            femenino: vals.femenino,
        }));
    }, [pyramidData]);

    // Provincia map data
    const provinciaMapData = useMemo(() => {
        if (!provinciaData?.data) return [];
        const rows = provinciaData.data;
        const total = rows.reduce((sum, row: MetricDataRow) => sum + (row.valor || 0), 0);
        return rows.map((row: MetricDataRow) => ({
            provincia: row.provincia || "Desconocido",
            valor: row.valor || 0,
            porcentaje: total > 0 ? ((row.valor || 0) / total) * 100 : 0,
        }));
    }, [provinciaData]);

    // Top Eventos table data (with comparison)
    const topEventosData = useMemo(() => {
        if (!eventosCompData?.data) return [];
        return eventosCompData.data
            .map((row: MetricDataRow) => ({
                evento: row.tipo_evento || "Otros",
                casos: row.valor_actual || row.valor || 0,
                variacion: row.valor_anterior && row.valor_anterior > 0
                    ? (((row.valor_actual || row.valor || 0) - row.valor_anterior) / row.valor_anterior) * 100
                    : undefined,
            }))
            .sort((a, b) => b.casos - a.casos)
            .slice(0, 6);
    }, [eventosCompData]);

    // KPI calculations
    const totalCasos = useMemo(() => {
        return corredorChartData.reduce((sum, d) => sum + (d.casos_actual || 0), 0);
    }, [corredorChartData]);

    const promedioSemanal = useMemo(() => {
        const semanas = corredorChartData.filter(d => d.casos_actual > 0).length;
        return semanas > 0 ? Math.round(totalCasos / semanas) : 0;
    }, [corredorChartData, totalCasos]);

    // YoY total from comparison query
    const yoyTotalCasos = useMemo(() => {
        if (!yoyData?.data || !Array.isArray(yoyData.data)) return 0;
        return yoyData.data.reduce((sum, d: MetricDataRow) => sum + (d.valor || 0), 0);
    }, [yoyData]);

    // Calculate trend (last 4 weeks vs previous 4 weeks)
    const trend4Weeks = useMemo(() => {
        const currentWeek = getCurrentWeek();
        const last4 = corredorChartData.filter(d => d.semana > currentWeek - 4 && d.semana <= currentWeek);
        const prev4 = corredorChartData.filter(d => d.semana > currentWeek - 8 && d.semana <= currentWeek - 4);

        const sumLast = last4.reduce((s, d) => s + (d.casos_actual || 0), 0);
        const sumPrev = prev4.reduce((s, d) => s + (d.casos_actual || 0), 0);

        return calculateDelta(sumLast, sumPrev);
    }, [corredorChartData]);

    // YoY delta
    const yoyDelta = useMemo(() => {
        if (comparisonMode !== "yoy" || yoyTotalCasos === 0) return null;
        return calculateDelta(totalCasos, yoyTotalCasos);
    }, [totalCasos, yoyTotalCasos, comparisonMode]);

    return (
        <SidebarProvider>
            <AppSidebar variant="inset" />
            <SidebarInset className="bg-muted/10 h-screen overflow-hidden flex flex-col">
                {/* Header with Filter Bar */}
                <header className="sticky top-0 z-10 bg-background/95 backdrop-blur border-b">
                    <div className="px-6 py-3 flex items-center justify-between">
                        <div>
                            <h1 className="text-2xl font-bold">Vigilancia Clínica</h1>
                            <p className="text-sm text-muted-foreground">
                                Síndromes respiratorios (ETI, IRAG, Neumonía, Bronquiolitis)
                            </p>
                        </div>
                        <Badge variant="outline" className="text-xs font-mono">
                            {periodo.anio_desde === periodo.anio_hasta
                                ? `SE ${periodo.semana_desde}-${periodo.semana_hasta}/${periodo.anio_desde}`
                                : `SE ${periodo.semana_desde}/${periodo.anio_desde} - ${periodo.semana_hasta}/${periodo.anio_hasta}`
                            }
                        </Badge>
                    </div>

                    {/* Filter Bar */}
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

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-6 space-y-6 max-w-[1600px] mx-auto w-full">
                    {/* KPIs */}
                    <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        {loadingCorredor ? (
                            <>
                                {[...Array(4)].map((_, i) => (
                                    <Skeleton key={i} className="h-[100px] rounded-xl" />
                                ))}
                            </>
                        ) : (
                            <>
                                <KpiCard
                                    title="Total Casos"
                                    value={totalCasos}
                                    icon={Activity}
                                    variant="default"
                                    description={periodo.anio_desde === periodo.anio_hasta ? `Acumulado ${periodo.anio_hasta}` : `Acumulado ${periodo.anio_desde}-${periodo.anio_hasta}`}
                                />
                                <KpiCard
                                    title="Promedio Semanal"
                                    value={promedioSemanal}
                                    icon={BarChart3}
                                    variant="default"
                                    description="Casos por semana"
                                />
                                <KpiCard
                                    title="Tendencia"
                                    value={trend4Weeks !== null ? `${trend4Weeks > 0 ? '+' : ''}${trend4Weeks}%` : "-"}
                                    icon={TrendingUp}
                                    variant={!trend4Weeks ? "default" : trend4Weeks > 0 ? "warning" : "success"}
                                    description="Últimas 4 semanas"
                                />
                                <KpiCard
                                    title="vs Año Anterior"
                                    value={yoyTotalCasos > 0 ? yoyTotalCasos.toLocaleString() : "-"}
                                    icon={TrendingUp}
                                    trend={yoyDelta !== null ? { value: Math.abs(yoyDelta), isPositive: yoyDelta > 0 } : undefined}
                                    variant={!yoyDelta ? "default" : yoyDelta > 0 ? "danger" : "success"}
                                    description={comparisonMode === "yoy" ? `Año ${periodo.anio_hasta - 1}` : "Comparación desactivada"}
                                />
                            </>
                        )}
                    </section>

                    {/* Main Chart: Corredor Endémico */}
                    <Card className="shadow-none">
                        <CardHeader>
                            <div className="flex items-center justify-between">
                                <div>
                                    <CardTitle>Corredor Endémico</CardTitle>
                                    <CardDescription>
                                        Casos {periodo.anio_hasta} vs percentiles históricos (P25, P50, P75)
                                    </CardDescription>
                                </div>
                                <div className="flex items-center gap-2">
                                    <ChartTypeSelector
                                        types={[
                                            { type: 'area', icon: AreaChartIcon, label: 'Área' },
                                            { type: 'line', icon: LineChartIcon, label: 'Línea' },
                                            { type: 'bar', icon: BarChart3, label: 'Barras' },
                                        ]}
                                        value={chartType}
                                        onChange={setChartType}
                                    />
                                    <Badge variant="outline" className="font-mono">SE 1 - 52</Badge>
                                </div>
                            </div>
                        </CardHeader>
                        <CardContent>
                            {loadingCorredor ? (
                                <Skeleton className="h-[400px] w-full" />
                            ) : (
                                <>
                                    {corredorWarnings.length > 0 && (
                                        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mb-4 flex items-start gap-3">
                                            <AlertTriangle className="h-5 w-5 text-amber-600 shrink-0" />
                                            <div>
                                                <h4 className="text-sm font-medium text-amber-800">Datos históricos insuficientes</h4>
                                                <p className="text-xs text-amber-700 mt-1">{corredorWarnings[0]}</p>
                                            </div>
                                        </div>
                                    )}
                                    <div className="h-[400px]">
                                        <ChartContainer config={corredorConfig} className="h-full w-full">
                                    <ComposedChart data={corredorChartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                                        <XAxis
                                            dataKey="label"
                                            tickLine={false}
                                            axisLine={false}
                                            tickMargin={8}
                                            minTickGap={30}
                                            style={{ fontSize: '12px' }}
                                        />
                                        <YAxis
                                            tickLine={false}
                                            axisLine={false}
                                            style={{ fontSize: '12px' }}
                                            width={50}
                                        />
                                        <ChartTooltip content={<ChartTooltipContent indicator="line" />} />

                                        {/* Historical Zones (stacked areas) */}
                                        <Area dataKey="brote" type="monotone" fill={CHART_COLORS.brote} stroke="none" fillOpacity={0.2} stackId="zones" />
                                        <Area dataKey="alerta" type="monotone" fill={CHART_COLORS.alerta} stroke="none" fillOpacity={0.2} stackId="zones" />
                                        <Area dataKey="seguridad" type="monotone" fill={CHART_COLORS.seguridad} stroke="none" fillOpacity={0.2} stackId="zones" />
                                        <Area dataKey="exito" type="monotone" fill={CHART_COLORS.exito} stroke="none" fillOpacity={0.2} stackId="zones" />

                                        {/* Current Year */}
                                        {chartType === 'bar' && (
                                            <Bar
                                                dataKey="casos_actual"
                                                name={`Casos ${periodo.anio_hasta}`}
                                                fill="hsl(var(--foreground))"
                                                fillOpacity={0.8}
                                                radius={[4, 4, 0, 0]}
                                                barSize={8}
                                                isAnimationActive={false}
                                            />
                                        )}
                                        {chartType === 'line' && (
                                            <Line
                                                dataKey="casos_actual"
                                                name={`Casos ${periodo.anio_hasta}`}
                                                type="monotone"
                                                stroke="#1f2937"
                                                strokeWidth={2.5}
                                                dot={{ r: 3, fill: "#1f2937", strokeWidth: 0 }}
                                                activeDot={{ r: 5, fill: "#1f2937", strokeWidth: 0 }}
                                                connectNulls={true}
                                                isAnimationActive={false}
                                            />
                                        )}
                                        {chartType === 'area' && (
                                            <Area
                                                dataKey="casos_actual"
                                                name={`Casos ${periodo.anio_hasta}`}
                                                type="monotone"
                                                stroke="hsl(var(--foreground))"
                                                fill="hsl(var(--foreground))"
                                                fillOpacity={0.1}
                                                strokeWidth={2.5}
                                                activeDot={{ r: 5, strokeWidth: 2 }}
                                                connectNulls={true}
                                                isAnimationActive={false}
                                            />
                                        )}

                                            <Legend content={<ChartLegendContent />} />
                                        </ComposedChart>
                                    </ChartContainer>
                                    </div>
                                </>
                            )}
                        </CardContent>
                    </Card>

                    {/* Secondary Charts */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* Distribución por Evento */}
                        <Card className="shadow-none">
                            <CardHeader>
                                <CardTitle className="text-base">Distribución por Evento</CardTitle>
                                <CardDescription>Top 6 eventos notificados</CardDescription>
                            </CardHeader>
                            <CardContent>
                                <div className="h-[300px]">
                                    {loadingEventos ? (
                                        <Skeleton className="h-full w-full" />
                                    ) : (
                                        <ResponsiveContainer width="100%" height="100%">
                                            <PieChart>
                                                <Pie
                                                    data={eventoPieData}
                                                    cx="50%"
                                                    cy="50%"
                                                    innerRadius={60}
                                                    outerRadius={100}
                                                    paddingAngle={2}
                                                    dataKey="value"
                                                    label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                                                    labelLine={false}
                                                >
                                                    {eventoPieData.map((entry, index) => (
                                                        <Cell key={`cell-${index}`} fill={entry.fill} />
                                                    ))}
                                                </Pie>
                                                <ChartTooltip />
                                            </PieChart>
                                        </ResponsiveContainer>
                                    )}
                                </div>
                            </CardContent>
                        </Card>

                        {/* Pirámide Poblacional */}
                        <Card className="shadow-none">
                            <CardHeader>
                                <CardTitle className="text-base">Pirámide Poblacional</CardTitle>
                                <CardDescription>Distribución por sexo y grupo etario</CardDescription>
                            </CardHeader>
                            <CardContent>
                                <div className="h-[300px]">
                                    {loadingPyramid ? (
                                        <Skeleton className="h-full w-full" />
                                    ) : (
                                        <PyramidChart data={pyramidChartData} />
                                    )}
                                </div>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Map and Table Section */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* Mapa por Provincia */}
                        <Card className="shadow-none">
                            <CardHeader>
                                <CardTitle className="text-base">Distribución Geográfica</CardTitle>
                                <CardDescription>Casos por provincia de residencia</CardDescription>
                            </CardHeader>
                            <CardContent>
                                <div className="h-[400px] flex items-center justify-center">
                                    {loadingProvincia ? (
                                        <Skeleton className="h-full w-full" />
                                    ) : (
                                        <ProvinceMap data={provinciaMapData} height={350} />
                                    )}
                                </div>
                            </CardContent>
                        </Card>

                        {/* Top Eventos Table */}
                        <Card className="shadow-none">
                            <CardHeader>
                                <CardTitle className="text-base">Top Eventos</CardTitle>
                                <CardDescription>Principales eventos notificados con tendencia</CardDescription>
                            </CardHeader>
                            <CardContent>
                                {loadingEventosComp ? (
                                    <Skeleton className="h-[200px] w-full" />
                                ) : (
                                    <TopEventosTable data={topEventosData} />
                                )}
                            </CardContent>
                        </Card>
                    </div>
                </div>
            </SidebarInset>
        </SidebarProvider>
    );
}

