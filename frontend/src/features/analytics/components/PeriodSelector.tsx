"use client";

import { Calendar, ChevronDown, Check } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { cn } from "@/lib/utils";
import type { PeriodType } from "@/lib/api/analytics";

interface PeriodOption {
  value: PeriodType;
  label: string;
  description: string;
}

const PERIOD_OPTIONS: PeriodOption[] = [
  {
    value: "ultima_semana_epi",
    label: "Última semana epi",
    description: "Última semana epidemiológica completa",
  },
  {
    value: "ultimas_4_semanas_epi",
    label: "Últimas 4 semanas epi",
    description: "Últimas 4 semanas epidemiológicas",
  },
  {
    value: "ultimas_12_semanas_epi",
    label: "Últimas 12 semanas epi",
    description: "Últimas 12 semanas epidemiológicas",
  },
];

const YEAR_OPTIONS: PeriodOption[] = [
  {
    value: "anio_hasta_fecha",
    label: "Año hasta la fecha",
    description: "Del 1 de enero hasta hoy",
  },
  {
    value: "anio_pasado",
    label: "Año completo anterior",
    description: "Año anterior completo",
  },
];

interface PeriodSelectorProps {
  value: PeriodType;
  onChange: (period: PeriodType) => void;
  fechaReferencia?: Date;
  onFechaReferenciaChange?: (fecha: Date | undefined) => void;
  className?: string;
}

export function PeriodSelector({
  value,
  onChange,
  fechaReferencia,
  onFechaReferenciaChange,
  className,
}: PeriodSelectorProps) {
  const [open, setOpen] = useState(false);
  const [datePickerOpen, setDatePickerOpen] = useState(false);

  const selectedOption = [...PERIOD_OPTIONS, ...YEAR_OPTIONS].find(
    (opt) => opt.value === value
  );

  const formatDate = (date: Date | undefined) => {
    if (!date) return "Hoy";
    return new Intl.DateTimeFormat("es-AR", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    }).format(date);
  };

  const getDisplayLabel = () => {
    if (!selectedOption) return "Seleccionar período";
    if (fechaReferencia) {
      return `${selectedOption.label} al ${formatDate(fechaReferencia)}`;
    }
    return selectedOption.label;
  };

  return (
    <div className="flex gap-2">
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            role="combobox"
            aria-expanded={open}
            className={cn("w-[280px] justify-between", className)}
          >
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4" />
              <span>{getDisplayLabel()}</span>
            </div>
            <ChevronDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-[320px] p-4" align="start">
          <div className="space-y-4">
            {/* Semanas epidemiológicas */}
            <div>
              <h4 className="font-medium text-sm mb-2">
                Semanas epidemiológicas
              </h4>
              <div className="space-y-1">
                {PERIOD_OPTIONS.map((option) => (
                  <button
                    key={option.value}
                    className={cn(
                      "w-full flex items-start gap-3 rounded-md border p-3 text-left transition-colors",
                      "hover:bg-accent cursor-pointer",
                      value === option.value && "bg-accent border-primary"
                    )}
                    onClick={() => {
                      onChange(option.value);
                      setOpen(false);
                    }}
                  >
                    <div className="mt-0.5">
                      {value === option.value && (
                        <Check className="h-4 w-4 text-primary" />
                      )}
                      {value !== option.value && <div className="h-4 w-4" />}
                    </div>
                    <div className="flex-1 space-y-0.5">
                      <div className="font-medium text-sm">{option.label}</div>
                      <div className="text-xs text-muted-foreground">
                        {option.description}
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Períodos anuales */}
            <div>
              <h4 className="font-medium text-sm mb-2">Períodos anuales</h4>
              <div className="space-y-1">
                {YEAR_OPTIONS.map((option) => (
                  <button
                    key={option.value}
                    className={cn(
                      "w-full flex items-start gap-3 rounded-md border p-3 text-left transition-colors",
                      "hover:bg-accent cursor-pointer",
                      value === option.value && "bg-accent border-primary"
                    )}
                    onClick={() => {
                      onChange(option.value);
                      setOpen(false);
                    }}
                  >
                    <div className="mt-0.5">
                      {value === option.value && (
                        <Check className="h-4 w-4 text-primary" />
                      )}
                      {value !== option.value && <div className="h-4 w-4" />}
                    </div>
                    <div className="flex-1 space-y-0.5">
                      <div className="font-medium text-sm">{option.label}</div>
                      <div className="text-xs text-muted-foreground">
                        {option.description}
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </PopoverContent>
      </Popover>

      {/* Selector de fecha de referencia */}
      {onFechaReferenciaChange && (
        <Popover open={datePickerOpen} onOpenChange={setDatePickerOpen}>
          <PopoverTrigger asChild>
            <Button
              variant="outline"
              className={cn(
                "w-[200px] justify-start text-left font-normal",
                !fechaReferencia && "text-muted-foreground"
              )}
            >
              <Calendar className="mr-2 h-4 w-4" />
              {formatDate(fechaReferencia)}
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-auto p-4" align="end">
            <div className="space-y-3">
              <div className="text-sm font-medium">Fecha de referencia</div>
              <div className="text-xs text-muted-foreground">
                Selecciona una fecha para "viajar en el tiempo" y ver las métricas
                en ese momento histórico
              </div>
              <input
                type="date"
                className="w-full px-3 py-2 border rounded-md"
                max={new Date().toISOString().split("T")[0]}
                min="2022-01-01"
                value={
                  fechaReferencia
                    ? fechaReferencia.toISOString().split("T")[0]
                    : ""
                }
                onChange={(e) => {
                  if (e.target.value) {
                    onFechaReferenciaChange(new Date(e.target.value));
                  } else {
                    onFechaReferenciaChange(undefined);
                  }
                }}
              />
              <Button
                variant="outline"
                size="sm"
                className="w-full"
                onClick={() => {
                  onFechaReferenciaChange(undefined);
                  setDatePickerOpen(false);
                }}
              >
                Restablecer a hoy
              </Button>
            </div>
          </PopoverContent>
        </Popover>
      )}
    </div>
  );
}
