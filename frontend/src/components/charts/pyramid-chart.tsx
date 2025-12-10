"use client";

import { useMemo } from "react";
import { cn } from "@/lib/utils";
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    ResponsiveContainer,
    Tooltip,
    Legend,
} from "recharts";

interface PyramidChartProps {
    data: Array<{
        grupo: string;
        masculino: number;
        femenino: number;
    }>;
    className?: string;
}

const MALE_COLOR = "hsl(217 91% 60%)";
const FEMALE_COLOR = "hsl(330 80% 60%)";

export function PyramidChart({ data, className }: PyramidChartProps) {
    // Hooks must be called before any early return
    const transformedData = useMemo(() => {
        if (!data || data.length === 0) return [];
        return data.map((d) => ({
            grupo: d.grupo,
            masculino: -d.masculino, // Negative for left side
            femenino: d.femenino,
            mLabel: d.masculino,
            fLabel: d.femenino,
        }));
    }, [data]);

    const maxValue = useMemo(() => {
        if (!data || data.length === 0) return 0;
        return Math.max(...data.flatMap((d) => [d.masculino, d.femenino]));
    }, [data]);

    // Empty state - after hooks
    if (!data || data.length === 0) {
        return (
            <div className={cn("h-full w-full flex items-center justify-center text-muted-foreground text-sm", className)}>
                No hay datos de pirámide poblacional
            </div>
        );
    }

    return (
        <div className={cn("h-full w-full", className)}>
            <ResponsiveContainer width="100%" height="100%">
                <BarChart
                    data={transformedData}
                    layout="vertical"
                    margin={{ top: 20, right: 30, left: 30, bottom: 20 }}
                    stackOffset="sign"
                >
                    <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} />
                    <XAxis
                        type="number"
                        domain={[-maxValue * 1.1, maxValue * 1.1]}
                        tickFormatter={(value) => Math.abs(value).toLocaleString()}
                        tickLine={false}
                        axisLine={false}
                    />
                    <YAxis
                        type="category"
                        dataKey="grupo"
                        tickLine={false}
                        axisLine={false}
                        width={60}
                        style={{ fontSize: "11px" }}
                    />
                    <Tooltip
                        formatter={(value: number, name: string) => [
                            Math.abs(value).toLocaleString(),
                            name === "masculino" ? "Masculino" : "Femenino",
                        ]}
                        labelFormatter={(label) => `Grupo: ${label}`}
                    />
                    <Legend
                        formatter={(value) => (value === "masculino" ? "Masculino" : "Femenino")}
                    />
                    <Bar dataKey="masculino" fill={MALE_COLOR} radius={[4, 0, 0, 4]} />
                    <Bar dataKey="femenino" fill={FEMALE_COLOR} radius={[0, 4, 4, 0]} />
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
}

export default PyramidChart;
