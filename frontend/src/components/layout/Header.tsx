import { useLocation } from 'react-router-dom';

interface HeaderProps {
  /** Заголовок поточної сторінки */
  title?: string;
  /** Підзаголовок */
  subtitle?: string;
  /** Іконка (React element) */
  icon?: React.ReactNode;
  /** Кнопки / елементи праворуч */
  actions?: React.ReactNode;
}

/** Маппінг маршрутів на заголовки за замовчуванням */
const ROUTE_TITLES: Record<string, { title: string; subtitle: string }> = {
  '/chat': { title: 'Чат з Emi', subtitle: 'Поговоримо про все, що хвилює' },
  '/emotions': { title: 'Щоденник емоцій', subtitle: 'Відстежуйте свій емоційний стан' },
  '/breathing': { title: 'Вправи на дихання', subtitle: 'Заспокойтесь та відновіть баланс' },
  '/profile': { title: 'Профіль', subtitle: 'Ваші налаштування та дані' },
  '/admin': { title: 'Адмін-панель', subtitle: 'Управління системою' },
};

export default function Header({ title, subtitle, icon, actions }: HeaderProps) {
  const location = useLocation();
  const routeInfo = ROUTE_TITLES[location.pathname];

  const displayTitle = title || routeInfo?.title || '';
  const displaySubtitle = subtitle || routeInfo?.subtitle || '';

  return (
    <header className="bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm border-b border-gray-100 dark:border-gray-800 sticky top-0 z-10">
      <div className="px-4 lg:px-6 py-3.5 flex items-center justify-between">
        {/* Ліва частина — залишаємо місце для мобільного меню */}
        <div className="flex items-center gap-3 pl-12 lg:pl-0">
          {icon && (
            <div className="w-9 h-9 bg-primary-50 dark:bg-primary-900/30 rounded-xl flex items-center justify-center flex-shrink-0">
              {icon}
            </div>
          )}
          <div>
            {displayTitle && (
              <h1 className="text-lg font-bold text-gray-800 dark:text-gray-100 leading-tight">
                {displayTitle}
              </h1>
            )}
            {displaySubtitle && (
              <p className="text-xs text-gray-500 dark:text-gray-400">{displaySubtitle}</p>
            )}
          </div>
        </div>

        {/* Права частина — actions */}
        <div className="flex items-center gap-2">

          {actions && <>{actions}</>}
        </div>
      </div>
    </header>
  );
}
