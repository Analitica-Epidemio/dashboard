"use client";

import { LucideIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export interface ChartTypeOption {
    type: string;
    icon: LucideIcon;
    label: string;
}

interface ChartTypeSelectorProps {
    types: ChartTypeOption[];
    value: string;
    onChange: (type: string) => void;
    size?: "sm" | "default";
    className?: string;
}

/**
 * Compact chart type selector for switching between visualization types.
 * 
 * @example
 * <ChartTypeSelector
 *   types={[
 *     { type: "area", icon: AreaChartIcon, label: "Área" },
 *     { type: "line", icon: LineChartIcon, label: "Línea" },
 *     { type: "bar", icon: BarChart3, label: "Barras" },
 *   ]}
 *   value={chartType}
 *   onChange={setChartType}
 * />
 */
export function ChartTypeSelector({
    types,
    value,
    onChange,
    size = "sm",
    className,
}: ChartTypeSelectorProps) {
    return (
        <div className={cn("flex items-center gap-0.5 border rounded-lg p-0.5 bg-muted/50", className)}>
            {types.map(({ type, icon: Icon, label }) => (
                <Button
                    key={type}
                    variant={value === type ? "secondary" : "ghost"}
                    size={size}
                    className={cn(
                        "h-7 px-2",
                        value === type && "shadow-sm"
                    )}
                    onClick={() => onChange(type)}
                    title={label}
                >
                    <Icon className="h-4 w-4" />
                </Button>
            ))}
        </div>
    );
}

export default ChartTypeSelector;
