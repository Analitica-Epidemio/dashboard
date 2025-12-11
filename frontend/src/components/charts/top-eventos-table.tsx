"use client";

import { useMemo } from "react";
import { cn } from "@/lib/utils";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";

interface TopEventosTableProps {
    data: Array<{
        evento: string;
        casos: number;
        variacion?: number;
        sparkline?: number[];
    }>;
    className?: string;
}

function MiniSparkline({ data, className }: { data: number[]; className?: string }) {
    if (!data || data.length === 0) return null;

    const max = Math.max(...data);
    const min = Math.min(...data);
    const range = max - min || 1;
    const width = 60;
    const height = 20;
    const padding = 2;

    const points = data.map((value, index) => {
        const x = padding + (index / (data.length - 1)) * (width - 2 * padding);
        const y = height - padding - ((value - min) / range) * (height - 2 * padding);
        return `${x},${y}`;
    }).join(" ");

    return (
        <svg width={width} height={height} className={cn("inline-block", className)}>
            <polyline
                points={points}
                fill="none"
                stroke="hsl(var(--primary))"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
            />
        </svg>
    );
}

function VariationBadge({ value }: { value: number }) {
    if (value === 0) {
        return (
            <span className="inline-flex items-center text-xs text-muted-foreground">
                <Minus className="h-3 w-3 mr-1" />
                0%
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

export function TopEventosTable({ data, className }: TopEventosTableProps) {
    // Hooks must be called before any early return
    const sortedData = useMemo(() => {
        if (!data || data.length === 0) return [];
        return [...data].sort((a, b) => b.casos - a.casos);
    }, [data]);

    // Empty state - after hooks
    if (!data || data.length === 0) {
        return (
            <div className={cn("h-[200px] flex items-center justify-center text-muted-foreground text-sm border rounded-md", className)}>
                No hay eventos registrados en este período
            </div>
        );
    }

    return (
        <div className={cn("rounded-md border", className)}>
            <Table>
                <TableHeader>
                    <TableRow>
                        <TableHead>Evento</TableHead>
                        <TableHead className="text-right">Casos</TableHead>
                        <TableHead className="text-right">Variación</TableHead>
                        <TableHead className="text-center">Tendencia</TableHead>
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {sortedData.map((row, index) => (
                        <TableRow key={index}>
                            <TableCell className="font-medium">{row.evento}</TableCell>
                            <TableCell className="text-right tabular-nums">
                                {row.casos.toLocaleString()}
                            </TableCell>
                            <TableCell className="text-right">
                                {row.variacion !== undefined && <VariationBadge value={row.variacion} />}
                            </TableCell>
                            <TableCell className="text-center">
                                {row.sparkline && <MiniSparkline data={row.sparkline} />}
                            </TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </div>
    );
}

export default TopEventosTable;
