"use client";

import { useMemo } from "react";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import type { PeriodoEpidemiologico } from "./EpidemiologicalPeriodPicker";

export type ComparisonMode = "none" | "yoy" | "previous_period";

interface ComparisonModeSelectProps {
    value: ComparisonMode;
    onChange: (value: ComparisonMode) => void;
    periodo: PeriodoEpidemiologico;
    className?: string;
}

/** Calcula el número de semanas en un período multi-año */
function calcularSemanas(p: PeriodoEpidemiologico): number {
    if (p.anio_desde === p.anio_hasta) {
        return p.semana_hasta - p.semana_desde + 1;
    }
    const semanasAnioInicio = 52 - p.semana_desde + 1;
    const semanasAnioFin = p.semana_hasta;
    const aniosIntermedios = p.anio_hasta - p.anio_desde - 1;
    return semanasAnioInicio + (aniosIntermedios * 52) + semanasAnioFin;
}

/** Formatea un período para mostrar al usuario */
function formatPeriodo(p: PeriodoEpidemiologico): string {
    if (p.anio_desde === p.anio_hasta) {
        return `SE ${p.semana_desde}-${p.semana_hasta}/${p.anio_desde}`;
    }
    return `SE ${p.semana_desde}/${p.anio_desde} - ${p.semana_hasta}/${p.anio_hasta}`;
}

/** Calcula el período YoY (mismo período, año anterior) */
function calcularYoY(p: PeriodoEpidemiologico): PeriodoEpidemiologico {
    return {
        anio_desde: p.anio_desde - 1,
        semana_desde: p.semana_desde,
        anio_hasta: p.anio_hasta - 1,
        semana_hasta: p.semana_hasta,
    };
}

/** Calcula el período anterior (N semanas antes) */
function calcularPeriodoAnterior(p: PeriodoEpidemiologico): PeriodoEpidemiologico {
    const duracion = calcularSemanas(p);

    let nuevoAnioDesde = p.anio_desde;
    let nuevaSemanaDesde = p.semana_desde - duracion;

    while (nuevaSemanaDesde < 1) {
        nuevoAnioDesde--;
        nuevaSemanaDesde += 52;
    }

    let nuevoAnioHasta = p.anio_desde;
    let nuevaSemanaHasta = p.semana_desde - 1;

    if (nuevaSemanaHasta < 1) {
        nuevoAnioHasta--;
        nuevaSemanaHasta = 52;
    }

    return {
        anio_desde: nuevoAnioDesde,
        semana_desde: nuevaSemanaDesde,
        anio_hasta: nuevoAnioHasta,
        semana_hasta: nuevaSemanaHasta,
    };
}

/**
 * Selector de modo de comparación con descripción del período comparado.
 */
export function ComparisonModeSelect({
    value,
    onChange,
    periodo,
    className,
}: ComparisonModeSelectProps) {
    const semanas = calcularSemanas(periodo);

    // Calcular períodos de comparación para mostrar en las opciones
    const yoyPeriodo = useMemo(() => calcularYoY(periodo), [periodo]);
    const prevPeriodo = useMemo(() => calcularPeriodoAnterior(periodo), [periodo]);

    return (
        <Select value={value} onValueChange={(v) => onChange(v as ComparisonMode)}>
            <SelectTrigger className={className ?? "w-[200px] h-8"}>
                <SelectValue placeholder="Comparar con..." />
            </SelectTrigger>
            <SelectContent>
                <SelectItem value="none">
                    <div className="flex flex-col items-start">
                        <span>Sin comparación</span>
                    </div>
                </SelectItem>
                <SelectItem value="yoy">
                    <div className="flex flex-col items-start">
                        <span>vs Año anterior</span>
                        <span className="text-[10px] text-muted-foreground">
                            {formatPeriodo(yoyPeriodo)}
                        </span>
                    </div>
                </SelectItem>
                <SelectItem value="previous_period">
                    <div className="flex flex-col items-start">
                        <span>vs Período anterior</span>
                        <span className="text-[10px] text-muted-foreground">
                            {formatPeriodo(prevPeriodo)} ({semanas} sem)
                        </span>
                    </div>
                </SelectItem>
            </SelectContent>
        </Select>
    );
}

export default ComparisonModeSelect;
