"use client";

import { useState, useMemo } from "react";
import { TrendingUp, TrendingDown, GitCompareArrows, ArrowRight } from "lucide-react";
import {
    Area,
    AreaChart,
    Line,
    LineChart,
    CartesianGrid,
    Legend,
    ReferenceLine,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";

import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { cn } from "@/lib/utils";

import { useEventoDetails, type EventoCambio } from "@/features/analytics/api";

type ChartMode = "continua" | "comparacion";

interface EventoDetailDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    evento: EventoCambio | null;
    semanaActual: number;
    anioActual: number;
    numSemanas: number;
}

export function EventoDetailDialog({
    open,
    onOpenChange,
    evento,
    semanaActual,
    anioActual,
    numSemanas,
}: EventoDetailDialogProps) {
    const [chartMode, setChartMode] = useState<ChartMode>("continua");

    const { data, isLoading } = useEventoDetails({
        tipo_eno_id: evento?.tipo_eno_id ?? 0,
        semana_actual: semanaActual,
        anio_actual: anioActual,
        num_semanas: numSemanas,
    });

    const details = data?.data;

    // Continuous timeline: anterior → actual stitched together
    const { continuousData, transitionLabel } = useMemo(() => {
        if (!details?.trend_semanal) return { continuousData: [], transitionLabel: "" };

        const anteriorPoints: { semana: number; anio: number; casos: number }[] = [];
        const actualPoints: { semana: number; anio: number; casos: number }[] = [];

        for (const point of details.trend_semanal) {
            if (point.periodo === "anterior") {
                anteriorPoints.push({ semana: point.semana, anio: point.anio, casos: point.casos });
            } else {
                actualPoints.push({ semana: point.semana, anio: point.anio, casos: point.casos });
            }
        }

        anteriorPoints.sort((a, b) => a.anio - b.anio || a.semana - b.semana);
        actualPoints.sort((a, b) => a.anio - b.anio || a.semana - b.semana);

        const data: { label: string; anterior: number | null; actual: number | null }[] = [];

        for (const p of anteriorPoints) {
            data.push({ label: `SE${p.semana}/${p.anio}`, anterior: p.casos, actual: null });
        }

        if (anteriorPoints.length > 0 && actualPoints.length > 0) {
            const lastAnt = anteriorPoints[anteriorPoints.length - 1];
            const firstAct = actualPoints[0];
            data.push({
                label: `SE${firstAct.semana}/${firstAct.anio}`,
                anterior: lastAnt.casos,
                actual: firstAct.casos,
            });
            for (let i = 1; i < actualPoints.length; i++) {
                const p = actualPoints[i];
                data.push({ label: `SE${p.semana}/${p.anio}`, anterior: null, actual: p.casos });
            }
        } else {
            for (const p of actualPoints) {
                data.push({ label: `SE${p.semana}/${p.anio}`, anterior: null, actual: p.casos });
            }
        }

        const tLabel = actualPoints.length > 0 ? `SE${actualPoints[0].semana}/${actualPoints[0].anio}` : "";
        return { continuousData: data, transitionLabel: tLabel };
    }, [details?.trend_semanal]);

    // Overlaid comparison: same X axis (semana), two series
    const comparisonData = useMemo(() => {
        if (!details?.trend_semanal) return [];
        const weekMap = new Map<number, { semana: number; actual: number; anterior: number }>();

        for (const point of details.trend_semanal) {
            const existing = weekMap.get(point.semana) || { semana: point.semana, actual: 0, anterior: 0 };
            if (point.periodo === "actual") {
                existing.actual = point.casos;
            } else {
                existing.anterior = point.casos;
            }
            weekMap.set(point.semana, existing);
        }

        return Array.from(weekMap.values())
            .sort((a, b) => a.semana - b.semana)
            .map((d) => ({ ...d, label: `SE ${d.semana}` }));
    }, [details?.trend_semanal]);

    const pctChange = evento?.diferencia_porcentual ?? 0;
    const isPositive = pctChange > 0;

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-3xl max-h-[90vh] overflow-y-auto">
                {isLoading || !details ? (
                    <div className="space-y-4">
                        <div className="space-y-2">
                            <Skeleton className="h-6 w-48" />
                            <Skeleton className="h-4 w-32" />
                        </div>
                        <div className="grid grid-cols-3 gap-3">
                            <Skeleton className="h-20" />
                            <Skeleton className="h-20" />
                            <Skeleton className="h-20" />
                        </div>
                        <Skeleton className="h-[300px] w-full" />
                    </div>
                ) : (
                    <>
                        {/* Header */}
                        <DialogHeader>
                            <div className="flex items-center gap-2 flex-wrap">
                                <DialogTitle className="text-lg">
                                    {details.tipo_eno.nombre}
                                </DialogTitle>
                                <Badge variant="outline" className="text-xs">
                                    {details.grupo_eno.nombre}
                                </Badge>
                                <Badge
                                    className={cn(
                                        "font-mono text-xs",
                                        isPositive
                                            ? "bg-rose-100 text-rose-800 hover:bg-rose-100"
                                            : "bg-emerald-100 text-emerald-800 hover:bg-emerald-100"
                                    )}
                                >
                                    {isPositive ? (
                                        <TrendingUp className="h-3 w-3 mr-1" />
                                    ) : (
                                        <TrendingDown className="h-3 w-3 mr-1" />
                                    )}
                                    {isPositive ? "+" : ""}
                                    {pctChange.toFixed(0)}%
                                </Badge>
                            </div>
                            <DialogDescription>
                                Comparación de {numSemanas} semanas: período actual vs anterior
                            </DialogDescription>
                        </DialogHeader>

                        {/* Summary cards */}
                        <div className="grid grid-cols-3 gap-3">
                            <SummaryCard
                                label="Período actual"
                                value={details.resumen.casos_actuales}
                                className="border-blue-200"
                            />
                            <SummaryCard
                                label="Período anterior"
                                value={details.resumen.casos_anteriores}
                                className="border-muted"
                            />
                            <div
                                className={cn(
                                    "rounded-lg border p-3 text-center",
                                    isPositive ? "border-rose-200 bg-rose-50/50" : "border-emerald-200 bg-emerald-50/50"
                                )}
                            >
                                <p className="text-xs text-muted-foreground mb-1">Diferencia</p>
                                <div className="flex items-center justify-center gap-1.5">
                                    {isPositive ? (
                                        <TrendingUp className="h-4 w-4 text-rose-600" />
                                    ) : (
                                        <TrendingDown className="h-4 w-4 text-emerald-600" />
                                    )}
                                    <span
                                        className={cn(
                                            "text-xl font-bold",
                                            isPositive ? "text-rose-700" : "text-emerald-700"
                                        )}
                                    >
                                        {isPositive ? "+" : ""}
                                        {details.resumen.diferencia_absoluta}
                                    </span>
                                </div>
                                <p
                                    className={cn(
                                        "text-xs font-mono mt-0.5",
                                        isPositive ? "text-rose-600" : "text-emerald-600"
                                    )}
                                >
                                    {isPositive ? "+" : ""}
                                    {details.resumen.diferencia_porcentual.toFixed(1)}%
                                </p>
                            </div>
                        </div>

                        {/* Trend chart */}
                        <div>
                            <div className="flex items-center justify-between mb-2">
                                <h4 className="text-sm font-medium">Tendencia semanal</h4>
                                <ToggleGroup
                                    type="single"
                                    value={chartMode}
                                    onValueChange={(v) => { if (v) setChartMode(v as ChartMode); }}
                                    variant="outline"
                                    size="sm"
                                >
                                    <ToggleGroupItem value="continua" className="text-[10px] h-7 px-2 gap-1">
                                        <ArrowRight className="h-3 w-3" />
                                        Continua
                                    </ToggleGroupItem>
                                    <ToggleGroupItem value="comparacion" className="text-[10px] h-7 px-2 gap-1">
                                        <GitCompareArrows className="h-3 w-3" />
                                        Comparación
                                    </ToggleGroupItem>
                                </ToggleGroup>
                            </div>

                            {chartMode === "continua" ? (
                                <ContinuousChart data={continuousData} transitionLabel={transitionLabel} />
                            ) : (
                                <ComparisonChart data={comparisonData} />
                            )}
                        </div>
                    </>
                )}
            </DialogContent>
        </Dialog>
    );
}

// ── Continuous timeline chart ────────────────────────────────────────────────

function ContinuousChart({
    data,
    transitionLabel,
}: {
    data: { label: string; anterior: number | null; actual: number | null }[];
    transitionLabel: string;
}) {
    if (data.length === 0) return <EmptyChart />;

    return (
        <ResponsiveContainer width="100%" height={280}>
            <LineChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis
                    dataKey="label"
                    tick={{ fontSize: 10 }}
                    interval={0}
                    angle={-35}
                    textAnchor="end"
                    height={50}
                />
                <YAxis tick={{ fontSize: 11 }} width={40} />
                {transitionLabel && (
                    <ReferenceLine
                        x={transitionLabel}
                        stroke="#94a3b8"
                        strokeDasharray="3 3"
                        label={{ value: "Inicio actual", position: "top", fontSize: 9, fill: "#64748b" }}
                    />
                )}
                <Tooltip
                    content={({ active, payload }) => {
                        if (!active || !payload?.length) return null;
                        const d = payload[0].payload;
                        const casos = d.actual ?? d.anterior;
                        const periodo = d.actual != null ? "Actual" : "Anterior";
                        const color = d.actual != null ? "#3b82f6" : "#9ca3af";
                        return (
                            <div className="rounded-lg border bg-background p-2.5 shadow-sm text-xs space-y-1">
                                <p className="font-medium">{d.label}</p>
                                <div className="flex items-center gap-2">
                                    <span className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
                                    <span className="text-muted-foreground">{periodo}:</span>
                                    <span className="font-mono font-medium">{casos} casos</span>
                                </div>
                            </div>
                        );
                    }}
                />
                <Line
                    type="monotone"
                    dataKey="anterior"
                    name="Período anterior"
                    stroke="#9ca3af"
                    strokeWidth={2}
                    dot={{ r: 3, fill: "#9ca3af", strokeWidth: 0 }}
                    connectNulls={false}
                />
                <Line
                    type="monotone"
                    dataKey="actual"
                    name="Período actual"
                    stroke="#3b82f6"
                    strokeWidth={2.5}
                    dot={{ r: 3.5, fill: "#3b82f6", strokeWidth: 0 }}
                    connectNulls={false}
                />
                <Legend wrapperStyle={{ fontSize: "11px" }} />
            </LineChart>
        </ResponsiveContainer>
    );
}

// ── Overlaid comparison chart ────────────────────────────────────────────────

function ComparisonChart({
    data,
}: {
    data: { label: string; actual: number; anterior: number }[];
}) {
    if (data.length === 0) return <EmptyChart />;

    return (
        <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <defs>
                    <linearGradient id="gradActual" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="gradAnterior" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#9ca3af" stopOpacity={0.2} />
                        <stop offset="95%" stopColor="#9ca3af" stopOpacity={0} />
                    </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} width={40} />
                <Tooltip
                    content={({ active, payload }) => {
                        if (!active || !payload?.length) return null;
                        const d = payload[0].payload;
                        return (
                            <div className="rounded-lg border bg-background p-2.5 shadow-sm text-xs space-y-1">
                                <p className="font-medium">{d.label}</p>
                                <div className="flex items-center gap-2">
                                    <span className="w-2 h-2 rounded-full bg-blue-500" />
                                    <span className="text-muted-foreground">Actual:</span>
                                    <span className="font-mono font-medium">{d.actual} casos</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <span className="w-2 h-2 rounded-full bg-gray-400" />
                                    <span className="text-muted-foreground">Anterior:</span>
                                    <span className="font-mono font-medium">{d.anterior} casos</span>
                                </div>
                            </div>
                        );
                    }}
                />
                <Area
                    type="monotone"
                    dataKey="anterior"
                    name="Período anterior"
                    stroke="#9ca3af"
                    strokeWidth={1.5}
                    strokeDasharray="4 3"
                    fillOpacity={1}
                    fill="url(#gradAnterior)"
                />
                <Area
                    type="monotone"
                    dataKey="actual"
                    name="Período actual"
                    stroke="#3b82f6"
                    strokeWidth={2.5}
                    fillOpacity={1}
                    fill="url(#gradActual)"
                />
                <Legend wrapperStyle={{ fontSize: "11px" }} />
            </AreaChart>
        </ResponsiveContainer>
    );
}

// ── Shared helpers ───────────────────────────────────────────────────────────

function EmptyChart() {
    return (
        <div className="h-[280px] flex items-center justify-center text-muted-foreground text-sm">
            No hay datos de tendencia disponibles
        </div>
    );
}

function SummaryCard({
    label,
    value,
    className,
}: {
    label: string;
    value: number;
    className?: string;
}) {
    return (
        <div className={cn("rounded-lg border p-3 text-center", className)}>
            <p className="text-xs text-muted-foreground mb-1">{label}</p>
            <p className="text-2xl font-bold">{value.toLocaleString()}</p>
            <p className="text-[10px] text-muted-foreground">casos</p>
        </div>
    );
}
