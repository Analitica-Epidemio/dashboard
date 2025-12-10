"use client";

import { useState, useMemo, useCallback } from "react";
import { cn } from "@/lib/utils";
import { ArrowUpDown, ChevronDown, ChevronUp } from "lucide-react";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";

interface LaboratorioTableRow {
    semana: string | number;
    muestras: number;
    fluA?: number;
    fluB?: number;
    vsr?: number;
    covid?: number;
    otros?: number;
    totalPositivos: number;
    positividad: number;
}

interface LaboratorioTableProps {
    data: LaboratorioTableRow[];
    className?: string;
    /** Compact mode - shows only essential columns */
    compact?: boolean;
    /** YoY comparison data - same structure as data, keyed by semana */
    comparisonData?: LaboratorioTableRow[];
    /** Show comparison columns */
    showComparison?: boolean;
    /** Label for comparison (e.g., "2024") */
    comparisonLabel?: string;
}

type SortField = "semana" | "muestras" | "totalPositivos" | "positividad";
type SortDirection = "asc" | "desc";

export function LaboratorioTable({
    data,
    className,
    compact = false,
    comparisonData,
    showComparison = false,
    comparisonLabel = "Anterior"
}: LaboratorioTableProps) {
    const [sortField, setSortField] = useState<SortField>("semana");
    const [sortDirection, setSortDirection] = useState<SortDirection>("desc");

    // All hooks must be called before any early returns
    const sortedData = useMemo(() => {
        if (!data || data.length === 0) return [];
        return [...data].sort((a, b) => {
            let aVal: number;
            let bVal: number;

            if (sortField === "semana") {
                aVal = typeof a.semana === 'number' ? a.semana : parseInt(String(a.semana).replace(/\D/g, '')) || 0;
                bVal = typeof b.semana === 'number' ? b.semana : parseInt(String(b.semana).replace(/\D/g, '')) || 0;
            } else {
                aVal = a[sortField] ?? 0;
                bVal = b[sortField] ?? 0;
            }

            return sortDirection === "asc" ? aVal - bVal : bVal - aVal;
        });
    }, [data, sortField, sortDirection]);

    // Build comparison map for quick lookup
    const comparisonMap = useMemo(() => {
        if (!comparisonData || !showComparison) return new Map<string | number, LaboratorioTableRow>();
        const map = new Map<string | number, LaboratorioTableRow>();
        comparisonData.forEach(row => {
            // Normalize semana key (e.g., "SE 5" -> 5)
            const key = typeof row.semana === 'string'
                ? row.semana.replace(/\D/g, '')
                : String(row.semana);
            map.set(key, row);
        });
        return map;
    }, [comparisonData, showComparison]);

    const handleSort = useCallback((field: SortField) => {
        if (sortField === field) {
            setSortDirection(prev => prev === "asc" ? "desc" : "asc");
        } else {
            setSortField(field);
            setSortDirection("desc");
        }
    }, [sortField]);

    // Helper to get comparison row
    const getComparison = useCallback((semana: string | number): LaboratorioTableRow | undefined => {
        const key = typeof semana === 'string' ? semana.replace(/\D/g, '') : String(semana);
        return comparisonMap.get(key);
    }, [comparisonMap]);

    // Helper to calculate delta
    const calcDelta = useCallback((current: number, previous: number | undefined): number | null => {
        if (previous === undefined || previous === 0) return null;
        return ((current - previous) / previous) * 100;
    }, []);

    // Empty state - after all hooks
    if (!data || data.length === 0) {
        return (
            <div className={cn("h-[200px] flex items-center justify-center text-muted-foreground text-sm border rounded-md", className)}>
                No hay datos de laboratorio en este período
            </div>
        );
    }

    const SortIcon = ({ field }: { field: SortField }) => {
        if (sortField !== field) {
            return <ArrowUpDown className="ml-2 h-4 w-4" />;
        }
        return sortDirection === "asc" ? (
            <ChevronUp className="ml-2 h-4 w-4" />
        ) : (
            <ChevronDown className="ml-2 h-4 w-4" />
        );
    };

    // Compact mode - simpler, more condensed table
    if (compact) {
        return (
            <div className={cn("rounded-md border text-sm", className)}>
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead className="py-2">Semana</TableHead>
                            <TableHead className="text-right py-2">Muestras</TableHead>
                            {showComparison && <TableHead className="text-right py-2">{comparisonLabel}</TableHead>}
                            <TableHead className="text-right py-2">Positivos</TableHead>
                            <TableHead className="text-right py-2">
                                {showComparison ? "Δ% Pos" : "% Pos"}
                            </TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {sortedData.map((row, index) => {
                            const comp = getComparison(row.semana);
                            const posDelta = calcDelta(row.positividad, comp?.positividad);
                            return (
                                <TableRow key={index}>
                                    <TableCell className="py-1.5 font-medium">{row.semana}</TableCell>
                                    <TableCell className="text-right py-1.5 tabular-nums">{row.muestras.toLocaleString()}</TableCell>
                                    {showComparison && (
                                        <TableCell className="text-right py-1.5 tabular-nums text-muted-foreground">
                                            {comp?.muestras?.toLocaleString() ?? "—"}
                                        </TableCell>
                                    )}
                                    <TableCell className="text-right py-1.5 tabular-nums">{row.totalPositivos}</TableCell>
                                    <TableCell className="text-right py-1.5 tabular-nums">
                                        {showComparison && posDelta !== null ? (
                                            <span className={cn(
                                                posDelta > 0 ? "text-rose-600" :
                                                    posDelta < 0 ? "text-emerald-600" :
                                                        "text-muted-foreground"
                                            )}>
                                                {posDelta > 0 ? "+" : ""}{posDelta.toFixed(0)}%
                                            </span>
                                        ) : showComparison ? (
                                            <span className="text-muted-foreground">—</span>
                                        ) : (
                                            <span className={cn(
                                                row.positividad > 30 ? "text-rose-600" :
                                                    row.positividad > 15 ? "text-amber-600" :
                                                        "text-emerald-600"
                                            )}>
                                                {row.positividad.toFixed(1)}%
                                            </span>
                                        )}
                                    </TableCell>
                                </TableRow>
                            );
                        })}
                    </TableBody>
                </Table>
            </div>
        );
    }

    // Full mode - all columns with sort buttons
    return (
        <div className={cn("rounded-md border", className)}>
            <Table>
                <TableHeader>
                    <TableRow>
                        <TableHead>
                            <Button variant="ghost" size="sm" className="-ml-4" onClick={() => handleSort("semana")}>
                                Semana
                                <SortIcon field="semana" />
                            </Button>
                        </TableHead>
                        <TableHead className="text-right">
                            <Button variant="ghost" size="sm" onClick={() => handleSort("muestras")}>
                                Muestras
                                <SortIcon field="muestras" />
                            </Button>
                        </TableHead>
                        <TableHead className="text-right">Flu A</TableHead>
                        <TableHead className="text-right">Flu B</TableHead>
                        <TableHead className="text-right">VSR</TableHead>
                        <TableHead className="text-right">COVID</TableHead>
                        <TableHead className="text-right">Otros</TableHead>
                        <TableHead className="text-right">
                            <Button variant="ghost" size="sm" onClick={() => handleSort("totalPositivos")}>
                                Total+
                                <SortIcon field="totalPositivos" />
                            </Button>
                        </TableHead>
                        <TableHead className="text-right">
                            <Button variant="ghost" size="sm" onClick={() => handleSort("positividad")}>
                                % Pos
                                <SortIcon field="positividad" />
                            </Button>
                        </TableHead>
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {sortedData.map((row, index) => (
                        <TableRow key={index}>
                            <TableCell className="font-medium">{row.semana}</TableCell>
                            <TableCell className="text-right tabular-nums">{row.muestras.toLocaleString()}</TableCell>
                            <TableCell className="text-right tabular-nums">{row.fluA ?? 0}</TableCell>
                            <TableCell className="text-right tabular-nums">{row.fluB ?? 0}</TableCell>
                            <TableCell className="text-right tabular-nums">{row.vsr ?? 0}</TableCell>
                            <TableCell className="text-right tabular-nums">{row.covid ?? 0}</TableCell>
                            <TableCell className="text-right tabular-nums">{row.otros ?? 0}</TableCell>
                            <TableCell className="text-right tabular-nums font-medium">{row.totalPositivos}</TableCell>
                            <TableCell className="text-right tabular-nums">
                                <span className={cn(
                                    row.positividad > 30 ? "text-rose-600" :
                                        row.positividad > 15 ? "text-amber-600" :
                                            "text-emerald-600"
                                )}>
                                    {row.positividad.toFixed(1)}%
                                </span>
                            </TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </div>
    );
}

export default LaboratorioTable;
