"use client";

import { DayPicker } from "react-day-picker";
import "react-day-picker/dist/style.css";
import { es } from "date-fns/locale";
import { useEffect } from "react";

function getEpidemiologicalWeek(date: Date): { week: number; year: number } {
  // Para debug
  const dateStr = date.toISOString().split("T")[0];

  // Determinar el año epidemiológico basado en la fecha
  let epiYear = date.getFullYear();

  // Encontrar el primer sábado del año que tenga al menos 4 días en enero
  let firstSat = new Date(epiYear, 0, 1); // 1 de enero

  // Avanzar hasta el primer sábado
  while (firstSat.getDay() !== 6) {
    firstSat.setDate(firstSat.getDate() + 1);
  }

  // Si el primer sábado es antes del día 4, ir al siguiente sábado
  if (firstSat.getDate() < 4) {
    firstSat.setDate(firstSat.getDate() + 7);
  }

  // El domingo que inicia la semana 1 del año epidemiológico
  const week1Sunday = new Date(firstSat);
  week1Sunday.setDate(week1Sunday.getDate() - 6);

  // Si la fecha está antes del inicio de la semana 1, pertenece al año anterior
  if (date < week1Sunday) {
    // Recalcular para el año anterior
    epiYear = epiYear - 1;

    // Encontrar el primer sábado del año anterior
    firstSat = new Date(epiYear, 0, 1);
    while (firstSat.getDay() !== 6) {
      firstSat.setDate(firstSat.getDate() + 1);
    }
    if (firstSat.getDate() < 4) {
      firstSat.setDate(firstSat.getDate() + 7);
    }

    // Calcular el domingo de la semana 1 del año anterior
    const prevYearWeek1Sunday = new Date(firstSat);
    prevYearWeek1Sunday.setDate(prevYearWeek1Sunday.getDate() - 6);

    // Calcular número de semana desde el inicio del año anterior
    const msPerWeek = 7 * 24 * 60 * 60 * 1000;
    const weekNum =
      Math.floor((date.getTime() - prevYearWeek1Sunday.getTime()) / msPerWeek) +
      1;

    return { week: weekNum, year: epiYear };
  }

  // Calcular el número de semana para el año actual
  const msPerWeek = 7 * 24 * 60 * 60 * 1000;
  const weekNum =
    Math.floor((date.getTime() - week1Sunday.getTime()) / msPerWeek) + 1;

  // Verificar si excedemos las 52/53 semanas (año siguiente)
  if (weekNum > 52) {
    // Verificar si el año tiene 53 semanas
    const lastDayOfYear = new Date(epiYear, 11, 31);
    const lastDayWeek =
      Math.floor(
        (lastDayOfYear.getTime() - week1Sunday.getTime()) / msPerWeek
      ) + 1;

    if (weekNum > lastDayWeek) {
      return { week: 1, year: epiYear + 1 };
    }
  }

  return { week: weekNum, year: epiYear };
}

function getLastEpidemiologicalWeek(year: number): number {
  // El último día del año
  const lastDay = new Date(year, 11, 31);
  const epiWeek = getEpidemiologicalWeek(lastDay);
  return epiWeek.year === year ? epiWeek.week : 52;
}

export default function DemoPage() {
  useEffect(() => {
    console.log("DemoPage mounted");
    // Test del cálculo de semanas epidemiológicas
    const testDates = [
      new Date(2024, 11, 29), // 29 dic 2024
      new Date(2025, 0, 1), // 1 ene 2025
      new Date(2025, 0, 4), // 4 ene 2025
      new Date(2025, 0, 5), // 5 ene 2025
      new Date(2025, 0, 11), // 11 ene 2025
    ];

    testDates.forEach((date) => {
      const epi = getEpidemiologicalWeek(date);
      console.log(
        `${date.toLocaleDateString("es")} => SE${epi.week} del ${epi.year}`
      );
    });
  }, []);

  return (
    <div className="container mx-auto p-8">
      <h1 className="text-2xl font-bold mb-6">
        Calendario con Semanas Epidemiológicas
      </h1>

      <div className="bg-white rounded-lg shadow-lg p-6">
        <div
          style={{
            marginBottom: "1rem",
            padding: "1rem",
            background: "#f3f4f6",
            borderRadius: "0.5rem",
          }}
        >
          <p>Test de fechas clave para 2025:</p>
          <ul style={{ fontSize: "0.875rem", marginTop: "0.5rem" }}>
            <li>
              • Primer sábado de enero 2025: 4 de enero (tiene 4 días en enero,
              así que termina SE1)
            </li>
            <li>• SE1 de 2025: 29 dic 2024 - 4 ene 2025</li>
            <li>• SE2 de 2025: 5 ene - 11 ene 2025</li>
          </ul>
        </div>

        <DayPicker
          locale={es}
          weekStartsOn={0} // 0 = Domingo, crítico para semanas epidemiológicas
          showWeekNumber
          showOutsideDays
          components={{
            WeekNumber: (props) => {
              console.log("WeekNumber component props:", props);
              const { week } = props;

              if (!week || !week.days || week.days.length === 0) {
                console.log("No week.days provided");
                return <td>--</td>;
              }

              // Extraer las fechas de los días de la semana
              const dates = week.days.map((day) => day.date);

              // Usar el miércoles de la semana para determinar la semana epidemiológica
              const midWeekDate = dates[3] || dates[0];
              const epiData = getEpidemiologicalWeek(midWeekDate);

              // Debug: mostrar las fechas de la semana
              console.log(
                "Semana:",
                dates[0]?.toLocaleDateString(),
                "-",
                dates[6]?.toLocaleDateString(),
                "=> SE",
                epiData.week,
                "del",
                epiData.year
              );

              return (
                <td
                  className="rdp-week_number"
                  style={{
                    padding: "0.25rem",
                    textAlign: "center",
                    background: "#f9fafb",
                  }}
                >
                  <div
                    style={{
                      fontSize: "0.75rem",
                      fontWeight: "600",
                      color: "#1f2937",
                    }}
                  >
                    SE{epiData.week}
                    {epiData.year !== new Date().getFullYear() && (
                      <span
                        style={{
                          display: "block",
                          fontSize: "0.625rem",
                          color: "#6b7280",
                        }}
                      >
                        {epiData.year}
                      </span>
                    )}
                  </div>
                </td>
              );
            },
          }}
        />

        <div className="mt-6 p-4 bg-blue-50 rounded-lg">
          <h2 className="font-semibold text-blue-900 mb-2">
            Información sobre Semanas Epidemiológicas:
          </h2>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• Las semanas epidemiológicas van de domingo a sábado</li>
            <li>
              • La semana 1 termina el primer sábado de enero con al menos 4
              días en enero
            </li>
            <li>
              • Se usan para estandarizar reportes de vigilancia epidemiológica
            </li>
            <li>
              • Siguen el estándar CDC/MMWR (Morbidity and Mortality Weekly
              Report)
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
