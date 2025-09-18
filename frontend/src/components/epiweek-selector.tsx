// Este componente está temporalmente deshabilitado
// No se usará react-calendar

import React from 'react';

interface EpiCalendarProps {
  onWeekSelect: (epiData: {
    year: number;
    week: number;
    startDate: Date;
    endDate: Date;
  }) => void;
}

const EpiCalendar: React.FC<EpiCalendarProps> = ({ onWeekSelect }) => {
  // Componente temporalmente deshabilitado
  return (
    <div>
      <p>Selector de semana epidemiológica no disponible</p>
    </div>
  );
};

export default EpiCalendar;