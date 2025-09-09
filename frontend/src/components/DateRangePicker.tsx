/**
 * Date Range Picker Component
 * Modern date range selector with dual calendars and presets
 */

import React, { useState, useEffect } from 'react';
import { format, subDays, subMonths, subYears, startOfMonth, endOfMonth, startOfYear, endOfYear, isAfter, isBefore, isEqual } from 'date-fns';
import { es } from 'date-fns/locale';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { 
  Calendar,
  CalendarDays,
  Clock,
  ChevronLeft,
  ChevronRight,
  Check,
  X,
} from 'lucide-react';

interface DateRange {
  from: Date | null;
  to: Date | null;
}

interface DateRangePickerProps {
  value: DateRange;
  onChange: (range: DateRange) => void;
  className?: string;
}

interface PresetRange {
  label: string;
  value: () => DateRange;
  icon?: React.ReactNode;
}

const presetRanges: PresetRange[] = [
  {
    label: 'Hoy',
    value: () => ({
      from: new Date(),
      to: new Date(),
    }),
  },
  {
    label: 'Últimos 7 días',
    value: () => ({
      from: subDays(new Date(), 6),
      to: new Date(),
    }),
  },
  {
    label: 'Últimos 30 días',
    value: () => ({
      from: subDays(new Date(), 29),
      to: new Date(),
    }),
  },
  {
    label: 'Últimos 90 días',
    value: () => ({
      from: subDays(new Date(), 89),
      to: new Date(),
    }),
  },
  {
    label: 'Este mes',
    value: () => ({
      from: startOfMonth(new Date()),
      to: endOfMonth(new Date()),
    }),
  },
  {
    label: 'Mes pasado',
    value: () => {
      const lastMonth = subMonths(new Date(), 1);
      return {
        from: startOfMonth(lastMonth),
        to: endOfMonth(lastMonth),
      };
    },
  },
  {
    label: 'Últimos 6 meses',
    value: () => ({
      from: subMonths(new Date(), 5),
      to: new Date(),
    }),
  },
  {
    label: 'Este año',
    value: () => ({
      from: startOfYear(new Date()),
      to: new Date(),
    }),
  },
  {
    label: 'Último año',
    value: () => ({
      from: subYears(new Date(), 1),
      to: new Date(),
    }),
  },
];

// Simple Calendar Component
const SimpleCalendar: React.FC<{
  selectedDate: Date | null;
  onSelect: (date: Date) => void;
  month: Date;
  onMonthChange: (date: Date) => void;
  minDate?: Date;
  maxDate?: Date;
  rangeStart?: Date | null;
  rangeEnd?: Date | null;
  label: string;
}> = ({ selectedDate, onSelect, month, onMonthChange, minDate, maxDate, rangeStart, rangeEnd, label }) => {
  const monthStart = startOfMonth(month);
  const daysInMonth = new Date(month.getFullYear(), month.getMonth() + 1, 0).getDate();
  const firstDayOfWeek = monthStart.getDay();
  
  const days = [];
  for (let i = 0; i < firstDayOfWeek; i++) {
    days.push(null);
  }
  for (let i = 1; i <= daysInMonth; i++) {
    days.push(new Date(month.getFullYear(), month.getMonth(), i));
  }

  const isInRange = (date: Date) => {
    if (!rangeStart || !rangeEnd || !date) return false;
    return (isAfter(date, rangeStart) || isEqual(date, rangeStart)) && 
           (isBefore(date, rangeEnd) || isEqual(date, rangeEnd));
  };

  const isDisabled = (date: Date) => {
    if (!date) return true;
    if (minDate && isBefore(date, minDate)) return true;
    if (maxDate && isAfter(date, maxDate)) return true;
    return false;
  };

  return (
    <div className="p-3">
      <div className="mb-3">
        <div className="flex items-center justify-between mb-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => onMonthChange(subMonths(month, 1))}
            className="h-7 w-7"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <div className="text-center">
            <h3 className="text-sm font-semibold">
              {format(month, 'MMMM yyyy', { locale: es })}
            </h3>
            <p className="text-xs text-gray-500">{label}</p>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => onMonthChange(subMonths(month, -1))}
            className="h-7 w-7"
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-7 gap-1 mb-2">
        {['D', 'L', 'M', 'X', 'J', 'V', 'S'].map((day) => (
          <div key={day} className="text-center text-xs font-medium text-gray-500 py-1">
            {day}
          </div>
        ))}
      </div>

      <div className="grid grid-cols-7 gap-1">
        {days.map((date, index) => (
          <Button
            key={index}
            variant="ghost"
            size="icon"
            className={cn(
              "h-8 w-8 p-0 font-normal",
              !date && "invisible",
              date && isInRange(date) && "bg-blue-100 hover:bg-blue-200",
              date && selectedDate && isEqual(date, selectedDate) && "bg-blue-600 text-white hover:bg-blue-700",
              date && rangeStart && isEqual(date, rangeStart) && "bg-blue-600 text-white hover:bg-blue-700",
              date && rangeEnd && isEqual(date, rangeEnd) && "bg-blue-600 text-white hover:bg-blue-700",
            )}
            disabled={!date || isDisabled(date)}
            onClick={() => date && onSelect(date)}
          >
            {date?.getDate()}
          </Button>
        ))}
      </div>
    </div>
  );
};

export const DateRangePicker: React.FC<DateRangePickerProps> = ({
  value,
  onChange,
  className,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [tempRange, setTempRange] = useState<DateRange>(value);
  const [startMonth, setStartMonth] = useState(value.from || new Date());
  const [endMonth, setEndMonth] = useState(value.to || subMonths(new Date(), -1));
  const [activePreset, setActivePreset] = useState<string | null>(null);

  useEffect(() => {
    setTempRange(value);
  }, [value]);

  const handleStartDateSelect = (date: Date) => {
    if (!tempRange.to || isAfter(date, tempRange.to)) {
      setTempRange({ from: date, to: date });
    } else {
      setTempRange({ ...tempRange, from: date });
    }
    setActivePreset(null);
  };

  const handleEndDateSelect = (date: Date) => {
    if (!tempRange.from || isBefore(date, tempRange.from)) {
      setTempRange({ from: date, to: date });
    } else {
      setTempRange({ ...tempRange, to: date });
    }
    setActivePreset(null);
  };

  const handlePresetSelect = (preset: PresetRange) => {
    const range = preset.value();
    setTempRange(range);
    setActivePreset(preset.label);
    if (range.from) setStartMonth(range.from);
    if (range.to) setEndMonth(range.to);
  };

  const handleApply = () => {
    onChange(tempRange);
    setIsOpen(false);
  };

  const handleCancel = () => {
    setTempRange(value);
    setIsOpen(false);
    setActivePreset(null);
  };

  const formatDateRange = () => {
    if (!value.from || !value.to) return 'Seleccionar rango de fechas';
    
    if (isEqual(value.from, value.to)) {
      return format(value.from, 'd \'de\' MMMM, yyyy', { locale: es });
    }
    
    return `${format(value.from, 'd MMM', { locale: es })} - ${format(value.to, 'd MMM, yyyy', { locale: es })}`;
  };

  const getDaysCount = () => {
    if (!tempRange.from || !tempRange.to) return 0;
    const diff = tempRange.to.getTime() - tempRange.from.getTime();
    return Math.ceil(diff / (1000 * 60 * 60 * 24)) + 1;
  };

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>
        <Button 
          variant="outline" 
          className={cn(
            "justify-start text-left font-normal",
            !value.from && "text-muted-foreground",
            className
          )}
        >
          <CalendarDays className="mr-2 h-4 w-4" />
          {formatDateRange()}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0" align="start">
        <div className="flex">
          {/* Presets sidebar */}
          <div className="w-48 border-r border-gray-200 p-3">
            <h4 className="text-sm font-semibold mb-3">Rangos rápidos</h4>
            <div className="space-y-1">
              {presetRanges.map((preset) => (
                <Button
                  key={preset.label}
                  variant={activePreset === preset.label ? "default" : "ghost"}
                  size="sm"
                  className="w-full justify-start text-left"
                  onClick={() => handlePresetSelect(preset)}
                >
                  <Clock className="mr-2 h-3 w-3" />
                  {preset.label}
                </Button>
              ))}
            </div>
          </div>

          {/* Calendars */}
          <div>
            <div className="flex">
              {/* Start Date Calendar */}
              <SimpleCalendar
                label="Fecha de inicio"
                selectedDate={tempRange.from}
                onSelect={handleStartDateSelect}
                month={startMonth}
                onMonthChange={setStartMonth}
                maxDate={new Date()}
                rangeStart={tempRange.from}
                rangeEnd={tempRange.to}
              />

              {/* End Date Calendar */}
              <div className="border-l border-gray-200">
                <SimpleCalendar
                  label="Fecha de fin"
                  selectedDate={tempRange.to}
                  onSelect={handleEndDateSelect}
                  month={endMonth}
                  onMonthChange={setEndMonth}
                  minDate={tempRange.from || undefined}
                  maxDate={new Date()}
                  rangeStart={tempRange.from}
                  rangeEnd={tempRange.to}
                />
              </div>
            </div>

            {/* Footer */}
            <div className="border-t border-gray-200 p-3">
              <div className="flex items-center justify-between mb-3">
                <div className="text-sm">
                  {tempRange.from && tempRange.to ? (
                    <div className="flex items-center gap-2">
                      <Badge variant="outline">
                        {format(tempRange.from, 'd MMM', { locale: es })} - {format(tempRange.to, 'd MMM', { locale: es })}
                      </Badge>
                      <span className="text-gray-500">
                        {getDaysCount()} días
                      </span>
                    </div>
                  ) : (
                    <span className="text-gray-500">Selecciona un rango de fechas</span>
                  )}
                </div>
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  className="flex-1"
                  onClick={handleCancel}
                >
                  <X className="h-4 w-4 mr-1" />
                  Cancelar
                </Button>
                <Button
                  size="sm"
                  className="flex-1"
                  onClick={handleApply}
                  disabled={!tempRange.from || !tempRange.to}
                >
                  <Check className="h-4 w-4 mr-1" />
                  Aplicar
                </Button>
              </div>
            </div>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
};