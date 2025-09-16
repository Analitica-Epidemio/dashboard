export interface EpiWeek {
  year: number;
  week: number;
  startDate: Date;
  endDate: Date;
}

/**
 * Devuelve la semana epidemiológica argentina para una fecha
 * (SE1 contiene el primer jueves de enero, semanas inician domingo).
 */
export function getEpiWeek(date: Date): { year: number; week: number } {
  const year = date.getFullYear();

  // Buscar el primer jueves de enero
  let firstThursday = new Date(year, 0, 1); // enero = 0
  while (firstThursday.getDay() !== 4) { // 4 = jueves
    firstThursday.setDate(firstThursday.getDate() + 1);
  }

  // Inicio de SE1 = domingo anterior al primer jueves
  const se1Start = new Date(firstThursday);
  se1Start.setDate(se1Start.getDate() - firstThursday.getDay()); // domingo anterior

  if (date < se1Start) {
    return getEpiWeek(new Date(date.getFullYear() - 1, 11, 31)); // recursivo
  }

  let weekStart = new Date(se1Start);
  let week = 1;

  while (true) {
    const weekEnd = new Date(weekStart);
    weekEnd.setDate(weekStart.getDate() + 6); // sábado

    if (date >= weekStart && date <= weekEnd) {
      return { year: weekStart.getFullYear(), week };
    }

    // avanzar a la siguiente semana
    weekStart.setDate(weekStart.getDate() + 7);
    week++;
	}
}

/**
 * Devuelve el rango de fechas (domingo-sábado) de una semana epidemiológica.
 */
export function epiWeekToDates(year: number, week: number): { start: Date; end: Date } {
  // Buscar primer jueves de enero
  let firstThursday = new Date(year, 0, 1);
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
