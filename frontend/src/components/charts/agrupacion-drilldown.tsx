/**
 * AgrupacionDrillDown - Panel de detalle para una agrupación de agentes.
 * 
 * Muestra los agentes individuales que componen una agrupación
 * con sus métricas y porcentajes.
 * 
 * Se usa como Sheet/Modal que se abre al hacer click en un chart.
 */

"use client";

import { useState, useEffect } from "react";
import { FlaskConical, Loader2 } from "lucide-react";

import {
    Sheet,
    SheetContent,
    SheetHeader,
    SheetTitle,
    SheetDescription,
} from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Progress } from "@/components/ui/progress";
import { useAgrupacionDetail } from "@/features/metricas/hooks/useAgrupaciones";
import type { PeriodoFilter } from "@/features/metricas";

interface AgrupacionDrillDownProps {
    /** Slug de la agrupación a mostrar */
    slug: string | null;
    /** Nombre display de la agrupación */
    nombre?: string;
    /** Color de la agrupación */
    color?: string;
    /** Filtro de período */
    periodoFilter: PeriodoFilter;
    /** Si el panel está abierto */
    open: boolean;
    /** Callback al cerrar */
    onClose: () => void;
}

interface AgenteData {
    id: number;
    slug: string;
    nombre: string;
    nombre_corto: string;
    valor: number;
}

export function AgrupacionDrillDown({
    slug,
    nombre,
    color,
    periodoFilter,
    open,
    onClose,
}: AgrupacionDrillDownProps) {
    const [agentesData, setAgentesData] = useState<AgenteData[]>([]);
    const [isLoadingMetrics, setIsLoadingMetrics] = useState(false);

    // Fetch agrupación detail con agentes
    const { data: agrupacionData, isLoading: loadingAgrupacion } = useAgrupacionDetail(
        slug || "",
        { enabled: open && !!slug }
    );

    // Fetch real metrics for each agente when agrupacion data is available
    useEffect(() => {
        if (!agrupacionData?.agentes || !open) {
            setAgentesData([]);
            return;
        }

        const fetchAgenteMetrics = async () => {
            setIsLoadingMetrics(true);

            try {
                // Fetch metrics for each agente individually using agente_id
                const results = await Promise.all(
                    agrupacionData.agentes.map(async (agente) => {
                        try {
                            const response = await fetch("/api/v1/metricas/query", {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                credentials: "include",
                                body: JSON.stringify({
                                    metric: "muestras_positivas",
                                    dimensions: [],
                                    filters: {
                                        periodo: periodoFilter,
                                        agente_id: agente.id,
                                    },
                                }),
                            });

                            if (!response.ok) {
                                return {
                                    id: agente.id,
                                    slug: agente.slug,
                                    nombre: agente.nombre,
                                    nombre_corto: agente.nombre_corto,
                                    valor: 0,
                                };
                            }

                            const data = await response.json();
                            const valor = data.data?.[0]?.valor || 0;

                            return {
                                id: agente.id,
                                slug: agente.slug,
                                nombre: agente.nombre,
                                nombre_corto: agente.nombre_corto,
                                valor: typeof valor === 'number' ? valor : 0,
                            };
                        } catch (error) {
                            console.warn(`Error fetching metrics for agente ${agente.id}:`, error);
                            return {
                                id: agente.id,
                                slug: agente.slug,
                                nombre: agente.nombre,
                                nombre_corto: agente.nombre_corto,
                                valor: 0,
                            };
                        }
                    })
                );

                // Sort by valor descending
                setAgentesData(results.sort((a, b) => b.valor - a.valor));
            } finally {
                setIsLoadingMetrics(false);
            }
        };

        fetchAgenteMetrics();
    }, [agrupacionData, periodoFilter, open]);

    const total = agentesData.reduce((sum, a) => sum + a.valor, 0);
    // isLoading calculated for potential future use
    const _ = loadingAgrupacion || isLoadingMetrics;
    void _; // Suppress unused warning

    return (
        <Sheet open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
            <SheetContent className="sm:max-w-lg">
                <SheetHeader className="pb-4">
                    <div className="flex items-center gap-3">
                        {color && (
                            <div
                                className="w-4 h-4 rounded-full shrink-0"
                                style={{ backgroundColor: color }}
                            />
                        )}
                        <SheetTitle className="text-xl flex items-center gap-2">
                            {nombre || agrupacionData?.nombre || "Cargando..."}
                            {isLoadingMetrics && <Loader2 className="h-4 w-4 animate-spin" />}
                        </SheetTitle>
                    </div>
                    <SheetDescription>
                        Detalle de agentes individuales que componen esta agrupación
                    </SheetDescription>
                </SheetHeader>

                {loadingAgrupacion ? (
                    <div className="space-y-4 mt-6">
                        {[1, 2, 3].map((i) => (
                            <div key={i} className="space-y-2">
                                <Skeleton className="h-5 w-3/4" />
                                <Skeleton className="h-4 w-full" />
                            </div>
                        ))}
                    </div>
                ) : agrupacionData?.agentes?.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-12 text-center text-muted-foreground">
                        <FlaskConical className="h-12 w-12 mb-4 opacity-30" />
                        <p>No hay agentes en esta agrupación</p>
                    </div>
                ) : (
                    <div className="space-y-6 mt-6">
                        {/* Summary card */}
                        <div className="bg-muted/50 rounded-lg p-4">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-muted-foreground">Total Positivos</p>
                                    <p className="text-3xl font-bold">
                                        {isLoadingMetrics ? (
                                            <Loader2 className="h-6 w-6 animate-spin inline" />
                                        ) : (
                                            total.toLocaleString()
                                        )}
                                    </p>
                                </div>
                                <div className="text-right">
                                    <p className="text-sm text-muted-foreground">Agentes</p>
                                    <p className="text-2xl font-semibold">
                                        {agrupacionData?.agentes?.length || 0}
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* Agents breakdown */}
                        <div className="space-y-3">
                            <h4 className="font-medium text-sm text-muted-foreground uppercase tracking-wide">
                                Desglose por agente
                            </h4>

                            {isLoadingMetrics ? (
                                <div className="space-y-4">
                                    {agrupacionData?.agentes?.slice(0, 5).map((_, i) => (
                                        <div key={i} className="space-y-2">
                                            <div className="flex justify-between">
                                                <Skeleton className="h-4 w-2/3" />
                                                <Skeleton className="h-4 w-16" />
                                            </div>
                                            <Skeleton className="h-2 w-full" />
                                        </div>
                                    ))}
                                </div>
                            ) : agentesData.length === 0 ? (
                                <p className="text-sm text-muted-foreground">
                                    No hay datos para el período seleccionado
                                </p>
                            ) : (
                                agentesData.map((agente) => {
                                    const pct = total > 0 ? (agente.valor / total) * 100 : 0;
                                    return (
                                        <div key={agente.id} className="space-y-1.5">
                                            <div className="flex items-center justify-between text-sm">
                                                <span className="font-medium truncate max-w-[70%]" title={agente.nombre}>
                                                    {agente.nombre_corto || agente.nombre.substring(0, 40)}
                                                </span>
                                                <div className="flex items-center gap-2">
                                                    <span className="font-mono">
                                                        {agente.valor.toLocaleString()}
                                                    </span>
                                                    <Badge variant="secondary" className="text-xs">
                                                        {pct.toFixed(1)}%
                                                    </Badge>
                                                </div>
                                            </div>
                                            <Progress
                                                value={pct}
                                                className="h-2"
                                                style={{
                                                    // @ts-expect-error CSS custom property
                                                    "--progress-background": color || "hsl(var(--primary))"
                                                }}
                                            />
                                        </div>
                                    );
                                })
                            )}
                        </div>

                        {/* Descripción */}
                        {agrupacionData?.descripcion && (
                            <div className="pt-4 border-t">
                                <h4 className="font-medium text-sm text-muted-foreground uppercase tracking-wide mb-2">
                                    Descripción
                                </h4>
                                <p className="text-sm text-muted-foreground">
                                    {agrupacionData.descripcion}
                                </p>
                            </div>
                        )}
                    </div>
                )}
            </SheetContent>
        </Sheet>
    );
}

export default AgrupacionDrillDown;
