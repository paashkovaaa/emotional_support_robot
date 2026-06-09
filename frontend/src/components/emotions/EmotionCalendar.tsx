import { useMemo } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { MONTH_NAMES_UA, WEEKDAY_NAMES_UA } from '../../utils/constants';
import { toISODate, isToday } from '../../utils/formatters';
import type { EmotionEntry } from '../../types';

interface Props {
  month: number; // 1-12
  year: number;
  entries: EmotionEntry[];
  selectedDate: string | null;
  onSelectDate: (date: string) => void;
  onPrevMonth: () => void;
  onNextMonth: () => void;
}

export default function EmotionCalendar({
  month,
  year,
  entries,
  selectedDate,
  onSelectDate,
  onPrevMonth,
  onNextMonth,
}: Props) {
  // Маппа дата → emoji
  const emojiMap = useMemo(() => {
    const map = new Map<string, string>();
    for (const e of entries) {
      if (e.emoji) map.set(e.entry_date, e.emoji);
    }
    return map;
  }, [entries]);

  // Генеруємо дні календаря
  const calendarDays = useMemo(() => {
    const firstDay = new Date(year, month - 1, 1);
    const lastDay = new Date(year, month, 0);

    // День тижня першого дня (0=Нд, 1=Пн … 6=Сб) → конвертуємо в Пн-першим
    let startWeekday = firstDay.getDay() - 1;
    if (startWeekday < 0) startWeekday = 6;

    const days: Array<{ date: Date; inMonth: boolean }> = [];

    // Дні попереднього місяця
    for (let i = startWeekday - 1; i >= 0; i--) {
      const d = new Date(year, month - 1, -i);
      days.push({ date: d, inMonth: false });
    }

    // Дні поточного місяця
    for (let d = 1; d <= lastDay.getDate(); d++) {
      days.push({ date: new Date(year, month - 1, d), inMonth: true });
    }

    // Дні наступного місяця (добиваємо до повних рядків)
    const remaining = 7 - (days.length % 7);
    if (remaining < 7) {
      for (let d = 1; d <= remaining; d++) {
        days.push({ date: new Date(year, month, d), inMonth: false });
      }
    }

    return days;
  }, [month, year]);

  const isFuture = (date: Date) => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return date > today;
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
      {/* Заголовок з навігацією */}
      <div className="flex items-center justify-between mb-6">
        <button
          onClick={onPrevMonth}
          className="p-2 hover:bg-gray-100 rounded-xl transition-colors"
          aria-label="Попередній місяць"
        >
          <ChevronLeft className="w-5 h-5 text-gray-600" />
        </button>

        <h2 className="text-lg font-semibold text-gray-800">
          {MONTH_NAMES_UA[month - 1]} {year}
        </h2>

        <button
          onClick={onNextMonth}
          className="p-2 hover:bg-gray-100 rounded-xl transition-colors"
          aria-label="Наступний місяць"
        >
          <ChevronRight className="w-5 h-5 text-gray-600" />
        </button>
      </div>

      {/* Дні тижня */}
      <div className="grid grid-cols-7 gap-1 mb-2">
        {WEEKDAY_NAMES_UA.map((name) => (
          <div
            key={name}
            className="text-center text-xs font-medium text-gray-400 py-2"
          >
            {name}
          </div>
        ))}
      </div>

      {/* Дні місяця */}
      <div className="grid grid-cols-7 gap-1">
        {calendarDays.map(({ date, inMonth }, idx) => {
          const dateStr = toISODate(date);
          const emoji = emojiMap.get(dateStr);
          const today = isToday(date);
          const future = isFuture(date);
          const selected = selectedDate === dateStr;
          const hasEntry = entries.some((e) => e.entry_date === dateStr);

          return (
            <button
              key={idx}
              onClick={() => !future && inMonth && onSelectDate(dateStr)}
              disabled={future || !inMonth}
              className={`
                relative flex flex-col items-center justify-center
                aspect-square rounded-xl text-sm transition-all duration-150
                ${!inMonth ? 'text-gray-300 cursor-default' : ''}
                ${inMonth && !future ? 'hover:bg-primary-50 cursor-pointer' : ''}
                ${future ? 'text-gray-300 cursor-not-allowed' : ''}
                ${today ? 'ring-2 ring-primary-400 ring-offset-1' : ''}
                ${selected ? 'bg-primary-100 ring-2 ring-primary-500 ring-offset-1' : ''}
                ${hasEntry && !selected ? 'bg-gray-50' : ''}
              `}
            >
              <span className={`text-xs ${inMonth ? 'text-gray-700' : 'text-gray-300'}`}>
                {date.getDate()}
              </span>
              {emoji && (
                <span className="text-lg leading-none mt-0.5">{emoji}</span>
              )}
              {hasEntry && !emoji && (
                <span className="w-1.5 h-1.5 rounded-full bg-primary-400 mt-1" />
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}

