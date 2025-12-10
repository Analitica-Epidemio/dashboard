"use client";

import { useMemo } from "react";
import { cn } from "@/lib/utils";
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip";

interface HeatmapProps {
    data: Array<{
        row: string;
        col: string;
        value: number;
    }>;
    className?: string;
    colorScale?: "blue" | "green" | "red" | "orange";
}

function getColor(value: number, max: number, scale: string): string {
    if (value === 0) return "hsl(var(--muted))";

    const intensity = Math.min(value / max, 1);

    const scales: Record<string, [number, number, number][]> = {
        blue: [[239, 246, 255], [59, 130, 246]],
        green: [[236, 253, 245], [16, 185, 129]],
        red: [[254, 242, 242], [239, 68, 68]],
        orange: [[255, 247, 237], [249, 115, 22]],
    };

    const [light, dark] = scales[scale] || scales.blue;

    const r = Math.round(light[0] + (dark[0] - light[0]) * intensity);
    const g = Math.round(light[1] + (dark[1] - light[1]) * intensity);
    const b = Math.round(light[2] + (dark[2] - light[2]) * intensity);

    return `rgb(${r}, ${g}, ${b})`;
}

export function AgenteHeatmap({ data, className, colorScale = "blue" }: HeatmapProps) {
    const { rows, cols, matrix, maxValue } = useMemo(() => {
        if (!data || data.length === 0) {
            return { rows: [], cols: [], matrix: {}, maxValue: 0 };
        }
        const rowSet = new Set<string>();
        const colSet = new Set<string>();

        data.forEach(d => {
            rowSet.add(d.row);
            colSet.add(d.col);
        });

        const rows = Array.from(rowSet).sort();
        const cols = Array.from(colSet).sort((a, b) => {
            // Try to sort numerically if they look like week numbers
            const numA = parseInt(a.replace(/\D/g, ''));
            const numB = parseInt(b.replace(/\D/g, ''));
            if (!isNaN(numA) && !isNaN(numB)) return numA - numB;
            return a.localeCompare(b);
        });

        const matrix: Record<string, Record<string, number>> = {};
        let maxValue = 0;

        rows.forEach(row => {
            matrix[row] = {};
            cols.forEach(col => {
                matrix[row][col] = 0;
            });
        });

        data.forEach(d => {
            matrix[d.row][d.col] = d.value;
            if (d.value > maxValue) maxValue = d.value;
        });

        return { rows, cols, matrix, maxValue };
    }, [data]);

    // Empty state - after hooks
    if (rows.length === 0 || cols.length === 0) {
        return (
            <div className={cn("h-[200px] flex items-center justify-center text-muted-foreground text-sm", className)}>
                No hay datos de actividad por agente
            </div>
        );
    }

    const cellSize = 24;
    const labelWidth = 100;
    const headerHeight = 40;

    return (
        <TooltipProvider>
            <div className={cn("overflow-x-auto", className)}>
                <div className="inline-block min-w-full">
                    {/* Header row */}
                    <div className="flex" style={{ paddingLeft: labelWidth }}>
                        {cols.map((col) => (
                            <div
                                key={col}
                                className="text-xs text-muted-foreground text-center"
                                style={{ width: cellSize, height: headerHeight }}
                            >
                                <span className="inline-block -rotate-45 origin-bottom-left whitespace-nowrap">
                                    {col}
                                </span>
                            </div>
                        ))}
                    </div>

                    {/* Data rows */}
                    {rows.map((row) => (
                        <div key={row} className="flex items-center">
                            <div
                                className="text-xs font-medium truncate pr-2"
                                style={{ width: labelWidth }}
                                title={row}
                            >
                                {row}
                            </div>
                            <div className="flex">
                                {cols.map((col) => {
                                    const value = matrix[row][col];
                                    return (
                                        <Tooltip key={`${row}-${col}`}>
                                            <TooltipTrigger asChild>
                                                <div
                                                    className="border border-background cursor-pointer transition-opacity hover:opacity-80"
                                                    style={{
                                                        width: cellSize,
                                                        height: cellSize,
                                                        backgroundColor: getColor(value, maxValue, colorScale),
                                                    }}
                                                />
                                            </TooltipTrigger>
                                            <TooltipContent>
                                                <div className="text-xs">
                                                    <p className="font-semibold">{row}</p>
                                                    <p>{col}: {value.toLocaleString()}</p>
                                                </div>
                                            </TooltipContent>
                                        </Tooltip>
                                    );
                                })}
                            </div>
                        </div>
                    ))}

                    {/* Legend */}
                    <div className="flex items-center gap-2 mt-4 ml-auto" style={{ paddingLeft: labelWidth }}>
                        <span className="text-xs text-muted-foreground">Menor</span>
                        <div className="flex">
                            {[0, 0.25, 0.5, 0.75, 1].map((intensity, i) => (
                                <div
                                    key={i}
                                    className="w-6 h-4"
                                    style={{
                                        backgroundColor: getColor(intensity * maxValue, maxValue, colorScale),
                                    }}
                                />
                            ))}
                        </div>
                        <span className="text-xs text-muted-foreground">Mayor</span>
                    </div>
                </div>
            </div>
        </TooltipProvider>
    );
}

export default AgenteHeatmap;
