"use client";

import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { CalendarIcon } from "lucide-react";
import { format, subDays, subMonths } from "date-fns";
import { es } from "date-fns/locale";
import { useState } from "react";
import { cn } from "@/lib/utils";

export type DatePreset =
  | "last-7-days"
  | "last-14-days"
  | "last-21-days"
  | "last-30-days"
  | "last-60-days"
  | "last-90-days"
  | "last-3-months"
  | "last-6-months"
  | "custom";

interface PeriodSelectorProps {
  fechaDesde: Date | null;
  fechaHasta: Date | null;
  onPeriodChange: (desde: Date | null, hasta: Date | null) => void;
  maxDate?: Date;
}

export function PeriodSelector({
  fechaDesde,
  fechaHasta,
  onPeriodChange,
  maxDate = new Date(),
}: PeriodSelectorProps) {
  const [selectedPreset, setSelectedPreset] = useState<DatePreset>("custom");
  const [isOpen, setIsOpen] = useState(false);

  type PresetItem = { value: DatePreset; label: string };

  const presetGroups: { label: string; presets: PresetItem[] }[] = [
    {
      label: "Días",
      presets: [
        { value: "last-7-days", label: "Últimos 7 días" },
        { value: "last-14-days", label: "Últimos 14 días" },
        { value: "last-21-days", label: "Últimas 3 semanas" },
        { value: "last-30-days", label: "Últimos 30 días" },
        { value: "last-60-days", label: "Últimos 60 días" },
        { value: "last-90-days", label: "Últimos 90 días" },
      ],
    },
    {
      label: "Meses",
      presets: [
        { value: "last-3-months", label: "Últimos 3 meses" },
        { value: "last-6-months", label: "Últimos 6 meses" },
      ],
    },
  ];

  const presets: PresetItem[] = presetGroups.flatMap((group) => group.presets);

  const applyPreset = (preset: DatePreset) => {
    setSelectedPreset(preset);
    const today = maxDate;

    switch (preset) {
      case "last-7-days":
        onPeriodChange(subDays(today, 6), today);
        break;
      case "last-14-days":
        onPeriodChange(subDays(today, 13), today);
        break;
      case "last-21-days":
        onPeriodChange(subDays(today, 20), today);
        break;
      case "last-30-days":
        onPeriodChange(subDays(today, 29), today);
        break;
      case "last-60-days":
        onPeriodChange(subDays(today, 59), today);
        break;
      case "last-90-days":
        onPeriodChange(subDays(today, 89), today);
        break;
      case "last-3-months":
        onPeriodChange(subMonths(today, 3), today);
        break;
      case "last-6-months":
        onPeriodChange(subMonths(today, 6), today);
        break;
      case "custom":
        // Don't change the date range, just mark as custom
        break;
    }
  };

  const handleDateRangeChange = (range: { from?: Date; to?: Date } | undefined) => {
    setSelectedPreset("custom");
    onPeriodChange(range?.from || null, range?.to || null);
  };

  const formatDateRange = () => {
    if (!fechaDesde) return "Seleccionar período";

    if (selectedPreset !== "custom") {
      const preset = presets.find((p) => p.value === selectedPreset);
      if (preset && fechaHasta) {
        return `${preset.label} (${format(fechaDesde, "d MMM", {
          locale: es,
        })} - ${format(fechaHasta, "d MMM yyyy", { locale: es })})`;
      }
      return "Período personalizado";
    }

    if (!fechaHasta) {
      return format(fechaDesde, "dd MMM yyyy", { locale: es });
    }

    return `${format(fechaDesde, "dd MMM", { locale: es })} - ${format(
      fechaHasta,
      "dd MMM yyyy",
      { locale: es }
    )}`;
  };

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen} modal={true}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          className={cn(
            "w-full justify-start text-left font-normal",
            !fechaDesde && "text-muted-foreground"
          )}
        >
          <CalendarIcon className="mr-2 h-4 w-4 shrink-0" />
          <span className="truncate">{formatDateRange()}</span>
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0 z-[100]" align="start">
        <div className="flex">
          {/* Left side - Presets */}
          <div className="border-r">
            <div className="p-3 space-y-3 min-w-[200px]">
              {presetGroups.map((group, groupIndex) => (
                <div key={group.label}>
                  {groupIndex > 0 && <div className="border-t -mx-3 mb-3" />}
                  <div className="text-xs font-semibold text-muted-foreground mb-2 px-2">
                    {group.label}
                  </div>
                  <div className="space-y-1">
                    {group.presets.map((preset) => (
                      <Button
                        key={preset.value}
                        variant={
                          selectedPreset === preset.value
                            ? "secondary"
                            : "ghost"
                        }
                        className="w-full justify-start text-xs"
                        size="sm"
                        onClick={() => {
                          applyPreset(preset.value);
                          setIsOpen(false);
                        }}
                      >
                        <span className="font-medium">{preset.label}</span>
                      </Button>
                    ))}
                  </div>
                </div>
              ))}
              <div className="border-t -mx-3 pt-3">
                <Button
                  variant={
                    selectedPreset === "custom" ? "secondary" : "ghost"
                  }
                  className="w-full justify-start text-xs"
                  size="sm"
                  onClick={() => setSelectedPreset("custom")}
                >
                  Personalizado
                </Button>
              </div>
            </div>
          </div>

          {/* Right side - Calendar */}
          <div className="p-3">
            <Calendar
              mode="range"
              selected={
                fechaDesde && fechaHasta
                  ? { from: fechaDesde, to: fechaHasta }
                  : undefined
              }
              onSelect={(range) => {
                handleDateRangeChange(range);
                if (range?.from && range?.to) {
                  setIsOpen(false);
                }
              }}
              numberOfMonths={2}
              locale={es}
              toDate={maxDate}
            />
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}
