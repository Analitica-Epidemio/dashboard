import React, { useState, useEffect } from 'react';
import { getEpiWeek } from './epiweek-utils'; // Asegurate de tener esta función
import { ChevronRight, ChevronLeft, ChevronFirst, ChevronLast } from 'lucide-react';

function getCalendarWeeks(year: number, month: number) {
  const startOfMonth = new Date(year, month, 1);
  const endOfMonth = new Date(year, month + 1, 0);

  // Empezar desde el domingo anterior al primer día del mes
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

const MONTH_NAMES = [
  'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
];

interface EpiCalendarProps {
  onWeekSelect?: (date: Date) => void;
  selectedStart?: { year: number; week: number; startDate: Date; endDate: Date } | null;
  selectedEnd?: { year: number; week: number; startDate: Date; endDate: Date } | null;
  selectingEnd?: boolean;
}

export default function EpiCalendar({ onWeekSelect, selectedStart, selectedEnd, selectingEnd }: EpiCalendarProps) {
	const today = new Date();

	// Inicializar en el mes de la fecha seleccionada relevante
	const initialDate = selectingEnd ? (selectedEnd?.startDate || today) : (selectedStart?.startDate || today);
	const [currentYear, setCurrentYear] = useState(initialDate.getFullYear());
	const [currentMonth, setCurrentMonth] = useState(initialDate.getMonth());

	// Actualizar el mes mostrado cuando cambian las selecciones
	useEffect(() => {
		const relevantDate = selectingEnd ? selectedEnd?.startDate : selectedStart?.startDate;
		if (relevantDate) {
			setCurrentYear(relevantDate.getFullYear());
			setCurrentMonth(relevantDate.getMonth());
		}
	}, [selectedStart, selectedEnd, selectingEnd]);

	const weeks = getCalendarWeeks(currentYear, currentMonth);

	const handleSelect = (date: Date) => {
		onWeekSelect?.(date);
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
  
  const goToPrevYear = () => {
      setCurrentYear(currentYear - 1);
  };

  const goToNextYear = () => {
      setCurrentYear(currentYear + 1);
  };

  return (
    <div className="w-full">
      {/* Header con navegación */}
      <div className="flex items-center justify-between mb-4">
        <button
          onClick={goToPrevYear}
          className="p-1.5 hover:bg-accent rounded-md transition-colors"
          aria-label="Año anterior"
        >
          <ChevronFirst className="h-4 w-4 text-muted-foreground" />
        </button>
        <button
          onClick={goToPrevMonth}
          className="p-1.5 hover:bg-accent rounded-md transition-colors"
          aria-label="Mes anterior"
        >
          <ChevronLeft className="h-4 w-4 text-muted-foreground" />
        </button>
        <h3 className="text-sm font-semibold text-foreground min-w-[140px] text-center">
          {MONTH_NAMES[currentMonth]} {currentYear}
        </h3>
        <button
          onClick={goToNextMonth}
          className="p-1.5 hover:bg-accent rounded-md transition-colors"
          aria-label="Mes siguiente"
        >
          <ChevronRight className="h-4 w-4 text-muted-foreground" />
        </button>
        <button
          onClick={goToNextYear}
          className="p-1.5 hover:bg-accent rounded-md transition-colors"
          aria-label="Año siguiente"
        >
          <ChevronLast className="h-4 w-4 text-muted-foreground" />
        </button>
      </div>

      {/* Tabla del calendario */}
      <table className="w-full border-collapse">
        <thead>
          <tr>
            <th className="p-2 text-xs font-medium text-muted-foreground bg-muted/50 rounded-tl-md">
              SE
            </th>
            {['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'].map((day, idx) => (
              <th
                key={day}
                className={`p-2 text-xs font-medium text-muted-foreground bg-muted/50 text-center ${
                  idx === 6 ? 'rounded-tr-md' : ''
                }`}
              >
                {day}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {weeks.map((week, wIdx) => {
            const epiWeek = getEpiWeek(week[0]).week;
            return (
              <tr key={wIdx}>
                <td className="p-2 text-xs font-semibold text-center bg-muted/30 text-muted-foreground border-r border-border">
                  {epiWeek}
                </td>
                {week.map((date, dIdx) => {
                  const isCurrentMonth = date.getMonth() === currentMonth;
                  const isToday = date.toDateString() === today.toDateString();

                  // Determinar si está en el rango seleccionado
                  const isInRange = selectedStart && selectedEnd &&
                    date >= selectedStart.startDate && date <= selectedEnd.endDate;

                  // Determinar si es el inicio o fin del rango
                  const isStartWeek = selectedStart &&
                    date >= selectedStart.startDate && date <= selectedStart.endDate;
                  const isEndWeek = selectedEnd &&
                    date >= selectedEnd.startDate && date <= selectedEnd.endDate;

                  // Clases base
                  let cellClasses = 'p-2 text-center cursor-pointer transition-all border border-border';

                  // Semanas de inicio/fin (máxima prioridad)
                  if (isStartWeek || isEndWeek) {
                    cellClasses += ' bg-primary text-primary-foreground font-bold ring-2 ring-primary ring-inset hover:bg-primary/90';
                  }
                  // Rango entre fechas
                  else if (isInRange) {
                    cellClasses += ' bg-primary/10 hover:bg-accent hover:text-accent-foreground';
                  }
                  // Día de hoy
                  else if (isToday) {
                    cellClasses += ' font-semibold text-primary hover:bg-accent hover:text-accent-foreground';
                  }
                  // Días normales
                  else {
                    cellClasses += ' hover:bg-accent hover:text-accent-foreground';
                  }

                  // Color para días fuera del mes
                  if (!isCurrentMonth && !isStartWeek && !isEndWeek) {
                    cellClasses += ' text-muted-foreground bg-muted/20';
                  }

                  return (
                    <td
                      key={dIdx}
                      onClick={() => handleSelect(date)}
                      className={cellClasses}
                    >
                      <div className="w-8 h-8 flex items-center justify-center text-sm mx-auto">
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
