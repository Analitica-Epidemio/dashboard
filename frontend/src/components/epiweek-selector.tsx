import React from 'react';
import Calendar from 'react-calendar';
import 'react-calendar/dist/Calendar.css';
import { getEpiWeek, epiWeekToDates } from './epiUtils';

interface EpiCalendarProps {
  onWeekSelect: (epiData: {
    year: number;
    week: number;
    startDate: Date;
    endDate: Date;
  }) => void;
}

const EpiCalendar: React.FC<EpiCalendarProps> = ({ onWeekSelect }) => {
  const handleClick = (date: Date) => {
    const { year, week } = getEpiWeek(date);
    const { start, end } = epiWeekToDates(year, week);
    onWeekSelect({ year, week, startDate: start, endDate: end });
  };

  return (
    <Calendar
      onClickDay={handleClick}
      calendarType="US" // semanas comienzan en domingo
      tileContent={({ date }) => {
        const { week } = getEpiWeek(date);
        return <small>SE {week}</small>;
      }}
    />
  );
};

export default EpiCalendar;
