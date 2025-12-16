"use client";

import { useState, useMemo } from "react";
import {
    AlertTriangle,
    BarChart3,
    AreaChart as AreaChartIcon,
    LineChart as LineChartIcon,
    Table2,
    TrendingUp,
    TrendingDown,
    Minus,
    ArrowUpRight,
    ArrowDownRight,
    Building2,
    Map,
    Users,
} from "lucide-react";

import { AppSidebar } from "@/features/layout/components/app-sidebar";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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

import { ProvinceMap, PyramidChart } from "@/components/charts";
import { ProvinciaSelect, EpidemiologicalPeriodPicker, ComparisonModeSelect, type PeriodoEpidemiologico, type ComparisonMode } from "@/components/filters";
import { useMetricQuery, useCorredorEndemico, type PeriodoFilter } from "@/features/metricas";

// ═══════════════════════════════════════════════════════════════════════════════
// CONSTANTS
// ═══════════════════════════════════════════════════════════════════════════════

function getCurrentWeek(): number {
    const now = new Date();
    const start = new Date(now.getFullYear(), 0, 1);
    const diff = now.getTime() - start.getTime();
    const oneWeek = 1000 * 60 * 60 * 24 * 7;
    return Math.ceil(diff / oneWeek);
}

const CURRENT_YEAR = new Date().getFullYear();

const CHART_COLORS = {
    exito: "hsl(142 76% 36%)",
    seguridad: "hsl(47 96% 53%)",
    alerta: "hsl(24 95% 53%)",
    brote: "hsl(0 84% 60%)",
};

const corredorConfig = {
    exito: { label: "Zona Éxito (P25)", color: CHART_COLORS.exito },
    seguridad: { label: "Zona Seguridad (P50)", color: CHART_COLORS.seguridad },
    alerta: { label: "Zona Alerta (P75)", color: CHART_COLORS.alerta },
    brote: { label: "Zona Brote", color: CHART_COLORS.brote },
    casos_actual: { label: "Internados", color: "hsl(var(--foreground))" },
} satisfies ChartConfig;

const PIE_COLORS = [
    "hsl(217 91% 60%)",
    "hsl(142 76% 36%)",
    "hsl(47 96% 53%)",
    "hsl(24 95% 53%)",
    "hsl(0 84% 60%)",
    "hsl(262 83% 58%)",
];

type ChartType = "area" | "line" | "bar";

// ═══════════════════════════════════════════════════════════════════════════════
// COMPONENTS
// ═══════════════════════════════════════════════════════════════════════════════

interface KpiProps {
    title: string;
    value: number | string;
    icon: React.ElementType;
    trend?: { value: number; isPositive: boolean };
    trendLabel?: string;
    variant?: "default" | "warning" | "danger" | "success";
    description?: string;
}

function KpiCard({ title, value, icon: Icon, trend, trendLabel, variant = "default", description }: KpiProps) {
    const colorMap = {
        default: "bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400",
        success: "bg-emerald-50 text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-400",
        warning: "bg-amber-50 text-amber-700 dark:bg-amber-900/20 dark:text-amber-400",
        danger: "bg-rose-50 text-rose-700 dark:bg-rose-900/20 dark:text-rose-400",
    };

    return (
        <Card className="shadow-none border-l-4" style={{
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
                            {Math.abs(trend.value)}% {trendLabel || "vs período anterior"}
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

function VariationBadge({ value }: { value: number | null }) {
    if (value === null) return null;

    if (value === 0) {
        return (
            <span className="inline-flex items-center text-xs text-muted-foreground">
                <Minus className="h-3 w-3 mr-1" />0%
            </span>
        );
    }

    const isPositive = value > 0;
    const Icon = isPositive ? TrendingUp : TrendingDown;
    const color = isPositive ? "text-rose-600" : "text-emerald-600";

    return (
        <span className={cn("inline-flex items-center text-xs font-medium", color)}>
            <Icon className="h-3 w-3 mr-1" />
            {isPositive ? "+" : ""}{value.toFixed(1)}%
        </span>
    );
}

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN PAGE
// ═══════════════════════════════════════════════════════════════════════════════

export default function VigilanciaHospitalariaPage() {
    // State
    const [periodo, setPeriodo] = useState<PeriodoEpidemiologico>({
        anio_desde: CURRENT_YEAR,
        semana_desde: 1,
        anio_hasta: CURRENT_YEAR,
        semana_hasta: getCurrentWeek(),
    });
    const [selectedProvincia, setSelectedProvincia] = useState("all");
    const [comparisonMode, setComparisonMode] = useState<ComparisonMode>("none");
    const [chartType, setChartType] = useState<ChartType>("area");
    const [tipoCamaView, setTipoCamaView] = useState<"pie" | "table">("pie");
    const [pyramidView, setPyramidView] = useState<"chart" | "table">("chart");
    const [mapView, setMapView] = useState<"map" | "table">("map");
    const [detalleView, setDetalleView] = useState<"bar" | "table">("table");

    // Período base para queries (same shape as PeriodoFilter)
    const periodoFilter: PeriodoFilter = periodo;

    // Filtros adicionales
    const filters = useMemo(() => ({
        ...(selectedProvincia !== "all" && { provincia_nombre: selectedProvincia }),
    }), [selectedProvincia]);

    // ═══════════════════════════════════════════════════════════════════════════
    // QUERIES - Usando el nuevo hook con comparación integrada
    // ═══════════════════════════════════════════════════════════════════════════

    // Corredor endémico (no usa comparación del hook, tiene su propio compute)
    const corredorQuery = useCorredorEndemico("ocupacion_camas_ira", periodoFilter, filters);

    // Eventos/Tipos de cama - CON comparación
    const eventosQuery = useMetricQuery({
        metric: "ocupacion_camas_ira",
        dimensions: ["TIPO_EVENTO"],
        periodo: periodoFilter,
        filters,
        comparison: comparisonMode,
    });

    // Pirámide (sexo + grupo etario)
    const pyramidQuery = useMetricQuery({
        metric: "ocupacion_camas_ira",
        dimensions: ["SEXO", "GRUPO_ETARIO"],
        periodo: periodoFilter,
        filters,
        comparison: "none", // Pirámide no necesita comparación
    });

    // Mapa por provincia
    const provinciaQuery = useMetricQuery({
        metric: "ocupacion_camas_ira",
        dimensions: ["PROVINCIA"],
        periodo: periodoFilter,
        filters: {}, // Sin filtro de provincia para el mapa
        comparison: comparisonMode,
    });

    // ═══════════════════════════════════════════════════════════════════════════
    // DATA PROCESSING
    // ═══════════════════════════════════════════════════════════════════════════

    const corredorWarnings = useMemo(() => {
        return (corredorQuery.metadata as { warnings?: string[] })?.warnings || [];
    }, [corredorQuery.metadata]);

    const corredorChartData = useMemo(() => {
        const data = corredorQuery.current;
        if (!data?.length) return [];

        return data.map((row) => {
            const p25 = (row.zona_exito as number) ?? 0;
            const p50 = (row.zona_seguridad as number) ?? 0;
            const p75 = (row.zona_alerta as number) ?? 0;

            return {
                semana: row.semana_epidemiologica as number,
                label: `SE ${row.semana_epidemiologica}`,
                p25,
                p50,
                p75,
                casos_actual: (row.valor_actual as number) ?? 0,
                exito: p25,
                seguridad: Math.max(0, p50 - p25),
                alerta: Math.max(0, p75 - p50),
                brote: 0,
                corredor_valido: row.corredor_valido as boolean,
            };
        }).sort((a, b) => a.semana - b.semana);
    }, [corredorQuery]);

    const eventoPieData = useMemo(() => {
        const data = eventosQuery.current;
        if (!data?.length) return [];
        return data
            .map((row, index) => ({
                name: (row.tipo_evento as string) || "Otros",
                value: (row.valor as number) || 0,
                fill: PIE_COLORS[index % PIE_COLORS.length],
            }))
            .sort((a, b) => b.value - a.value)
            .slice(0, 6);
    }, [eventosQuery]);

    // Tabla de eventos con comparación
    const eventosTableData = useMemo(() => {
        if (!eventosQuery.current?.length) return [];

        return eventosQuery.current
            .map((row) => {
                const currentValue = (row.valor as number) ?? 0;
                const previousValue = eventosQuery.getPreviousValue({ tipo_evento: row.tipo_evento });
                const delta = previousValue !== null
                    ? eventosQuery.calculateDelta(currentValue, previousValue)
                    : null;

                return {
                    evento: (row.tipo_evento as string) || "Otros",
                    casos: currentValue,
                    casosAnterior: previousValue,
                    variacion: delta?.porcentaje ?? null,
                    tendencia: delta?.tendencia ?? null,
                };
            })
            .sort((a, b) => b.casos - a.casos);
    }, [eventosQuery]);

    // Pirámide poblacional
    const pyramidChartData = useMemo(() => {
        const data = pyramidQuery.current;
        if (!data?.length) return [];
        const grouped: Record<string, { masculino: number; femenino: number }> = {};

        data.forEach((row) => {
            const grupo = (row.grupo_etario as string) || "Desconocido";
            const sexo = ((row.sexo as string) || "").toUpperCase();
            const valor = (row.valor as number) || 0;

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
    }, [pyramidQuery]);

    // Mapa de provincias
    const provinciaMapData = useMemo(() => {
        const data = provinciaQuery.current;
        if (!data?.length) return [];
        const total = data.reduce((sum, row) => sum + ((row.valor as number) || 0), 0);
        return data.map((row) => ({
            provincia: (row.provincia as string) || "Desconocido",
            valor: (row.valor as number) || 0,
            porcentaje: total > 0 ? (((row.valor as number) || 0) / total) * 100 : 0,
        }));
    }, [provinciaQuery]);

    // ═══════════════════════════════════════════════════════════════════════════
    // KPI CALCULATIONS
    // ═══════════════════════════════════════════════════════════════════════════

    const totalInternados = useMemo(() => {
        return corredorChartData.reduce((sum, d) => sum + (d.casos_actual || 0), 0);
    }, [corredorChartData]);

    const promedioSemanal = useMemo(() => {
        const semanas = corredorChartData.filter(d => d.casos_actual > 0).length;
        return semanas > 0 ? Math.round(totalInternados / semanas) : 0;
    }, [corredorChartData, totalInternados]);

    // Tendencia últimas 4 semanas vs 4 anteriores
    const trend4Weeks = useMemo(() => {
        const currentWeek = periodo.semana_hasta;
        const last4 = corredorChartData.filter(d => d.semana > currentWeek - 4 && d.semana <= currentWeek);
        const prev4 = corredorChartData.filter(d => d.semana > currentWeek - 8 && d.semana <= currentWeek - 4);

        const sumLast = last4.reduce((s, d) => s + (d.casos_actual || 0), 0);
        const sumPrev = prev4.reduce((s, d) => s + (d.casos_actual || 0), 0);

        if (sumPrev === 0) return null;
        return Math.round(((sumLast - sumPrev) / sumPrev) * 100);
    }, [corredorChartData, periodo.semana_hasta]);

    // Total período anterior (para KPI de comparación)
    const previousTotal = useMemo(() => {
        if (comparisonMode === "none" || !eventosQuery.previous) return null;
        return eventosQuery.previous.reduce((sum, row) => sum + ((row.valor as number) || 0), 0);
    }, [comparisonMode, eventosQuery.previous]);

    const yoyDelta = useMemo(() => {
        if (previousTotal === null || previousTotal === 0) return null;
        const data = eventosQuery.current;
        const currentTotal = data.reduce((sum, row) => sum + ((row.valor as number) || 0), 0);
        return Math.round(((currentTotal - previousTotal) / previousTotal) * 100);
    }, [eventosQuery, previousTotal]);

    // ═══════════════════════════════════════════════════════════════════════════
    // RENDER
    // ═══════════════════════════════════════════════════════════════════════════

    return (
        <SidebarProvider>
            <AppSidebar variant="inset" />
            <SidebarInset className="bg-muted/10 h-screen overflow-hidden flex flex-col">
                {/* Header */}
                <header className="sticky top-0 z-10 bg-background/95 backdrop-blur border-b">
                    <div className="px-6 py-3 flex items-center justify-between">
                        <div>
                            <h1 className="text-2xl font-bold">Vigilancia Hospitalaria</h1>
                            <p className="text-sm text-muted-foreground">
                                Monitoreo de internaciones por Infección Respiratoria Aguda (IRA)
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
                        {/* Period Picker */}
                        <EpidemiologicalPeriodPicker
                            value={periodo}
                            onChange={setPeriodo}
                        />

                        <div className="h-6 w-px bg-border" />

                        <ProvinciaSelect value={selectedProvincia} onChange={setSelectedProvincia} />

                        <div className="h-6 w-px bg-border" />

                        {/* Comparison Mode - con validación de restricciones */}
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
                        {corredorQuery.isLoading ? (
                            <>
                                {[...Array(4)].map((_, i) => (
                                    <Skeleton key={i} className="h-[100px] rounded-xl" />
                                ))}
                            </>
                        ) : (
                            <>
                                <KpiCard
                                    title="Total Internados"
                                    value={totalInternados}
                                    icon={Building2}
                                    variant="default"
                                    description={periodo.anio_desde === periodo.anio_hasta ? `Acumulado ${periodo.anio_hasta}` : `Acumulado ${periodo.anio_desde}-${periodo.anio_hasta}`}
                                />
                                <KpiCard
                                    title="Promedio Semanal"
                                    value={promedioSemanal}
                                    icon={BarChart3}
                                    variant="default"
                                    description="Internaciones/semana"
                                />
                                <KpiCard
                                    title="Tendencia"
                                    value={trend4Weeks !== null ? `${trend4Weeks > 0 ? '+' : ''}${trend4Weeks}%` : "-"}
                                    icon={TrendingUp}
                                    variant={!trend4Weeks ? "default" : trend4Weeks > 0 ? "warning" : "success"}
                                    description="Últimas 4 semanas"
                                />
                                <KpiCard
                                    title={comparisonMode === "yoy" ? `vs ${periodo.anio_hasta - 1}` : "Comparación"}
                                    value={previousTotal !== null ? previousTotal.toLocaleString() : "-"}
                                    icon={TrendingUp}
                                    trend={yoyDelta !== null ? { value: Math.abs(yoyDelta), isPositive: yoyDelta > 0 } : undefined}
                                    variant={!yoyDelta ? "default" : yoyDelta > 0 ? "danger" : "success"}
                                    description={comparisonMode !== "none" ? `Período de comparación` : "Activa comparación arriba"}
                                />
                            </>
                        )}
                    </section>

                    {/* Main Chart: Corredor Endémico */}
                    <Card className="shadow-none">
                        <CardHeader>
                            <div className="flex items-center justify-between">
                                <div>
                                    <CardTitle>Curva de Internaciones</CardTitle>
                                    <CardDescription>
                                        Casos {periodo.anio_hasta} vs Histórico (P25, P50, P75)
                                    </CardDescription>
                                </div>
                                <div className="flex items-center gap-2">
                                    <div className="flex items-center gap-1 border rounded-lg p-0.5">
                                        {[
                                            { type: "area" as ChartType, icon: AreaChartIcon },
                                            { type: "line" as ChartType, icon: LineChartIcon },
                                            { type: "bar" as ChartType, icon: BarChart3 },
                                        ].map(({ type, icon: Icon }) => (
                                            <Button
                                                key={type}
                                                variant={chartType === type ? "default" : "ghost"}
                                                size="sm"
                                                className="h-7 w-7 p-0"
                                                onClick={() => setChartType(type)}
                                            >
                                                <Icon className="h-4 w-4" />
                                            </Button>
                                        ))}
                                    </div>
                                    <Badge variant="outline" className="font-mono">SE 1 - 52</Badge>
                                </div>
                            </div>
                        </CardHeader>
                        <CardContent>
                            {corredorQuery.isLoading ? (
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

                                                {/* Historical Zones */}
                                                <Area dataKey="brote" type="monotone" fill={CHART_COLORS.brote} stroke="none" fillOpacity={0.2} stackId="zones" />
                                                <Area dataKey="alerta" type="monotone" fill={CHART_COLORS.alerta} stroke="none" fillOpacity={0.2} stackId="zones" />
                                                <Area dataKey="seguridad" type="monotone" fill={CHART_COLORS.seguridad} stroke="none" fillOpacity={0.2} stackId="zones" />
                                                <Area dataKey="exito" type="monotone" fill={CHART_COLORS.exito} stroke="none" fillOpacity={0.2} stackId="zones" />

                                                {/* Current Year */}
                                                {chartType === 'bar' && (
                                                    <Bar dataKey="casos_actual" name={`Internados ${periodo.anio_hasta}`} fill="hsl(var(--foreground))" fillOpacity={0.8} radius={[4, 4, 0, 0]} barSize={8} isAnimationActive={false} />
                                                )}
                                                {chartType === 'line' && (
                                                    <Line dataKey="casos_actual" name={`Internados ${periodo.anio_hasta}`} type="monotone" stroke="#1f2937" strokeWidth={2.5} dot={{ r: 3, fill: "#1f2937", strokeWidth: 0 }} activeDot={{ r: 5, fill: "#1f2937", strokeWidth: 0 }} connectNulls isAnimationActive={false} />
                                                )}
                                                {chartType === 'area' && (
                                                    <Area dataKey="casos_actual" name={`Internados ${periodo.anio_hasta}`} type="monotone" stroke="hsl(var(--foreground))" fill="hsl(var(--foreground))" fillOpacity={0.1} strokeWidth={2.5} activeDot={{ r: 5, strokeWidth: 2 }} connectNulls isAnimationActive={false} />
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
                        {/* Distribución por Tipo */}
                        <Card className="shadow-none">
                            <CardHeader>
                                <div className="flex items-center justify-between">
                                    <div>
                                        <CardTitle className="text-base">Distribución por Tipo de Cama</CardTitle>
                                        <CardDescription>Internación General, UTI, Neonatología</CardDescription>
                                    </div>
                                    <div className="flex items-center gap-1 border rounded-lg p-0.5">
                                        <Button variant={tipoCamaView === "pie" ? "default" : "ghost"} size="sm" className="h-7 w-7 p-0" onClick={() => setTipoCamaView("pie")}>
                                            <BarChart3 className="h-4 w-4" />
                                        </Button>
                                        <Button variant={tipoCamaView === "table" ? "default" : "ghost"} size="sm" className="h-7 w-7 p-0" onClick={() => setTipoCamaView("table")}>
                                            <Table2 className="h-4 w-4" />
                                        </Button>
                                    </div>
                                </div>
                            </CardHeader>
                            <CardContent>
                                <div className="h-[300px]">
                                    {eventosQuery.isLoading ? (
                                        <Skeleton className="h-full w-full" />
                                    ) : tipoCamaView === "pie" ? (
                                        <ResponsiveContainer width="100%" height="100%">
                                            <PieChart>
                                                <Pie data={eventoPieData} cx="50%" cy="50%" innerRadius={60} outerRadius={100} paddingAngle={2} dataKey="value" label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`} labelLine={false}>
                                                    {eventoPieData.map((entry, index) => (
                                                        <Cell key={`cell-${index}`} fill={entry.fill} />
                                                    ))}
                                                </Pie>
                                                <ChartTooltip />
                                            </PieChart>
                                        </ResponsiveContainer>
                                    ) : (
                                        <div className="overflow-auto h-full">
                                            <table className="w-full text-sm">
                                                <thead>
                                                    <tr className="border-b">
                                                        <th className="text-left py-2 font-medium">Tipo</th>
                                                        <th className="text-right py-2 font-medium">Cantidad</th>
                                                        {comparisonMode !== "none" && (
                                                            <th className="text-right py-2 font-medium">Anterior</th>
                                                        )}
                                                        <th className="text-right py-2 font-medium">
                                                            {comparisonMode !== "none" ? "Var." : "%"}
                                                        </th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {eventosTableData.slice(0, 8).map((row, index) => {
                                                        const total = eventosTableData.reduce((s, r) => s + r.casos, 0);
                                                        const pct = total > 0 ? (row.casos / total * 100).toFixed(1) : "0";
                                                        return (
                                                            <tr key={index} className="border-b last:border-0">
                                                                <td className="py-2 flex items-center gap-2">
                                                                    <span className="w-3 h-3 rounded-full" style={{ backgroundColor: PIE_COLORS[index % PIE_COLORS.length] }} />
                                                                    <span className="truncate max-w-[150px]" title={row.evento}>{row.evento}</span>
                                                                </td>
                                                                <td className="text-right py-2 tabular-nums">{row.casos.toLocaleString()}</td>
                                                                {comparisonMode !== "none" && (
                                                                    <td className="text-right py-2 tabular-nums text-muted-foreground">
                                                                        {row.casosAnterior !== null ? row.casosAnterior.toLocaleString() : "-"}
                                                                    </td>
                                                                )}
                                                                <td className="text-right py-2">
                                                                    {comparisonMode !== "none" ? (
                                                                        <VariationBadge value={row.variacion} />
                                                                    ) : (
                                                                        <span className="tabular-nums text-muted-foreground">{pct}%</span>
                                                                    )}
                                                                </td>
                                                            </tr>
                                                        );
                                                    })}
                                                </tbody>
                                            </table>
                                        </div>
                                    )}
                                </div>
                            </CardContent>
                        </Card>

                        {/* Pirámide Poblacional */}
                        <Card className="shadow-none">
                            <CardHeader>
                                <div className="flex items-center justify-between">
                                    <div>
                                        <CardTitle className="text-base">Pirámide Poblacional</CardTitle>
                                        <CardDescription>Internados por sexo y grupo etario</CardDescription>
                                    </div>
                                    <div className="flex items-center gap-1 border rounded-lg p-0.5">
                                        <Button variant={pyramidView === "chart" ? "default" : "ghost"} size="sm" className="h-7 w-7 p-0" onClick={() => setPyramidView("chart")}>
                                            <Users className="h-4 w-4" />
                                        </Button>
                                        <Button variant={pyramidView === "table" ? "default" : "ghost"} size="sm" className="h-7 w-7 p-0" onClick={() => setPyramidView("table")}>
                                            <Table2 className="h-4 w-4" />
                                        </Button>
                                    </div>
                                </div>
                            </CardHeader>
                            <CardContent>
                                <div className="h-[300px]">
                                    {pyramidQuery.isLoading ? (
                                        <div className="h-full flex items-center justify-center">
                                            <Skeleton className="h-full w-full" />
                                        </div>
                                    ) : pyramidQuery.error ? (
                                        <div className="h-full flex items-center justify-center text-sm text-destructive">
                                            Error cargando datos: {pyramidQuery.error.message}
                                        </div>
                                    ) : pyramidView === "chart" ? (
                                        <PyramidChart data={pyramidChartData} />
                                    ) : (
                                        <div className="overflow-auto h-full">
                                            <table className="w-full text-sm">
                                                <thead>
                                                    <tr className="border-b">
                                                        <th className="text-left py-2 font-medium">Grupo Etario</th>
                                                        <th className="text-right py-2 font-medium">Masculino</th>
                                                        <th className="text-right py-2 font-medium">Femenino</th>
                                                        <th className="text-right py-2 font-medium">Total</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {pyramidChartData.length === 0 ? (
                                                        <tr>
                                                            <td colSpan={4} className="py-8 text-center text-muted-foreground">
                                                                No hay datos disponibles
                                                            </td>
                                                        </tr>
                                                    ) : (
                                                        pyramidChartData.map((row, index) => (
                                                            <tr key={index} className="border-b last:border-0">
                                                                <td className="py-2">{row.grupo}</td>
                                                                <td className="text-right py-2 tabular-nums text-blue-600">{row.masculino.toLocaleString()}</td>
                                                                <td className="text-right py-2 tabular-nums text-pink-600">{row.femenino.toLocaleString()}</td>
                                                                <td className="text-right py-2 tabular-nums font-medium">{(row.masculino + row.femenino).toLocaleString()}</td>
                                                            </tr>
                                                        ))
                                                    )}
                                                </tbody>
                                            </table>
                                        </div>
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
                                <div className="flex items-center justify-between">
                                    <div>
                                        <CardTitle className="text-base">Distribución Geográfica</CardTitle>
                                        <CardDescription>Internaciones por provincia</CardDescription>
                                    </div>
                                    <div className="flex items-center gap-1 border rounded-lg p-0.5">
                                        <Button variant={mapView === "map" ? "default" : "ghost"} size="sm" className="h-7 w-7 p-0" onClick={() => setMapView("map")}>
                                            <Map className="h-4 w-4" />
                                        </Button>
                                        <Button variant={mapView === "table" ? "default" : "ghost"} size="sm" className="h-7 w-7 p-0" onClick={() => setMapView("table")}>
                                            <Table2 className="h-4 w-4" />
                                        </Button>
                                    </div>
                                </div>
                            </CardHeader>
                            <CardContent>
                                <div className="h-[400px]">
                                    {provinciaQuery.isLoading ? (
                                        <div className="h-full flex items-center justify-center">
                                            <Skeleton className="h-full w-full" />
                                        </div>
                                    ) : provinciaQuery.error ? (
                                        <div className="h-full flex items-center justify-center text-sm text-destructive">
                                            Error cargando datos: {provinciaQuery.error.message}
                                        </div>
                                    ) : mapView === "map" ? (
                                        provinciaMapData.length === 0 ? (
                                            <div className="h-full flex items-center justify-center text-sm text-muted-foreground">
                                                No hay datos geográficos disponibles
                                            </div>
                                        ) : (
                                            <ProvinceMap data={provinciaMapData} height={350} />
                                        )
                                    ) : (
                                        <div className="overflow-auto h-full">
                                            <table className="w-full text-sm">
                                                <thead>
                                                    <tr className="border-b">
                                                        <th className="text-left py-2 font-medium">Provincia</th>
                                                        <th className="text-right py-2 font-medium">Casos</th>
                                                        <th className="text-right py-2 font-medium">%</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {provinciaMapData.length === 0 ? (
                                                        <tr>
                                                            <td colSpan={3} className="py-8 text-center text-muted-foreground">
                                                                No hay datos disponibles
                                                            </td>
                                                        </tr>
                                                    ) : (
                                                        provinciaMapData
                                                            .sort((a, b) => b.valor - a.valor)
                                                            .map((row, index) => (
                                                                <tr key={index} className="border-b last:border-0">
                                                                    <td className="py-2">{row.provincia}</td>
                                                                    <td className="text-right py-2 tabular-nums font-medium">{row.valor.toLocaleString()}</td>
                                                                    <td className="text-right py-2 tabular-nums text-muted-foreground">{row.porcentaje.toFixed(1)}%</td>
                                                                </tr>
                                                            ))
                                                    )}
                                                </tbody>
                                            </table>
                                        </div>
                                    )}
                                </div>
                            </CardContent>
                        </Card>

                        {/* Detalle por Tipo de Cama */}
                        <Card className="shadow-none">
                            <CardHeader>
                                <div className="flex items-center justify-between">
                                    <div>
                                        <CardTitle className="text-base">Detalle por Tipo de Cama</CardTitle>
                                        <CardDescription>
                                            {comparisonMode !== "none"
                                                ? `Comparación ${comparisonMode === "yoy" ? "interanual" : "con período anterior"}`
                                                : "Ocupación y tendencia"}
                                        </CardDescription>
                                    </div>
                                    <div className="flex items-center gap-1 border rounded-lg p-0.5">
                                        <Button variant={detalleView === "bar" ? "default" : "ghost"} size="sm" className="h-7 w-7 p-0" onClick={() => setDetalleView("bar")}>
                                            <BarChart3 className="h-4 w-4" />
                                        </Button>
                                        <Button variant={detalleView === "table" ? "default" : "ghost"} size="sm" className="h-7 w-7 p-0" onClick={() => setDetalleView("table")}>
                                            <Table2 className="h-4 w-4" />
                                        </Button>
                                    </div>
                                </div>
                            </CardHeader>
                            <CardContent>
                                <div className="h-[400px]">
                                    {eventosQuery.isLoading ? (
                                        <Skeleton className="h-full w-full" />
                                    ) : detalleView === "bar" ? (
                                        <ResponsiveContainer width="100%" height="100%">
                                            <ComposedChart
                                                data={eventosTableData}
                                                layout="vertical"
                                                margin={{ top: 10, right: 30, left: 10, bottom: 10 }}
                                            >
                                                <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} />
                                                <XAxis type="number" tickFormatter={(v) => v.toLocaleString()} />
                                                <YAxis
                                                    type="category"
                                                    dataKey="evento"
                                                    width={120}
                                                    tick={{ fontSize: 10 }}
                                                    tickFormatter={(value: string) => value.length > 18 ? value.slice(0, 16) + "..." : value}
                                                />
                                                <ChartTooltip
                                                    formatter={(value: number) => value.toLocaleString()}
                                                    labelFormatter={(label: string) => label}
                                                />
                                                <Bar dataKey="casos" name="Actual" fill="hsl(217 91% 60%)" radius={[0, 4, 4, 0]} />
                                                {comparisonMode !== "none" && (
                                                    <Bar dataKey="casosAnterior" name="Anterior" fill="hsl(var(--muted-foreground))" radius={[0, 4, 4, 0]} fillOpacity={0.5} />
                                                )}
                                            </ComposedChart>
                                        </ResponsiveContainer>
                                    ) : (
                                        <div className="rounded-md border h-full overflow-auto">
                                            <table className="w-full text-sm">
                                                <thead>
                                                    <tr className="border-b bg-muted/50">
                                                        <th className="text-left py-2 px-3 font-medium">Tipo de Cama</th>
                                                        <th className="text-right py-2 px-3 font-medium">Casos</th>
                                                        {comparisonMode !== "none" && (
                                                            <>
                                                                <th className="text-right py-2 px-3 font-medium">Anterior</th>
                                                                <th className="text-right py-2 px-3 font-medium">Variación</th>
                                                            </>
                                                        )}
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {eventosTableData.length === 0 ? (
                                                        <tr>
                                                            <td colSpan={comparisonMode !== "none" ? 4 : 2} className="py-8 text-center text-muted-foreground">
                                                                No hay datos para el período seleccionado
                                                            </td>
                                                        </tr>
                                                    ) : (
                                                        eventosTableData.map((row, index) => (
                                                            <tr key={index} className="border-b last:border-0">
                                                                <td className="py-2 px-3">{row.evento}</td>
                                                                <td className="text-right py-2 px-3 tabular-nums font-medium">
                                                                    {row.casos.toLocaleString()}
                                                                </td>
                                                                {comparisonMode !== "none" && (
                                                                    <>
                                                                        <td className="text-right py-2 px-3 tabular-nums text-muted-foreground">
                                                                            {row.casosAnterior !== null ? row.casosAnterior.toLocaleString() : "-"}
                                                                        </td>
                                                                        <td className="text-right py-2 px-3">
                                                                            <VariationBadge value={row.variacion} />
                                                                        </td>
                                                                    </>
                                                                )}
                                                            </tr>
                                                        ))
                                                    )}
                                                </tbody>
                                            </table>
                                        </div>
                                    )}
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                </div>
            </SidebarInset>
        </SidebarProvider>
    );
}
