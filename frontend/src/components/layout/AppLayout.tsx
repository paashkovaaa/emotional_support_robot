import Sidebar from './Sidebar';
import Header from './Header';

interface AppLayoutProps {
  children: React.ReactNode;
  /** Заголовок для Header (опціонально, визначається автоматично з маршруту) */
  title?: string;
  subtitle?: string;
  icon?: React.ReactNode;
  /** Кнопки / елементи праворуч в Header */
  headerActions?: React.ReactNode;
  /** Вимкнути Header (наприклад для чату з власним header) */
  hideHeader?: boolean;
}

/**
 * Загальний каркас додатку: Sidebar + Header + Content.
 *
 * Використовується для всіх захищених сторінок.
 */
export default function AppLayout({
  children,
  title,
  subtitle,
  icon,
  headerActions,
  hideHeader = false,
}: AppLayoutProps) {
  return (
    <div className="h-screen overflow-hidden bg-gradient-to-br from-gray-50 to-primary-50/30 flex">
      {/* Sidebar */}
      <Sidebar />

      {/* Main area */}
      <div className="flex-1 flex flex-col min-w-0 min-h-0">
        {!hideHeader && (
          <Header title={title} subtitle={subtitle} icon={icon} actions={headerActions} />
        )}

        {/* Page content */}
        <main className="flex-1 overflow-auto min-h-0">
          {children}
        </main>
      </div>
    </div>
  );
}

