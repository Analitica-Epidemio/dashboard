"use client";

import { ComposableMap, Geographies, Geography } from "react-simple-maps";
import { useMemo, useState } from "react";
import { cn } from "@/lib/utils";
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip";

interface ProvinceData {
    provincia_id?: number;
    /** Province name - accepts 'provincia' or 'provincia_nombre' */
    provincia_nombre?: string;
    /** Alternative property name for province */
    provincia?: string;
    valor: number;
    porcentaje?: number;
}

interface ProvinceMapProps {
    /** Data array with province name and value */
    data: ProvinceData[];
    /** Color scale type */
    colorScale?: "blue" | "red" | "green";
    /** Callback when province is clicked */
    onProvinceClick?: (provinciaId: string, nombre: string) => void;
    /** Additional className */
    className?: string;
    /** Height of the map container */
    height?: number | string;
}

// Color scales for different use cases
const COLOR_SCALES = {
    blue: {
        empty: "#e2e8f0", // slate-200
        light: [219, 234, 254], // blue-100
        mid: [96, 165, 250],   // blue-400
        dark: [29, 78, 216],   // blue-700
    },
    red: {
        empty: "#e2e8f0",
        light: [254, 226, 226], // red-100
        mid: [248, 113, 113],   // red-400
        dark: [185, 28, 28],    // red-700
    },
    green: {
        empty: "#e2e8f0",
        light: [220, 252, 231], // green-100
        mid: [74, 222, 128],    // green-400
        dark: [21, 128, 61],    // green-700
    },
};

function getColor(value: number, max: number, scale: keyof typeof COLOR_SCALES): string {
    if (max === 0 || value === 0) return COLOR_SCALES[scale].empty;

    const colors = COLOR_SCALES[scale];
    const intensity = Math.min(value / max, 1);

    if (intensity < 0.5) {
        // Light to mid range
        const t = intensity / 0.5;
        const r = Math.round(colors.light[0] + t * (colors.mid[0] - colors.light[0]));
        const g = Math.round(colors.light[1] + t * (colors.mid[1] - colors.light[1]));
        const b = Math.round(colors.light[2] + t * (colors.mid[2] - colors.light[2]));
        return `rgb(${r}, ${g}, ${b})`;
    } else {
        // Mid to dark range
        const t = (intensity - 0.5) / 0.5;
        const r = Math.round(colors.mid[0] + t * (colors.dark[0] - colors.mid[0]));
        const g = Math.round(colors.mid[1] + t * (colors.dark[1] - colors.mid[1]));
        const b = Math.round(colors.mid[2] + t * (colors.dark[2] - colors.mid[2]));
        return `rgb(${r}, ${g}, ${b})`;
    }
}

// Normalize province names for matching
function normalizeProvinceName(name: string): string {
    return name
        .toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "") // Remove accents
        .replace(/ciudad autonoma de buenos aires|caba/gi, "caba")
        .replace(/buenos aires/gi, "buenos aires")
        .trim();
}

export function ProvinceMap({
    data,
    colorScale = "blue",
    onProvinceClick,
    className,
    height = 400,
}: ProvinceMapProps) {
    const [tooltipContent, setTooltipContent] = useState<{
        name: string;
        value: number;
        porcentaje?: number;
    } | null>(null);

    // Create lookup by normalized province name (accepts both 'provincia' and 'provincia_nombre')
    const dataByName = useMemo(() => {
        const lookup: Record<string, ProvinceData> = {};
        data.forEach((d) => {
            const name = d.provincia_nombre || d.provincia;
            if (name) {
                const normalized = normalizeProvinceName(name);
                lookup[normalized] = d;
            }
        });
        return lookup;
    }, [data]);

    const maxValue = useMemo(() => {
        return Math.max(...data.map((d) => d.valor), 1);
    }, [data]);

    return (
        <TooltipProvider>
            <div className={cn("relative", className)} style={{ height }}>
                <Tooltip open={!!tooltipContent}>
                    <TooltipTrigger asChild>
                        <div className="w-full h-full">
                            <ComposableMap
                                projection="geoMercator"
                                projectionConfig={{
                                    center: [-65, -40],
                                    scale: 650,
                                }}
                                style={{ width: "100%", height: "100%" }}
                            >
                                <Geographies geography="/geo/provincias.geojson">
                                    {({ geographies }) =>
                                        geographies.map((geo) => {
                                            const provinceName = geo.properties.nombre || "";
                                            const normalizedName = normalizeProvinceName(provinceName);
                                            const provinceData = dataByName[normalizedName];
                                            const value = provinceData?.valor || 0;

                                            return (
                                                <Geography
                                                    key={geo.rsmKey}
                                                    geography={geo}
                                                    fill={getColor(value, maxValue, colorScale)}
                                                    stroke="#94a3b8"
                                                    strokeWidth={0.5}
                                                    style={{
                                                        default: { outline: "none" },
                                                        hover: {
                                                            fill: colorScale === "blue" ? "#3b82f6" :
                                                                  colorScale === "red" ? "#ef4444" : "#22c55e",
                                                            outline: "none",
                                                            cursor: "pointer",
                                                        },
                                                        pressed: { outline: "none" },
                                                    }}
                                                    onMouseEnter={() => {
                                                        setTooltipContent({
                                                            name: provinceName,
                                                            value,
                                                            porcentaje: provinceData?.porcentaje,
                                                        });
                                                    }}
                                                    onMouseLeave={() => {
                                                        setTooltipContent(null);
                                                    }}
                                                    onClick={() => {
                                                        const id = geo.properties.id;
                                                        if (onProvinceClick) {
                                                            onProvinceClick(id, provinceName);
                                                        }
                                                    }}
                                                />
                                            );
                                        })
                                    }
                                </Geographies>
                            </ComposableMap>
                        </div>
                    </TooltipTrigger>
                    {tooltipContent && (
                        <TooltipContent side="right" className="pointer-events-none">
                            <div className="text-sm">
                                <p className="font-semibold">{tooltipContent.name}</p>
                                <p>Casos: {tooltipContent.value.toLocaleString("es-AR")}</p>
                                {tooltipContent.porcentaje !== undefined && (
                                    <p className="text-muted-foreground">
                                        ({tooltipContent.porcentaje.toFixed(1)}% del total)
                                    </p>
                                )}
                            </div>
                        </TooltipContent>
                    )}
                </Tooltip>

                {/* Legend */}
                <div className="absolute bottom-2 left-2 bg-background/90 backdrop-blur rounded p-2 text-xs">
                    <div className="flex items-center gap-1">
                        <div
                            className="w-3 h-3 rounded-sm"
                            style={{ backgroundColor: COLOR_SCALES[colorScale].empty }}
                        />
                        <span>0</span>
                        <div
                            className="w-8 h-3 rounded-sm"
                            style={{
                                background: `linear-gradient(to right, rgb(${COLOR_SCALES[colorScale].light.join(",")}), rgb(${COLOR_SCALES[colorScale].dark.join(",")}))`
                            }}
                        />
                        <span>{maxValue.toLocaleString("es-AR")}</span>
                    </div>
                </div>
            </div>
        </TooltipProvider>
    );
}

export default ProvinceMap;
