import React, { useState } from 'react';
import { getEpiWeek } from './epiweek-utils'; // Asegurate de tener esta función
import { ChevronRight, ChevronLeft, ChevronFirst, ChevronLast } from 'lucide-react';

// 🧠 Utilidad: generar matriz de semanas (domingo a sábado)
function getCalendarWeeks(year: number, month: number) {
  const startOfMonth = new Date(year, month, 1);
  const endOfMonth = new Date(year, month + 1, 0);

  // Empezar desde el domingo anterior al primer día del mes
  const startDate = new Date(startOfMonth);
  startDate.setDate(startOfMonth.getDate() - startOfMonth.getDay());

  const weeks: Date[][] = [];
  let current = new Date(startDate);

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

// 🗓️ Meses en español (puede traducirse según necesidad)
const MONTH_NAMES = [
  'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
];

interface EpiCalendarProps {
  onWeekSelect?: (date: Date) => void;
}

export default function EpiCalendar({ onWeekSelect }: EpiCalendarProps) {
  const today = new Date();
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [currentYear, setCurrentYear] = useState(today.getFullYear());
  const [currentMonth, setCurrentMonth] = useState(today.getMonth());

  const weeks = getCalendarWeeks(currentYear, currentMonth);


  const handleSelect = (date: Date) => {
    setSelectedDate(date);
    onWeekSelect?.(date); // 👈 Avisamos al padre
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
    <div style={{ display: 'inline-block', fontFamily: 'sans-serif' }}>
      {/* 📅 Barra de navegación */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
		 <button onClick={goToPrevYear} style={{ background: 'none', border: 'none', cursor: 'pointer' }}>
			<ChevronFirst size={20}/>
		 </button>
        <button onClick={goToPrevMonth} style={{ background: 'none', border: 'none', cursor: 'pointer' }}>
			<ChevronLeft size={20}/>
        </button>
        <h3 style={{ margin: 0 }}>
          {MONTH_NAMES[currentMonth]} {currentYear}
        </h3>
        <button onClick={goToNextMonth} style={{ background: 'none', border: 'none', cursor: 'pointer' }}>
			<ChevronRight size={20}/>
        </button>
        <button onClick={goToNextYear} style={{ background: 'none', border: 'none', cursor: 'pointer' }}>
			<ChevronLast size={20}/>
        </button>
      </div>

      {/* 📆 Tabla del calendario */}
      <table style={{ borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            <th style={{ padding: '4px' }}>SE</th>
            {['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'].map((day) => (
              <th key={day} style={{ padding: '4px', textAlign: 'center' }}>{day}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {weeks.map((week, wIdx) => {
            const epiWeek = getEpiWeek(week[0]).week;
            return (
              <tr key={wIdx}>
                <td style={{ padding: '4px', fontWeight: 'bold', textAlign: 'center', backgroundColor: '#f0f0f0' }}>
                  SE {epiWeek}
                </td>
                {week.map((date, dIdx) => {
                  const isCurrentMonth = date.getMonth() === currentMonth;
                  const isSelected = selectedDate?.toDateString() === date.toDateString();

                  return (
                    <td
                      key={dIdx}
                      onClick={() => handleSelect(date)}
                      style={{
                        padding: '8px',
                        textAlign: 'center',
                        backgroundColor: isSelected ? '#d0eaff' : isCurrentMonth ? '#fff' : '#eee',
                        cursor: 'pointer',
                        border: '1px solid #ccc',
                        width: '40px',
                        height: '40px'
                      }}
                    >
                      {date.getDate()}
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
