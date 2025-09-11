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
  se1Start.setDate(se1Start.getDate() - ((firstThursday.getDay() + 1) % 7)); // domingo anterior

  if (date < se1Start) {
    return getEpiWeek(new Date(date.getFullYear() - 1, 11, 31)); // recursivo
  }

  const daysDiff = Math.floor((date.getTime() - se1Start.getTime()) / (1000 * 60 * 60 * 24));
  const week = Math.floor(daysDiff / 7) + 1;

  const epiYear = (week === 1) ? se1Start.getFullYear() : date.getFullYear();

  return { year: epiYear, week };
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
  se1Start.setDate(se1Start.getDate() - ((firstThursday.getDay() + 1) % 7));

  const start = new Date(se1Start);
  start.setDate(start.getDate() + (week - 1) * 7);
  const end = new Date(start);
  end.setDate(start.getDate() + 6);

  return { start, end };
}





