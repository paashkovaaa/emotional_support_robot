import { format, parseISO } from 'date-fns';
import { uk } from 'date-fns/locale';

/** Форматує дату у "28 березня 2026" */
export function formatDateLong(dateStr: string): string {
  return format(parseISO(dateStr), 'd MMMM yyyy', { locale: uk });
}

/** Форматує дату у "YYYY-MM-DD" */
export function toISODate(date: Date): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

/** Перевіряє чи дата — сьогодні */
export function isToday(date: Date): boolean {
  const now = new Date();
  return (
    date.getFullYear() === now.getFullYear() &&
    date.getMonth() === now.getMonth() &&
    date.getDate() === now.getDate()
  );
}

