"use client";

import React, { useState, useMemo, useCallback, useEffect } from "react";
import { ChevronRight, ChevronLeft, ChevronFirst, ChevronLast, Calendar, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { cn } from "@/lib/utils";
import type { PeriodoFilter } from "@/features/metricas";

// ═══════════════════════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Alias for PeriodoFilter - same structure, different semantic name for UI context.
 * Re-exported from API types for DRY principle.
 */
export type PeriodoEpidemiologico = PeriodoFilter;

interface EpiWeekInfo {
    year: number;
    week: number;
    startDate: Date;
    endDate: Date;
}

interface PresetOption {
    id: string;
    label: string;
    description: string;
    getValue: () => PeriodoEpidemiologico;
}

interface EpidemiologicalPeriodPickerProps {
    value: PeriodoEpidemiologico;
    onChange: (value: PeriodoEpidemiologico) => void;
    className?: string;
}

// ═══════════════════════════════════════════════════════════════════════════════
// EPI WEEK UTILITIES
// ═══════════════════════════════════════════════════════════════════════════════

function getEpiWeek(date: Date): { year: number; week: number } {
    const year = date.getFullYear();

    const firstThursday = new Date(year, 0, 1);
    while (firstThursday.getDay() !== 4) {
        firstThursday.setDate(firstThursday.getDate() + 1);
    }
    const se1Start = new Date(firstThursday);
    se1Start.setDate(se1Start.getDate() - firstThursday.getDay());

    const nextFirstThursday = new Date(year + 1, 0, 1);
    while (nextFirstThursday.getDay() !== 4) {
        nextFirstThursday.setDate(nextFirstThursday.getDate() + 1);
    }
    const nextSe1Start = new Date(nextFirstThursday);
    nextSe1Start.setDate(nextSe1Start.getDate() - nextFirstThursday.getDay());

    if (date < se1Start) {
        return getEpiWeek(new Date(year - 1, 11, 31));
    }

    if (date >= nextSe1Start) {
        return getEpiWeek(new Date(year + 1, 0, 1));
    }

    const weekStart = new Date(se1Start);
    let week = 1;

    while (weekStart < nextSe1Start) {
        const weekEnd = new Date(weekStart);
        weekEnd.setDate(weekStart.getDate() + 6);

        if (date >= weekStart && date <= weekEnd) {
            return { year, week };
        }

        weekStart.setDate(weekStart.getDate() + 7);
        week++;
    }

    return { year, week: 1 };
}

function epiWeekToDates(year: number, week: number): { start: Date; end: Date } {
    const firstThursday = new Date(year, 0, 1);
    while (firstThursday.getDay() !== 4) {
        firstThursday.setDate(firstThursday.getDate() + 1);
    }
    const se1Start = new Date(firstThursday);
    se1Start.setDate(se1Start.getDate() - firstThursday.getDay());
    const start = new Date(se1Start);
    start.setDate(start.getDate() + (week - 1) * 7);
    const end = new Date(start);
    end.setDate(start.getDate() + 6);

    return { start, end };
}

/** Calcula el número de semanas en un rango multi-año */
function calcularSemanas(p: PeriodoEpidemiologico): number {
    if (p.anio_desde === p.anio_hasta) {
        return p.semana_hasta - p.semana_desde + 1;
    }
    // Cruzando años
    const semanasAnioInicio = 52 - p.semana_desde + 1;
    const semanasAnioFin = p.semana_hasta;
    const aniosIntermedios = p.anio_hasta - p.anio_desde - 1;
    return semanasAnioInicio + (aniosIntermedios * 52) + semanasAnioFin;
}

/** Compara si una semana es anterior a otra */
function isWeekBefore(
    year1: number, week1: number,
    year2: number, week2: number
): boolean {
    if (year1 < year2) return true;
    if (year1 > year2) return false;
    return week1 < week2;
}

/** Compara si una semana está en el rango (inclusive) */
function isWeekInRange(
    year: number, week: number,
    startYear: number, startWeek: number,
    endYear: number, endWeek: number
): boolean {
    // Check if >= start
    const afterStart = year > startYear || (year === startYear && week >= startWeek);
    // Check if <= end
    const beforeEnd = year < endYear || (year === endYear && week <= endWeek);
    return afterStart && beforeEnd;
}

// ═══════════════════════════════════════════════════════════════════════════════
// PRESETS (Multi-año aware)
// ═══════════════════════════════════════════════════════════════════════════════

function getPresets(): PresetOption[] {
    const today = new Date();
    const currentEpi = getEpiWeek(today);
    const currentYear = currentEpi.year;
    const currentWeek = currentEpi.week;

    // Helper para calcular semanas hacia atrás cruzando años
    const weeksAgo = (n: number): { year: number; week: number } => {
        let y = currentYear;
        let w = currentWeek - n;
        while (w < 1) {
            y--;
            w += 52;
        }
        return { year: y, week: w };
    };

    const w4 = weeksAgo(3);
    const w12 = weeksAgo(11);
    const w52 = weeksAgo(51);

    return [
        {
            id: "ultima_semana",
            label: "Última semana",
            description: `SE ${currentWeek}/${currentYear}`,
            getValue: () => ({
                anio_desde: currentYear,
                semana_desde: currentWeek,
                anio_hasta: currentYear,
                semana_hasta: currentWeek,
            }),
        },
        {
            id: "ultimas_4_semanas",
            label: "Últimas 4 semanas",
            description: w4.year === currentYear
                ? `SE ${w4.week}-${currentWeek}`
                : `SE ${w4.week}/${w4.year} - ${currentWeek}/${currentYear}`,
            getValue: () => ({
                anio_desde: w4.year,
                semana_desde: w4.week,
                anio_hasta: currentYear,
                semana_hasta: currentWeek,
            }),
        },
        {
            id: "ultimas_12_semanas",
            label: "Últimas 12 semanas",
            description: w12.year === currentYear
                ? `SE ${w12.week}-${currentWeek}`
                : `SE ${w12.week}/${w12.year} - ${currentWeek}/${currentYear}`,
            getValue: () => ({
                anio_desde: w12.year,
                semana_desde: w12.week,
                anio_hasta: currentYear,
                semana_hasta: currentWeek,
            }),
        },
        {
            id: "ultimas_52_semanas",
            label: "Últimas 52 semanas",
            description: `SE ${w52.week}/${w52.year} - ${currentWeek}/${currentYear}`,
            getValue: () => ({
                anio_desde: w52.year,
                semana_desde: w52.week,
                anio_hasta: currentYear,
                semana_hasta: currentWeek,
            }),
        },
        {
            id: "temporada_respiratoria",
            label: "Temporada respiratoria",
            description: currentWeek >= 40
                ? `SE 40/${currentYear} - 20/${currentYear + 1}`
                : `SE 40/${currentYear - 1} - 20/${currentYear}`,
            getValue: () => {
                // Si estamos en SE >= 40, temporada actual es este año -> siguiente
                // Si estamos en SE < 40, temporada actual es año anterior -> este año
                if (currentWeek >= 40) {
                    return {
                        anio_desde: currentYear,
                        semana_desde: 40,
                        anio_hasta: currentYear + 1,
                        semana_hasta: 20,
                    };
                }
                return {
                    anio_desde: currentYear - 1,
                    semana_desde: 40,
                    anio_hasta: currentYear,
                    semana_hasta: 20,
                };
            },
        },
        {
            id: "ytd",
            label: "Año en curso",
            description: `SE 1-${currentWeek}/${currentYear}`,
            getValue: () => ({
                anio_desde: currentYear,
                semana_desde: 1,
                anio_hasta: currentYear,
                semana_hasta: currentWeek,
            }),
        },
        {
            id: "anio_completo",
            label: "Año completo",
            description: `SE 1-52/${currentYear}`,
            getValue: () => ({
                anio_desde: currentYear,
                semana_desde: 1,
                anio_hasta: currentYear,
                semana_hasta: 52,
            }),
        },
        {
            id: "anio_anterior",
            label: "Año anterior",
            description: `${currentYear - 1} completo`,
            getValue: () => ({
                anio_desde: currentYear - 1,
                semana_desde: 1,
                anio_hasta: currentYear - 1,
                semana_hasta: 52,
            }),
        },
    ];
}

// ═══════════════════════════════════════════════════════════════════════════════
// EPI CALENDAR MINI
// ═══════════════════════════════════════════════════════════════════════════════

const MONTH_NAMES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
];

function getCalendarWeeks(year: number, month: number) {
    const startOfMonth = new Date(year, month, 1);
    const endOfMonth = new Date(year, month + 1, 0);

    const startDate = new Date(startOfMonth);
    startDate.setDate(startOfMonth.getDate() - startOfMonth.getDay());

    const weeks: Date[][] = [];
    const current = new Date(startDate);

    while (current <= endOfMonth || weeks.length < 6) {
        const week: Date[] = [];
        for (let i = 0; i < 7; i++) {
            week.push(new Date(current));
            current.setDate(current.getDate() + 1);
        }
        weeks.push(week);
    }

    return weeks;
}

interface MiniEpiCalendarProps {
    rangeStart: EpiWeekInfo | null;
    rangeEnd: EpiWeekInfo | null;
    onWeekSelect: (info: EpiWeekInfo) => void;
    label: string;
    initialDate?: Date;
}

function MiniEpiCalendar({ rangeStart, rangeEnd, onWeekSelect, label, initialDate }: MiniEpiCalendarProps) {
    const today = new Date();
    const defaultDate = initialDate || rangeStart?.startDate || today;
    const [currentYear, setCurrentYear] = useState(defaultDate.getFullYear());
    const [currentMonth, setCurrentMonth] = useState(defaultDate.getMonth());

    const weeks = useMemo(() => getCalendarWeeks(currentYear, currentMonth), [currentYear, currentMonth]);

    const handleSelect = (date: Date) => {
        const epi = getEpiWeek(date);
        const dates = epiWeekToDates(epi.year, epi.week);
        onWeekSelect({
            year: epi.year,
            week: epi.week,
            startDate: dates.start,
            endDate: dates.end,
        });
    };

    const goToPrevMonth = () => {
        if (currentMonth === 0) {
            setCurrentMonth(11);
            setCurrentYear(currentYear - 1);
        } else {
            setCurrentMonth(currentMonth - 1);
        }
    };

    const goToNextMonth = () => {
        if (currentMonth === 11) {
            setCurrentMonth(0);
            setCurrentYear(currentYear + 1);
        } else {
            setCurrentMonth(currentMonth + 1);
        }
    };

    const goToPrevYear = () => setCurrentYear(currentYear - 1);
    const goToNextYear = () => setCurrentYear(currentYear + 1);

    return (
        <div className="w-full">
            <div className="text-xs font-medium text-muted-foreground mb-2 text-center">
                {label}
            </div>
            <div className="flex items-center justify-between mb-2">
                <button
                    onClick={goToPrevYear}
                    className="p-1 hover:bg-accent rounded transition-colors"
                    type="button"
                >
                    <ChevronFirst className="h-3 w-3 text-muted-foreground" />
                </button>
                <button
                    onClick={goToPrevMonth}
                    className="p-1 hover:bg-accent rounded transition-colors"
                    type="button"
                >
                    <ChevronLeft className="h-3 w-3 text-muted-foreground" />
                </button>
                <span className="text-xs font-medium min-w-[100px] text-center">
                    {MONTH_NAMES[currentMonth]} {currentYear}
                </span>
                <button
                    onClick={goToNextMonth}
                    className="p-1 hover:bg-accent rounded transition-colors"
                    type="button"
                >
                    <ChevronRight className="h-3 w-3 text-muted-foreground" />
                </button>
                <button
                    onClick={goToNextYear}
                    className="p-1 hover:bg-accent rounded transition-colors"
                    type="button"
                >
                    <ChevronLast className="h-3 w-3 text-muted-foreground" />
                </button>
            </div>

            <table className="w-full border-collapse text-xs">
                <thead>
                    <tr>
                        <th className="p-1 text-[10px] font-medium text-muted-foreground bg-muted/50">SE</th>
                        {["D", "L", "M", "X", "J", "V", "S"].map((day) => (
                            <th key={day} className="p-1 text-[10px] font-medium text-muted-foreground bg-muted/50 text-center">
                                {day}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {weeks.map((week, wIdx) => {
                        const epiWeek = getEpiWeek(week[3]); // Use Thursday for accurate week number
                        return (
                            <tr key={wIdx}>
                                <td className="p-1 text-[10px] font-semibold text-center bg-muted/30 text-muted-foreground">
                                    {epiWeek.week}
                                </td>
                                {week.map((date, dIdx) => {
                                    const dateEpi = getEpiWeek(date);
                                    const isCurrentMonth = date.getMonth() === currentMonth;
                                    const isToday = date.toDateString() === today.toDateString();

                                    const isInRange = rangeStart && rangeEnd && isWeekInRange(
                                        dateEpi.year, dateEpi.week,
                                        rangeStart.year, rangeStart.week,
                                        rangeEnd.year, rangeEnd.week
                                    );

                                    const isStartWeek = rangeStart &&
                                        dateEpi.year === rangeStart.year && dateEpi.week === rangeStart.week;
                                    const isEndWeek = rangeEnd &&
                                        dateEpi.year === rangeEnd.year && dateEpi.week === rangeEnd.week;

                                    let cellClasses = "p-0.5 text-center cursor-pointer transition-all";

                                    if (isStartWeek || isEndWeek) {
                                        cellClasses += " bg-primary text-primary-foreground font-bold";
                                    } else if (isInRange) {
                                        cellClasses += " bg-primary/20";
                                    } else if (isToday) {
                                        cellClasses += " font-semibold text-primary";
                                    }

                                    if (!isCurrentMonth && !isStartWeek && !isEndWeek && !isInRange) {
                                        cellClasses += " text-muted-foreground/50";
                                    }

                                    return (
                                        <td
                                            key={dIdx}
                                            onClick={() => handleSelect(date)}
                                            className={cellClasses}
                                        >
                                            <div className="w-5 h-5 flex items-center justify-center mx-auto rounded hover:bg-accent/50">
                                                {date.getDate()}
                                            </div>
                                        </td>
                                    );
                                })}
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
}

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN COMPONENT
// ═══════════════════════════════════════════════════════════════════════════════

export function EpidemiologicalPeriodPicker({
    value,
    onChange,
    className,
}: EpidemiologicalPeriodPickerProps) {
    const [open, setOpen] = useState(false);
    const presets = useMemo(() => getPresets(), []);

    // Draft state - changes here don't affect parent until "Aplicar"
    const [draft, setDraft] = useState<PeriodoEpidemiologico>(value);

    // Reset draft when popover opens
    useEffect(() => {
        if (open) {
            setDraft(value);
        }
    }, [open, value]);

    const draftStartInfo = useMemo((): EpiWeekInfo => {
        const dates = epiWeekToDates(draft.anio_desde, draft.semana_desde);
        return {
            year: draft.anio_desde,
            week: draft.semana_desde,
            startDate: dates.start,
            endDate: dates.end,
        };
    }, [draft.anio_desde, draft.semana_desde]);

    const draftEndInfo = useMemo((): EpiWeekInfo => {
        const dates = epiWeekToDates(draft.anio_hasta, draft.semana_hasta);
        return {
            year: draft.anio_hasta,
            week: draft.semana_hasta,
            startDate: dates.start,
            endDate: dates.end,
        };
    }, [draft.anio_hasta, draft.semana_hasta]);

    const handleStartSelect = useCallback((info: EpiWeekInfo) => {
        setDraft(prev => {
            // Si la nueva fecha inicio es después de la fecha fin, mover fin también
            if (isWeekBefore(prev.anio_hasta, prev.semana_hasta, info.year, info.week)) {
                return {
                    anio_desde: info.year,
                    semana_desde: info.week,
                    anio_hasta: info.year,
                    semana_hasta: info.week,
                };
            }
            return {
                ...prev,
                anio_desde: info.year,
                semana_desde: info.week,
            };
        });
    }, []);

    const handleEndSelect = useCallback((info: EpiWeekInfo) => {
        setDraft(prev => {
            // Si la nueva fecha fin es antes de la fecha inicio, intercambiar
            if (isWeekBefore(info.year, info.week, prev.anio_desde, prev.semana_desde)) {
                return {
                    anio_desde: info.year,
                    semana_desde: info.week,
                    anio_hasta: prev.anio_desde,
                    semana_hasta: prev.semana_desde,
                };
            }
            return {
                ...prev,
                anio_hasta: info.year,
                semana_hasta: info.week,
            };
        });
    }, []);

    const handlePresetClick = useCallback((preset: PresetOption) => {
        const presetValue = preset.getValue();
        setDraft(presetValue);
        // Apply immediately for presets
        onChange(presetValue);
        setOpen(false);
    }, [onChange]);

    const handleApply = useCallback(() => {
        onChange(draft);
        setOpen(false);
    }, [draft, onChange]);

    const handleCancel = useCallback(() => {
        setDraft(value);
        setOpen(false);
    }, [value]);

    const isPresetActive = useCallback((preset: PresetOption) => {
        const presetValue = preset.getValue();
        return (
            presetValue.anio_desde === draft.anio_desde &&
            presetValue.semana_desde === draft.semana_desde &&
            presetValue.anio_hasta === draft.anio_hasta &&
            presetValue.semana_hasta === draft.semana_hasta
        );
    }, [draft]);

    const hasChanges = useMemo(() => {
        return draft.anio_desde !== value.anio_desde ||
            draft.semana_desde !== value.semana_desde ||
            draft.anio_hasta !== value.anio_hasta ||
            draft.semana_hasta !== value.semana_hasta;
    }, [draft, value]);

    // Display text format: "SE 45/2024 - SE 10/2025" or "SE 1-10/2025" for same year
    const displayText = useMemo(() => {
        if (value.anio_desde === value.anio_hasta) {
            if (value.semana_desde === value.semana_hasta) {
                return `SE ${value.semana_desde}/${value.anio_desde}`;
            }
            return `SE ${value.semana_desde}-${value.semana_hasta}/${value.anio_desde}`;
        }
        return `SE ${value.semana_desde}/${value.anio_desde} - ${value.semana_hasta}/${value.anio_hasta}`;
    }, [value]);

    // Draft display for footer
    const draftDisplayText = useMemo(() => {
        if (draft.anio_desde === draft.anio_hasta) {
            return `SE ${draft.semana_desde} - ${draft.semana_hasta} / ${draft.anio_desde}`;
        }
        return `SE ${draft.semana_desde}/${draft.anio_desde} - SE ${draft.semana_hasta}/${draft.anio_hasta}`;
    }, [draft]);

    const weekCount = calcularSemanas(value);
    const draftWeekCount = calcularSemanas(draft);

    return (
        <Popover open={open} onOpenChange={setOpen}>
            <PopoverTrigger asChild>
                <Button
                    variant="outline"
                    className={cn(
                        "justify-start text-left font-normal",
                        !value && "text-muted-foreground",
                        className
                    )}
                >
                    <Calendar className="mr-2 h-4 w-4" />
                    <span>{displayText}</span>
                    <span className="ml-2 text-xs text-muted-foreground">
                        ({weekCount} {weekCount === 1 ? "semana" : "semanas"})
                    </span>
                </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0" align="start">
                <div className="flex">
                    {/* Presets sidebar */}
                    <div className="w-48 border-r p-2 space-y-0.5 bg-muted/30">
                        <div className="text-xs font-semibold text-muted-foreground px-2 py-1.5 uppercase tracking-wide">
                            Períodos rápidos
                        </div>
                        {presets.map((preset) => (
                            <button
                                key={preset.id}
                                onClick={() => handlePresetClick(preset)}
                                className={cn(
                                    "w-full text-left px-2 py-1.5 rounded text-sm transition-colors flex items-center gap-2",
                                    isPresetActive(preset)
                                        ? "bg-primary text-primary-foreground"
                                        : "hover:bg-accent"
                                )}
                                type="button"
                            >
                                {isPresetActive(preset) && <Check className="h-3 w-3 flex-shrink-0" />}
                                <div className={cn("flex-1", isPresetActive(preset) && "ml-0")}>
                                    <div className="font-medium text-xs">{preset.label}</div>
                                    <div className={cn(
                                        "text-[10px]",
                                        isPresetActive(preset) ? "text-primary-foreground/70" : "text-muted-foreground"
                                    )}>
                                        {preset.description}
                                    </div>
                                </div>
                            </button>
                        ))}
                    </div>

                    {/* Calendars */}
                    <div className="p-3">
                        <div className="flex gap-4">
                            <div className="border rounded-lg p-2 bg-card">
                                <MiniEpiCalendar
                                    rangeStart={draftStartInfo}
                                    rangeEnd={draftEndInfo}
                                    onWeekSelect={handleStartSelect}
                                    label="Semana inicial"
                                    initialDate={draftStartInfo.startDate}
                                />
                            </div>
                            <div className="border rounded-lg p-2 bg-card">
                                <MiniEpiCalendar
                                    rangeStart={draftStartInfo}
                                    rangeEnd={draftEndInfo}
                                    onWeekSelect={handleEndSelect}
                                    label="Semana final"
                                    initialDate={draftEndInfo.startDate}
                                />
                            </div>
                        </div>

                        {/* Selection summary and actions */}
                        <div className="mt-3 pt-3 border-t flex items-center justify-between">
                            <div className="text-xs text-muted-foreground">
                                <span className="font-medium text-foreground">
                                    {draftDisplayText}
                                </span>
                                <span className="ml-2">
                                    ({draftWeekCount} {draftWeekCount === 1 ? "semana" : "semanas"})
                                </span>
                            </div>
                            <div className="flex gap-2">
                                <Button
                                    size="sm"
                                    variant="ghost"
                                    onClick={handleCancel}
                                    className="h-7 text-xs"
                                >
                                    Cancelar
                                </Button>
                                <Button
                                    size="sm"
                                    onClick={handleApply}
                                    className="h-7 text-xs"
                                    disabled={!hasChanges}
                                >
                                    Aplicar
                                </Button>
                            </div>
                        </div>
                    </div>
                </div>
            </PopoverContent>
        </Popover>
    );
}

export default EpidemiologicalPeriodPicker;
