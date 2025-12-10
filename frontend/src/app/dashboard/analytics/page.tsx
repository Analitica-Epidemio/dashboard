"use client";

/**
 * Generador de Boletines Epidemiológicos
 *
 * UI clara que muestra:
 * 1. Selector de semana de referencia
 * 2. Resumen de secciones que se incluirán con sus rangos temporales
 * 3. Vista previa de datos con indicadores claros de qué período cubren
 */

import { useState, useMemo, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
    Activity,
    BarChart3,
    AreaChart as AreaChartIcon,
    LineChart as LineChartIcon,
    TrendingUp,
    TrendingDown,
    FlaskConical,
    FileText,
    Loader2,
    Newspaper,
    ChevronDown,
    ChevronUp,
    Clock,
    Calendar,
    Info,
    Eye,
    Table as TableIcon,
    PieChart as PieChartIcon,
} from "lucide-react";

import { AppSidebar } from "@/features/layout/components/app-sidebar";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
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
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip";
import {
    Collapsible,
    CollapsibleContent,
    CollapsibleTrigger,
} from "@/components/ui/collapsible";
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
    BarChart,
    Bar,
    ResponsiveContainer,
    PieChart,
    Pie,
    Cell,
} from "recharts";

import { $api } from "@/lib/api/client";
import { ChartTypeSelector } from "@/components/charts";
import { useTopChangesByGroup, useGenerateDraft, useSeccionesConfig, type EventoCambio, type SeccionConfig, type BloqueConfig } from "@/features/analytics/api";

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

// --- Components ---

/** Badge que indica el rango temporal de un chart/sección */
function RangoBadge({ rango, className }: { rango: string; className?: string }) {
    return (
        <TooltipProvider>
            <Tooltip>
                <TooltipTrigger asChild>
                    <Badge variant="outline" className={cn("text-xs gap-1 font-normal", className)}>
                        <Clock className="h-3 w-3" />
                        {rango}
                    </Badge>
                </TooltipTrigger>
                <TooltipContent>
                    <p>Rango de datos incluidos en este gráfico</p>
                </TooltipContent>
            </Tooltip>
        </TooltipProvider>
    );
}

/** Icono según tipo de visualización */
function VisualizacionIcon({ tipo }: { tipo: string }) {
    switch (tipo) {
        case "area_chart":
            return <AreaChartIcon className="h-4 w-4" />;
        case "stacked_bar":
        case "grouped_bar":
            return <BarChart3 className="h-4 w-4" />;
        case "table":
            return <TableIcon className="h-4 w-4" />;
        case "pie_chart":
            return <PieChartIcon className="h-4 w-4" />;
        default:
            return <BarChart3 className="h-4 w-4" />;
    }
}

/** Card de sección con bloques */
function SeccionCard({ seccion, isOpen, onToggle }: {
    seccion: SeccionConfig;
    isOpen: boolean;
    onToggle: () => void;
}) {
    const bloques = seccion.bloques ?? [];
    return (
        <Collapsible open={isOpen} onOpenChange={onToggle}>
            <Card className="border-l-4 border-l-primary/50">
                <CollapsibleTrigger asChild>
                    <CardHeader className="cursor-pointer hover:bg-muted/30 transition-colors py-3">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <CardTitle className="text-base">{seccion.titulo}</CardTitle>
                                <Badge variant="secondary" className="text-xs">
                                    {bloques.length} {bloques.length === 1 ? 'bloque' : 'bloques'}
                                </Badge>
                            </div>
                            {isOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                        </div>
                    </CardHeader>
                </CollapsibleTrigger>
                <CollapsibleContent>
                    <CardContent className="pt-0 pb-4">
                        <div className="space-y-3">
                            {bloques.map((bloque) => (
                                <BloqueItem key={bloque.id} bloque={bloque} />
                            ))}
                        </div>
                    </CardContent>
                </CollapsibleContent>
            </Card>
        </Collapsible>
    );
}

/** Item de bloque dentro de una sección */
function BloqueItem({ bloque }: { bloque: BloqueConfig }) {
    return (
        <div className="flex items-start gap-3 p-3 bg-muted/30 rounded-lg">
            <div className="p-2 bg-background rounded-md border">
                <VisualizacionIcon tipo={bloque.tipo_visualizacion} />
            </div>
            <div className="flex-1 min-w-0">
                <div className="font-medium text-sm">{bloque.titulo_template}</div>
                <div className="flex items-center gap-2 mt-1 flex-wrap">
                    <Badge variant="outline" className="text-[10px] capitalize">
                        {bloque.tipo_visualizacion.replace(/_/g, ' ')}
                    </Badge>
                    {bloque.rango_temporal && (
                        <span className="text-xs text-muted-foreground flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {bloque.rango_temporal.ejemplo}
                        </span>
                    )}
                </div>
            </div>
        </div>
    );
}

// --- Main Page ---
export default function AnalyticsPage() {
    const router = useRouter();

    // State
    const [semanaReferencia, setSemanaReferencia] = useState(getCurrentWeek());
    const [anioReferencia, setAnioReferencia] = useState(CURRENT_YEAR);
    const [eventosSeleccionados, setEventosSeleccionados] = useState<Set<number>>(new Set());
    const [chartType, setChartType] = useState<string>("area");
    const [showPreview, setShowPreview] = useState(true);
    const [openSecciones, setOpenSecciones] = useState<Set<number>>(new Set([1])); // Primera sección abierta por defecto

    // Rango para el dashboard de preview (año completo hasta semana de referencia)
    const rangoPreview = `SE 1 - ${semanaReferencia} / ${anioReferencia}`;

    // Period filter for MetricService
    const periodoFilter = useMemo(() => ({
        anio_desde: anioReferencia,
        semana_desde: 1,
        anio_hasta: anioReferencia,
        semana_hasta: semanaReferencia,
    }), [semanaReferencia, anioReferencia]);

    const buildFilters = (extras: Record<string, unknown> = {}) => ({
        periodo: periodoFilter,
        ...extras,
    });

    // === QUERIES ===

    const { data: corredorData, isLoading: loadingCorredor } = $api.useQuery("post", "/api/v1/metricas/query", {
        body: {
            metric: "casos_clinicos",
            dimensions: ["SEMANA_EPIDEMIOLOGICA", "ANIO_EPIDEMIOLOGICO"],
            filters: buildFilters({ comparar_con: "yoy" }),
            compute: "corredor_endemico",
        },
    });

    const { data: eventosData, isLoading: loadingEventos } = $api.useQuery("post", "/api/v1/metricas/query", {
        body: {
            metric: "casos_clinicos",
            dimensions: ["TIPO_EVENTO"],
            filters: buildFilters(),
        },
    });

    const { data: grupoEtarioData, isLoading: loadingGrupo } = $api.useQuery("post", "/api/v1/metricas/query", {
        body: {
            metric: "casos_clinicos",
            dimensions: ["GRUPO_ETARIO"],
            filters: buildFilters(),
        },
    });

    const { data: labData, isLoading: loadingLab } = $api.useQuery("post", "/api/v1/metricas/query", {
        body: {
            metric: "muestras_positivas",
            dimensions: ["SEMANA_EPIDEMIOLOGICA", "AGENTE_ETIOLOGICO"],
            filters: buildFilters(),
        },
    });

    const { data: topChangesData, isLoading: loadingTopChanges } = useTopChangesByGroup({
        semana_actual: semanaReferencia,
        anio_actual: anioReferencia,
        num_semanas: 4,
        limit: 10,
    });

    const { data: seccionesConfigData, isLoading: loadingSeccionesConfig } = useSeccionesConfig({
        semana: semanaReferencia,
        anio: anioReferencia,
    });

    const generateDraftMutation = useGenerateDraft();

    // Toggle functions
    const toggleEvento = useCallback((tipoEnoId: number) => {
        setEventosSeleccionados(prev => {
            const next = new Set(prev);
            if (next.has(tipoEnoId)) {
                next.delete(tipoEnoId);
            } else {
                next.add(tipoEnoId);
            }
            return next;
        });
    }, []);

    const toggleSeccion = useCallback((seccionId: number) => {
        setOpenSecciones(prev => {
            const next = new Set(prev);
            if (next.has(seccionId)) {
                next.delete(seccionId);
            } else {
                next.add(seccionId);
            }
            return next;
        });
    }, []);

    // Generate boletín
    const handleGenerateBoletin = useCallback(async () => {
        try {
            const result = await generateDraftMutation.mutateAsync({
                semana: semanaReferencia,
                anio: anioReferencia,
                num_semanas: 4,
                eventos_seleccionados: eventosSeleccionados.size > 0
                    ? Array.from(eventosSeleccionados).map(id => ({
                        tipo_eno_id: id,
                        incluir_charts: true,
                    }))
                    : [],
            });

            if (result?.data?.boletin_instance_id) {
                router.push(`/dashboard/boletines/${result.data.boletin_instance_id}`);
            }
        } catch (error) {
            console.error("Error generating boletín:", error);
        }
    }, [eventosSeleccionados, semanaReferencia, anioReferencia, generateDraftMutation, router]);

    // Process data
    const topCrecimiento = useMemo((): EventoCambio[] => {
        if (!topChangesData?.data?.top_crecimiento) return [];
        return topChangesData.data.top_crecimiento
            .sort((a, b) => b.diferencia_porcentual - a.diferencia_porcentual)
            .slice(0, 10);
    }, [topChangesData]);

    const topDecrecimiento = useMemo((): EventoCambio[] => {
        if (!topChangesData?.data?.top_decrecimiento) return [];
        return topChangesData.data.top_decrecimiento
            .sort((a, b) => a.diferencia_porcentual - b.diferencia_porcentual)
            .slice(0, 10);
    }, [topChangesData]);

    const corredorChartData = useMemo(() => {
        if (!corredorData?.data || !Array.isArray(corredorData.data)) return [];

        return (corredorData.data as Array<Record<string, number | boolean>>).map((row) => {
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
            };
        }).sort((a, b) => a.semana - b.semana);
    }, [corredorData]);

    const eventoPieData = useMemo(() => {
        if (!eventosData?.data) return [];
        return (eventosData.data as Array<Record<string, string | number>>)
            .map((row, index) => ({
                name: (row.tipo_evento as string) || "Otros",
                value: (row.valor as number) || 0,
                fill: PIE_COLORS[index % PIE_COLORS.length],
            }))
            .sort((a, b) => b.value - a.value)
            .slice(0, 6);
    }, [eventosData]);

    const grupoBarData = useMemo(() => {
        if (!grupoEtarioData?.data) return [];
        return (grupoEtarioData.data as Array<Record<string, string | number>>).map((row) => ({
            grupo: (row.grupo_etario as string) || "Desconocido",
            casos: (row.valor as number) || 0,
        }));
    }, [grupoEtarioData]);

    const labChartData = useMemo(() => {
        if (!labData?.data || !Array.isArray(labData.data)) return { chartData: [], agentes: [] };

        const MAX_AGENTES = 10;
        const agenteTotals = new Map<string, number>();
        (labData.data as Array<Record<string, string | number>>).forEach((d) => {
            const agente = (d.agente_etiologico as string) || "Desconocido";
            const valor = (d.valor as number) || 0;
            agenteTotals.set(agente, (agenteTotals.get(agente) || 0) + valor);
        });

        const topAgentes = Array.from(agenteTotals.entries())
            .sort(([, a], [, b]) => b - a)
            .slice(0, MAX_AGENTES)
            .map(([agente]) => agente);

        const topAgentesSet = new Set(topAgentes);
        const weekMap = new Map<number, Record<string, number>>();

        (labData.data as Array<Record<string, string | number>>).forEach((d) => {
            const agenteRaw = (d.agente_etiologico as string) || "Desconocido";
            const agente = topAgentesSet.has(agenteRaw) ? agenteRaw : "Otros";
            const semana = d.semana_epidemiologica as number;
            const valor = (d.valor as number) || 0;

            const weekData = weekMap.get(semana) || {};
            weekData[agente] = (weekData[agente] || 0) + valor;
            weekMap.set(semana, weekData);
        });

        const chartData = Array.from(weekMap.entries())
            .sort(([a], [b]) => a - b)
            .map(([semana, agentesData]) => ({
                semana: `SE ${semana}`,
                ...agentesData,
            }));

        const agentesFinales = [...topAgentes];
        if (agenteTotals.size > MAX_AGENTES) {
            agentesFinales.push("Otros");
        }

        return { chartData, agentes: agentesFinales };
    }, [labData]);

    const secciones = seccionesConfigData?.data?.secciones as SeccionConfig[] || [];

    return (
        <SidebarProvider>
            <AppSidebar variant="inset" />
            <SidebarInset className="bg-muted/10 h-screen overflow-hidden flex flex-col">
                {/* Header */}
                <header className="sticky top-0 z-10 bg-background/95 backdrop-blur border-b">
                    <div className="px-6 py-4">
                        <h1 className="text-2xl font-bold flex items-center gap-2">
                            <Newspaper className="h-6 w-6" />
                            Generador de Boletines
                        </h1>
                        <p className="text-sm text-muted-foreground mt-1">
                            Seleccioná la semana de referencia y revisá qué datos se incluirán en el boletín
                        </p>
                    </div>
                </header>

                {/* Content */}
                <div className="flex-1 overflow-y-auto">
                    <div className="p-6 space-y-6 max-w-[1400px] mx-auto">

                        {/* === PANEL DE CONFIGURACIÓN === */}
                        <Card className="border-2 border-primary/30 shadow-lg">
                            <CardHeader className="pb-4">
                                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                                    {/* Selector de semana */}
                                    <div className="flex items-center gap-4">
                                        <div className="p-3 bg-primary/10 rounded-lg">
                                            <Calendar className="h-6 w-6 text-primary" />
                                        </div>
                                        <div>
                                            <div className="text-sm text-muted-foreground mb-1">Semana de referencia</div>
                                            <div className="flex items-center gap-2">
                                                <Select
                                                    value={semanaReferencia.toString()}
                                                    onValueChange={(v) => setSemanaReferencia(parseInt(v))}
                                                >
                                                    <SelectTrigger className="w-[110px] font-mono">
                                                        <SelectValue />
                                                    </SelectTrigger>
                                                    <SelectContent>
                                                        {Array.from({ length: 52 }, (_, i) => i + 1).map((se) => (
                                                            <SelectItem key={se} value={se.toString()}>
                                                                SE {se}
                                                            </SelectItem>
                                                        ))}
                                                    </SelectContent>
                                                </Select>
                                                <span className="text-muted-foreground">/</span>
                                                <Select
                                                    value={anioReferencia.toString()}
                                                    onValueChange={(v) => setAnioReferencia(parseInt(v))}
                                                >
                                                    <SelectTrigger className="w-[90px] font-mono">
                                                        <SelectValue />
                                                    </SelectTrigger>
                                                    <SelectContent>
                                                        {Array.from({ length: 5 }, (_, i) => CURRENT_YEAR - i).map((anio) => (
                                                            <SelectItem key={anio} value={anio.toString()}>
                                                                {anio}
                                                            </SelectItem>
                                                        ))}
                                                    </SelectContent>
                                                </Select>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Botón generar */}
                                    <Button
                                        onClick={handleGenerateBoletin}
                                        disabled={generateDraftMutation.isPending}
                                        size="lg"
                                        className="gap-2"
                                    >
                                        {generateDraftMutation.isPending ? (
                                            <>
                                                <Loader2 className="h-4 w-4 animate-spin" />
                                                Generando...
                                            </>
                                        ) : (
                                            <>
                                                <FileText className="h-5 w-5" />
                                                Generar Boletín SE {semanaReferencia}/{anioReferencia}
                                            </>
                                        )}
                                    </Button>
                                </div>
                            </CardHeader>

                            <CardContent className="border-t pt-4">
                                {/* Info box explicativo */}
                                <div className="bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-4">
                                    <div className="flex items-start gap-3">
                                        <Info className="h-5 w-5 text-blue-600 dark:text-blue-400 shrink-0 mt-0.5" />
                                        <div className="text-sm">
                                            <p className="font-medium text-blue-900 dark:text-blue-100">
                                                ¿Qué datos se incluirán?
                                            </p>
                                            <p className="text-blue-700 dark:text-blue-300 mt-1">
                                                El boletín incluirá <strong>{secciones.length} secciones</strong> con datos calculados
                                                a partir de la <strong>SE {semanaReferencia}/{anioReferencia}</strong>.
                                                Cada sección usa un rango temporal diferente según su tipo (corredor endémico,
                                                tablas de últimas semanas, series históricas, etc.).
                                            </p>
                                        </div>
                                    </div>
                                </div>

                                {/* Lista de secciones */}
                                {loadingSeccionesConfig ? (
                                    <div className="space-y-3">
                                        {[1, 2, 3].map((i) => (
                                            <Skeleton key={i} className="h-20 w-full" />
                                        ))}
                                    </div>
                                ) : secciones.length > 0 ? (
                                    <div className="space-y-3">
                                        <div className="flex items-center justify-between mb-2">
                                            <h3 className="font-medium text-sm">Secciones del boletín</h3>
                                            <Button
                                                variant="ghost"
                                                size="sm"
                                                onClick={() => {
                                                    if (openSecciones.size === secciones.length) {
                                                        setOpenSecciones(new Set());
                                                    } else {
                                                        setOpenSecciones(new Set(secciones.map(s => s.id)));
                                                    }
                                                }}
                                            >
                                                {openSecciones.size === secciones.length ? "Colapsar todo" : "Expandir todo"}
                                            </Button>
                                        </div>
                                        {secciones.map((seccion) => (
                                            <SeccionCard
                                                key={seccion.id}
                                                seccion={seccion}
                                                isOpen={openSecciones.has(seccion.id)}
                                                onToggle={() => toggleSeccion(seccion.id)}
                                            />
                                        ))}
                                    </div>
                                ) : (
                                    <div className="text-center py-8 text-muted-foreground">
                                        No hay secciones configuradas
                                    </div>
                                )}
                            </CardContent>
                        </Card>

                        {/* === VISTA PREVIA DE DATOS === */}
                        <Collapsible open={showPreview} onOpenChange={setShowPreview}>
                            <div className="flex items-center justify-between mb-4">
                                <div className="flex items-center gap-2">
                                    <Eye className="h-5 w-5" />
                                    <h2 className="text-lg font-semibold">Vista previa de datos</h2>
                                    <RangoBadge rango={rangoPreview} />
                                </div>
                                <CollapsibleTrigger asChild>
                                    <Button variant="ghost" size="sm">
                                        {showPreview ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                                        {showPreview ? "Ocultar" : "Mostrar"}
                                    </Button>
                                </CollapsibleTrigger>
                            </div>

                            <CollapsibleContent className="space-y-6">
                                {/* Corredor Endémico */}
                                <Card>
                                    <CardHeader className="pb-2">
                                        <div className="flex items-center justify-between">
                                            <div>
                                                <CardTitle className="text-base">Corredor Endémico - Casos Clínicos</CardTitle>
                                                <CardDescription>
                                                    Casos {anioReferencia} vs percentiles históricos
                                                </CardDescription>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <RangoBadge rango={`SE 1-${semanaReferencia} / ${anioReferencia}`} />
                                                <ChartTypeSelector
                                                    types={[
                                                        { type: 'area', icon: AreaChartIcon, label: 'Área' },
                                                        { type: 'line', icon: LineChartIcon, label: 'Línea' },
                                                        { type: 'bar', icon: BarChart3, label: 'Barras' },
                                                    ]}
                                                    value={chartType}
                                                    onChange={setChartType}
                                                />
                                            </div>
                                        </div>
                                    </CardHeader>
                                    <CardContent>
                                        {loadingCorredor ? (
                                            <Skeleton className="h-[350px] w-full" />
                                        ) : (
                                            <div className="h-[350px]">
                                                <ChartContainer config={corredorConfig} className="h-full w-full">
                                                    <ComposedChart data={corredorChartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                                                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                                                        <XAxis dataKey="label" tickLine={false} axisLine={false} tickMargin={8} minTickGap={30} style={{ fontSize: '12px' }} />
                                                        <YAxis tickLine={false} axisLine={false} style={{ fontSize: '12px' }} width={50} />
                                                        <ChartTooltip content={<ChartTooltipContent indicator="line" />} />
                                                        <Area dataKey="brote" type="monotone" fill={CHART_COLORS.brote} stroke="none" fillOpacity={0.2} stackId="zones" />
                                                        <Area dataKey="alerta" type="monotone" fill={CHART_COLORS.alerta} stroke="none" fillOpacity={0.2} stackId="zones" />
                                                        <Area dataKey="seguridad" type="monotone" fill={CHART_COLORS.seguridad} stroke="none" fillOpacity={0.2} stackId="zones" />
                                                        <Area dataKey="exito" type="monotone" fill={CHART_COLORS.exito} stroke="none" fillOpacity={0.2} stackId="zones" />
                                                        {chartType === 'bar' && <Bar dataKey="casos_actual" name={`Casos ${anioReferencia}`} fill="hsl(var(--foreground))" fillOpacity={0.8} radius={[4, 4, 0, 0]} barSize={8} />}
                                                        {chartType === 'line' && <Line dataKey="casos_actual" name={`Casos ${anioReferencia}`} type="monotone" stroke="#1f2937" strokeWidth={2.5} dot={{ r: 3, fill: "#1f2937", strokeWidth: 0 }} />}
                                                        {chartType === 'area' && <Area dataKey="casos_actual" name={`Casos ${anioReferencia}`} type="monotone" stroke="hsl(var(--foreground))" fill="hsl(var(--foreground))" fillOpacity={0.1} strokeWidth={2.5} />}
                                                        <Legend content={<ChartLegendContent />} />
                                                    </ComposedChart>
                                                </ChartContainer>
                                            </div>
                                        )}
                                    </CardContent>
                                </Card>

                                {/* Charts secundarios */}
                                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                    <Card>
                                        <CardHeader className="pb-2">
                                            <div className="flex items-center justify-between">
                                                <CardTitle className="text-base">Distribución por Evento</CardTitle>
                                                <RangoBadge rango={rangoPreview} />
                                            </div>
                                        </CardHeader>
                                        <CardContent>
                                            <div className="h-[280px]">
                                                {loadingEventos ? (
                                                    <Skeleton className="h-full w-full" />
                                                ) : (
                                                    <ResponsiveContainer width="100%" height="100%">
                                                        <PieChart>
                                                            <Pie data={eventoPieData} cx="50%" cy="50%" innerRadius={50} outerRadius={90} paddingAngle={2} dataKey="value" label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`} labelLine={false}>
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

                                    <Card>
                                        <CardHeader className="pb-2">
                                            <div className="flex items-center justify-between">
                                                <CardTitle className="text-base">Distribución por Edad</CardTitle>
                                                <RangoBadge rango={rangoPreview} />
                                            </div>
                                        </CardHeader>
                                        <CardContent>
                                            <div className="h-[280px]">
                                                {loadingGrupo ? (
                                                    <Skeleton className="h-full w-full" />
                                                ) : (
                                                    <ResponsiveContainer width="100%" height="100%">
                                                        <BarChart data={grupoBarData} layout="vertical" margin={{ left: 80 }}>
                                                            <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} />
                                                            <XAxis type="number" />
                                                            <YAxis dataKey="grupo" type="category" tick={{ fontSize: 11 }} width={80} />
                                                            <ChartTooltip />
                                                            <Bar dataKey="casos" fill="hsl(217 91% 60%)" radius={[0, 4, 4, 0]} />
                                                        </BarChart>
                                                    </ResponsiveContainer>
                                                )}
                                            </div>
                                        </CardContent>
                                    </Card>
                                </div>

                                {/* Laboratorio */}
                                <Card>
                                    <CardHeader className="pb-2">
                                        <div className="flex items-center justify-between">
                                            <div>
                                                <CardTitle className="text-base flex items-center gap-2">
                                                    <FlaskConical className="h-4 w-4" />
                                                    Muestras Positivas por Agente
                                                </CardTitle>
                                                <CardDescription>Top 10 agentes etiológicos</CardDescription>
                                            </div>
                                            <RangoBadge rango={rangoPreview} />
                                        </div>
                                    </CardHeader>
                                    <CardContent>
                                        {loadingLab ? (
                                            <Skeleton className="h-[300px] w-full" />
                                        ) : labChartData.chartData.length > 0 ? (
                                            <div className="h-[300px]">
                                                <ResponsiveContainer width="100%" height="100%">
                                                    <BarChart data={labChartData.chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                                                        <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                                                        <XAxis dataKey="semana" tick={{ fontSize: 11 }} />
                                                        <YAxis tick={{ fontSize: 11 }} />
                                                        <ChartTooltip />
                                                        <Legend wrapperStyle={{ fontSize: "11px" }} />
                                                        {labChartData.agentes.map((agente, i) => (
                                                            <Bar key={agente} dataKey={agente} stackId="a" fill={agente === "Otros" ? "#9CA3AF" : PIE_COLORS[i % PIE_COLORS.length]} name={agente} />
                                                        ))}
                                                    </BarChart>
                                                </ResponsiveContainer>
                                            </div>
                                        ) : (
                                            <div className="h-[300px] flex items-center justify-center text-muted-foreground">
                                                No hay datos de laboratorio disponibles
                                            </div>
                                        )}
                                    </CardContent>
                                </Card>

                                {/* Eventos con cambios */}
                                <div className="border-t pt-6">
                                    <div className="mb-4">
                                        <h3 className="font-semibold flex items-center gap-2">
                                            <Activity className="h-5 w-5" />
                                            Eventos con Cambios Significativos
                                        </h3>
                                        <p className="text-sm text-muted-foreground">
                                            Comparando últimas 4 semanas vs 4 semanas anteriores
                                        </p>
                                        {topChangesData?.data?.periodo_actual && (
                                            <RangoBadge
                                                rango={`SE ${topChangesData.data.periodo_actual.semana_inicio}-${topChangesData.data.periodo_actual.semana_fin} vs ${topChangesData.data.periodo_anterior.semana_inicio}-${topChangesData.data.periodo_anterior.semana_fin}`}
                                                className="mt-2"
                                            />
                                        )}
                                    </div>

                                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                        {/* Crecimiento */}
                                        <Card className="border-rose-200 dark:border-rose-800">
                                            <CardHeader className="pb-2">
                                                <CardTitle className="text-base flex items-center gap-2 text-rose-700 dark:text-rose-400">
                                                    <TrendingUp className="h-4 w-4" />
                                                    Mayor Crecimiento
                                                </CardTitle>
                                            </CardHeader>
                                            <CardContent>
                                                {loadingTopChanges ? (
                                                    <Skeleton className="h-40 w-full" />
                                                ) : topCrecimiento.length > 0 ? (
                                                    <Table>
                                                        <TableHeader>
                                                            <TableRow>
                                                                <TableHead className="w-8"></TableHead>
                                                                <TableHead>Evento</TableHead>
                                                                <TableHead className="text-right">Cambio</TableHead>
                                                            </TableRow>
                                                        </TableHeader>
                                                        <TableBody>
                                                            {topCrecimiento.slice(0, 5).map((evento) => (
                                                                <TableRow key={evento.tipo_eno_id} className="cursor-pointer hover:bg-muted/50" onClick={() => toggleEvento(evento.tipo_eno_id)}>
                                                                    <TableCell>
                                                                        <Checkbox checked={eventosSeleccionados.has(evento.tipo_eno_id)} />
                                                                    </TableCell>
                                                                    <TableCell className="font-medium text-sm">{evento.tipo_eno_nombre}</TableCell>
                                                                    <TableCell className="text-right">
                                                                        <Badge variant="destructive" className="font-mono">+{evento.diferencia_porcentual.toFixed(0)}%</Badge>
                                                                    </TableCell>
                                                                </TableRow>
                                                            ))}
                                                        </TableBody>
                                                    </Table>
                                                ) : (
                                                    <p className="text-center py-4 text-muted-foreground text-sm">Sin datos</p>
                                                )}
                                            </CardContent>
                                        </Card>

                                        {/* Decrecimiento */}
                                        <Card className="border-emerald-200 dark:border-emerald-800">
                                            <CardHeader className="pb-2">
                                                <CardTitle className="text-base flex items-center gap-2 text-emerald-700 dark:text-emerald-400">
                                                    <TrendingDown className="h-4 w-4" />
                                                    Mayor Decrecimiento
                                                </CardTitle>
                                            </CardHeader>
                                            <CardContent>
                                                {loadingTopChanges ? (
                                                    <Skeleton className="h-40 w-full" />
                                                ) : topDecrecimiento.length > 0 ? (
                                                    <Table>
                                                        <TableHeader>
                                                            <TableRow>
                                                                <TableHead className="w-8"></TableHead>
                                                                <TableHead>Evento</TableHead>
                                                                <TableHead className="text-right">Cambio</TableHead>
                                                            </TableRow>
                                                        </TableHeader>
                                                        <TableBody>
                                                            {topDecrecimiento.slice(0, 5).map((evento) => (
                                                                <TableRow key={evento.tipo_eno_id} className="cursor-pointer hover:bg-muted/50" onClick={() => toggleEvento(evento.tipo_eno_id)}>
                                                                    <TableCell>
                                                                        <Checkbox checked={eventosSeleccionados.has(evento.tipo_eno_id)} />
                                                                    </TableCell>
                                                                    <TableCell className="font-medium text-sm">{evento.tipo_eno_nombre}</TableCell>
                                                                    <TableCell className="text-right">
                                                                        <Badge className="font-mono bg-emerald-100 text-emerald-800">{evento.diferencia_porcentual.toFixed(0)}%</Badge>
                                                                    </TableCell>
                                                                </TableRow>
                                                            ))}
                                                        </TableBody>
                                                    </Table>
                                                ) : (
                                                    <p className="text-center py-4 text-muted-foreground text-sm">Sin datos</p>
                                                )}
                                            </CardContent>
                                        </Card>
                                    </div>
                                </div>
                            </CollapsibleContent>
                        </Collapsible>

                    </div>
                </div>
            </SidebarInset>
        </SidebarProvider>
    );
}
