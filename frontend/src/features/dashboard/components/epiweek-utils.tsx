export interface EpiWeek {
  year: number;
  week: number;
  startDate: Date;
  endDate: Date;
}

/**
 * Devuelve el año y semana epidemiológica para una fecha
 */
export function getEpiWeek(date: Date): { year: number; week: number } {
  const year = date.getFullYear();

  // buscar primer jueves de enero
  let firstThursday = new Date(year, 0, 1);
  while (firstThursday.getDay() !== 4) {
    firstThursday.setDate(firstThursday.getDate() + 1);
  }
  const se1Start = new Date(firstThursday);
  se1Start.setDate(se1Start.getDate() - firstThursday.getDay()); // domingo anterior

  // buscar primer jueves del año siguiente
  let nextFirstThursday = new Date(year + 1, 0, 1);
  while (nextFirstThursday.getDay() !== 4) {
    nextFirstThursday.setDate(nextFirstThursday.getDate() + 1);
  }
  const nextSe1Start = new Date(nextFirstThursday);
  nextSe1Start.setDate(nextSe1Start.getDate() - nextFirstThursday.getDay());

  // caso: fecha pertenece al año anterior
  if (date < se1Start) {
    return getEpiWeek(new Date(year - 1, 12 - 1, 31)); // 31 de diciembre del anterior
  }

  // caso: fecha pertenece al año siguiente
  if (date >= nextSe1Start) {
    return getEpiWeek(new Date(year + 1, 0, 1)); // 1 de enero del siguiente
  }

  // calcular semanas
  let weekStart = new Date(se1Start);
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
  
}


/**
 * Devuelve el rango de fechas de una semana epidemiológica.
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
