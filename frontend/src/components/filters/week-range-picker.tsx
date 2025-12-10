"use client";

import { Slider } from "@/components/ui/slider";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

interface WeekRangePickerProps {
    value: [number, number];
    onChange: (value: [number, number]) => void;
    min?: number;
    max?: number;
    className?: string;
}

export function WeekRangePicker({
    value,
    onChange,
    min = 1,
    max = 52,
    className,
}: WeekRangePickerProps) {
    return (
        <div className={cn("space-y-2", className)}>
            <div className="flex items-center justify-between">
                <Label className="text-sm font-medium">Semanas</Label>
                <span className="text-sm text-muted-foreground">
                    SE {value[0]} - SE {value[1]}
                </span>
            </div>
            <Slider
                value={value}
                onValueChange={(val) => onChange(val as [number, number])}
                min={min}
                max={max}
                step={1}
                className="py-2"
            />
        </div>
    );
}

export default WeekRangePicker;
