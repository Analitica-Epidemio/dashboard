"use client";

/**
 * Analytics page with 2-column layout:
 * - Left: Dashboard analítico (charts + cambios significativos)
 * - Right: Panel de creación de boletín
 * Sidebar collapsed by default to maximize horizontal space.
 */

import { useState, useMemo, useCallback } from "react";
import {
    Activity,
    BarChart3,
    AreaChart as AreaChartIcon,
    LineChart as LineChartIcon,
    TrendingUp,
    TrendingDown,
    FlaskConical,
    Clock,
    Newspaper,
} from "lucide-react";

import { AppSidebar } from "@/features/layout/components/app-sidebar";
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Checkbox } from "@/components/ui/checkbox";
import { Separator } from "@/components/ui/separator";
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
    ResizablePanelGroup,
    ResizablePanel,
    ResizableHandle,
} from "@/components/ui/resizable";
import { cn } from "@/lib/utils";

import {
    ChartContainer,
    ChartTooltip,
    ChartTooltipContent,
    ChartLegendContent,
    type ChartConfig,
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
import { useTopChangesByGroup, useGenerateDraft, usePreviewDraft, type EventoCambio } from "@/features/analytics/api";
import { useEventosDisponibles } from "@/features/boletines/api";
import { BoletinCreationPanel } from "@/features/analytics/components/boletin-creation-panel";
import type { EventoSeleccionado } from "@/features/boletines/types";

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

export default function AnalyticsPage() {
    // State
    const [semanaReferencia, setSemanaReferencia] = useState(getCurrentWeek());
    const [anioReferencia, setAnioReferencia] = useState(CURRENT_YEAR);
    const [eventosSeleccionados, setEventosSeleccionados] = useState<EventoSeleccionado[]>([]);
    const [chartType, setChartType] = useState<string>("area");
    const [numSemanas, setNumSemanas] = useState(4);
    const [tituloCustom, setTituloCustom] = useState("");
    const [generatedContent, setGeneratedContent] = useState<string | null>(null);
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const [generatedInstanceId, setGeneratedInstanceId] = useState<number | null>(null);

    const rangoPreview = `SE 1 - ${semanaReferencia} / ${anioReferencia}`;

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

    const { data: eventosDisponiblesData } = useEventosDisponibles();

    // Lookup map: tipo_eno_id -> evento info
    const eventosLookup = useMemo(() => {
        const map = new Map<number, { id: number; codigo: string; nombre: string; tipo: EventoSeleccionado["tipo"] }>();
        const eventos = eventosDisponiblesData?.data || [];
        for (const e of eventos) {
            map.set(e.id, { id: e.id, codigo: e.codigo, nombre: e.nombre, tipo: e.tipo as EventoSeleccionado["tipo"] });
        }
        return map;
    }, [eventosDisponiblesData]);

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
        num_semanas: numSemanas,
        limit: 10,
    });

    const previewDraftMutation = usePreviewDraft();
    const generateDraftMutation = useGenerateDraft();

    // Selected IDs set for checkbox lookup
    const selectedIds = useMemo(
        () => new Set(eventosSeleccionados.map((e) => e.id)),
        [eventosSeleccionados]
    );

    // Toggle evento from checkbox in changes table
    const toggleEventoFromTable = useCallback((evento: EventoCambio) => {
        setEventosSeleccionados(prev => {
            const exists = prev.some(e => e.id === evento.tipo_eno_id);
            if (exists) {
                return prev.filter(e => e.id !== evento.tipo_eno_id).map((e, i) => ({ ...e, order: i }));
            }
            // Look up full info from eventos disponibles
            const lookup = eventosLookup.get(evento.tipo_eno_id);
            const newEvento: EventoSeleccionado = {
                id: evento.tipo_eno_id,
                codigo: lookup?.codigo || `ENO_${evento.tipo_eno_id}`,
                nombre: evento.tipo_eno_nombre,
                tipo: lookup?.tipo || "tipo_eno",
                order: prev.length,
            };
            return [...prev, newEvento];
        });
    }, [eventosLookup]);

    // Add evento from quick-add
    const handleAddEvento = useCallback((evento: EventoSeleccionado) => {
        setEventosSeleccionados(prev => {
            if (prev.some(e => e.codigo === evento.codigo)) return prev;
            return [...prev, { ...evento, order: prev.length }];
        });
    }, []);

    const buildRequestBody = useCallback(() => ({
        semana: semanaReferencia,
        anio: anioReferencia,
        num_semanas: numSemanas,
        eventos_seleccionados: eventosSeleccionados.length > 0
            ? eventosSeleccionados.map(e => ({
                tipo_eno_id: e.id,
                incluir_charts: true,
            }))
            : [],
    }), [eventosSeleccionados, semanaReferencia, anioReferencia, numSemanas]);

    // Preview boletín (does NOT save to DB)
    const handlePreview = useCallback(async () => {
        try {
            const result = await previewDraftMutation.mutateAsync(buildRequestBody());
            if (result?.data) {
                setGeneratedContent(result.data.content || null);
            }
        } catch (error) {
            console.error("Error previewing boletín:", error);
        }
    }, [buildRequestBody, previewDraftMutation]);

    // Create boletín in DB and navigate to editor
    const handleEditInEditor = useCallback(async () => {
        try {
            const result = await generateDraftMutation.mutateAsync(buildRequestBody());
            if (result?.data?.boletin_instance_id) {
                setGeneratedInstanceId(result.data.boletin_instance_id);
                return result.data.boletin_instance_id;
            }
        } catch (error) {
            console.error("Error creating boletín:", error);
        }
        return null;
    }, [buildRequestBody, generateDraftMutation]);

    // === PROCESS DATA ===

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
                p25, p50, p75,
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
            .map(([semana, agentesData]) => ({ semana: `SE ${semana}`, ...agentesData }));
        const agentesFinales = [...topAgentes];
        if (agenteTotals.size > MAX_AGENTES) agentesFinales.push("Otros");
        return { chartData, agentes: agentesFinales };
    }, [labData]);

    return (
        <SidebarProvider defaultOpen={false}>
            <AppSidebar variant="inset" />
            <SidebarInset className="bg-muted/10 h-screen overflow-hidden flex flex-col">
                {/* Compact header */}
                <header className="flex items-center h-14 gap-3 border-b bg-background px-4 shrink-0">
                    <SidebarTrigger className="-ml-1" />
                    <Separator orientation="vertical" className="h-6" />
                    <Newspaper className="h-5 w-5 text-muted-foreground shrink-0" />
                    <h1 className="text-lg font-semibold whitespace-nowrap">Boletines</h1>
                    <div className="flex items-center gap-2 ml-auto">
                        <Select
                            value={semanaReferencia.toString()}
                            onValueChange={(v) => setSemanaReferencia(parseInt(v))}
                        >
                            <SelectTrigger className="w-[100px] h-8 text-xs font-mono">
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
                        <span className="text-muted-foreground text-sm">/</span>
                        <Select
                            value={anioReferencia.toString()}
                            onValueChange={(v) => setAnioReferencia(parseInt(v))}
                        >
                            <SelectTrigger className="w-[80px] h-8 text-xs font-mono">
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
                </header>

                {/* Two-column layout */}
                <ResizablePanelGroup direction="horizontal" className="flex-1">
                    {/* Left panel: Dashboard analítico */}
                    <ResizablePanel defaultSize={62} minSize={45}>
                        <div className="flex-1 overflow-y-auto h-full p-4 space-y-4">
                            {/* Corredor Endémico - Hero chart */}
                            <Card>
                                <CardHeader className="pb-2 py-3">
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <CardTitle className="text-sm">Corredor Endémico</CardTitle>
                                            <CardDescription className="text-xs">
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
                                <CardContent className="pb-3">
                                    {loadingCorredor ? (
                                        <Skeleton className="h-[280px] w-full" />
                                    ) : (
                                        <div className="h-[280px]">
                                            <ChartContainer config={corredorConfig} className="h-full w-full">
                                                <ComposedChart data={corredorChartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                                                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                                                    <XAxis dataKey="label" tickLine={false} axisLine={false} tickMargin={8} minTickGap={30} style={{ fontSize: '11px' }} />
                                                    <YAxis tickLine={false} axisLine={false} style={{ fontSize: '11px' }} width={45} />
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

                            {/* Cambios Significativos - 2 col with checkboxes */}
                            <div>
                                <div className="flex items-center gap-2 mb-3">
                                    <Activity className="h-4 w-4 text-muted-foreground" />
                                    <h3 className="text-sm font-semibold">Cambios Significativos</h3>
                                    {topChangesData?.data?.periodo_actual && (
                                        <RangoBadge
                                            rango={`SE ${topChangesData.data.periodo_actual.semana_inicio}-${topChangesData.data.periodo_actual.semana_fin} vs ${topChangesData.data.periodo_anterior.semana_inicio}-${topChangesData.data.periodo_anterior.semana_fin}`}
                                        />
                                    )}
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    {/* Crecimiento */}
                                    <Card className="border-rose-200 dark:border-rose-800">
                                        <CardHeader className="pb-1 py-2 px-3">
                                            <CardTitle className="text-xs flex items-center gap-1.5 text-rose-700 dark:text-rose-400">
                                                <TrendingUp className="h-3.5 w-3.5" />
                                                Mayor Crecimiento
                                            </CardTitle>
                                        </CardHeader>
                                        <CardContent className="px-3 pb-2">
                                            {loadingTopChanges ? (
                                                <Skeleton className="h-32 w-full" />
                                            ) : topCrecimiento.length > 0 ? (
                                                <Table>
                                                    <TableHeader>
                                                        <TableRow>
                                                            <TableHead className="w-7 px-1"></TableHead>
                                                            <TableHead className="text-xs px-1">Evento</TableHead>
                                                            <TableHead className="text-xs text-right px-1">Cambio</TableHead>
                                                        </TableRow>
                                                    </TableHeader>
                                                    <TableBody>
                                                        {topCrecimiento.map((evento) => (
                                                            <TableRow
                                                                key={evento.tipo_eno_id}
                                                                className="cursor-pointer hover:bg-muted/50"
                                                                onClick={() => toggleEventoFromTable(evento)}
                                                            >
                                                                <TableCell className="px-1">
                                                                    <Checkbox checked={selectedIds.has(evento.tipo_eno_id)} />
                                                                </TableCell>
                                                                <TableCell className="font-medium text-xs px-1 truncate max-w-[180px]">
                                                                    {evento.tipo_eno_nombre}
                                                                </TableCell>
                                                                <TableCell className="text-right px-1">
                                                                    <Badge variant="destructive" className="font-mono text-[10px]">
                                                                        +{evento.diferencia_porcentual.toFixed(0)}%
                                                                    </Badge>
                                                                </TableCell>
                                                            </TableRow>
                                                        ))}
                                                    </TableBody>
                                                </Table>
                                            ) : (
                                                <p className="text-center py-3 text-muted-foreground text-xs">Sin datos</p>
                                            )}
                                        </CardContent>
                                    </Card>

                                    {/* Decrecimiento */}
                                    <Card className="border-emerald-200 dark:border-emerald-800">
                                        <CardHeader className="pb-1 py-2 px-3">
                                            <CardTitle className="text-xs flex items-center gap-1.5 text-emerald-700 dark:text-emerald-400">
                                                <TrendingDown className="h-3.5 w-3.5" />
                                                Mayor Decrecimiento
                                            </CardTitle>
                                        </CardHeader>
                                        <CardContent className="px-3 pb-2">
                                            {loadingTopChanges ? (
                                                <Skeleton className="h-32 w-full" />
                                            ) : topDecrecimiento.length > 0 ? (
                                                <Table>
                                                    <TableHeader>
                                                        <TableRow>
                                                            <TableHead className="w-7 px-1"></TableHead>
                                                            <TableHead className="text-xs px-1">Evento</TableHead>
                                                            <TableHead className="text-xs text-right px-1">Cambio</TableHead>
                                                        </TableRow>
                                                    </TableHeader>
                                                    <TableBody>
                                                        {topDecrecimiento.map((evento) => (
                                                            <TableRow
                                                                key={evento.tipo_eno_id}
                                                                className="cursor-pointer hover:bg-muted/50"
                                                                onClick={() => toggleEventoFromTable(evento)}
                                                            >
                                                                <TableCell className="px-1">
                                                                    <Checkbox checked={selectedIds.has(evento.tipo_eno_id)} />
                                                                </TableCell>
                                                                <TableCell className="font-medium text-xs px-1 truncate max-w-[180px]">
                                                                    {evento.tipo_eno_nombre}
                                                                </TableCell>
                                                                <TableCell className="text-right px-1">
                                                                    <Badge className="font-mono text-[10px] bg-emerald-100 text-emerald-800">
                                                                        {evento.diferencia_porcentual.toFixed(0)}%
                                                                    </Badge>
                                                                </TableCell>
                                                            </TableRow>
                                                        ))}
                                                    </TableBody>
                                                </Table>
                                            ) : (
                                                <p className="text-center py-3 text-muted-foreground text-xs">Sin datos</p>
                                            )}
                                        </CardContent>
                                    </Card>
                                </div>
                            </div>

                            {/* Pie + Bar - 2 col */}
                            <div className="grid grid-cols-2 gap-4">
                                <Card>
                                    <CardHeader className="pb-1 py-2 px-3">
                                        <div className="flex items-center justify-between">
                                            <CardTitle className="text-xs">Distribución por Evento</CardTitle>
                                            <RangoBadge rango={rangoPreview} />
                                        </div>
                                    </CardHeader>
                                    <CardContent className="px-3 pb-2">
                                        <div className="h-[220px]">
                                            {loadingEventos ? (
                                                <Skeleton className="h-full w-full" />
                                            ) : (
                                                <ResponsiveContainer width="100%" height="100%">
                                                    <PieChart>
                                                        <Pie
                                                            data={eventoPieData}
                                                            cx="50%"
                                                            cy="50%"
                                                            innerRadius={40}
                                                            outerRadius={75}
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

                                <Card>
                                    <CardHeader className="pb-1 py-2 px-3">
                                        <div className="flex items-center justify-between">
                                            <CardTitle className="text-xs">Distribución por Edad</CardTitle>
                                            <RangoBadge rango={rangoPreview} />
                                        </div>
                                    </CardHeader>
                                    <CardContent className="px-3 pb-2">
                                        <div className="h-[220px]">
                                            {loadingGrupo ? (
                                                <Skeleton className="h-full w-full" />
                                            ) : (
                                                <ResponsiveContainer width="100%" height="100%">
                                                    <BarChart data={grupoBarData} layout="vertical" margin={{ left: 70 }}>
                                                        <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} />
                                                        <XAxis type="number" tick={{ fontSize: 10 }} />
                                                        <YAxis dataKey="grupo" type="category" tick={{ fontSize: 10 }} width={70} />
                                                        <ChartTooltip />
                                                        <Bar dataKey="casos" fill="hsl(217 91% 60%)" radius={[0, 4, 4, 0]} />
                                                    </BarChart>
                                                </ResponsiveContainer>
                                            )}
                                        </div>
                                    </CardContent>
                                </Card>
                            </div>

                            {/* Lab chart */}
                            <Card>
                                <CardHeader className="pb-1 py-2 px-3">
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <CardTitle className="text-xs flex items-center gap-1.5">
                                                <FlaskConical className="h-3.5 w-3.5" />
                                                Muestras Positivas por Agente
                                            </CardTitle>
                                            <CardDescription className="text-[10px]">Top 10 agentes etiológicos</CardDescription>
                                        </div>
                                        <RangoBadge rango={rangoPreview} />
                                    </div>
                                </CardHeader>
                                <CardContent className="px-3 pb-2">
                                    {loadingLab ? (
                                        <Skeleton className="h-[250px] w-full" />
                                    ) : labChartData.chartData.length > 0 ? (
                                        <div className="h-[250px]">
                                            <ResponsiveContainer width="100%" height="100%">
                                                <BarChart data={labChartData.chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                                                    <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                                                    <XAxis dataKey="semana" tick={{ fontSize: 10 }} />
                                                    <YAxis tick={{ fontSize: 10 }} />
                                                    <ChartTooltip />
                                                    <Legend wrapperStyle={{ fontSize: "10px" }} />
                                                    {labChartData.agentes.map((agente, i) => (
                                                        <Bar key={agente} dataKey={agente} stackId="a" fill={agente === "Otros" ? "#9CA3AF" : PIE_COLORS[i % PIE_COLORS.length]} name={agente} />
                                                    ))}
                                                </BarChart>
                                            </ResponsiveContainer>
                                        </div>
                                    ) : (
                                        <div className="h-[250px] flex items-center justify-center text-muted-foreground text-xs">
                                            No hay datos de laboratorio disponibles
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        </div>
                    </ResizablePanel>

                    <ResizableHandle withHandle />

                    {/* Right panel: Boletín creation */}
                    <ResizablePanel defaultSize={38} minSize={25} maxSize={50}>
                        <BoletinCreationPanel
                            eventosSeleccionados={eventosSeleccionados}
                            semana={semanaReferencia}
                            anio={anioReferencia}
                            numSemanas={numSemanas}
                            tituloCustom={tituloCustom}
                            onEventosChange={setEventosSeleccionados}
                            onAddEvento={handleAddEvento}
                            onNumSemanasChange={setNumSemanas}
                            onTituloChange={setTituloCustom}
                            onPreview={handlePreview}
                            isPreviewing={previewDraftMutation.isPending}
                            onEditInEditor={handleEditInEditor}
                            isCreating={generateDraftMutation.isPending}
                            generatedContent={generatedContent}
                        />
                    </ResizablePanel>
                </ResizablePanelGroup>
            </SidebarInset>
        </SidebarProvider>
    );
}
