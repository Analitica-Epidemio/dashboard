"use client";

import { useMemo } from "react";
import { cn } from "@/lib/utils";
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip";

// Argentina provinces SVG paths (simplified)
const PROVINCES: Record<string, { path: string; name: string; center: [number, number] }> = {
    "buenos_aires": {
        name: "Buenos Aires",
        path: "M 320 380 L 380 350 L 420 400 L 400 480 L 340 520 L 280 480 L 280 420 Z",
        center: [350, 430],
    },
    "caba": {
        name: "CABA",
        path: "M 355 395 L 365 390 L 370 400 L 360 405 Z",
        center: [362, 397],
    },
    "catamarca": {
        name: "Catamarca",
        path: "M 220 200 L 260 180 L 280 220 L 260 270 L 220 260 Z",
        center: [250, 225],
    },
    "chaco": {
        name: "Chaco",
        path: "M 320 150 L 380 140 L 400 180 L 380 230 L 320 230 L 300 190 Z",
        center: [350, 185],
    },
    "chubut": {
        name: "Chubut",
        path: "M 180 540 L 300 530 L 320 600 L 280 660 L 180 660 Z",
        center: [250, 595],
    },
    "cordoba": {
        name: "Córdoba",
        path: "M 260 270 L 320 250 L 350 300 L 320 360 L 270 360 L 240 320 Z",
        center: [295, 310],
    },
    "corrientes": {
        name: "Corrientes",
        path: "M 380 170 L 440 150 L 460 200 L 440 250 L 380 250 L 370 210 Z",
        center: [415, 200],
    },
    "entre_rios": {
        name: "Entre Ríos",
        path: "M 350 270 L 400 260 L 420 310 L 390 360 L 340 350 L 340 300 Z",
        center: [375, 310],
    },
    "formosa": {
        name: "Formosa",
        path: "M 320 100 L 400 80 L 420 120 L 400 160 L 320 160 L 300 130 Z",
        center: [360, 120],
    },
    "jujuy": {
        name: "Jujuy",
        path: "M 230 40 L 260 30 L 270 80 L 250 110 L 220 90 Z",
        center: [245, 70],
    },
    "la_pampa": {
        name: "La Pampa",
        path: "M 200 400 L 280 380 L 300 430 L 280 490 L 200 490 L 180 450 Z",
        center: [240, 440],
    },
    "la_rioja": {
        name: "La Rioja",
        path: "M 200 200 L 230 190 L 240 240 L 220 290 L 190 280 L 180 230 Z",
        center: [210, 240],
    },
    "mendoza": {
        name: "Mendoza",
        path: "M 160 300 L 210 290 L 230 350 L 200 420 L 150 410 L 140 350 Z",
        center: [185, 360],
    },
    "misiones": {
        name: "Misiones",
        path: "M 440 120 L 480 100 L 500 140 L 480 180 L 440 170 L 430 140 Z",
        center: [460, 140],
    },
    "neuquen": {
        name: "Neuquén",
        path: "M 140 440 L 200 420 L 220 480 L 180 530 L 130 520 L 120 480 Z",
        center: [170, 480],
    },
    "rio_negro": {
        name: "Río Negro",
        path: "M 160 500 L 280 480 L 300 540 L 260 580 L 160 580 L 140 540 Z",
        center: [220, 530],
    },
    "salta": {
        name: "Salta",
        path: "M 250 50 L 320 40 L 340 100 L 320 160 L 270 160 L 240 120 Z",
        center: [290, 100],
    },
    "san_juan": {
        name: "San Juan",
        path: "M 160 240 L 200 230 L 210 290 L 180 340 L 140 320 L 140 280 Z",
        center: [175, 285],
    },
    "san_luis": {
        name: "San Luis",
        path: "M 200 320 L 260 300 L 280 360 L 250 400 L 200 400 L 180 360 Z",
        center: [230, 355],
    },
    "santa_cruz": {
        name: "Santa Cruz",
        path: "M 160 660 L 280 650 L 300 740 L 260 800 L 160 800 L 140 730 Z",
        center: [220, 725],
    },
    "santa_fe": {
        name: "Santa Fe",
        path: "M 320 220 L 370 210 L 390 280 L 360 350 L 310 340 L 300 280 Z",
        center: [345, 280],
    },
    "santiago_del_estero": {
        name: "Santiago del Estero",
        path: "M 280 160 L 340 150 L 360 220 L 330 280 L 280 280 L 260 220 Z",
        center: [310, 215],
    },
    "tierra_del_fuego": {
        name: "Tierra del Fuego",
        path: "M 200 820 L 280 810 L 300 860 L 260 900 L 200 890 L 180 850 Z",
        center: [240, 855],
    },
    "tucuman": {
        name: "Tucumán",
        path: "M 260 150 L 290 140 L 300 180 L 280 210 L 250 200 L 250 170 Z",
        center: [275, 175],
    },
};

interface ProvinciaMapProps {
    data: Array<{
        provincia: string;
        valor: number;
        porcentaje?: number;
    }>;
    colorScale?: "sequential" | "diverging";
    className?: string;
}

function getColorFromValue(value: number, max: number): string {
    const intensity = Math.min(value / max, 1);
    // Blue scale
    const r = Math.round(59 + (1 - intensity) * 196);
    const g = Math.round(130 + (1 - intensity) * 125);
    const b = Math.round(246 - intensity * 46);
    return `rgb(${r}, ${g}, ${b})`;
}

function normalizeProvinceName(name: string): string {
    return name
        .toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .replace(/\s+/g, "_")
        .replace(/[áàâã]/g, "a")
        .replace(/[éèê]/g, "e")
        .replace(/[íìî]/g, "i")
        .replace(/[óòôõ]/g, "o")
        .replace(/[úùû]/g, "u");
}

export function ProvinciaMap({ data, className }: ProvinciaMapProps) {
    const dataMap = useMemo(() => {
        const map = new Map<string, { valor: number; porcentaje?: number }>();
        data.forEach((d) => {
            const key = normalizeProvinceName(d.provincia);
            map.set(key, { valor: d.valor, porcentaje: d.porcentaje });
        });
        return map;
    }, [data]);

    const maxValue = useMemo(() => {
        return Math.max(...data.map((d) => d.valor), 1);
    }, [data]);

    return (
        <TooltipProvider>
            <svg
                viewBox="0 0 520 920"
                className={cn("w-full h-full", className)}
                style={{ maxHeight: "400px" }}
            >
                <defs>
                    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
                        <feDropShadow dx="0" dy="1" stdDeviation="2" floodOpacity="0.1" />
                    </filter>
                </defs>
                {Object.entries(PROVINCES).map(([key, prov]) => {
                    const provinceData = dataMap.get(key);
                    const valor = provinceData?.valor ?? 0;
                    const fillColor = valor > 0 ? getColorFromValue(valor, maxValue) : "hsl(var(--muted))";

                    return (
                        <Tooltip key={key}>
                            <TooltipTrigger asChild>
                                <path
                                    d={prov.path}
                                    fill={fillColor}
                                    stroke="hsl(var(--border))"
                                    strokeWidth="1"
                                    className="cursor-pointer transition-all hover:opacity-80 hover:stroke-2"
                                    filter="url(#shadow)"
                                />
                            </TooltipTrigger>
                            <TooltipContent>
                                <div className="text-sm">
                                    <p className="font-semibold">{prov.name}</p>
                                    <p>Casos: {valor.toLocaleString()}</p>
                                    {provinceData?.porcentaje !== undefined && (
                                        <p>({provinceData.porcentaje.toFixed(1)}%)</p>
                                    )}
                                </div>
                            </TooltipContent>
                        </Tooltip>
                    );
                })}
            </svg>
        </TooltipProvider>
    );
}

export default ProvinciaMap;
